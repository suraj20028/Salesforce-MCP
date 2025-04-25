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
    username: str = None,
    password: str = None,
    domain_url: str = None,
) -> Tuple[str, str]:
    """
    Authenticate with Salesforce using OAuth 2.0 Client Credentials flow

    Args:
        client_id: Connected app client ID
        client_secret: Connected app client secret
        username: Salesforce username (not used in payload)
        password: Salesforce password (not used in payload)
        domain_url: Custom Salesforce domain URL

    Returns:
        Tuple of (access_token, instance_url)
    """
    if not domain_url:
        raise ValueError("SALESFORCE_DOMAIN_URL must be provided.")
    auth_url = f"{domain_url.rstrip('/')}/services/oauth2/token"
    payload = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
    }
    response = requests.post(auth_url, data=payload)
    response.raise_for_status()
    access_token = response.json().get("access_token")
    instance_url = response.json().get("instance_url")
    print(f"[SUCCESS] Authenticated using client_credentials.")
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
    creds = {
        "client_id": os.environ.get("SALESFORCE_CLIENT_ID"),
        "client_secret": os.environ.get("SALESFORCE_CLIENT_SECRET"),
        "domain_url": os.environ.get("SALESFORCE_DOMAIN_URL"),
    }

    if not hasattr(get_connection, "_instance") or not cached:
        access_token, instance_url = authenticate(
            creds["client_id"],
            creds["client_secret"],
            domain_url=creds["domain_url"],
        )
        get_connection._instance = Salesforce(
            instance_url=instance_url,
            session_id=access_token,
        )
        get_connection._access_token = access_token
        get_connection._instance_url = instance_url
        get_connection._connection_info = {
            "instance_url": instance_url,
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
