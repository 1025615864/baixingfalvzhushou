import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST", "")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.smtp_from = os.getenv("SMTP_FROM", "noreply@baixinglaw.com")
        self._enabled = bool(self.smtp_host and self.smtp_user)

    @property
    def is_enabled(self) -> bool:
        return self._enabled

    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None,
    ) -> bool:
        if not self._enabled:
            logger.info(f"Email disabled, would send to {to}: {subject}")
            return False

        try:
            import aiosmtplib
            from email.mime.multipart import MIMEMultipart
            from email.mime.text import MIMEText

            message = MIMEMultipart("alternative")
            message["From"] = self.smtp_from
            message["To"] = to
            message["Subject"] = subject

            message.attach(MIMEText(body, "plain", "utf-8"))
            if html_body:
                message.attach(MIMEText(html_body, "html", "utf-8"))

            await aiosmtplib.send(
                message,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_user,
                password=self.smtp_password,
                use_tls=True,
            )
            logger.info(f"Email sent to {to}: {subject}")
            return True
        except ImportError:
            logger.warning("aiosmtplib not installed, email sending skipped")
            return False
        except Exception as e:
            logger.error(f"Failed to send email to {to}: {e}")
            return False


email_service = EmailService()
