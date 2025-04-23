# basic import
from mcp.server.fastmcp import FastMCP, Context
import math
import requests
import datetime
from typing import Dict, List, Any, Optional
import logging
import sys

# Import our organized Salesforce tools
from tools import (
    search_objects,
    describe_object,
    describe_object_with_api,
    get_picklist_values,
    describe_relationship_fields,
    get_fields_by_type,
    query_records,
    get_validation_rules,
    manage_debug_logs,
)
from sf_connection import get_connection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("sf_mcp_server.log"), logging.StreamHandler()],
)
logger = logging.getLogger("sf_mcp_server")

# =================================================================
# MCP Server Initialization
# =================================================================
# The FastMCP class creates a Model Context Protocol server that exposes
# Salesforce API functionality through tools, resources, and prompts
# =================================================================

mcp = FastMCP(
    "Salesforce MCP Server",
    description="A server providing Salesforce API integration tools through the Model Context Protocol",
)

# =================================================================
# SALESFORCE OBJECTS AND SCHEMA TOOLS
# =================================================================
# These tools allow users to explore Salesforce object schemas, search
# for objects, examine field definitions, and understand relationships
# =================================================================


@mcp.tool()
def search_salesforce_objects(pattern: str, sandbox: bool = True) -> str:
    """
    Search for Salesforce standard and custom objects by name pattern.

    This tool allows you to quickly find Salesforce objects (standard or custom) by
    searching for patterns in their names. It's useful when you're not sure about
    the exact name of an object or want to discover related objects.

    Examples:
    - "Search for Account related objects"
    - "Find all objects with 'Order' in their name"
    - "Look for custom objects related to Billing"

    Args:
        pattern: The search pattern to match object names (e.g., 'Account', 'Order')
        sandbox: Whether to connect to sandbox (True) or production (False)

    Returns:
        A formatted list of matching Salesforce objects
    """
    try:
        logger.info(f"Searching for Salesforce objects with pattern: {pattern}")
        result = search_objects(pattern)
        return result
    except Exception as e:
        logger.error(f"Error searching Salesforce objects: {str(e)}")
        return f"Error searching Salesforce objects: {str(e)}"


@mcp.tool()
def describe_salesforce_object(object_name: str) -> str:
    """
    Get detailed schema metadata including all fields, relationships, and field properties of any Salesforce object.

    This tool provides a comprehensive view of an object's structure including:
    - Field names and types
    - Required/optional status
    - Lookup and master-detail relationships
    - Custom field attributes
    - Field-level help text and descriptions

    Examples:
    - 'Account' shows all Account fields including custom fields
    - 'Case' shows all Case fields including relationships to Account, Contact etc.
    - 'Custom_Object__c' shows the structure of a custom object
    - 'Describe the OpportunityLineItem object structure'
    - 'What fields are on the Campaign object?'

    Args:
        object_name: API name of the object (e.g., 'Account', 'Contact', 'Custom_Object__c')

    Returns:
        Detailed schema information for the object
    """
    try:
        logger.info(f"Describing Salesforce object: {object_name}")
        return describe_object(object_name)
    except Exception as e:
        logger.error(f"Error describing object {object_name}: {str(e)}")
        return f"Error describing object {object_name}: {str(e)}"


@mcp.tool()
def describe_salesforce_object_raw_json(object_name: str) -> str:
    """
    Get the complete Salesforce object schema as raw JSON.
    This returns the unfiltered API response directly from Salesforce.

    This tool is useful when you need the complete, detailed metadata for advanced
    analysis or when you need to access specific metadata properties not included
    in the standard describe format.

    Examples:
    - Get raw JSON schema for Lead
    - Show complete API response for Account object
    - Return full JSON metadata for Custom_Object__c
    - "I need the complete metadata schema for Opportunity in JSON format"
    - "Show me all the technical metadata details for Account"

    Args:
        object_name: API name of the object (e.g., 'Account', 'Contact', 'Custom_Object__c')

    Returns:
        Complete raw JSON schema from Salesforce API
    """
    try:
        logger.info(f"Getting raw JSON schema for object: {object_name}")
        return describe_object_with_api(object_name, raw_json=True)
    except Exception as e:
        logger.error(f"Error retrieving raw JSON for {object_name}: {str(e)}")
        return f"Error retrieving raw JSON for {object_name}: {str(e)}"


