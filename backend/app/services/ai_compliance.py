"""AI 合规声明与用户知情同意工具

提供 AI 服务使用声明、用户知情同意和合规日志功能。
"""
import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import Request

logger = logging.getLogger(__name__)

# 合规声明文本
AI_COMPLIANCE_STATEMENT = """
【AI 法律助手服务声明】

1. AI 辅助性质
本服务提供的法律建议由 AI 模型生成，仅供参考，不构成正式法律意见。实际法律问题请咨询专业律师。

2. 数据使用声明
- 您输入的内容将用于 AI 模型推理，以提供更准确的服务
- 我们不会将您的个人数据用于 AI 模型训练
- 您的咨询记录将按照我们的隐私政策进行处理

3. 免责声明
- AI 生成的建议仅供参考，不保证准确性和完整性
- 对于因使用本服务导致的任何损失，我们不承担责任
- 请在重要法律事务中寻求专业律师的帮助

4. 您的权利
- 您有权随时停止使用本服务
- 您有权请求删除您的历史记录
- 您有权了解您的数据如何被使用

如您继续使用本服务，即表示您已阅读并同意上述声明。
"""

# 简短的知情同意提示
AI_CONSENT_NOTICE = "使用本服务即表示您同意我们的 AI 服务声明和隐私政策"


class AIComplianceService:
    """AI 合规服务"""

    def __init__(self):
        self._consent_records: dict[str, dict[str, Any]] = {}
        self._compliance_logs: list[dict[str, Any]] = []

    async def record_consent(
        self,
        user_id: int,
        consent_type: str = "ai_service",
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> dict[str, Any]:
        """记录用户同意

        Args:
            user_id: 用户ID
            consent_type: 同意类型
            ip_address: IP 地址
            user_agent: 用户代理

        Returns:
            同意记录
        """
        record: dict[str, Any] = {
            "user_id": user_id,
            "consent_type": consent_type,
            "consent_time": datetime.now(timezone.utc).isoformat(),
            "ip_address": ip_address,
            "user_agent": user_agent,
            "version": "1.0",
        }

        key = f"{user_id}:{consent_type}"
        self._consent_records[key] = record

        logger.info(
            f"AI consent recorded for user {user_id}, type: {consent_type}")

        return record

    async def check_consent(
        self,
        user_id: int,
        consent_type: str = "ai_service",
    ) -> dict[str, Any]:
        """检查用户是否已同意

        Args:
            user_id: 用户ID
            consent_type: 同意类型

        Returns:
            同意状态
        """
        key = f"{user_id}:{consent_type}"
        record = self._consent_records.get(key)

        if record:
            return {
                "has_consent": True,
                "consent_time": record.get("consent_time"),
                "version": record.get("version"),
            }

        return {
            "has_consent": False,
            "consent_time": None,
            "version": None,
        }

    async def revoke_consent(
        self,
        user_id: int,
        consent_type: str = "ai_service",
    ) -> bool:
        """撤销用户同意

        Args:
            user_id: 用户ID
            consent_type: 同意类型

        Returns:
            是否成功撤销
        """
        key = f"{user_id}:{consent_type}"

        if key in self._consent_records:
            del self._consent_records[key]
            logger.info(
                f"AI consent revoked for user {user_id}, type: {consent_type}")
            return True

        return False

    async def log_compliance_event(
        self,
        event_type: str,
        user_id: int | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """记录合规事件

        Args:
            event_type: 事件类型
            user_id: 用户ID
            details: 详细信息
        """
        log_entry: dict[str, Any] = {
            "event_type": event_type,
            "user_id": user_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": details or {},
        }

        self._compliance_logs.append(log_entry)

        logger.info(f"AI compliance event: {event_type}, user: {user_id}")

    async def get_compliance_report(
        self,
        days: int = 7,
    ) -> dict[str, Any]:
        """获取合规报告

        Args:
            days: 统计天数

        Returns:
            合规报告
        """
        now = datetime.now(timezone.utc)

        recent_logs = [
            log for log in self._compliance_logs
            if log.get("timestamp")
        ]

        event_counts: dict[str, int] = {}
        for log in recent_logs:
            event_type = log.get("event_type", "unknown")
            event_counts[event_type] = event_counts.get(event_type, 0) + 1

        consent_count = sum(
            1 for record in self._consent_records.values()
            if record.get("consent_type") == "ai_service"
        )

        return {
            "period_days": days,
            "total_consents": consent_count,
            "event_counts": event_counts,
            "compliance_status": "active",
            "generated_at": now.isoformat(),
        }

    def get_statement(self) -> str:
        """获取合规声明文本"""
        return AI_COMPLIANCE_STATEMENT.strip()

    def get_consent_notice(self) -> str:
        """获取简短同意提示"""
        return AI_CONSENT_NOTICE


class AIComplianceMiddleware:
    """AI 合规中间件工具"""

    @staticmethod
    async def extract_consent_info(request: Request) -> dict[str, str | None]:
        """提取请求中的同意相关信息

        Args:
            request: FastAPI 请求

        Returns:
            同意相关信息
        """
        headers = request.headers

        return {
            "ip_address": request.client.host if request.client else None,
            "user_agent": headers.get("User-Agent"),
            "consent_version": headers.get("X-AI-Consent-Version"),
        }

    @staticmethod
    async def check_consent_header(request: Request) -> bool:
        """检查请求头中的同意标记

        Args:
            request: FastAPI 请求

        Returns:
            是否已同意
        """
        consent_header = request.headers.get("X-AI-Consent-Accepted")
        return consent_header == "true"


# 单例实例
ai_compliance_service = AIComplianceService()


async def record_ai_consent(
    user_id: int,
    consent_type: str = "ai_service",
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> dict[str, Any]:
    """便捷函数：记录 AI 服务同意

    Args:
        user_id: 用户ID
        consent_type: 同意类型
        ip_address: IP 地址
        user_agent: 用户代理

    Returns:
        同意记录
    """
    return await ai_compliance_service.record_consent(
        user_id=user_id,
        consent_type=consent_type,
        ip_address=ip_address,
        user_agent=user_agent,
    )


async def check_ai_consent(user_id: int) -> dict[str, Any]:
    """便捷函数：检查用户 AI 服务同意状态

    Args:
        user_id: 用户ID

    Returns:
        同意状态
    """
    return await ai_compliance_service.check_consent(user_id)


def get_ai_statement() -> str:
    """获取 AI 服务合规声明"""
    return ai_compliance_service.get_statement()


def get_ai_consent_notice() -> str:
    """获取 AI 服务简短同意提示"""
    return ai_compliance_service.get_consent_notice()
