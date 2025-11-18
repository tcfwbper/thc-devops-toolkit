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
"""This module provides utility functions for sending email notifications."""

import smtplib
from collections.abc import Iterator
from contextlib import contextmanager
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from thc_devops_toolkit.observability import LogLevel, logger


class EMailSender:
    """A utility class for sending email notifications via SMTP."""

    def __init__(  # pylint: disable=too-many-arguments
        self, smtp_server: str, smtp_port: int, smtp_username: str, smtp_password: str, from_email: str
    ) -> None:
        """Initializes the EMailSender with SMTP server details and credentials.

        Args:
            smtp_server (str): The SMTP server address.
            smtp_port (int): The SMTP server port.
            smtp_username (str): The username for SMTP authentication.
            smtp_password (str): The password for SMTP authentication.
            from_email (str): The email address to send from.
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.smtp_username = smtp_username
        self.smtp_password = smtp_password
        self.from_email = from_email

    @contextmanager
    def _connect(self) -> Iterator[smtplib.SMTP]:
        """Context manager to handle SMTP server connection.

        Yields:
            smtplib.SMTP: An active SMTP server connection.
        """
        server = smtplib.SMTP(self.smtp_server, self.smtp_port)
        server.starttls()
        server.login(self.smtp_username, self.smtp_password)
        try:
            # yield the server for use
            yield server
        finally:
            # housekeeping
            server.quit()

    def send_email(self, subject: str, body: str, to_emails: list[str]) -> None:
        """Sends an email with the specified subject and body to the given recipient.

        Args:
            subject (str): The subject of the email.
            body (str): The body content of the email.
            to_emails (list[str]): The recipients' email address.
        """
        if len(to_emails) == 0:
            raise ValueError("No recipient email addresses provided")

        msg = MIMEMultipart()
        msg["From"] = self.from_email
        msg["To"] = ", ".join(to_emails)
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "plain"))

        with self._connect() as server:
            server.send_message(msg)
            logger.highlight(LogLevel.INFO, f"Email sent to: {to_emails} with subject: '{subject}'")
