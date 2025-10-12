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
import logging

from thc_devops_toolkit.security.mend_api_helper import (
    get_alerts_by_library,
    get_jwt_token,
    get_refresh_token,
    get_vulnerabilities_by_project,
)

# Set up a default logger for this module
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def main() -> None:
    parser = argparse.ArgumentParser(description="Mend API Helper")
    parser.add_argument("--email", required=True, help="Your Mend account email")
    parser.add_argument("--user_key", required=True, help="Your Mend user key")
    parser.add_argument("--project_token", required=True, help="Your Mend project token")
    args = parser.parse_args()

    refresh_token = get_refresh_token(args.email, args.user_key)
    jwt_token = get_jwt_token(refresh_token)
    alerts = get_alerts_by_library(args.project_token, jwt_token)
    logger.info("Alerts: %s", alerts)
    vulnerabilities = get_vulnerabilities_by_project(args.project_token, jwt_token)
    logger.info("Vulnerabilities: %s", vulnerabilities)


if __name__ == "__main__":
    main()
