"""
Search for Salesforce objects by name pattern

This module provides functionality to search for Salesforce objects (standard and custom)
by matching patterns in their names or labels. This is useful for discovering available
objects in a Salesforce organization when you don't know the exact name.

Functions:
- search_objects: Search for Salesforce objects by name or label pattern
"""

from typing import Dict, List, Any, Optional
import logging
from sf_connection import get_connection

# Configure logging
logger = logging.getLogger("sf_mcp_server.search_objects")


def search_objects(pattern: str, include_fields: bool = False) -> str:
    """
    Search for Salesforce objects by name or label pattern.

    This function searches through all available objects in the Salesforce org
    and returns those whose API name or label contains any of the search terms.
    Results are returned as a formatted markdown table.

    The search is case-insensitive and supports multiple search terms (space-separated),
    matching objects that contain ANY of the provided terms.

    Args:
        pattern: Search pattern for object names (e.g., "account", "contact", "custom")
                 Can include multiple space-separated terms
        include_fields: Whether to include fields in the response (default: False)

    Returns:
        Formatted markdown table with matching objects showing:
        - API Name (the name used in code and API calls)
        - Label (the user-friendly display name in Salesforce UI)
        - Whether the object is custom or standard

    Examples:
        # Search for Account-related objects
        search_objects("account")

        # Search for custom objects
        search_objects("__c custom")

        # Search for objects related to orders or products
        search_objects("order product")
    """
    logger.info(f"Searching for Salesforce objects matching pattern: '{pattern}'")

    # Get connection to Salesforce
    sf = get_connection()

    # Get global describe (list of all objects)
    try:
        describe_global = sf.describe()
        logger.debug(
            f"Retrieved {len(describe_global['sobjects'])} objects from global describe"
        )
    except Exception as e:
        logger.error(f"Error retrieving global describe: {str(e)}")
        return f"Error retrieving Salesforce objects: {str(e)}"

    # Split the search pattern into individual terms for more flexible matching
    search_terms = pattern.lower().split()
    logger.debug(f"Using search terms: {search_terms}")

    # Filter objects based on search terms (match ANY term)
    matching_objects = [
        obj
        for obj in describe_global["sobjects"]
        if any(
            term in obj["name"].lower() or term in obj["label"].lower()
            for term in search_terms
        )
    ]

    # Handle case where no objects match
    if not matching_objects:
        logger.info(f"No objects found matching pattern: '{pattern}'")
        return f"No Salesforce objects found matching '{pattern}'."

    # Format results as a markdown table
    logger.info(f"Found {len(matching_objects)} objects matching pattern: '{pattern}'")
    result = (
        f"Found {len(matching_objects)} Salesforce objects matching '{pattern}':\n\n"
    )
    result += "| API Name | Label | Custom Object |\n"
    result += "|----------|-------|---------------|\n"

    # Add each matching object to the table
    for obj in matching_objects:
        is_custom = "Yes" if obj.get("custom", False) else "No"
        result += (
            f"| {obj.get('name', 'N/A')} | {obj.get('label', 'N/A')} | {is_custom} |\n"
        )

    return result