@mcp.tool()
def get_salesforce_picklist_values(object_name: str, field_name: str) -> str:
    """
    Get all values from a picklist field.

    This tool returns all available options for a dropdown/picklist field, including:
    - Value labels
    - API names
    - Default value indicator
    - Active/inactive status
    - Controlling field dependencies (if any)

    Examples:
    - Get all Case Status values
    - Show picklist values for Lead.Source
    - List all values for Account.Type
    - "What are the available Industry options for Account?"
    - "Show me all the possible values for Opportunity Stage"
    - "What picklist values can I use for Case Priority?"

    Args:
        object_name: API name of the object (e.g., 'Case', 'Lead')
        field_name: API name of the picklist field (e.g., 'Status', 'Source')

    Returns:
        List of picklist values with their properties
    """
    try:
        logger.info(f"Getting picklist values for {object_name}.{field_name}")
        return get_picklist_values(object_name, field_name)
    except Exception as e:
        logger.error(f"Error getting picklist values: {str(e)}")
        return f"Error getting picklist values for {object_name}.{field_name}: {str(e)}"


@mcp.tool()
def describe_salesforce_relationship_fields(object_name: str) -> str:
    """
    Show all relationship fields (lookups, master-detail) for a Salesforce object.

    This tool identifies all relationship fields, showing:
    - Parent and child relationships
    - Lookup vs master-detail relationship types
    - Related object names
    - Cascade delete behavior
    - Required relationship status

    This is useful for understanding dependencies and connections between objects.

    Examples:
    - List all related objects for Opportunity
    - Show relationships in Contact object
    - Describe references in Case object
    - "What objects are related to Account?"
    - "Show me all the lookup relationships on the Contact object"
    - "What are the parent-child relationships for Opportunity?"

    Args:
        object_name: API name of the object (e.g., 'Opportunity', 'Contact')

    Returns:
        Detailed information about relationship fields
    """
    try:
        logger.info(f"Describing relationship fields for: {object_name}")
        return describe_relationship_fields(object_name)
    except Exception as e:
        logger.error(f"Error describing relationship fields: {str(e)}")
        return f"Error describing relationship fields for {object_name}: {str(e)}"


@mcp.tool()
def get_salesforce_fields_by_type(object_name: str, field_type: str = None) -> str:
    """
    Get fields of a specific type for a Salesforce object.
    If no type is specified, returns all fields.

    This tool allows you to filter fields by their data type, which is useful when
    you're looking for specific kinds of fields such as:
    - Text fields (string)
    - Number fields (double, integer)
    - Date/time fields
    - Picklist fields
    - Reference/lookup fields
    - Formula fields
    - And more

    Examples:
    - Show all picklist fields in Lead
    - Get all reference fields in Account
    - List all text fields in Contact
    - Get all fields in Opportunity
    - "Find all datetime fields on the Event object"
    - "What currency fields exist in the Opportunity object?"
    - "Show me all formula fields on the Account object"

    Args:
        object_name: API name of the object (e.g., 'Lead', 'Account')
        field_type: Optional type to filter fields by (e.g., 'picklist', 'reference', 'string')

    Returns:
        Table of fields with their properties
    """
    try:
        logger.info(
            f"Getting fields for {object_name}, type filter: {field_type or 'None'}"
        )
        return get_fields_by_type(object_name, field_type)
    except Exception as e:
        logger.error(f"Error getting fields by type: {str(e)}")
        return f"Error getting fields for {object_name}: {str(e)}"


# =================================================================
# SALESFORCE QUERY TOOLS
# =================================================================
# These tools allow users to query Salesforce records using SOQL
# with filtering, sorting, and other options
# =================================================================


@mcp.tool()
def query_salesforce_records(
    object_name: str,
    fields: List[str],
    where_clause: Optional[str] = None,
    order_by: Optional[str] = None,
    limit: Optional[int] = 10,
) -> str:
    """
    Query Salesforce records using SOQL with filtering, sorting, and limiting options.

    This tool enables you to retrieve records from any Salesforce object with:
    - Specific field selection
    - Optional WHERE filtering conditions
    - Optional sorting (ORDER BY)
    - Limit on number of records returned

    Results are returned in a well-formatted table for easy reading.

    Examples:
    - Get all Accounts created this month
    - Find Opportunities over $100,000
    - Show high-priority Cases with their Contacts
    - "Show me the last 5 Accounts created"
    - "Find all Opportunities worth more than $50,000 closing this month"
    - "List Contacts with the title 'CEO' sorted by company name"

    Args:
        object_name: API name of the object to query (e.g., 'Account', 'Opportunity')
        fields: List of fields to retrieve
        where_clause: Optional filtering criteria
        order_by: Optional sorting criteria
        limit: Maximum number of records to return (default: 10)

    Returns:
        Query results in a formatted table
    """
    try:
        # Validate inputs
        if not object_name or not object_name.strip():
            return "Error: Object name is required"

        if not fields or len(fields) == 0:
            return "Error: At least one field must be specified"

        # Validate and sanitize limit
        if limit is not None:
            if limit < 1:
                limit = 1
            elif limit > 100:
                limit = 100  # Cap at reasonable maximum

        logger.info(f"Querying {object_name} records. Fields: {fields}, Limit: {limit}")
        return query_records(object_name, fields, where_clause, order_by, limit)
    except Exception as e:
        logger.error(f"Error querying records: {str(e)}")
        return f"Error querying {object_name} records: {str(e)}"


