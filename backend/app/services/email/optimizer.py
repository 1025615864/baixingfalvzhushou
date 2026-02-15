"""邮件服务优化工具

提供模板管理和送达率监控功能。
"""
import logging
from datetime import datetime, timezone
from typing import Any, Dict

from .core import email_service

logger = logging.getLogger(__name__)


class EmailTemplateManager:
    """邮件模板管理器"""

    TEMPLATES: dict[str, dict[str, str]] = {
        "password_reset": {
            "subject": "密码重置 - 百姓法律助手",
            "text_template": "请访问以下链接重置密码：{reset_url}\n\n链接有效期：24小时\n\n如果这不是您的请求，请忽略此邮件。",
            "html_template": """
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: Arial, sans-serif; line-height: 1.6;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #333;">密码重置</h2>
        <p>您好，</p>
        <p>请点击下方按钮重置密码：</p>
        <p><a href="{reset_url}" style="background: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px;">重置密码</a></p>
        <p style="color: #666; font-size: 14px;">链接有效期：24小时</p>
        <p style="color: #999; font-size: 12px;">如果这不是您的请求，请忽略此邮件。</p>
    </div>
</body>
</html>
""",
        },
        "email_verification": {
            "subject": "邮箱验证 - 百姓法律助手",
            "text_template": "请访问以下链接验证邮箱：{verify_url}\n\n链接有效期：24小时\n\n如果这不是您的请求，请忽略此邮件。",
            "html_template": """
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: Arial, sans-serif; line-height: 1.6;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #333;">邮箱验证</h2>
        <p>您好，</p>
        <p>请点击下方按钮验证邮箱：</p>
        <p><a href="{verify_url}" style="background: #28a745; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px;">验证邮箱</a></p>
        <p style="color: #666; font-size: 14px;">链接有效期：24小时</p>
        <p style="color: #999; font-size: 12px;">如果这不是您的请求，请忽略此邮件。</p>
    </div>
</body>
</html>
""",
        },
        "notification": {
            "subject": "通知 - 百姓法律助手",
            "text_template": "{content}",
            "html_template": """
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: Arial, sans-serif; line-height: 1.6;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #333;">通知</h2>
        <p>{content}</p>
    </div>
</body>
</html>
""",
        },
    }

    @classmethod
    def get_template(cls, template_name: str,
                     template_type: str = "text") -> str | None:
        """获取模板

        Args:
            template_name: 模板名称
            template_type: 模板类型（text/html）

        Returns:
            模板内容
        """
        template = cls.TEMPLATES.get(template_name)
        if not template:
            return None

        key = f"{template_type}_template" if template_type == "text" else "html_template"
        return template.get(key)

    @classmethod
    def render_template(cls, template_name: str,
                        variables: dict[str, Any]) -> str:
        """渲染模板

        Args:
            template_name: 模板名称
            variables: 变量字典

        Returns:
            渲染后的内容
        """
        text_template = cls.get_template(template_name, "text")
        if text_template:
            for key, value in variables.items():
                text_template = text_template.replace(f"{{{key}}}", str(value))
            return text_template
        return ""

    @classmethod
    def render_html_template(cls, template_name: str,
                             variables: dict[str, Any]) -> str:
        """渲染 HTML 模板

        Args:
            template_name: 模板名称
            variables: 变量字典

        Returns:
            渲染后的 HTML 内容
        """
        html_template = cls.get_template(template_name, "html")
        if html_template:
            for key, value in variables.items():
                html_template = html_template.replace(f"{{{key}}}", str(value))
            return html_template
        return ""

    @classmethod
    def get_subject(cls, template_name: str) -> str:
        """获取模板主题"""
        template = cls.TEMPLATES.get(template_name)
        return template.get("subject", "") if template else ""


