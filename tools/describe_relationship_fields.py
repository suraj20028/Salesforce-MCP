"""
Get relationship fields for a Salesforce object

This module provides functionality to identify and describe all relationship fields
for any Salesforce object. It covers both incoming relationships (lookup/master-detail)
and outgoing relationships (child relationships).

The results include:
- Parent relationships: Fields on this object that reference other objects
- Child relationships: Fields on other objects that reference this object
- Field names, labels, and relationship types
- Cascade delete settings for relationships

This is useful for understanding object dependencies and data model architecture.
"""

from sf_connection import get_connection
import logging

# Configure logging
logger = logging.getLogger("sf_mcp_server.describe_relationship_fields")


def describe_relationship_fields(object_name: str) -> str:
    """
    Get detailed information about all relationship fields for a Salesforce object.

    This function retrieves and formats information about both parent relationships
    (lookup/master-detail fields on this object) and child relationships (fields on
    other objects that reference this object). The results are presented in
    markdown format for easy reading.

    Parent relationships show:
    - Field API name and label
    - Objects referenced by the field
    - Relationship name (used in SOQL queries)
    - Relationship type (Lookup vs Master-Detail)

    Child relationships show:
    - Child object API name
    - Relationship name
    - Field on child object
    - Whether cascade delete is enabled

    Args:
        object_name: API name of the object (e.g., 'Account', 'Contact', 'Custom_Object__c')

    Returns:
        Formatted markdown text with relationship field details

    Examples:
        # Get relationships for Account object
        describe_relationship_fields("Account")

        # Get relationships for a custom object
        describe_relationship_fields("Custom_Object__c")
    """
    logger.info(f"Describing relationship fields for object: {object_name}")
    sf = get_connection()

    try:
        # Get object describe info
        logger.debug(f"Retrieving object describe for {object_name}")
        describe = sf.__getattr__(object_name).describe()

        # Filter for reference fields (lookups and master-detail relationships)
        reference_fields = [
            f
            for f in describe["fields"]
            if f["type"] == "reference" and f.get("referenceTo")
        ]
        logger.debug(f"Found {len(reference_fields)} parent relationship fields")

        # Get child relationships (other objects that reference this one)
        child_relationships = describe.get("childRelationships", [])
        logger.debug(f"Found {len(child_relationships)} child relationships")

        # Prepare the markdown output
        result = (
            f"# Relationship Fields for {describe['label']} ({describe['name']})\n\n"
        )

        # Format parent relationships section
        if reference_fields:
            result += "## Lookup/Master-Detail Fields (Parent Relationships)\n\n"
            result += (
                "| API Name | Field Label | Related To | Relationship Name | Type |\n"
            )
            result += (
                "|----------|------------|-----------|------------------|------|\n"
            )

            for field in reference_fields:
                # Join multiple reference targets if a polymorphic lookup
                related_to = ", ".join(field["referenceTo"])
                rel_name = field.get("relationshipName", "N/A")

                # Determine relationship type based on nillable status
                # Non-nillable fields are master-detail relationships
                rel_type = "Master-Detail" if not field["nillable"] else "Lookup"

                result += f"| {field['name']} | {field['label']} | {related_to} | {rel_name} | {rel_type} |\n"
        else:
            result += "No parent relationship fields found.\n\n"

        # Format child relationships section
        if child_relationships:
            result += "\n## Child Relationships\n\n"
            result += (
                "| Child Object | Relationship Name | Field Name | Cascade Delete |\n"
            )
            result += "|-------------|------------------|-----------|---------------|\n"

            for rel in child_relationships:
                # Some child relationships may not have relationship names (system relationships)
                rel_name = (
                    rel.get("relationshipName", "N/A")
                    if rel.get("relationshipName")
                    else "N/A"
                )
                cascade = "Yes" if rel.get("cascadeDelete", False) else "No"
                result += f"| {rel['childSObject']} | {rel_name} | {rel['field']} | {cascade} |\n"
        else:
            result += "\nNo child relationships found.\n"

        logger.info(f"Successfully described relationships for {object_name}")
        return result

    except Exception as e:
        logger.error(
            f"Error describing relationship fields for {object_name}: {str(e)}"
        )
        return f"Error describing relationship fields for {object_name}: {str(e)}"
