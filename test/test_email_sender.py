import unittest
from unittest.mock import MagicMock, patch, call

from thc_devops_toolkit.utils.notification import EMailSender


class TestEMailSender(unittest.TestCase):
    """Test cases for EMailSender class."""

    def setUp(self):
        """Set up test fixtures."""
        self.smtp_server = "smtp.example.com"
        self.smtp_port = 587
        self.smtp_username = "user@example.com"
        self.smtp_password = "password123"
        self.from_email = "sender@example.com"
        
        self.email_sender = EMailSender(
            smtp_server=self.smtp_server,
            smtp_port=self.smtp_port,
            smtp_username=self.smtp_username,
            smtp_password=self.smtp_password,
            from_email=self.from_email
        )

    @patch('thc_devops_toolkit.utils.notification.smtplib.SMTP')
    def test_send_email_success(self, mock_smtp):
        """Test successful email sending."""
        # Arrange
        mock_server = MagicMock()
        mock_smtp.return_value = mock_server
        
        subject = "Test Subject"
        body = "Test Body"
        to_emails = ["recipient@example.com"]
        
        # Act
        self.email_sender.send_email(subject, body, to_emails)
        
        # Assert
        mock_smtp.assert_called_once_with(self.smtp_server, self.smtp_port)
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with(self.smtp_username, self.smtp_password)
        mock_server.send_message.assert_called_once()
        mock_server.quit.assert_called_once()

    @patch('thc_devops_toolkit.utils.notification.smtplib.SMTP')
    def test_send_email_multiple_recipients(self, mock_smtp):
        """Test sending email to multiple recipients."""
        # Arrange
        mock_server = MagicMock()
        mock_smtp.return_value = mock_server
        
        subject = "Test Subject"
        body = "Test Body"
        to_emails = ["recipient1@example.com", "recipient2@example.com", "recipient3@example.com"]
        
        # Act
        self.email_sender.send_email(subject, body, to_emails)
        
        # Assert
        mock_server.send_message.assert_called_once()
        # Verify the message contains all recipients
        call_args = mock_server.send_message.call_args[0][0]
        self.assertIn("recipient1@example.com", call_args["To"])
        self.assertIn("recipient2@example.com", call_args["To"])
        self.assertIn("recipient3@example.com", call_args["To"])

    def test_send_email_no_recipients(self):
        """Test that sending email with no recipients raises ValueError."""
        # Arrange
        subject = "Test Subject"
        body = "Test Body"
        to_emails = []
        
        # Act & Assert
        with self.assertRaises(ValueError) as context:
            self.email_sender.send_email(subject, body, to_emails)
        
        self.assertIn("No recipient email addresses provided", str(context.exception))

    @patch('thc_devops_toolkit.utils.notification.smtplib.SMTP')
    def test_send_email_message_content(self, mock_smtp):
        """Test that email message contains correct content."""
        # Arrange
        mock_server = MagicMock()
        mock_smtp.return_value = mock_server
        
        subject = "Important Notice"
        body = "This is an important message."
        to_emails = ["recipient@example.com"]
        
        # Act
        self.email_sender.send_email(subject, body, to_emails)
        
        # Assert
        call_args = mock_server.send_message.call_args[0][0]
        self.assertEqual(call_args["Subject"], subject)
        self.assertEqual(call_args["From"], self.from_email)
        self.assertEqual(call_args["To"], "recipient@example.com")

    @patch('thc_devops_toolkit.utils.notification.smtplib.SMTP')
    def test_connection_cleanup_on_success(self, mock_smtp):
        """Test that SMTP connection is properly closed after successful send."""
        # Arrange
        mock_server = MagicMock()
        mock_smtp.return_value = mock_server
        
        # Act
        self.email_sender.send_email("Test", "Body", ["test@example.com"])
        
        # Assert
        mock_server.quit.assert_called_once()

    @patch('thc_devops_toolkit.utils.notification.smtplib.SMTP')
    def test_connection_cleanup_on_error(self, mock_smtp):
        """Test that SMTP connection is properly closed even when error occurs."""
        # Arrange
        mock_server = MagicMock()
        mock_server.send_message.side_effect = Exception("SMTP error")
        mock_smtp.return_value = mock_server
        
        # Act & Assert
        with self.assertRaises(Exception):
            self.email_sender.send_email("Test", "Body", ["test@example.com"])
        
        # Connection should still be closed
        mock_server.quit.assert_called_once()


if __name__ == "__main__":
    unittest.main()