# =================================================================
# SALESFORCE VALIDATION RULES & DEBUG LOGS
# =================================================================
# These tools provide access to validation rules and debug logging
# functionality to help with troubleshooting and understanding
# business logic enforced at the object level
# =================================================================


@mcp.tool()
def get_salesforce_validation_rules(object_name: str) -> str:
    """
    Get validation rules for a specific Salesforce object.

    This tool retrieves all validation rules for an object, including:
    - Rule name and status (active/inactive)
    - Error messages shown to users
    - Fields where errors display
    - Rule descriptions

    Validation rules enforce data quality by preventing records from being saved
    if they don't meet specific criteria.

    Examples:
    - Get all validation rules for the Lead object
    - Show validation rules for Opportunity
    - List active validations for Account
    - "What validation rules are enforced on the Contact object?"
    - "Show me all the data quality rules for Opportunity"
    - "List the validation conditions for Account records"

    Args:
        object_name: API name of the object (e.g., 'Account', 'Lead', 'Opportunity')

    Returns:
        List of validation rules with their details
    """
    try:
        if not object_name or not object_name.strip():
            return "Error: Object name is required"

        logger.info(f"Getting validation rules for: {object_name}")
        return get_validation_rules(object_name)
    except Exception as e:
        logger.error(f"Error retrieving validation rules: {str(e)}")
        return f"Error retrieving validation rules for {object_name}: {str(e)}"


@mcp.tool()
def manage_salesforce_debug_logs(
    operation: str,
    username: str,
    log_level: Optional[str] = None,
    expiration_time: Optional[int] = 30,
    limit: Optional[int] = 10,
    log_id: Optional[str] = None,
    include_body: Optional[bool] = False,
) -> str:
    """
    Manage debug logs for Salesforce users - enable, disable, or retrieve logs.

    This tool helps with troubleshooting by managing debug logging for specific users.
    You can:
    - Enable logging to capture debug information
    - Disable logging when finished troubleshooting
    - Retrieve and view logs to analyze issues
    - Configure the level of detail in logs

    Debug logs are crucial for troubleshooting code execution, integrations,
    automations, and other Salesforce functionality.

    Examples:
    - Enable debug logs for a user: provide 'enable' operation, username, and log level
    - Disable debug logs for a user: provide 'disable' operation and username
    - Retrieve debug logs for a user: provide 'retrieve' operation and username
    - Retrieve a specific log with full content: provide 'retrieve' operation, username, log_id, and include_body=True
    - "Enable debug logs for admin@example.com at FINEST level"
    - "Disable debug logging for user.name@company.com"
    - "Get recent debug logs for the system administrator"
    - "Show me the debug log content for log ID 07L000000..."

    Args:
        operation: Operation to perform - 'enable', 'disable', or 'retrieve'
        username: Username of the Salesforce user
        log_level: Log level for debug logs (required for 'enable' operation)
                   Valid options: NONE, ERROR, WARN, INFO, DEBUG, FINE, FINER, FINEST
        expiration_time: Minutes until the debug log configuration expires (optional, defaults to 30)
        limit: Maximum number of logs to retrieve (optional, defaults to 10)
        log_id: ID of a specific log to retrieve (optional)
        include_body: Whether to include the full log content (optional, defaults to False)

    Returns:
        Formatted string with the result of the operation
    """
    try:
        logger.info(f"Managing debug logs: {operation} for {username}")
        return manage_debug_logs(
            operation=operation,
            username=username,
            log_level=log_level,
            expiration_time=expiration_time,
            limit=limit,
            log_id=log_id,
            include_body=include_body,
        )
    except Exception as e:
        logger.error(f"Error managing debug logs: {str(e)}")
        return f"Error managing debug logs: {str(e)}"


# =================================================================
# SALESFORCE RESOURCES
# =================================================================
# These resources allow direct access to Salesforce schemas and
# picklist values through MCP resource URIs
# =================================================================


