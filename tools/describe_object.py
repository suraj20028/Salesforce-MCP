"""
Get detailed schema information for a Salesforce object

This module provides functionality to retrieve and format detailed metadata
for any Salesforce object (standard or custom). The information includes:
- Basic object properties (label, API name, CRUD permissions)
- Field definitions and properties
- Relationship fields
- Picklist values

This is useful for understanding the structure of Salesforce objects, their
available fields, and relationships to other objects in the system.
"""

from sf_connection import get_connection
import logging

# Configure logging
logger = logging.getLogger("sf_mcp_server.describe_object")


def describe_object(object_name: str, include_field_details: bool = True) -> str:
    """
    Get detailed schema information for a Salesforce object.

    This function retrieves comprehensive metadata about a specified object,
    including its fields, relationships, and properties. The result is formatted
    as markdown text for easy reading.

    The describe includes:
    - Basic object information (label, API name, custom status)
    - CRUD permissions (createable, updateable, deletable)
    - Complete field list with data types and properties
    - Relationship fields with related objects
    - Picklist fields with their available values

    Args:
        object_name: API name of the object (e.g., 'Account', 'Contact', 'Custom_Object__c')
        include_field_details: Whether to include detailed field information (default: True)

    Returns:
        Formatted markdown text with object schema details

    Examples:
        # Get schema for the Account object
        describe_object("Account")

        # Get schema for a custom object
        describe_object("Custom_Object__c")

        # Get only basic object info without field details
        describe_object("Opportunity", include_field_details=False)
    """
    logger.info(f"Describing Salesforce object: {object_name}")
    sf = get_connection()

    try:
        # Get object describe info using the Salesforce API
        logger.debug(f"Fetching describe information for {object_name}")
        describe = sf.__getattr__(object_name).describe()
        logger.info(f"Successfully retrieved metadata for {object_name}")

        # Format basic object information section
        result = f"## {describe['label']} ({describe['name']})\n\n"
        result += f"**Type:** {'Custom Object' if describe['custom'] else 'Standard Object'}\n"
        result += f"**API Name:** {describe['name']}\n"
        result += f"**Label:** {describe['label']}\n"
        result += f"**Plural Label:** {describe['labelPlural']}\n"
        result += f"**Key Prefix:** {describe.get('keyPrefix', 'N/A')}\n"
        result += f"**Createable:** {describe['createable']}\n"
        result += f"**Updateable:** {describe['updateable']}\n"
        result += f"**Deletable:** {describe['deletable']}\n\n"

        # Only include detailed field information if requested
        if include_field_details:
            # Format fields table
            result += "## Fields\n\n"
            result += "| API Name | Label | Type | Required | Unique | External ID |\n"
            result += "|----------|-------|------|----------|--------|------------|\n"

            for field in describe["fields"]:
                required = "Yes" if not field["nillable"] else "No"
                unique = "Yes" if field.get("unique", False) else "No"
                external_id = "Yes" if field.get("externalId", False) else "No"

                result += f"| {field['name']} | {field['label']} | {field['type']} | {required} | {unique} | {external_id} |\n"

            # Add reference fields section if there are any
            reference_fields = [
                f
                for f in describe["fields"]
                if f["type"] == "reference" and f.get("referenceTo")
            ]
            if reference_fields:
                result += "\n## Relationship Fields\n\n"
                result += "| API Name | Related To | Relationship Name |\n"
                result += "|----------|-----------|-------------------|\n"

                for field in reference_fields:
                    related_to = ", ".join(field["referenceTo"])
                    rel_name = field.get("relationshipName", "N/A")
                    result += f"| {field['name']} | {related_to} | {rel_name} |\n"

            # Add picklist fields section if there are any
            picklist_fields = [
                f
                for f in describe["fields"]
                if f["type"] in ("picklist", "multipicklist")
                and f.get("picklistValues")
            ]
            if picklist_fields:
                result += "\n## Picklist Fields\n\n"

                for field in picklist_fields:
                    result += f"### {field['label']} ({field['name']})\n\n"
                    result += "| Value | Label | Default |\n"
                    result += "|-------|-------|--------|\n"

                    for value in field["picklistValues"]:
                        is_default = "Yes" if value.get("defaultValue", False) else "No"
                        result += (
                            f"| {value['value']} | {value['label']} | {is_default} |\n"
                        )

                    result += "\n"

        return result

    except Exception as e:
        logger.error(f"Error describing object {object_name}: {str(e)}")
        return f"Error describing object {object_name}: {str(e)}"
