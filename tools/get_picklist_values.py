"""
Get picklist values for a specific Salesforce field

This module provides functionality to retrieve and format picklist (dropdown) values
for any Salesforce field. It returns comprehensive details about each value including:
- API value (the value stored in the database)
- Label (the text shown to users in the UI)
- Whether the value is the default selection
- Whether the value is active or inactive

This is useful for understanding all possible values for dropdown fields in Salesforce
objects and for building integration validation logic.
"""

from sf_connection import get_connection
import logging

# Configure logging
logger = logging.getLogger("sf_mcp_server.get_picklist_values")


def get_picklist_values(object_name: str, field_name: str) -> str:
    """
    Get picklist values for a specific Salesforce field.

    This function retrieves all available values for a picklist or multi-select
    picklist field, including their labels, default status, and active status.
    Results are formatted as a markdown table for easy reading.

    Args:
        object_name: API name of the object (e.g., 'Account', 'Lead', 'Custom_Object__c')
        field_name: API name of the picklist field (e.g., 'Industry', 'Status', 'Custom_Field__c')

    Returns:
        Formatted markdown table with picklist values and their properties

    Examples:
        # Get Industry options for Account
        get_picklist_values("Account", "Industry")

        # Get Status values for Case
        get_picklist_values("Case", "Status")

        # Get picklist options for a custom field
        get_picklist_values("Custom_Object__c", "Custom_Picklist_Field__c")
    """
    logger.info(f"Getting picklist values for {object_name}.{field_name}")
    sf = get_connection()

    try:
        # Get object describe info
        logger.debug(f"Retrieving object describe for {object_name}")
        describe = sf.__getattr__(object_name).describe()

        # Find the specific field
        field = next((f for f in describe["fields"] if f["name"] == field_name), None)

        # Handle field not found
        if not field:
            logger.warning(f"Field '{field_name}' not found on object '{object_name}'")
            return f"Field '{field_name}' not found on object '{object_name}'."

        # Verify that the field is a picklist type
        if field["type"] not in ("picklist", "multipicklist"):
            logger.warning(
                f"Field '{field_name}' is not a picklist (type: {field['type']})"
            )
            return (
                f"Field '{field_name}' is not a picklist field (type: {field['type']})."
            )

        # Format results as a markdown table
        result = (
            f"Picklist values for {object_name}.{field_name} ({field['label']}):\n\n"
        )
        result += "| Value | Label | Default | Active |\n"
        result += "|-------|-------|---------|--------|\n"

        # Add each picklist value as a row in the table
        for value in field.get("picklistValues", []):
            # Format boolean properties as Yes/No for readability
            is_default = "Yes" if value.get("defaultValue", False) else "No"
            is_active = "Yes" if value.get("active", True) else "No"

            # Escape any pipe characters that might break table formatting
            val = str(value["value"]).replace("|", "\\|")
            label = str(value["label"]).replace("|", "\\|")

            # Add row to table
            result += f"| {val} | {label} | {is_default} | {is_active} |\n"

        logger.info(
            f"Retrieved {len(field.get('picklistValues', []))} picklist values for {object_name}.{field_name}"
        )
        return result

    except Exception as e:
        logger.error(
            f"Error getting picklist values for {object_name}.{field_name}: {str(e)}"
        )
        return f"Error getting picklist values for {object_name}.{field_name}: {str(e)}"
