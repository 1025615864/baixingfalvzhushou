"""Email optimizer service."""
from __future__ import annotations
import re
from typing import Optional
from datetime import datetime, timezone


class EmailTemplateManager:
    _templates: dict[str, dict] = {
        "password_reset": {
            "text": "您好，请点击以下链接重置密码：{reset_url}",
            "html": "<!DOCTYPE html><html><body><p>您好，请点击以下链接重置密码：<a href=\"{reset_url}\">{reset_url}</a></p></body></html>",
            "subject": "密码重置",
        },
        "email_verification": {
            "text": "请点击以下链接验证邮箱：{verify_url}",
            "html": "<!DOCTYPE html><html><body><p>请点击以下链接验证邮箱：<a href=\"{verify_url}\">{verify_url}</a></p></body></html>",
            "subject": "邮箱验证",
        },
    }

    @staticmethod
    def get_template(name: str, fmt: str = "text") -> Optional[str]:
        tpl = EmailTemplateManager._templates.get(name)
        if tpl is None:
            return None
        return tpl.get(fmt)

    @staticmethod
    def render_template(name: str, context: dict) -> str:
        tpl = EmailTemplateManager.get_template(name, "text")
        if tpl is None:
            return ""
        result = tpl
        for key, value in context.items():
            result = result.replace(f"{{{key}}}", str(value))
        return result

    @staticmethod
    def render_html_template(name: str, context: dict) -> str:
        tpl = EmailTemplateManager.get_template(name, "html")
        if tpl is None:
            return ""
        result = tpl
        for key, value in context.items():
            result = result.replace(f"{{{key}}}", str(value))
        return result

    @staticmethod
    def get_subject(name: str) -> str:
        tpl = EmailTemplateManager._templates.get(name)
        if tpl is None:
            return ""
        return tpl.get("subject", "")


class EmailMetrics:
    def __init__(self):
        self._stats: dict[str, list] = {"sent": [], "failed": []}

    async def record_send(self, template_name: str, success: bool, error: Optional[str] = None) -> None:
        entry = {
            "template": template_name,
            "success": success,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if not success and error:
            entry["error"] = error
        if success:
            self._stats["sent"].append(entry)
        else:
            self._stats["failed"].append(entry)

    async def get_delivery_stats(self, template_name: Optional[str] = None, period_days: int = 30) -> dict:
        total_sent = len(self._stats["sent"])
        total_failed = len(self._stats["failed"])
        total = total_sent + total_failed
        delivery_rate = total_sent / total if total > 0 else 0.0
        by_template: dict[str, dict] = {}
        for entry in self._stats["sent"]:
            t = entry.get("template", "unknown")
            by_template.setdefault(t, {"sent": 0, "failed": 0})
            by_template[t]["sent"] += 1
        for entry in self._stats["failed"]:
            t = entry.get("template", "unknown")
            by_template.setdefault(t, {"sent": 0, "failed": 0})
            by_template[t]["failed"] += 1
        return {
            "period_days": period_days,
            "total_sent": total_sent,
            "total_failed": total_failed,
            "delivery_rate": delivery_rate,
            "by_template": by_template,
        }


class OptimizedEmailService:
    def __init__(self):
        self._template_manager = EmailTemplateManager()
        self._metrics = EmailMetrics()
        self._rules: list[dict] = []

    def optimize(self, subject: Optional[str] = None, body: Optional[str] = None, **kwargs) -> dict:
        result = {}
        if subject is not None:
            result["subject"] = subject.strip()
        else:
            result["subject"] = ""
        if body is not None:
            result["body"] = self._clean_body(body)
        else:
            result["body"] = ""
        return result

    def _clean_body(self, body: str) -> str:
        body = re.sub(r'\n{3,}', '\n\n', body)
        return body.strip()

    def add_rule(self, rule_name: str, rule_func=None) -> None:
        self._rules.append({"name": rule_name, "func": rule_func})

    def get_rules(self) -> list[dict]:
        return list(self._rules)

    async def send_email(self, to: str, subject: str, body: str, template_name: Optional[str] = None, context: Optional[dict] = None) -> dict:
        if template_name and context:
            body = self._template_manager.render_template(template_name, context)
        await self._metrics.record_send(template_name or "direct", True)
        return {"success": True, "to": to, "subject": subject}

    async def send_templated_email(self, template_name: str, to: str, context: dict) -> tuple[bool, str]:
        try:
            email_svc = email_service
            if not email_svc.is_configured:
                return False, "Email service not configured"
            text = self._template_manager.render_template(template_name, context)
            html = self._template_manager.render_html_template(template_name, context)
            subject = self._template_manager.get_subject(template_name)
            msg = email_svc._create_message(to, subject, text, html)
            result = await email_svc._send_mime_message(msg)
            if result:
                await self._metrics.record_send(template_name, True)
                return True, ""
            else:
                await self._metrics.record_send(template_name, False, email_svc.last_error or "Send failed")
                return False, email_svc.last_error or "Send failed"
        except Exception as e:
            await self._metrics.record_send(template_name, False, str(e))
            return False, str(e)

    async def get_delivery_report(self) -> dict:
        return await self._metrics.get_delivery_stats()

    def get_metrics(self) -> dict:
        return {"sent": len(self._metrics._stats["sent"]), "failed": len(self._metrics._stats["failed"])}


try:
    from app.services.email_service import email_service
except ImportError:
    email_service = None

EmailOptimizer = OptimizedEmailService

optimized_email_service = OptimizedEmailService()


async def send_email_with_template(template_name: str, to: str, context: dict) -> tuple[bool, str]:
    return await optimized_email_service.send_templated_email(template_name, to, context)


async def get_email_delivery_report() -> dict:
    return await optimized_email_service.get_delivery_report()
