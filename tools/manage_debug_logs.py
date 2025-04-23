"""
Manage debug logs for Salesforce users

This module provides functionality to enable, disable, and retrieve debug logs for Salesforce users.
Debug logs are essential for troubleshooting Salesforce integrations, Apex code execution,
and general API behavior.

Functions:
- manage_debug_logs: Main function that handles all debug log operations

Operations:
- enable: Sets up debug logging for a specific user with configurable log level
- disable: Turns off debug logging for a user
- retrieve: Gets logs for a user, with options to view log details

Log levels (increasing detail):
- NONE: No logs
- ERROR: Only error events
- WARN: Warning and error events
- INFO: Info, warning, and error events
- DEBUG: Debug, info, warning, and error events
- FINE: Fine and all higher events
- FINER: Finer and all higher events
- FINEST: Finest and all higher events (most detailed)
"""

from typing import Dict, List, Any, Optional
from sf_connection import get_connection
import datetime
import logging
import json

# Configure logging
logger = logging.getLogger("sf_mcp_server.debug_logs")


def manage_debug_logs(
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

    This function allows comprehensive management of Salesforce debug logs:
    1. ENABLE: Set up debug logging for a specific user with a chosen log level
    2. DISABLE: Turn off debug logging for a user
    3. RETRIEVE: Get logs for a user, with options to view specific log details

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

    Examples:
        # Enable debug logs
        manage_debug_logs('enable', 'user@example.com', 'DEBUG', 60)

        # Disable debug logs
        manage_debug_logs('disable', 'user@example.com')

        # Retrieve recent logs
        manage_debug_logs('retrieve', 'user@example.com', limit=5)

        # Get a specific log with full content
        manage_debug_logs('retrieve', 'user@example.com', log_id='07L1g000000XXXX', include_body=True)
    """
    try:
        # Input validation
        if not username:
            return "Error: Username is required"

        if operation == "enable" and not log_level:
            return "Error: Log level is required for 'enable' operation. Valid options: NONE, ERROR, WARN, INFO, DEBUG, FINE, FINER, FINEST"

        # Get connection to Salesforce
        sf = get_connection()

        # Extract instance URL for direct API calls
        instance_url = sf.base_url.split("/services/data")[0]
        headers = sf.headers

        # Determine if the input is likely a username or a full name
        is_likely_username = "@" in username or " " not in username

        # Build the query based on whether the input looks like a username or a full name
        if is_likely_username:
            # Query by username
            soql = f"SELECT Id, Username, Name, IsActive FROM User WHERE Username = '{username}'"
        else:
            # Query by full name
            soql = f"""SELECT Id, Username, Name, IsActive 
                    FROM User 
                    WHERE Name LIKE '%{username}%'
                    ORDER BY LastModifiedDate DESC
                    LIMIT 5"""

        # Execute user query
        params = {"q": soql}
        response = sf.session.get(
            f"{instance_url}/services/data/v63.0/query/", headers=headers, params=params
        )
        response.raise_for_status()
        user_query = response.json()

        if not user_query.get("records") or len(user_query["records"]) == 0:
            # If no results with the initial query, try a more flexible search
            soql = f"""SELECT Id, Username, Name, IsActive 
                    FROM User 
                    WHERE Name LIKE '%{username}%' 
                    OR Username LIKE '%{username}%'
                    ORDER BY LastModifiedDate DESC
                    LIMIT 5"""

            params = {"q": soql}
            response = sf.session.get(
                f"{instance_url}/services/data/v63.0/query/",
                headers=headers,
                params=params,
            )
            response.raise_for_status()
            user_query = response.json()

            if not user_query.get("records") or len(user_query["records"]) == 0:
                return f"Error: No user found matching '{username}'. Please verify the username or full name and try again."

            # If multiple users found, ask for clarification
            if len(user_query["records"]) > 1:
                response_text = f"Multiple users found matching '{username}'. Please specify which user by providing the exact username:\n\n"

                for user in user_query["records"]:
                    response_text += f"- {user['Name']} ({user['Username']})\n"

                return response_text

        user = user_query["records"][0]

        if not user["IsActive"]:
            return f"Warning: User '{username}' exists but is inactive. Debug logs may not be generated for inactive users."

        # Handle operations
        if operation == "enable":
            # Set default expiration time if not provided
            expiration_time = expiration_time or 30

            # Format datetime for SOQL: milliseconds, no quotes, Z
            now = datetime.datetime.utcnow()
            expiration_soql = now.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

            # Check if a trace flag already exists for this user
            soql = f"""
                SELECT Id, DebugLevelId, ExpirationDate FROM TraceFlag 
                WHERE TracedEntityId = '{user['Id']}' 
                AND ExpirationDate > {expiration_soql}
            """
            # Execute trace flag query using tooling API
            params = {"q": soql}
            response = sf.session.get(
                f"{instance_url}/services/data/v63.0/tooling/query/",
                headers=headers,
                params=params,
            )
            response.raise_for_status()
            existing_trace_flag = response.json()

            # Calculate expiration date
            expiration_date = datetime.datetime.now() + datetime.timedelta(
                minutes=expiration_time
            )

            # --- Find or create DebugLevel for requested log_level ---
            # First, try to find a standard DebugLevel with the requested log level
            soql_debug_level = (
                f"SELECT Id FROM DebugLevel WHERE ApexCode = '{log_level}'"
            )
            params_debug_level = {"q": soql_debug_level}
            response = sf.session.get(
                f"{instance_url}/services/data/v63.0/tooling/query/",
                headers=headers,
                params=params_debug_level,
            )
            response.raise_for_status()
            debug_level_query = response.json()

            if debug_level_query.get("records"):
                # Use existing DebugLevel
                debug_level_id = debug_level_query["records"][0]["Id"]
                logger.info(f"Using existing DebugLevel with ID: {debug_level_id}")
            else:
                # Create a new DebugLevel if none exists
                logger.info(f"Creating new DebugLevel with log level: {log_level}")
                debug_level_data = {
                    "DeveloperName": log_level,
                    "MasterLabel": log_level,
                    "ApexCode": log_level,
                    "ApexProfiling": log_level,
                    "Callout": log_level,
                    "Database": log_level,
                    "System": log_level,
                    "Validation": log_level,
                    "Visualforce": log_level,
                    "Workflow": log_level,
                }
                response = sf.session.post(
                    f"{instance_url}/services/data/v63.0/tooling/sobjects/DebugLevel",
                    headers=headers,
                    json=debug_level_data,
                )
                response.raise_for_status()
                debug_level_result = response.json()
                debug_level_id = debug_level_result["id"]
                logger.info(f"Created new DebugLevel with ID: {debug_level_id}")

            if (
                existing_trace_flag.get("records")
                and len(existing_trace_flag["records"]) > 0
            ):
                # A trace flag already exists for this user - update it
                trace_flag = existing_trace_flag["records"][0]
                current_expiration = trace_flag.get("ExpirationDate")
                # Always add 30 seconds to the current expiration and update
                try:
                    if current_expiration:
                        current_exp_dt = datetime.datetime.fromisoformat(
                            current_expiration.replace("Z", "+00:00")
                        )
                        new_expiration = current_exp_dt + datetime.timedelta(seconds=30)
                    else:
                        new_expiration = datetime.datetime.now() + datetime.timedelta(
                            seconds=30
                        )
                except Exception:
                    new_expiration = datetime.datetime.now() + datetime.timedelta(
                        seconds=30
                    )

                # Only update ExpirationDate and DebugLevelId (NOT LogType)
                update_data = {
                    "ExpirationDate": new_expiration.isoformat(),
                    "DebugLevelId": debug_level_id,
                }
                logger.info(
                    f"Updating TraceFlag {trace_flag['Id']} with: {update_data}"
                )
                response = sf.session.patch(
                    f"{instance_url}/services/data/v63.0/tooling/sobjects/TraceFlag/{trace_flag['Id']}",
                    headers=headers,
                    json=update_data,
                )
                logger.info(f"PATCH response: {response.status_code}")
                response.raise_for_status()
                operation_status = "updated"
                return f"Successfully updated debug log expiration for user '{username}'.\n\n**Log Level:** {log_level}\n**New Expiration:** {new_expiration.strftime('%Y-%m-%d %H:%M:%S')}\n**Trace Flag ID:** {trace_flag['Id']}\n"
            else:
                # No existing trace flag - create a new one
                logger.info(f"Creating new TraceFlag for user ID: {user['Id']}")
                trace_flag_data = {
                    "TracedEntityId": user["Id"],
                    "DebugLevelId": debug_level_id,
                    "LogType": "USER_DEBUG",  # LogType can be set on creation
                    "StartDate": datetime.datetime.now().isoformat(),
                    "ExpirationDate": expiration_date.isoformat(),
                }
                response = sf.session.post(
                    f"{instance_url}/services/data/v63.0/tooling/sobjects/TraceFlag",
                    headers=headers,
                    json=trace_flag_data,
                )
                response.raise_for_status()
                trace_flag_result = response.json()
                trace_flag_id = trace_flag_result["id"]
                operation_status = "enabled"
                logger.info(f"Created new TraceFlag with ID: {trace_flag_id}")

            return f"""Successfully {operation_status} debug logs for user '{username}'.

**Log Level:** {log_level}
**Expiration:** {expiration_date.strftime('%Y-%m-%d %H:%M:%S')} ({expiration_time} minutes from now)
**Trace Flag ID:** {trace_flag_id if 'trace_flag_id' in locals() else 'N/A'}
"""

        elif operation == "disable":
            # Format datetime for SOQL: milliseconds, no quotes, Z
            now = datetime.datetime.utcnow()
            current_time_iso = now.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
            soql = f"""
                SELECT Id FROM TraceFlag 
                WHERE TracedEntityId = '{user["Id"]}' 
                AND ExpirationDate > {current_time_iso}
            """

            # Execute trace flag query using tooling API
            params = {"q": soql}
            logger.info(f"Querying for active TraceFlags for user: {username}")
            response = sf.session.get(
                f"{instance_url}/services/data/v63.0/tooling/query/",
                headers=headers,
                params=params,
            )
            response.raise_for_status()
            trace_flags = response.json()

            if not trace_flags.get("records") or len(trace_flags["records"]) == 0:
                return f"No active debug logs found for user '{username}'."

            try:
                # First attempt: DELETE trace flags (preferred method)
                trace_flag_ids = [tf["Id"] for tf in trace_flags["records"]]
                delete_count = 0
                logger.info(f"Attempting to delete {len(trace_flag_ids)} TraceFlags")

                for trace_flag_id in trace_flag_ids:
                    response = sf.session.delete(
                        f"{instance_url}/services/data/v63.0/tooling/sobjects/TraceFlag/{trace_flag_id}",
                        headers=headers,
                    )
                    response.raise_for_status()
                    delete_count += 1
                    logger.info(f"Successfully deleted TraceFlag: {trace_flag_id}")

                return f"Successfully disabled {delete_count} debug log configuration(s) for user '{username}' by removing them."
            except Exception as delete_error:
                logger.error(f"Error deleting trace flags: {str(delete_error)}")

                # Fallback: Set expiration date to immediate future (5 minutes)
                try:
                    logger.info(
                        "Delete failed, attempting to update expiration date instead"
                    )
                    # Set expiration date to 5 minutes in the future
                    near_future_expiration = (
                        datetime.datetime.now() + datetime.timedelta(minutes=5)
                    )

                    trace_flag_ids = [tf["Id"] for tf in trace_flags["records"]]
                    update_count = 0

                    for trace_flag_id in trace_flag_ids:
                        update_data = {
                            "ExpirationDate": near_future_expiration.isoformat()
                        }

                        response = sf.session.patch(
                            f"{instance_url}/services/data/v63.0/tooling/sobjects/TraceFlag/{trace_flag_id}",
                            headers=headers,
                            json=update_data,
                        )
                        response.raise_for_status()
                        update_count += 1
                        logger.info(
                            f"Updated expiration date for TraceFlag: {trace_flag_id}"
                        )

                    return f"Successfully disabled {update_count} debug log configuration(s) for user '{username}'. They will expire in 5 minutes."
                except Exception as update_error:
                    logger.error(f"Error updating trace flags: {str(update_error)}")
                    return f"Error disabling debug logs: {str(delete_error)}"

        elif operation == "retrieve":
            # Set default limit if not provided
            limit = limit or 10

            # If a specific log ID is provided, retrieve that log directly
            if log_id:
                try:
                    logger.info(f"Retrieving specific log with ID: {log_id}")
                    # Check if the log exists
                    soql = f"""
                        SELECT Id, LogUserId, Operation, Application, Status, LogLength, LastModifiedDate, Request
                        FROM ApexLog 
                        WHERE Id = '{log_id}'
                    """

                    # Execute log query using tooling API
                    params = {"q": soql}
                    response = sf.session.get(
                        f"{instance_url}/services/data/v63.0/tooling/query/",
                        headers=headers,
                        params=params,
                    )
                    response.raise_for_status()
                    log_query = response.json()

                    if not log_query.get("records") or len(log_query["records"]) == 0:
                        return f"No log found with ID '{log_id}'."

                    log = log_query["records"][0]

                    # If include_body is true, retrieve the full log content
                    if include_body:
                        try:
                            logger.info(
                                f"Retrieving full log body for log ID: {log_id}"
                            )
                            # Retrieve the log body
                            response = sf.session.get(
                                f"{instance_url}/services/data/v63.0/tooling/sobjects/ApexLog/{log['Id']}/Body",
                                headers=headers,
                            )
                            response.raise_for_status()
                            log_body = response.text

                            last_modified_date = datetime.datetime.fromisoformat(
                                log["LastModifiedDate"].replace("Z", "+00:00")
                            )

                            response_text = f"""**Log Details:**

- **ID:** {log['Id']}
- **Operation:** {log.get('Operation', 'N/A')}
- **Application:** {log.get('Application', 'N/A')}
- **Status:** {log.get('Status', 'N/A')}
- **Size:** {log.get('LogLength', 'N/A')} bytes
- **Date:** {last_modified_date.strftime('%Y-%m-%d %H:%M:%S')}

**Log Body:**
```
{log_body}
```
"""
                            return response_text
                        except Exception as log_error:
                            logger.error(f"Error retrieving log body: {str(log_error)}")
                            return f"Error retrieving log body: {str(log_error)}"
                    else:
                        # Just return the log metadata
                        last_modified_date = datetime.datetime.fromisoformat(
                            log["LastModifiedDate"].replace("Z", "+00:00")
                        )

                        response_text = f"""**Log Details:**

- **ID:** {log['Id']}
- **Operation:** {log.get('Operation', 'N/A')}
- **Application:** {log.get('Application', 'N/A')}
- **Status:** {log.get('Status', 'N/A')}
- **Size:** {log.get('LogLength', 'N/A')} bytes
- **Date:** {last_modified_date.strftime('%Y-%m-%d %H:%M:%S')}

To view the full log content, add "include_body": true to your request.
"""
                        return response_text
                except Exception as error:
                    logger.error(f"Error retrieving log: {str(error)}")
                    return f"Error retrieving log: {str(error)}"

            # Query for all logs for the user
            logger.info(f"Retrieving up to {limit} logs for user: {username}")
            soql = f"""
                SELECT Id, LogUserId, Operation, Application, Status, LogLength, LastModifiedDate, Request
                FROM ApexLog 
                WHERE LogUserId = '{user["Id"]}'
                ORDER BY LastModifiedDate DESC 
                LIMIT {limit}
            """

            # Execute logs query using tooling API
            params = {"q": soql}
            response = sf.session.get(
                f"{instance_url}/services/data/v63.0/tooling/query/",
                headers=headers,
                params=params,
            )
            response.raise_for_status()
            logs = response.json()

            if not logs.get("records") or len(logs["records"]) == 0:
                return f"No debug logs found for user '{username}'."

            # Format log information
            response_text = (
                f"Found {len(logs['records'])} debug logs for user '{username}':\n\n"
            )

            for i, log in enumerate(logs["records"]):
                last_modified_date = datetime.datetime.fromisoformat(
                    log["LastModifiedDate"].replace("Z", "+00:00")
                )

                response_text += f"""**Log {i + 1}**
- **ID:** {log['Id']}
- **Operation:** {log.get('Operation', 'N/A')}
- **Application:** {log.get('Application', 'N/A')}
- **Status:** {log.get('Status', 'N/A')}
- **Size:** {log.get('LogLength', 'N/A')} bytes
- **Date:** {last_modified_date.strftime('%Y-%m-%d %H:%M:%S')}

"""

            # Add a note about viewing specific logs with full content
            response_text += """To view a specific log with full content, use:
```json
{
  "operation": "retrieve",
  "username": "username@example.com",
  "log_id": "<LOG_ID>",
  "include_body": true
}
```
"""
            return response_text

        else:
            # Invalid operation provided
            valid_operations = ["enable", "disable", "retrieve"]
            return f"Invalid operation: '{operation}'. Must be one of: {', '.join(valid_operations)}"

    except Exception as e:
        logger.error(f"Error managing debug logs: {str(e)}")
        return f"Error managing debug logs: {str(e)}"
