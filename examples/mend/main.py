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

import argparse

from thc_devops_toolkit.observability import LogLevel, logger
from thc_devops_toolkit.security.mend_api_helper import (
    get_alerts_by_library,
    get_jwt_token,
    get_refresh_token,
    get_vulnerabilities_by_project,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Mend API Helper")
    parser.add_argument("--email", required=True, help="Your Mend account email")
    parser.add_argument("--user-key", required=True, help="Your Mend user key")
    parser.add_argument("--project-token", required=True, help="Your Mend project token")
    args = parser.parse_args()

    refresh_token = get_refresh_token(args.email, args.user_key)
    jwt_token = get_jwt_token(refresh_token)
    alerts = get_alerts_by_library(args.project_token, jwt_token)
    logger.highlight(
        level=LogLevel.DEBUG,
        message=f"Alerts: {alerts}",
    )
    vulnerabilities = get_vulnerabilities_by_project(args.project_token, jwt_token)
    logger.highlight(
        level=LogLevel.DEBUG,
        message=f"Vulnerabilities: {vulnerabilities}",
    )


if __name__ == "__main__":
    main()
