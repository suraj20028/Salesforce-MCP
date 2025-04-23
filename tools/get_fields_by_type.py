"""
Get fields of a specific type for a Salesforce object

This module provides functionality to retrieve field metadata from any Salesforce object,
with optional filtering by field type. This is useful for:
- Finding all fields of a specific type (e.g., all picklists, all lookups)
- Getting a complete list of fields for an object with their key properties
- Understanding which fields are required, updateable, or custom

The results include field API names, labels, types, and other important attributes
presented in a clear markdown table format.
"""

from sf_connection import get_connection
import logging

# Configure logging
logger = logging.getLogger("sf_mcp_server.get_fields_by_type")


def get_fields_by_type(object_name: str, field_type: str = None) -> str:
    """
    Get fields of a specific type for a Salesforce object.

    This function retrieves metadata for fields from any Salesforce object,
    with optional filtering by field type. Results are presented as a markdown
    table showing key field properties including API names, labels, requirements,
    and custom status.

    Common Salesforce field types include:
    - string: Text fields
    - boolean: Checkboxes
    - picklist: Standard dropdown select fields
    - multipicklist: Multi-select dropdown fields
    - reference: Lookup or master-detail relationship fields
    - date: Date fields
    - datetime: Date and time fields
    - currency: Currency fields
    - percent: Percentage fields
    - phone: Phone number fields
    - email: Email fields

    Args:
        object_name: API name of the object (e.g., 'Account', 'Contact', 'Custom_Object__c')
        field_type: Type to filter fields by (e.g., 'picklist', 'reference', etc.)
                   If None or empty, returns all fields

    Returns:
        Formatted markdown table with field details

    Examples:
        # Get all fields for the Account object
        get_fields_by_type("Account")

        # Get only picklist fields for the Lead object
        get_fields_by_type("Lead", "picklist")

        # Get all lookup/master-detail fields for a custom object
        get_fields_by_type("Custom_Object__c", "reference")
    """
    logger.info(
        f"Getting fields for object {object_name}"
        + (f" of type {field_type}" if field_type else "")
    )

    sf = get_connection()

    try:
        # Get object describe info
        logger.debug(f"Retrieving object describe for {object_name}")
        describe = sf.__getattr__(object_name).describe()
        fields = describe["fields"]
        logger.debug(f"Retrieved {len(fields)} fields for {object_name}")

        # Filter by type if specified
        if field_type:
            logger.debug(f"Filtering fields by type: {field_type}")
            fields = [f for f in fields if f["type"].lower() == field_type.lower()]
            logger.debug(f"Found {len(fields)} fields of type {field_type}")

            if not fields:
                logger.info(
                    f"No fields of type '{field_type}' found on object '{object_name}'"
                )
                return (
                    f"No fields of type '{field_type}' found on object '{object_name}'."
                )

        # Format results as a markdown table
        if field_type:
            result = f"# {field_type.capitalize()} Fields on {describe['label']} ({describe['name']})\n\n"
        else:
            result = f"# All Fields on {describe['label']} ({describe['name']})\n\n"

        result += "| API Name | Label | Type | Required | Updateable | Custom | Description |\n"
        result += "|----------|-------|------|----------|------------|--------|-------------|\n"

        # Sort fields by name for consistent output
        fields.sort(key=lambda f: f["name"])

        for field in fields:
            # Format boolean properties as Yes/No for readability
            required = "Yes" if not field["nillable"] else "No"
            updateable = "Yes" if field["updateable"] else "No"
            custom = "Yes" if field["custom"] else "No"

            # Clean up description text for table formatting
            description = field.get("inlineHelpText", "")
            if description:
                # Remove newlines and escape pipe characters that would break markdown tables
                description = description.replace("\n", " ").replace("|", "\\|")

            # Add field to table
            result += f"| {field['name']} | {field['label']} | {field['type']} | {required} | {updateable} | {custom} | {description} |\n"

        logger.info(f"Successfully returned {len(fields)} fields for {object_name}")
        return result

    except Exception as e:
        logger.error(f"Error getting fields for {object_name}: {str(e)}")
        return f"Error getting fields for {object_name}: {str(e)}"
