"""
Get detailed schema information for a Salesforce object using direct REST API calls

This module provides functionality to retrieve comprehensive metadata for any
Salesforce object using direct REST API calls. It offers more detailed information
than the standard describe call, including all object properties, child relationships,
record types, and complete field metadata.

This is particularly useful when:
- You need the complete raw JSON metadata from Salesforce
- You need access to advanced metadata properties not available in simple describes
- You're troubleshooting object configurations or permissions
"""

from sf_connection import get_connection
import logging
import json

# Configure logging
logger = logging.getLogger("sf_mcp_server.describe_object_with_api")


def describe_object_with_api(object_name: str, raw_json: bool = False) -> str:
    """
    Get detailed schema information for a Salesforce object using direct REST API calls.

    This function retrieves complete object metadata directly from the Salesforce REST API,
    providing access to all available properties and metadata for the specified object.

    The describe includes:
    - Complete object properties and permissions
    - All field metadata with all available properties
    - Child relationships
    - Record types
    - Picklist values with all metadata

    When raw_json=True, it returns the complete unfiltered JSON response,
    which is useful for technical analysis or debugging.

    Args:
        object_name: API name of the object (e.g., 'Account', 'Contact', 'Custom_Object__c')
        raw_json: If True, returns the raw JSON response instead of formatted markdown (default: False)

    Returns:
        Formatted markdown with object schema details or raw JSON string if raw_json=True

    Examples:
        # Get formatted detailed schema for Account
        describe_object_with_api("Account")

        # Get raw JSON metadata for a custom object
        describe_object_with_api("Custom_Object__c", raw_json=True)

        # Get complete technical details for Opportunity
        describe_object_with_api("Opportunity")
    """
    logger.info(f"Describing Salesforce object {object_name} with direct API call")
    sf = get_connection()

    try:
        # Extract instance URL from base_url
        instance_url = sf.base_url.split("/services/data")[0]

        # Use the appropriate API version
        api_version = "v63.0"  # Update this as needed

        # Build the describe URL
        url = f"{instance_url}/services/data/{api_version}/sobjects/{object_name}/describe/"
        logger.debug(f"Making API request to: {url}")

        # Make the direct API call
        response = sf.session.get(url, headers=sf.headers)
        response.raise_for_status()

        # Get the full describe result with all metadata
        describe = response.json()
        logger.debug(f"Retrieved {len(describe)} metadata properties for {object_name}")

        # If raw_json is requested, return the complete JSON response as a formatted string
        if raw_json:
            logger.info(f"Returning raw JSON for {object_name}")
            return json.dumps(describe, indent=2)

        # Format basic object information
        result = f"## {describe['label']} ({describe['name']})\n\n"
        result += f"**Type:** {'Custom Object' if describe.get('custom', False) else 'Standard Object'}\n"
        result += f"**API Name:** {describe['name']}\n"
        result += f"**Label:** {describe['label']}\n"
        result += f"**Plural Label:** {describe.get('labelPlural', 'N/A')}\n"
        result += f"**Key Prefix:** {describe.get('keyPrefix', 'N/A')}\n"

        # Add all object properties
        result += "\n## Object Properties\n\n"
        result += "| Property | Value |\n"
        result += "|----------|-------|\n"

        # Include all boolean properties from the raw describe
        for prop in sorted(
            [p for p in describe.keys() if isinstance(describe[p], bool)]
        ):
            result += f"| {prop} | {describe[p]} |\n"

        # Add fields section
        if "fields" in describe:
            result += "\n## Fields\n\n"
            result += "| API Name | Label | Type | Required | Unique | External ID |\n"
            result += "|----------|-------|------|----------|--------|------------|\n"

            for field in describe["fields"]:
                required = "Yes" if not field.get("nillable", True) else "No"
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
                    result += "| Value | Label | Default | Active |\n"
                    result += "|-------|-------|---------|--------|\n"

                    for value in field["picklistValues"]:
                        is_default = "Yes" if value.get("defaultValue", False) else "No"
                        is_active = "Yes" if value.get("active", True) else "No"
                        result += f"| {value['value']} | {value['label']} | {is_default} | {is_active} |\n"

                    result += "\n"

        # Include child relationships
        if "childRelationships" in describe and describe["childRelationships"]:
            result += "\n## Child Relationships\n\n"
            result += "| Child Object | Relationship Name | Field | Cascade Delete |\n"
            result += "|-------------|------------------|-------|---------------|\n"

            for rel in describe["childRelationships"]:
                child_obj = rel.get("childSObject", "N/A")
                rel_name = (
                    rel.get("relationshipName", "N/A")
                    if rel.get("relationshipName")
                    else "N/A"
                )
                field = rel.get("field", "N/A")
                cascade = "Yes" if rel.get("cascadeDelete", False) else "No"

                result += f"| {child_obj} | {rel_name} | {field} | {cascade} |\n"

        # Include record types if present
        if "recordTypeInfos" in describe and describe["recordTypeInfos"]:
            result += "\n## Record Types\n\n"
            result += "| Record Type ID | Name | Developer Name | Default | Active |\n"
            result += "|---------------|------|----------------|---------|--------|\n"

            for rt in describe["recordTypeInfos"]:
                rt_id = rt.get("recordTypeId", "N/A")
                name = rt.get("name", "N/A")
                dev_name = rt.get("developerName", "N/A")
                is_default = (
                    "Yes" if rt.get("defaultRecordTypeMapping", False) else "No"
                )
                is_active = "Yes" if rt.get("available", False) else "No"

                result += (
                    f"| {rt_id} | {name} | {dev_name} | {is_default} | {is_active} |\n"
                )

        logger.info(f"Successfully described {object_name} with direct API")
        return result

    except Exception as e:
        logger.error(f"Error describing object {object_name} with direct API: {str(e)}")
        return f"Error describing object {object_name} with direct API: {str(e)}"
