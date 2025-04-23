# Salesforce MCP Server

An MCP (Model Context Protocol) server implementation that integrates Claude/VS Code with Salesforce, enabling natural language interactions with your Salesforce data and metadata. This server allows Claude to query, modify, and manage your Salesforce objects and records using everyday language.

## Features

- **Smart Object Search**: Find Salesforce objects using partial name matches
- **Detailed Schema Information**: Get comprehensive field and relationship details for any object
- **Flexible Data Queries**: Query records with relationship support and complex filters
- **Picklist Value Retrieval**: Get all values for any picklist field
- **Field Type Filtering**: Find fields of specific types across objects
- **Relationship Exploration**: Analyze parent-child relationships between objects
- **Enhanced API Metadata**: Access complete object metadata through direct API calls
- **Debug Log Management**: Configure and retrieve debug logs for Salesforce users
- **Validation Rules Management**: Get details about validation rules on objects

## Prerequisites

1. To run the server in a container, you will need to have [Docker](https://www.docker.com/) installed.
2. Once Docker is installed, you will also need to ensure Docker is running.
3. You will need Salesforce OAuth2 credentials:
   - For OAuth 2.0 Client Credentials Flow: Client ID, Client Secret, and Instance URL

## Installation

### Usage with VS Code

For manual installation, add the following JSON block to your User Settings (JSON) file in VS Code. You can do this by pressing `Ctrl + Shift + P` (or `Cmd + Shift + P` on macOS) and typing `Preferences: Open User Settings (JSON)`.

Optionally, you can add it to a file called `.vscode/mcp.json` in your workspace. This will allow you to share the configuration with others.

> Note that the `mcp` key is not needed in the `.vscode/mcp.json` file.

```json
"mcp": {
  "inputs": [
    {
      "type": "promptString",
      "id": "client_id",
      "description": "Salesforce Client ID",
      "password": false
    },
    {
      "type": "promptString",
      "id": "client_secret",
      "description": "Salesforce Client Secret",
      "password": false
    },
    {
      "type": "promptString",
      "id": "username",
      "description": "Salesforce Username",
      "password": false
    },
    {
      "type": "promptString",
      "id": "password",
      "description": "Salesforce Password",
      "password": false
    }
  ],
  "servers": {
    "salesforce": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-e", "SALESFORCE_CLIENT_ID",
        "-e", "SALESFORCE_CLIENT_SECRET",
        "-e", "SALESFORCE_USERNAME",
        "-e", "SALESFORCE_PASSWORD",
        "suraj20028/salesforce-mcp-server"
      ],
      "env": {
        "SALESFORCE_CLIENT_ID": "${input:client_id}",
        "SALESFORCE_CLIENT_SECRET": "${input:client_secret}",
        "SALESFORCE_USERNAME": "${input:username}",
        "SALESFORCE_PASSWORD": "${input:password}"
      }
    }
  }
}
```

More about using MCP server tools in VS Code's [agent mode documentation](https://code.visualstudio.com/docs/copilot/chat/mcp-servers).

## Tools

| Tool Name                        | Description                                                    | Parameters                                                                                                                                   |
| -------------------------------- | -------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| **search_objects**               | Search for standard and custom objects by partial name matches | `query`: The search string for object names                                                                                                  |
| **describe_object**              | Get detailed schema information for a Salesforce object        | `objectName`: The API name of the object                                                                                                     |
| **describe_object_with_api**     | Get extended object metadata using direct REST API calls       | `objectName`: The API name of the object, `raw`: (Optional) Return raw JSON                                                                  |
| **describe_relationship_fields** | Explore parent-child relationships between objects             | `objectName`: The API name of the object                                                                                                     |
| **query_records**                | Query records with support for relationships and filters       | `object`: Object to query, `fields`: Fields to return, `where`: (Optional) WHERE conditions, `limit`: (Optional) Number of records to return |
| **get_fields_by_type**           | Find fields of specific data types in an object                | `objectName`: The API name of the object, `fieldType`: Data type to filter by                                                                |
| **get_picklist_values**          | Retrieve all values for a picklist field                       | `objectName`: The API name of the object, `fieldName`: The picklist field name                                                               |
| **get_validation_rules**         | Get details about validation rules on an object                | `objectName`: The API name of the object                                                                                                     |
| **manage_debug_logs**            | Configure and retrieve debug logs for users                    | `action`: Action to perform (enable, disable, retrieve), `userId`: User ID, `logLevel`: (Optional) Debug log level                           |

## Example Usage

### Searching Objects

```
"Find all objects related to Accounts"
"Show me objects that handle customer service"
"What objects are available for order management?"
```

### Getting Schema Information

```
"What fields are available in the Account object?"
"Show me the picklist values for Case Status"
"Describe the relationship fields in Opportunity"
```

### Querying Records

```
"Get all Accounts created this month"
"Show me high-priority Cases with their related Contacts"
"Find all Opportunities over $100k"
```

### Working with Fields by Type

```
"Show me all picklist fields on the Lead object"
"Get all reference fields on Opportunity"
"Find all required fields on Account"
```

### Getting Picklist Values

```
"What are the possible values for Lead Status?"
"Show me all Industry options for Accounts"
"List all Case Priority values"
```

### Exploring Relationships

```
"Show me all relationships for the Account object"
"What objects are related to Opportunity?"
"Describe the parent-child relations for Contact"
```

### Managing Debug Logs

```
"Enable debug logs for user@example.com"
"Retrieve recent logs for an admin user"
"Disable debug logs for a specific user"
"Configure log level to DEBUG for a user"
```

### Checking Validation Rules

```
"Show me all validation rules on Opportunity"
"Get details about Account validation rules"
"What validation rules exist for custom objects?"
```

## Development

### Project Structure

```
salesforce-mcp-server/
├── server.py             # MCP server implementation
├── sf_connection.py      # Salesforce authentication
├── tools/
│   ├── __init__.py       # Tools package initialization
│   ├── search_objects.py # Object search functionality
│   ├── describe_object.py # Object schema retrieval
│   ├── query_records.py  # SOQL query functionality
│   └── ...               # Other tool modules
```

### Adding New Tools

1. Create a new Python file in the `tools` directory
2. Implement your function with proper docstrings and error handling
3. Import and register the function in the MCP server

## Contributing

Contributions are welcome! Feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Issues and Support

If you encounter any issues or need support, please file an issue on the GitHub repository.
