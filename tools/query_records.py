"""
Query records in Salesforce using SOQL

This module provides functionality to query Salesforce records using SOQL
(Salesforce Object Query Language) with filtering, sorting, and limiting options.
Results are returned in a formatted markdown table for easy reading.

The query builder handles:
- Field selection
- WHERE clause filtering
- ORDER BY sorting
- Record limiting
- Relationship field traversal (e.g., Account.Name)
"""

from typing import List, Optional
import logging
from sf_connection import get_connection

# Configure logging
logger = logging.getLogger("sf_mcp_server.query_records")


def query_records(
    object_name: str,
    fields: List[str],
    where_clause: Optional[str] = None,
    order_by: Optional[str] = None,
    limit: Optional[int] = 10,
) -> str:
    """
    Query Salesforce records with filtering, sorting, and limiting options.

    This function builds and executes a SOQL query against any Salesforce object,
    with support for complex queries including filtering conditions, sorting,
    and relationship field traversal. Results are formatted as a markdown table.

    Args:
        object_name: API name of the object to query (e.g., 'Account', 'Contact', 'Custom_Object__c')
        fields: List of fields to retrieve (e.g., ['Name', 'Phone', 'CreatedDate'])
        where_clause: Optional filtering criteria (e.g., "CreatedDate = LAST_MONTH")
        order_by: Optional sorting criteria (e.g., "Name ASC", "CreatedDate DESC")
        limit: Maximum number of records to return (default: 10, max: 2000)

    Returns:
        Formatted markdown table with query results

    Examples:
        # Basic query for recent accounts
        query_records("Account", ["Name", "Phone", "Website"], limit=5)

        # Query with WHERE clause
        query_records(
            "Opportunity",
            ["Name", "Amount", "CloseDate"],
            where_clause="Amount > 50000 AND IsClosed = false",
            order_by="Amount DESC"
        )

        # Query with relationship fields
        query_records(
            "Contact",
            ["Name", "Email", "Account.Name"],
            where_clause="Email != null",
            limit=10
        )
    """
    logger.info(f"Querying {object_name} records with fields: {fields}")
    sf = get_connection()

    try:
        # Validate and sanitize limit
        if limit is None:
            limit = 10
        elif limit < 1:
            logger.warning(f"Invalid limit {limit}, using minimum of 1")
            limit = 1
        elif limit > 2000:
            logger.warning(f"Limit {limit} exceeds maximum, capping at 2000")
            limit = 2000

        # Build SOQL query
        field_list = ", ".join(fields)
        query = f"SELECT {field_list} FROM {object_name}"

        if where_clause:
            logger.debug(f"Adding WHERE clause: {where_clause}")
            query += f" WHERE {where_clause}"

        if order_by:
            logger.debug(f"Adding ORDER BY clause: {order_by}")
            query += f" ORDER BY {order_by}"

        query += f" LIMIT {limit}"
        logger.info(f"Executing SOQL query: {query}")

        # Execute query
        results = sf.query(query)
        logger.debug(f"Query returned {results.get('totalSize', 0)} records")

        # Format results
        if not results.get("records"):
            logger.info(f"No records found for query: {query}")
            return f"No records found for query: {query}"

        total_records = results.get("totalSize", 0)
        displayed_records = len(results.get("records", []))

        # Start with query information
        result = f"Query: {query}\n\n"
        result += f"Found {total_records} records. Displaying {displayed_records}.\n\n"

        # Create table header
        result += "| " + " | ".join(fields) + " |\n"
        result += "|" + "|".join(["-" * (len(f) + 2) for f in fields]) + "|\n"

        # Add table rows
        for record in results.get("records", []):
            row = []
            for field in fields:
                # Handle relationship fields (e.g., Account.Name)
                if "." in field:
                    parts = field.split(".")
                    value = record
                    for part in parts:
                        if isinstance(value, dict):
                            value = value.get(part, "")
                        else:
                            value = ""
                            break
                else:
                    # Handle direct fields
                    value = record.get(field, "")

                # Format value for table cell
                if value is None:
                    formatted_value = ""
                elif isinstance(value, bool):
                    formatted_value = str(value)
                elif isinstance(value, (int, float)):
                    formatted_value = str(value)
                else:
                    # Escape pipe characters and remove newlines to maintain table format
                    formatted_value = str(value).replace("\n", " ").replace("|", "\\|")

                row.append(formatted_value)

            result += "| " + " | ".join(row) + " |\n"

        return result

    except Exception as e:
        logger.error(f"Error querying {object_name} records: {str(e)}")
        return f"Error querying {object_name} records: {str(e)}"
