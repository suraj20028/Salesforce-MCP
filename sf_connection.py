#!/usr/bin/env python3
"""
Salesforce connection utility module for MCP tools
Handles authentication and connection management
"""
import os
import requests
from typing import Tuple, Dict, Any, Optional
from simple_salesforce import Salesforce


def authenticate(
    client_id: str,
    client_secret: str,
    username: str,
    password: str,
    sandbox: bool = False,
) -> Tuple[str, str]:
    """
    Authenticate with Salesforce using OAuth 2.0 Password flow

    Args:
        client_id: Connected app client ID
        client_secret: Connected app client secret
        username: Salesforce username
        password: Salesforce password
        sandbox: Whether to connect to sandbox (True) or production (False)

    Returns:
        Tuple of (access_token, instance_url)
    """
    auth_url = (
        "https://login.salesforce.com/services/oauth2/token"
        if not sandbox
        else "https://test.salesforce.com/services/oauth2/token"
    )
    payload = {
        "grant_type": "password",
        "client_id": client_id,
        "client_secret": client_secret,
        "username": username,
        "password": password,
    }

    response = requests.post(auth_url, data=payload)
    response.raise_for_status()
    access_token = response.json().get("access_token")
    instance_url = response.json().get("instance_url")
    return access_token, instance_url


def get_connection(cached: bool = True) -> Salesforce:
    """
    Get a connection to Salesforce using credentials from environment
    or cached values if they exist and cached=True

    Args:
        cached: Whether to use cached credentials if available

    Returns:
        Salesforce connection object
    """
    # Default credentials - you should replace these with environment variables in production
    creds = {
        "client_id": os.environ.get("SALESFORCE_CLIENT_ID"),
        "client_secret": os.environ.get("SALESFORCE_CLIENT_SECRET"),
        "username": os.environ.get("SALESFORCE_USERNAME"),
        "password": os.environ.get("SALESFORCE_PASSWORD"),
        "sandbox": os.environ.get("SANDBOX", "True").lower() == 'true',
    }

    # Static variable to cache the connection
    if not hasattr(get_connection, "_instance") or not cached:
        # Get OAuth tokens using the authenticate function
        access_token, instance_url = authenticate(
            creds["client_id"],
            creds["client_secret"],
            creds["username"],
            creds["password"],
            creds["sandbox"],
        )
        
        # Create Salesforce instance with proper initialization for all APIs
        # We're using session_id to pass the OAuth token, but also specifying domain
        # to ensure proper initialization of the Tooling API
        domain = 'test' if creds["sandbox"] else 'login'
        get_connection._instance = Salesforce(
            instance_url=instance_url, 
            session_id=access_token,
            domain=domain  # This ensures Tooling API is properly initialized
        )
        
        # Store the tokens for future reference if needed
        get_connection._access_token = access_token
        get_connection._instance_url = instance_url
        get_connection._connection_info = {
            "username": creds["username"],
            "instance_url": instance_url,
            "domain": domain,
        }

    return get_connection._instance

def get_connection_info() -> Dict[str, str]:
    """
    Get information about the current Salesforce connection.
    """
    if hasattr(get_connection, "_connection_info"):
        return get_connection._connection_info
    get_connection()
    return get_connection._connection_info
