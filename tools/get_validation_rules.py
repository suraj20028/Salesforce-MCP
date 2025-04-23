"""
Get validation rules for Salesforce objects

This module provides functionality to retrieve and format validation rules for any Salesforce object.
Validation rules enforce business logic and data quality by preventing records from being
saved if they don't meet specific criteria.

Functions:
- get_validation_rules: Retrieves validation rules for a specified object

The tool returns details such as:
- Rule names
- Active/inactive status
- Error messages shown to users
- Error display field locations
- Rule descriptions
"""

from sf_connection import get_connection
import logging

# Configure logging
logger = logging.getLogger("sf_mcp_server.validation_rules")


def get_validation_rules(object_name: str) -> str:
    """
    Get validation rules for a specific object using Tooling API.

    This function retrieves all validation rules defined for a Salesforce object,
    including both active and inactive rules. It returns a formatted markdown
    table with comprehensive details about each rule.

    Args:
        object_name: API name of the object (e.g., 'Account', 'Lead', 'Opportunity', 'Custom_Object__c')

    Returns:
        Formatted string with validation rule details in markdown table format

    Examples:
        # Get validation rules for Account object
        get_validation_rules("Account")

        # Get validation rules for a custom object
        get_validation_rules("Custom_Object__c")
    """
    logger.info(f"Retrieving validation rules for object: {object_name}")
    sf = get_connection()

    try:
        # Extract the instance URL from the base_url (which includes API version path)
        instance_url = sf.base_url.split("/services/data")[0]

        # Construct the Tooling API query URL
        url = f"{instance_url}/services/data/v63.0/tooling/query/"

        # Build SOQL query to retrieve validation rules
        # This query gets key details about validation rules for the specified object
        soql = f"""
            SELECT Id, ValidationName, Active, Description, 
                   EntityDefinition.DeveloperName, ErrorDisplayField, 
                   ErrorMessage 
            FROM ValidationRule 
            WHERE EntityDefinition.DeveloperName='{object_name}'
            ORDER BY ValidationName
        """

        # Set up request headers using the Salesforce session
        headers = sf.headers
        params = {"q": soql}

        # Execute the Tooling API request
        logger.debug(f"Executing SOQL query for validation rules: {soql}")
        response = sf.session.get(url, headers=headers, params=params)
        response.raise_for_status()
        result = response.json()

        # Handle case where no validation rules exist
        if not result.get("records"):
            logger.info(f"No validation rules found for {object_name}")
            return f"No validation rules found for {object_name}."

        # Format results as a markdown table
        logger.info(
            f"Found {len(result['records'])} validation rules for {object_name}"
        )
        output = (
            f"Found {len(result['records'])} validation rules for {object_name}:\n\n"
        )

        # Create table header
        output += "| Name | Active | Error Message | Error Field | Description |\n"
        output += "|------|--------|--------------|------------|-------------|\n"

        # Add each validation rule as a row in the table
        for rule in result["records"]:
            # Format the active status as Yes/No
            active = "Yes" if rule.get("Active", False) else "No"

            # Get error display field or default to N/A
            error_field = rule.get("ErrorDisplayField", "N/A")

            # Handle None values safely with default empty strings
            # Also escape pipe characters to prevent breaking markdown tables
            error_message = rule.get("ErrorMessage", "")
            if error_message is not None:
                error_message = error_message.replace("\n", " ").replace("|", "\\|")
            else:
                error_message = "N/A"

            description = rule.get("Description", "")
            if description is not None:
                # Truncate very long descriptions for readability in table
                if len(description) > 100:
                    description = description[:97] + "..."
                description = description.replace("\n", " ").replace("|", "\\|")
            else:
                description = "N/A"

            # Add the rule details to the output table
            output += f"| {rule.get('ValidationName', 'N/A')} | {active} | {error_message} | {error_field} | {description} |\n"

        return output

    except Exception as e:
        logger.error(f"Error retrieving validation rules: {str(e)}")
        return f"Error retrieving validation rules: {str(e)}"