class EmailMetrics:
    """邮件送达率监控"""

    def __init__(self):
        self._stats: dict[str, dict[str, int]] = {
            "sent": {},
            "delivered": {},
            "failed": {},
            "opened": {},
        }

    async def record_send(
        self,
        template_name: str,
        success: bool,
        error: str | None = None,
    ) -> None:
        """记录发送结果

        Args:
            template_name: 模板名称
            success: 是否发送成功
            error: 错误信息
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        if success:
            key = f"{template_name}:{timestamp}"
            self._stats["sent"][key] = self._stats["sent"].get(key, 0) + 1
        else:
            key = f"{template_name}:{error}:{timestamp}"
            self._stats["failed"][key] = self._stats["failed"].get(key, 0) + 1

    async def get_delivery_stats(
        self,
        template_name: str | None = None,
        days: int = 7,
    ) -> dict[str, Any]:
        """获取送达率统计

        Args:
            template_name: 模板名称（可选）
            days: 统计天数

        Returns:
            统计信息
        """
        stats: Dict[str, Any] = {
            "period_days": days,
            "total_sent": 0,
            "total_delivered": 0,
            "total_failed": 0,
            "delivery_rate": 0.0,
            "by_template": {},
        }

        for template in EmailTemplateManager.TEMPLATES.keys():
            if template_name and template != template_name:
                continue

            sent_key = f"{template}:"
            failed_key = f"{template}:"

            sent_count = sum(
                v for k, v in self._stats["sent"].items()
                if k.startswith(sent_key)
            )
            failed_count = sum(
                v for k, v in self._stats["failed"].items()
                if k.startswith(failed_key)
            )

            total = sent_count + failed_count
            delivery_rate = (sent_count / total * 100) if total > 0 else 0

            stats["by_template"][template] = {
                "sent": sent_count,
                "failed": failed_count,
                "delivery_rate": f"{delivery_rate:.2f}%",
            }

            stats["total_sent"] += sent_count
            stats["total_failed"] += failed_count

        total = stats["total_sent"] + stats["total_failed"]
        stats["total_delivered"] = stats["total_sent"]
        stats["delivery_rate"] = (
            f"{(stats['total_sent'] / total * 100):.2f}%" if total > 0 else "0%"
        )

        return stats


class OptimizedEmailService:
    """优化后的邮件服务"""

    def __init__(self):
        self.template_manager = EmailTemplateManager()
        self.metrics = EmailMetrics()

    async def send_templated_email(
        self,
        template_name: str,
        to_email: str,
        variables: dict[str, Any],
        user_id: int | None = None,
    ) -> tuple[bool, str]:
        """发送模板邮件

        Args:
            template_name: 模板名称
            to_email: 收件人邮箱
            variables: 模板变量
            user_id: 用户ID（用于限流）

        Returns:
            (是否成功, 错误信息)
        """
        subject = self.template_manager.get_subject(template_name)
        text_content = self.template_manager.render_template(
            template_name, variables)
        html_content = self.template_manager.render_html_template(
            template_name, variables)

        if not email_service.is_configured:
            logger.warning("Email service not configured")
            return False, "Email service not configured"

        try:
            message = email_service._create_message(
                to_email=to_email,
                subject=subject,
                text_content=text_content,
                html_content=html_content,
            )

            success = await email_service._send_mime_message(message)

            await self.metrics.record_send(
                template_name=template_name,
                success=success,
                error=None if success else "send_failed",
            )

            if success:
                logger.info(
                    f"Templated email sent: {template_name} to {to_email}")
            else:
                logger.error(
                    f"Failed to send email: {template_name} to {to_email}")

            return success, email_service.last_error or ""
        except Exception as e:
            logger.error(f"Error sending templated email: {e}")
            await self.metrics.record_send(
                template_name=template_name,
                success=False,
                error=str(e),
            )
            return False, str(e)

    async def get_delivery_report(
            self, template_name: str | None = None) -> dict[str, Any]:
        """获取送达率报告

        Args:
            template_name: 模板名称（可选）

        Returns:
            报告信息
        """
        return await self.metrics.get_delivery_stats(template_name)


# 单例实例
optimized_email_service = OptimizedEmailService()


async def send_email_with_template(
    template_name: str,
    to_email: str,
    variables: dict[str, Any],
    user_id: int | None = None,
) -> tuple[bool, str]:
    """便捷函数：发送模板邮件

    Args:
        template_name: 模板名称
        to_email: 收件人邮箱
        variables: 模板变量
        user_id: 用户ID（用于限流）

    Returns:
        (是否成功, 错误信息)
    """
    return await optimized_email_service.send_templated_email(
        template_name=template_name,
        to_email=to_email,
        variables=variables,
        user_id=user_id,
    )


async def get_email_delivery_report(
    template_name: str | None = None,
) -> dict[str, Any]:
    """获取邮件送达率报告

    Args:
        template_name: 模板名称（可选）

    Returns:
        报告信息
    """
    return await optimized_email_service.get_delivery_report(template_name)
