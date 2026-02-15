"""邮件服务核心类

提供 SMTP 配置、限流、邮件发送等核心功能
"""
import logging
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ...config import get_settings
from ...models.system import SystemConfig, SystemSecret
from ...utils.secret_crypto import decrypt_secret
from .templates import (
    get_password_reset_html_template,
    get_password_reset_text_template,
    get_email_verification_html_template,
    get_email_verification_text_template,
)
from .storage import ResetTokenData as EmailServiceResetTokenData, EmailVerificationTokenData
from .password_reset import password_reset_service
from .verification import email_verification_service

logger = logging.getLogger(__name__)

# ============================================================================
# 常量定义
# ============================================================================

_EMAIL_RATE_LIMIT_PREFIX = "email_rate_limit:"
_EMAIL_RATE_LIMIT_MAX_PER_MINUTE = 3  # 每分钟最多发送3封邮件
_EMAIL_RATE_LIMIT_WINDOW_SECONDS = 60  # 限流窗口时间（秒）
_EMAIL_VERIFY_TOKEN_TTL_SECONDS = 60 * 60 * 24  # 24小时


# ============================================================================
# 邮件服务类
# ============================================================================

class EmailService:
    """邮件服务类

    Attributes:
        SMTP_TIMEOUT: SMTP 超时配置（秒）
        smtp_host: SMTP 服务器地址
        smtp_port: SMTP 端口
        smtp_user: SMTP 用户名
        smtp_password: SMTP 密码
        smtp_use_tls: 是否使用隐式 TLS
        smtp_start_tls: 是否使用 STARTTLS
        from_email: 发件人邮箱
        from_name: 发件人名称
        last_error: 最后一次错误信息
    """

    # SMTP 超时配置（秒）
    SMTP_TIMEOUT = 30

    def __init__(self):
        self.smtp_host: str | None = None
        self.smtp_port: int = 587
        self.smtp_user: str | None = None
        self.smtp_password: str | None = None
        self.smtp_use_tls: bool = False
        self.smtp_start_tls: bool = True
        self.from_email: str = "noreply@baixing-law.com"
        self.from_name: str = "百姓法律助手"
        self.last_error: str | None = None

    async def _check_rate_limit(self,
                                user_id: int | None = None,
                                email: str | None = None) -> tuple[bool,
                                                                   str]:
        """检查邮件发送限流

        Args:
            user_id: 用户ID（可选）
            email: 邮箱地址（可选）

        Returns:
            (是否允许发送, 错误信息)
        """
        # 优先使用 user_id，其次使用 email
        rate_key = None
        if user_id:
            rate_key = f"{_EMAIL_RATE_LIMIT_PREFIX}user:{user_id}"
        elif email:
            rate_key = f"{_EMAIL_RATE_LIMIT_PREFIX}email:{email}"
        else:
            # 没有用户信息，不进行限流
            return True, ""

        try:
            from ..cache_service import cache_service
            current_count = await cache_service.get(rate_key)
            if current_count is None:
                # 首次发送，设置计数器
                await cache_service.set(rate_key, "1", expire=_EMAIL_RATE_LIMIT_WINDOW_SECONDS)
                return True, ""

            count = int(current_count)
            if count >= _EMAIL_RATE_LIMIT_MAX_PER_MINUTE:
                return False, f"发送过于频繁，请稍后再试（每分钟最多{_EMAIL_RATE_LIMIT_MAX_PER_MINUTE}封邮件）"

            # 增加计数
            await cache_service.set(rate_key, str(count + 1), expire=_EMAIL_RATE_LIMIT_WINDOW_SECONDS)
            return True, ""
        except (ConnectionError, TimeoutError) as e:
            # 缓存不可用时，允许发送但记录警告
            logger.warning(
                f"Cache unavailable for rate limiting, allowing email send: {e}")
            return True, ""
        except Exception as e:
            logger.error(f"Unexpected error checking rate limit: {e}")
            return True, ""

    def configure(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_user: str,
        smtp_password: str,
        from_email: str | None = None,
        from_name: str | None = None,
        use_tls: bool | None = None,
        start_tls: bool | None = None,
    ) -> None:
        """配置 SMTP 服务器

        Args:
            smtp_host: SMTP 服务器地址
            smtp_port: SMTP 端口
            smtp_user: SMTP 用户名
            smtp_password: SMTP 密码
            from_email: 发件人邮箱（可选）
            from_name: 发件人名称（可选）
            use_tls: 是否使用隐式 TLS（可选）
            start_tls: 是否使用 STARTTLS（可选）
        """
        self.last_error = None
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password

        # TLS 默认策略：465 走 implicit TLS（use_tls=True），587 走
        # STARTTLS（start_tls=True）
        inferred_use_tls = bool(int(smtp_port) == 465)
        inferred_start_tls = not inferred_use_tls
        self.smtp_use_tls = bool(
            inferred_use_tls if use_tls is None else use_tls)
        self.smtp_start_tls = bool(
            inferred_start_tls if start_tls is None else start_tls)

        if from_email:
            self.from_email = from_email
        if from_name:
            self.from_name = from_name

    async def configure_from_db(self, db: AsyncSession) -> bool:
        """从数据库配置 SMTP 服务器

        Args:
            db: 数据库会话

        Returns:
            是否配置成功
        """
        # Avoid stale singleton state: always reset before loading from DB.
        self.smtp_host = None
        self.smtp_user = None
        self.smtp_password = None
        self.smtp_port = 587
        self.smtp_use_tls = False
        self.smtp_start_tls = True
        self.last_error = None

        keys = [
            "EMAIL_SMTP_HOST",
            "EMAIL_SMTP_PORT",
            "EMAIL_SMTP_USER",
            "EMAIL_FROM_EMAIL",
            "EMAIL_FROM_NAME",
            "EMAIL_SMTP_USE_TLS",
            "EMAIL_SMTP_START_TLS",
        ]

        res = await db.execute(select(SystemConfig).where(SystemConfig.key.in_(keys)))
        cfg_rows = res.scalars().all()
        cfg: dict[str, str] = {}
        for row in cfg_rows:
            if row.value is None:
                continue
            v = str(row.value).strip()
            if not v:
                continue
            cfg[str(row.key)] = v

        sec_key = "EMAIL_SMTP_PASSWORD"
        sec_res = await db.execute(select(SystemSecret).where(SystemSecret.key == sec_key))
        sec_row = sec_res.scalar_one_or_none()
        decrypted_password = ""
        if sec_row is not None and sec_row.value is not None:
            decrypted_password = decrypt_secret(str(sec_row.value))

        smtp_host = str(cfg.get("EMAIL_SMTP_HOST", "")).strip()
        smtp_user = str(cfg.get("EMAIL_SMTP_USER", "")).strip()
        from_email = (str(cfg.get("EMAIL_FROM_EMAIL", "")).strip() or None)
        from_name = (str(cfg.get("EMAIL_FROM_NAME", "")).strip() or None)

        if not from_email:
            from_email = smtp_user

        port_raw = str(cfg.get("EMAIL_SMTP_PORT", "587")).strip() or "587"
        try:
            smtp_port = int(port_raw)
        except Exception:
            smtp_port = 587

        def _parse_bool(raw: str | None) -> bool | None:
            if raw is None:
                return None
            s = str(raw).strip().lower()
            if not s:
                return None
            if s in {"1", "true", "yes", "y", "on"}:
                return True
            if s in {"0", "false", "no", "n", "off"}:
                return False
            return None

        use_tls = _parse_bool(cfg.get("EMAIL_SMTP_USE_TLS"))
        start_tls = _parse_bool(cfg.get("EMAIL_SMTP_START_TLS"))

        if not (smtp_host and smtp_user and decrypted_password):
            return False

        self.configure(
            smtp_host=smtp_host,
            smtp_port=int(smtp_port),
            smtp_user=smtp_user,
            smtp_password=str(decrypted_password),
            from_email=from_email,
            from_name=from_name,
            use_tls=use_tls,
            start_tls=start_tls,
        )
        return True

    @property
    def is_configured(self) -> bool:
        """检查是否已配置"""
        return bool(self.smtp_host and self.smtp_user and self.smtp_password)

    async def _send_mime_message(self, message) -> bool:
        """统一的邮件发送方法

        Args:
            message: MIME 消息对象

        Returns:
            是否发送成功
        """
        try:
            import importlib
            aiosmtplib = importlib.import_module("aiosmtplib")

            await aiosmtplib.send(
                message,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_user,
                password=self.smtp_password,
                use_tls=bool(self.smtp_use_tls),
                start_tls=bool(self.smtp_start_tls),
                timeout=self.SMTP_TIMEOUT,
            )
            return True
        except ImportError:
            logger.error(
                "aiosmtplib not installed. Run: pip install aiosmtplib")
            self.last_error = "aiosmtplib not installed"
            return False
        except TimeoutError as e:
            logger.error(f"SMTP connection timeout: {e}")
            self.last_error = str(e)
            return False
        except ConnectionError as e:
            logger.error(f"SMTP connection error: {e}")
            self.last_error = str(e)
            return False
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            self.last_error = str(e)
            return False

    def _create_message(
        self,
        to_email: str,
        subject: str,
        text_content: str,
        html_content: str | None = None,
    ) -> MIMEMultipart:
        """创建 MIME 消息

        Args:
            to_email: 收件人邮箱
            subject: 邮件主题
            text_content: 纯文本内容
            html_content: HTML 内容（可选）

        Returns:
            MIME 消息对象
        """
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        from_name = str(self.from_name or "").strip()
        from_email = str(self.from_email or "").strip()
        message["From"] = formataddr(
            (str(Header(from_name, "utf-8")), from_email))
        message["To"] = to_email

        message.attach(MIMEText(text_content, "plain", "utf-8"))
        if html_content:
            message.attach(MIMEText(html_content, "html", "utf-8"))

        return message

    async def send_password_reset_email(
        self,
        email: str,
        reset_token: str,
        reset_url: str,
        user_id: int | None = None,
    ) -> bool:
        """发送密码重置邮件

        Args:
            email: 收件人邮箱
            reset_token: 重置令牌
            reset_url: 重置链接
            user_id: 用户ID（用于限流）

        Returns:
            是否发送成功
        """
        # 检查限流
        allowed, error_msg = await self._check_rate_limit(user_id=user_id, email=email)
        if not allowed:
            logger.warning(f"Rate limit exceeded for {email}: {error_msg}")
            return False

        if not self.is_configured:
            logger.warning("Email service not configured, skipping email send")
            # 开发模式：打印令牌
            settings = get_settings()
            if bool(settings.debug):
                logger.info(
                    f"[DEV] Password reset token for {email}: {reset_token}")
                logger.info(f"[DEV] Reset URL: {reset_url}")
                return True
            self.last_error = "Email service not configured"
            return False

        try:
            text_content = get_password_reset_text_template(reset_url)
            html_content = get_password_reset_html_template(reset_url)

            message = self._create_message(
                to_email=email,
                subject="密码重置 - 百姓法律助手",
                text_content=text_content,
                html_content=html_content,
            )

            success = await self._send_mime_message(message)
            if success:
                logger.info(f"Password reset email sent to {email}")
            return success
        except Exception as e:
            logger.error(f"Failed to prepare password reset email: {e}")
            self.last_error = str(e)
            return False

    async def send_notification_email(
        self,
        email: str,
        subject: str,
        content: str,
        user_id: int | None = None,
    ) -> bool:
        """发送通知邮件

        Args:
            email: 收件人邮箱
            subject: 邮件主题
            content: 邮件内容
            user_id: 用户ID（用于限流）

        Returns:
            是否发送成功
        """
        # 检查限流
        allowed, error_msg = await self._check_rate_limit(user_id=user_id, email=email)
        if not allowed:
            logger.warning(f"Rate limit exceeded for {email}: {error_msg}")
            return False

        if not self.is_configured:
            logger.warning("Email service not configured")
            self.last_error = "Email service not configured"
            return False

        try:
            message = MIMEText(content, "plain", "utf-8")
            message["Subject"] = subject
            from_name = str(self.from_name or "").strip()
            from_email = str(self.from_email or "").strip()
            message["From"] = formataddr(
                (str(Header(from_name, "utf-8")), from_email))
            message["To"] = email

            success = await self._send_mime_message(message)
            if success:
                logger.info(f"Notification email sent to {email}")
            return success
        except Exception as e:
            logger.error(f"Failed to prepare notification email: {e}")
            self.last_error = str(e)
            return False

    async def send_email_verification_email(
        self,
        email: str,
        verify_url: str,
        user_id: int | None = None,
    ) -> bool:
        """发送邮箱验证邮件

        Args:
            email: 收件人邮箱
            verify_url: 验证链接
            user_id: 用户ID（用于限流）

        Returns:
            是否发送成功
        """
        # 检查限流
        allowed, error_msg = await self._check_rate_limit(user_id=user_id, email=email)
        if not allowed:
            logger.warning(f"Rate limit exceeded for {email}: {error_msg}")
            return False

        if not self.is_configured:
            logger.warning("Email service not configured, skipping email send")
            settings = get_settings()
            if bool(settings.debug):
                logger.info(
                    f"[DEV] Email verification url for {email}: {verify_url}")
                return True
            self.last_error = "Email service not configured"
            return False

        try:
            text_content = get_email_verification_text_template(verify_url)
            html_content = get_email_verification_html_template(verify_url)

            message = self._create_message(
                to_email=email,
                subject="邮箱验证 - 百姓法律助手",
                text_content=text_content,
                html_content=html_content,
            )

            success = await self._send_mime_message(message)
            if success:
                logger.info(f"Email verification email sent to {email}")
            return success
        except Exception as e:
            logger.error(f"Failed to prepare email verification email: {e}")
            self.last_error = str(e)
            return False

    # =========================================================================
    # 密码重置令牌方法（委托给 password_reset_service）
    # =========================================================================

    async def generate_reset_token(self, user_id: int, email: str) -> str:
        """生成密码重置令牌"""
        return await password_reset_service.generate_reset_token(user_id, email)

    async def verify_reset_token(
            self, token: str) -> EmailServiceResetTokenData | None:
        """验证密码重置令牌"""
        return await password_reset_service.verify_reset_token(token)

    async def invalidate_token(self, token: str) -> None:
        """使密码重置令牌失效"""
        await password_reset_service.invalidate_token(token)

    # =========================================================================
    # 邮箱验证令牌方法（委托给 email_verification_service）
    # =========================================================================

    async def generate_email_verification_token(
            self, user_id: int, email: str) -> str:
        """生成邮箱验证令牌"""
        return await email_verification_service.generate_token(user_id, email)

    async def verify_email_verification_token(
            self, token: str) -> EmailVerificationTokenData | None:
        """验证邮箱验证令牌"""
        return await email_verification_service.verify_token(token)

    async def invalidate_email_verification_token(self, token: str) -> None:
        """使邮箱验证令牌失效"""
        await email_verification_service.invalidate_token(token)

    def _cleanup_expired_tokens(self) -> None:
        """清理过期的令牌（密码重置和邮箱验证）"""
        password_reset_service._cleanup_expired_tokens()
        email_verification_service._cleanup_expired_tokens()


# 单例实例
email_service = EmailService()
