"""通知模板服务"""
from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class TemplateVariable:
    name: str
    description: str


@dataclass
class NotificationTemplate:
    name: str
    title_template: str
    content_template: str
    variables: Dict[str, TemplateVariable]
    default_channels: list = None

    def render(self, variables: Dict[str, str]) -> Dict[str, str]:
        """渲染模板"""
        title = self.title_template
        content = self.content_template

        for key, value in variables.items():
            placeholder = f"{{{key}}}"
            title = title.replace(placeholder, value)
            content = content.replace(placeholder, value)

        return {
            "title": title,
            "content": content,
        }


class TemplateService:
    """通知模板服务"""

    def __init__(self):
        self._templates: Dict[str, NotificationTemplate] = {}
        self._register_default_templates()

    def _register_default_templates(self):
        """注册默认模板"""
        self.register(
            NotificationTemplate(
                name="system_announcement",
                title_template="{title}",
                content_template="{content}",
                variables={
                    "title": TemplateVariable("title", "公告标题"),
                    "content": TemplateVariable("content", "公告内容"),
                },
                default_channels=["push", "email"],
            )
        )

        self.register(
            NotificationTemplate(
                name="order_status_change",
                title_template="订单状态更新",
                content_template="您的订单 {order_id} 状态已变更为 {status}",
                variables={
                    "order_id": TemplateVariable("order_id", "订单ID"),
                    "status": TemplateVariable("status", "订单状态"),
                },
                default_channels=["push", "sms"],
            )
        )

        self.register(
            NotificationTemplate(
                name="new_comment",
                title_template="收到新评论",
                content_template="您的{item_type}收到了来自 {username} 的评论",
                variables={
                    "item_type": TemplateVariable("item_type", "项目类型"),
                    "username": TemplateVariable("username", "用户名"),
                },
                default_channels=["push"],
            )
        )

        self.register(
            NotificationTemplate(
                name="consultation_reply",
                title_template="咨询回复",
                content_template="律师 {lawyer_name} 已回复您的咨询",
                variables={
                    "lawyer_name": TemplateVariable("lawyer_name", "律师姓名"),
                },
                default_channels=["push", "sms"],
            )
        )

        self.register(
            NotificationTemplate(
                name="payment_success",
                title_template="支付成功",
                content_template="您已成功支付 {amount} 元，订单号 {order_id}",
                variables={
                    "amount": TemplateVariable("amount", "支付金额"),
                    "order_id": TemplateVariable("order_id", "订单号"),
                },
                default_channels=["push", "sms", "email"],
            )
        )

    def register(self, template: NotificationTemplate):
        """注册模板"""
        self._templates[template.name] = template

    def get(self, name: str) -> Optional[NotificationTemplate]:
        """获取模板"""
        return self._templates.get(name)

    def render(self, template_name: str, variables: Dict[str, str]) -> Optional[Dict[str, str]]:
        """渲染模板"""
        template = self.get(template_name)
        if not template:
            return None

        return template.render(variables)

    def list_templates(self) -> list:
        """列出所有模板"""
        return list(self._templates.keys())


template_service = TemplateService()
