# Copyright 2025 Tsung-Han Chang. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""A collection of utilities for Mend (formerly WhiteSource) API interactions."""
import json
from typing import Any

import requests

from thc_devops_toolkit.observability import THCLoggerHighlightLevel, thc_logger


def get_refresh_token(email: str, user_key: str) -> str:
    """Obtains a Mend API refresh token.

    Args:
        email (str): User email address.
        user_key (str): Mend user key.

    Returns:
        str: Refresh token.
    """
    url = "https://api-saas.whitesourcesoftware.com/api/v3.0/login"
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, headers=headers, data=json.dumps({"email": email, "userKey": user_key}))

    data = response.json()
    return str(data["response"]["refreshToken"])


def get_jwt_token(refresh_token: str) -> str:
    """Obtains a Mend API JWT token using a refresh token.

    Args:
        refresh_token (str): Mend refresh token.

    Returns:
        str: JWT token.
    """
    url = "https://api-saas.whitesourcesoftware.com/api/v3.0/login/accessToken"
    headers = {"Content-Type": "application/json", "wss-refresh-token": refresh_token}
    response = requests.post(url, headers=headers)

    data = response.json()
    return str(data["response"]["jwtToken"])


def get_alerts_by_library(project_token: str, jwt_token: str) -> dict[str, Any]:
    """Retrieves security alerts grouped by library for a given project.

    Args:
        project_token (str): Mend project token.
        jwt_token (str): JWT token for authentication.

    Returns:
        dict: Alerts grouped by library.
    """
    thc_logger.highlight(
        level=THCLoggerHighlightLevel.INFO,
        message="Start getting alerts by library",
    )
    url = (
        f"https://api-saas.whitesourcesoftware.com/api/v2.0/projects/{project_token}"
        "/alerts/security/groupBy/component?search=status:equals:ACTIVE"
    )
    headers = {"Authorization": f"Bearer {jwt_token}", "Content-Type": "application/json"}
    response = requests.get(url, headers=headers)

    data = response.json()["retVal"]
    if not isinstance(data, dict):
        raise ValueError("Expected data to be a dictionary")
    for key in data:
        if not isinstance(key, str):
            raise ValueError(f"Expected key '{key}' to be a string")
    thc_logger.highlight(
        level=THCLoggerHighlightLevel.INFO,
        message="Successfully finished getting alerts by library",
    )
    return data


def get_vulnerabilities_by_project(project_token: str, jwt_token: str) -> dict[str, Any]:
    """Retrieves vulnerabilities for a given project.

    Args:
        project_token (str): Mend project token.
        jwt_token (str): JWT token for authentication.

    Returns:
        dict: Vulnerabilities for the project.
    """
    thc_logger.highlight(
        level=THCLoggerHighlightLevel.INFO,
        message="Start getting vulnerabilities by project",
    )
    url = f"https://api-saas.whitesourcesoftware.com/api/v2.0/projects/{project_token}/alerts/security?search=status:equals:ACTIVE"
    headers = {"Authorization": f"Bearer {jwt_token}", "Content-Type": "application/json"}
    response = requests.get(url, headers=headers)

    data = response.json()["retVal"]
    if not isinstance(data, dict):
        raise ValueError("Expected data to be a dictionary")
    for key in data:
        if not isinstance(key, str):
            raise ValueError(f"Expected key '{key}' to be a string")
    thc_logger.highlight(
        level=THCLoggerHighlightLevel.INFO,
        message="Successfully finished getting vulnerabilities by project",
    )
    return data
