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
import getpass
import smtplib

from thc_devops_toolkit.observability import LogLevel, logger
from thc_devops_toolkit.utils import EMailSender

google_smtp_server = "smtp.gmail.com"
google_smtp_port = 587
subject = "[Test EMailSender] Notification from thc-devops-toolkit"
body = """Dear User,\n
This is a test email sent using the EMailSender utility from thc-devops-toolkit.\n
Happy Coding!\n
Best Regards,\n
Tsung-Han Chang
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Test EMailSender with Gmail")
    parser.add_argument("--gmail", required=True, help="Gmail address")
    args = parser.parse_args()

    app_password = getpass.getpass("Gmail app password: ")
    app_password = app_password.replace(" ", "")

    email_sender = EMailSender(
        smtp_server=google_smtp_server,
        smtp_port=google_smtp_port,
        smtp_username=args.gmail,
        smtp_password=app_password,
        from_email=args.gmail,
    )
    try:
        email_sender.send_email(subject=subject, body=body, to_emails=[args.gmail])
    except smtplib.SMTPAuthenticationError as _:
        logger.highlight(LogLevel.ERROR, "SMTP authentication failed.")
        logger.highlight(
            LogLevel.ERROR, "Please check your credentials and ensure that you aren't using your email password but an app password."
        )


if __name__ == "__main__":
    main()
