"""律师工作台服务

提供线索管理、数据看板、模板库等律师增值功能。
"""
import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


class LeadManager:
    """线索管理器"""

    def __init__(self):
        self._leads: dict[int, dict[str, Any]] = {}
        self._lead_history: list[dict[str, Any]] = []

    async def create_lead(
        self,
        lawyer_id: int,
        client_name: str,
        client_phone: str,
        case_type: str,
        description: str,
        source: str = "web",
    ) -> dict[str, Any]:
        """创建线索

        Args:
            lawyer_id: 律师ID
            client_name: 客户姓名
            client_phone: 客户电话
            case_type: 案件类型
            description: 描述
            source: 来源

        Returns:
            线索信息
        """
        lead_id = len(self._leads) + 1
        now = datetime.now(timezone.utc).isoformat()

        lead: dict[str, Any] = {
            "id": lead_id,
            "lawyer_id": lawyer_id,
            "client_name": client_name,
            "client_phone": client_phone,
            "case_type": case_type,
            "description": description,
            "source": source,
            "status": "new",
            "created_at": now,
            "updated_at": now,
            "follow_ups": 0,
            "converted": False,
        }

        self._leads[lead_id] = lead

        logger.info(f"Created lead {lead_id} for lawyer {lawyer_id}")

        return {
            "lead_id": lead_id,
            "status": "new",
            "created_at": now,
        }

    async def update_lead_status(
        self,
        lead_id: int,
        status: str,
        notes: str | None = None,
    ) -> dict[str, Any]:
        """更新线索状态

        Args:
            lead_id: 线索ID
            status: 状态
            notes: 备注

        Returns:
            更新结果
        """
        lead = self._leads.get(lead_id)

        if not lead:
            return {
                "success": False,
                "error": "线索不存在",
            }

        lead["status"] = status
        lead["updated_at"] = datetime.now(timezone.utc).isoformat()

        if notes:
            lead["notes"] = notes

        logger.info(f"Updated lead {lead_id} status to {status}")

        return {
            "success": True,
            "lead_id": lead_id,
            "new_status": status,
        }

    async def get_leads(
        self,
        lawyer_id: int,
        status: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """获取线索列表

        Args:
            lawyer_id: 律师ID
            status: 状态筛选
            limit: 限制数量

        Returns:
            线索列表
        """
        leads = [
            lead for lead in self._leads.values()
            if lead["lawyer_id"] == lawyer_id
        ]

        if status:
            leads = [l for l in leads if l["status"] == status]

        return leads[:limit]

    def get_lead_stats(self, lawyer_id: int) -> dict[str, Any]:
        """获取线索统计

        Args:
            lawyer_id: 律师ID

        Returns:
            统计信息
        """
        lawyer_leads = [
            lead for lead in self._leads.values()
            if lead["lawyer_id"] == lawyer_id
        ]

        new_count = sum(1 for l in lawyer_leads if l["status"] == "new")
        contact_count = sum(
            1 for l in lawyer_leads if l["status"] == "contacted")
        converted_count = sum(1 for l in lawyer_leads if l["converted"])

        return {
            "total": len(lawyer_leads),
            "new": new_count,
            "contacted": contact_count,
            "converted": converted_count,
            "conversion_rate": f"{(converted_count / len(lawyer_leads) * 100):.1f}%" if lawyer_leads else "0%",
        }


class DashboardManager:
    """数据看板管理器"""

    def __init__(self):
        self._metrics: dict[str, dict[str, Any]] = {}

    async def record_metric(
        self,
        lawyer_id: int,
        metric_type: str,
        value: int | float,
    ) -> None:
        """记录指标

        Args:
            lawyer_id: 律师ID
            metric_type: 指标类型
            value: 值
        """
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        key = f"{lawyer_id}_{metric_type}_{date}"
        self._metrics[key] = {
            "lawyer_id": lawyer_id,
            "metric_type": metric_type,
            "date": date,
            "value": value,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

    async def get_dashboard(
        self,
        lawyer_id: int,
        days: int = 7,
    ) -> dict[str, Any]:
        """获取看板数据

        Args:
            lawyer_id: 律师ID
            days: 天数

        Returns:
            看板数据
        """
        end_date = datetime.now(timezone.utc)
        _ = end_date.replace(
            day=end_date.day - days
        )

        metrics: dict[str, list[dict[str, Any]]] = {}
        for _, metric in self._metrics.items():
            if metric["lawyer_id"] == lawyer_id:
                if metric["metric_type"] not in metrics:
                    metrics[metric["metric_type"]] = []
                metrics[metric["metric_type"]].append(metric)

        return {
            "lawyer_id": lawyer_id,
            "period_days": days,
            "metrics": metrics,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    def get_summary(self, lawyer_id: int) -> dict[str, Any]:
        """获取摘要

        Args:
            lawyer_id: 律师ID

        Returns:
            摘要信息
        """
        lawyer_metrics = {
            k: v for k, v in self._metrics.items()
            if v["lawyer_id"] == lawyer_id
        }

        total_consultations = sum(
            m["value"] for m in lawyer_metrics.values()
            if m["metric_type"] == "consultation"
        )

        total_cases = sum(
            m["value"] for m in lawyer_metrics.values()
            if m["metric_type"] == "case"
        )

        return {
            "lawyer_id": lawyer_id,
            "total_consultations": total_consultations,
            "total_cases": total_cases,
            "active_cases": total_cases,
            "pending_tasks": 0,
        }


class TemplateLibrary:
    """模板库"""

    def __init__(self):
        self._templates: dict[str, dict[str, Any]] = {}
        self._categories: list[str] = [
            "合同审查",
            "法律意见书",
            "诉讼文书",
            "非诉文书",
            "咨询记录",
        ]

    def add_template(
        self,
        name: str,
        category: str,
        content: str,
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        """添加模板

        Args:
            name: 模板名称
            category: 分类
            content: 内容
            tags: 标签

        Returns:
            模板信息
        """
        template_id = f"TPL-{len(self._templates) + 1:04d}"
        now = datetime.now(timezone.utc).isoformat()

        template: dict[str, Any] = {
            "id": template_id,
            "name": name,
            "category": category,
            "content": content,
            "tags": tags or [],
            "created_at": now,
            "updated_at": now,
            "usage_count": 0,
        }

        self._templates[template_id] = template

        logger.info(f"Added template {template_id}: {name}")

        return {
            "template_id": template_id,
            "name": name,
            "category": category,
        }

    def get_templates(
        self,
        category: str | None = None,
        tags: list[str] | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """获取模板列表

        Args:
            category: 分类筛选
            tags: 标签筛选
            limit: 限制数量

        Returns:
            模板列表
        """
        templates = list(self._templates.values())

        if category:
            templates = [t for t in templates if t["category"] == category]

        if tags:
            templates = [
                t for t in templates
                if any(tag in t["tags"] for tag in tags)
            ]

        return templates[:limit]

    def search_templates(
        self,
        query: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """搜索模板

        Args:
            query: 搜索词
            limit: 限制数量

        Returns:
            模板列表
        """
        query = query.lower()
        results = [
            t for t in self._templates.values()
            if query in t["name"].lower()
            or query in t["content"].lower()
            or any(query in tag for tag in t["tags"])
        ]

        return results[:limit]

    def get_categories(self) -> list[str]:
        """获取分类列表

        Returns:
            分类列表
        """
        return self._categories

    def increment_usage(self, template_id: str) -> None:
        """增加使用次数

        Args:
            template_id: 模板ID
        """
        if template_id in self._templates:
            self._templates[template_id]["usage_count"] += 1


class LawyerWorkbenchService:
    """律师工作台服务"""

    def __init__(self):
        self.lead_manager = LeadManager()
        self.dashboard_manager = DashboardManager()
        self.template_library = TemplateLibrary()

    async def get_workbench_overview(self, lawyer_id: int) -> dict[str, Any]:
        """获取工作台概览

        Args:
            lawyer_id: 律师ID

        Returns:
            概览信息
        """
        lead_stats = self.lead_manager.get_lead_stats(lawyer_id)
        dashboard = await self.dashboard_manager.get_dashboard(lawyer_id)
        recent_templates = self.template_library.get_templates(limit=5)

        return {
            "lawyer_id": lawyer_id,
            "leads": lead_stats,
            "dashboard": dashboard,
            "recent_templates": recent_templates,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }


# 单例实例
lawyer_workbench_service = LawyerWorkbenchService()


async def create_lead(
    lawyer_id: int,
    client_name: str,
    client_phone: str,
    case_type: str,
    description: str,
    source: str = "web",
) -> dict[str, Any]:
    """便捷函数：创建线索

    Args:
        lawyer_id: 律师ID
        client_name: 客户姓名
        client_phone: 客户电话
        case_type: 案件类型
        description: 描述
        source: 来源

    Returns:
        线索信息
    """
    return await lawyer_workbench_service.lead_manager.create_lead(
        lawyer_id=lawyer_id,
        client_name=client_name,
        client_phone=client_phone,
        case_type=case_type,
        description=description,
        source=source,
    )


async def update_lead_status(
    lead_id: int,
    status: str,
    notes: str | None = None,
) -> dict[str, Any]:
    """便捷函数：更新线索状态

    Args:
        lead_id: 线索ID
        status: 状态
        notes: 备注

    Returns:
        更新结果
    """
    return await lawyer_workbench_service.lead_manager.update_lead_status(
        lead_id=lead_id,
        status=status,
        notes=notes,
    )


async def get_leads(
    lawyer_id: int,
    status: str | None = None,
) -> list[dict[str, Any]]:
    """便捷函数：获取线索列表

    Args:
        lawyer_id: 律师ID
        status: 状态筛选

    Returns:
        线索列表
    """
    return await lawyer_workbench_service.lead_manager.get_leads(
        lawyer_id=lawyer_id,
        status=status,
    )


async def get_dashboard(
    lawyer_id: int,
    days: int = 7,
) -> dict[str, Any]:
    """便捷函数：获取数据看板

    Args:
        lawyer_id: 律师ID
        days: 天数

    Returns:
        看板数据
    """
    return await lawyer_workbench_service.dashboard_manager.get_dashboard(
        lawyer_id=lawyer_id,
        days=days,
    )


def search_templates(
    query: str,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """便捷函数：搜索模板

    Args:
        query: 搜索词
        limit: 限制数量

    Returns:
        模板列表
    """
    return lawyer_workbench_service.template_library.search_templates(
        query=query,
        limit=limit,
    )