@mcp.resource("salesforce://schema/{object_name}")
def get_object_schema_resource(object_name: str) -> str:
    """
    Get schema for a Salesforce object

    This resource provides direct access to Salesforce object schemas
    through a URI format. It returns detailed field information for
    the specified object.
    """
    try:
        logger.info(f"Resource request: Schema for {object_name}")
        return describe_object(object_name, include_field_details=True)
    except Exception as e:
        logger.error(f"Error serving schema resource: {str(e)}")
        return f"Error retrieving schema for {object_name}: {str(e)}"


@mcp.resource("salesforce://picklist/{object_name}/{field_name}")
def get_picklist_resource(object_name: str, field_name: str) -> str:
    """
    Get picklist values for a specific field

    This resource provides direct access to Salesforce picklist values
    through a URI format. It returns all available picklist values
    for the specified object field.
    """
    try:
        logger.info(f"Resource request: Picklist values for {object_name}.{field_name}")
        return get_picklist_values(object_name, field_name)
    except Exception as e:
        logger.error(f"Error serving picklist resource: {str(e)}")
        return (
            f"Error retrieving picklist values for {object_name}.{field_name}: {str(e)}"
        )


# =================================================================
# SALESFORCE PROMPTS
# =================================================================
# These prompts help users formulate effective questions to
# interact with the Salesforce tools above
# =================================================================


@mcp.prompt()
def search_objects_prompt() -> str:
    """Create a prompt for searching Salesforce objects"""
    return """
    I'll help you search for Salesforce objects.
    
    You can ask for:
    - Objects related to a specific domain (e.g., "Find objects related to Accounts")
    - Objects for a business function (e.g., "Show me objects for customer service")
    - Objects with specific features or capabilities
    - Standard or custom objects matching a naming pattern
    
    Examples:
    - "Find all objects related to orders or products"
    - "Show me objects used for marketing campaigns"
    - "What custom objects exist in this org?"
    - "List objects that might contain customer information"
    
    What objects are you looking for?
    """


@mcp.prompt()
def query_records_prompt() -> str:
    """Create a prompt for querying Salesforce records"""
    return """
    I'll help you retrieve data from your Salesforce org.
    
    You can ask for:
    - Recent accounts or contacts
    - High-value opportunities
    - Cases with specific statuses
    - Custom queries with your own filters
    
    Examples:
    - "Show me the 5 most recent accounts created"
    - "Find opportunities worth more than $100,000 that are closing this month"
    - "List contacts with titles containing 'Director' or 'VP'"
    - "Get cases with high priority that have been open for more than 3 days"
    
    What kind of data would you like to see?
    """


@mcp.prompt()
def describe_object_prompt() -> str:
    """Create a prompt for describing Salesforce objects"""
    return """
    I'll help you explore and understand Salesforce objects.
    
    You can ask for:
    - Schema information for any standard or custom object
    - Field details including data types, required fields, and relationships
    - Picklist values and available options
    - Object relationships and dependencies
    - Complete API metadata in raw JSON format
    
    Examples:
    - "Tell me about the Lead object"
    - "What fields are available on Opportunity?"
    - "Show me the structure of the Account object"
    - "What are the picklist values for Case Status?"
    - "Get the raw JSON schema for Contact"
    - "Describe the Campaign object and its fields"
    
    Which Salesforce object would you like to explore?
    """


@mcp.prompt()
def picklist_values_prompt() -> str:
    """Create a prompt for retrieving picklist values"""
    return """
    I'll help you explore picklist values for any Salesforce field.
    
    Examples:
    - "What are the available Status values for Case?"
    - "Show me all the Industry options for Account"
    - "What are the possible Stage values for Opportunity?"
    - "List the Priority options for Task"
    - "What values can be selected for Lead Source?"
    - "Show me all picklist options for Campaign Status"
    
    Which object and field would you like to explore?
    """


@mcp.prompt()
def relationship_fields_prompt() -> str:
    """Create a prompt for exploring relationship fields"""
    return """
    I'll help you understand the relationships between Salesforce objects.
    
    Examples:
    - "Show me all relationships for the Contact object"
    - "What objects are related to Account?"
    - "How is Case connected to other objects?"
    - "Explain the parent-child relationships for Opportunity"
    - "What lookups exist on the Lead object?"
    - "Show me all master-detail relationships for the custom object"
    
    Which object's relationships would you like to explore?
    """


@mcp.prompt()
def validation_rules_prompt() -> str:
    """Create a prompt for exploring validation rules"""
    return """
    I'll help you understand the validation rules applied to Salesforce objects.
    
    Examples:
    - "What validation rules exist for Opportunity?"
    - "Show me all validation conditions for Lead"
    - "Explain the validation requirements for Account"
    - "What validation logic is applied to Contact records?"
    - "List all the rules that prevent records from being saved"
    - "What data quality rules are enforced on Opportunity?"
    
    Which object's validation rules would you like to explore?
    """


@mcp.prompt()
def cross_object_search_prompt() -> str:
    """Create a prompt for searching across multiple objects"""
    return """
    I'll help you search for content across multiple Salesforce objects.
    
    Examples:
    - "Find records containing 'cloud' in Accounts and Opportunities"
    - "Search for 'network issue' in Cases and Knowledge Articles"
    - "Look for customer name across all relevant objects"
    - "Find mentions of 'quarterly review' in recent records"
    - "Search for 'Smith & Co' across accounts, contacts and leads"
    - "Find data related to 'renewable energy' across all objects"
    
    What would you like to search for?
    """


@mcp.prompt()
def field_type_exploration_prompt() -> str:
    """Create a prompt for exploring fields by their type"""
    return """
    I'll help you find fields of specific types within Salesforce objects.
    
    Examples:
    - "Show me all picklist fields in Lead"
    - "Find all text fields in the Account object"
    - "Which fields in Opportunity are dates?"
    - "List all currency fields in the Order object"
    - "What formula fields exist on the Contact object?"
    - "Find all lookup fields on Case"
    
    Which type of fields would you like to explore?
    """


@mcp.prompt()
def debug_logs_prompt() -> str:
    """Create a prompt for managing debug logs"""
    return """
    I'll help you manage debug logs for troubleshooting Salesforce issues.
    
    You can:
    - Enable debug logs for specific users
    - Configure log detail levels (ERROR, WARN, INFO, DEBUG, FINE, FINER, FINEST)
    - Retrieve and analyze recent logs
    - View detailed log content
    - Disable logging when finished troubleshooting
    
    Examples:
    - "Enable debug logs for admin@example.com at DEBUG level"
    - "Set up FINEST debug logging for user.name@company.com for 60 minutes"
    - "Show me recent debug logs for the system administrator"
    - "Retrieve the full content of a specific debug log"
    - "Disable debug logging for admin@example.com"
    
    What would you like to do with debug logs?
    """


# =================================================================
# CONNECTION HEALTH CHECK
# =================================================================
# This tool verifies the connection to Salesforce and provides basic
# organization information to confirm connectivity
# =================================================================


@mcp.tool()
def check_salesforce_connection() -> str:
    """
    Check the connection to Salesforce and return basic org information.

    This tool validates that your Salesforce connection is working properly
    and returns basic information about the connected org including:
    - Connection status
    - Username
    - Instance URL
    - Environment type (production/sandbox)
    - Number of available objects

    Use this as a first step to diagnose connection issues.

    Examples:
    - "Check if Salesforce connection is working"
    - "Verify Salesforce API connectivity"
    - "Test connection to Salesforce org"
    - "Show Salesforce connection status"

    Returns:
        Status of the Salesforce connection and basic org details
    """
    try:
        logger.info("Checking Salesforce connection status")
        sf = get_connection()

        # Use the get_connection_info function to get connection details
        from sf_connection import get_connection_info

        # Get connection information
        connection_info = get_connection_info()

        # Test connection by attempting a simple request
        try:
            # Simply fetch global describe which should work with any permissions
            describe_global = sf.describe()
            total_objects = (
                len(describe_global["sobjects"])
                if describe_global and "sobjects" in describe_global
                else 0
            )
            connection_status = f"Successful ({total_objects} objects available)"
        except Exception as e:
            connection_status = f"Partially working (API connection active but describe failed: {str(e)})"

        return f"""
        Salesforce connection is active.
        
        Connection Status: {connection_status}
        Username: {connection_info.get('username', 'Unknown')}
        Instance URL: {connection_info.get('instance_url', 'Unknown')}
        Environment: {"Sandbox" if connection_info.get('domain') == "test" else "Production"}
        """

    except Exception as e:
        logger.error(f"Connection check failed: {str(e)}")
        return f"Error connecting to Salesforce: {str(e)}"


# =================================================================
# Main entry point for running the MCP server
# =================================================================

# execute and return the stdio output
if __name__ == "__main__":
    try:
        logger.info("Starting Salesforce MCP Server")
        # Explicitly set transport to stdio to avoid SSE connection issues
        mcp.run()
    except Exception as e:
        logger.critical(f"Failed to start MCP server: {str(e)}")
        raise
