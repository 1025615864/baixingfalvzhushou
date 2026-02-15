"""企业合规SaaS服务

提供合同审查、合规模板库等企业合规功能。
"""
import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


class EnterpriseAccountManager:
    """企业账号管理器"""

    def __init__(self):
        self._accounts: dict[int, dict[str, Any]] = {}
        self._users: dict[int, dict[str, Any]] = {}

    async def create_enterprise_account(
        self,
        company_name: str,
        admin_email: str,
        industry: str = "general",
        scale: str = "smb",
    ) -> dict[str, Any]:
        """创建企业账号

        Args:
            company_name: 公司名称
            admin_email: 管理员邮箱
            industry: 行业
            scale: 规模

        Returns:
            账号信息
        """
        account_id = len(self._accounts) + 1
        now = datetime.now(timezone.utc).isoformat()

        account = {
            "id": account_id,
            "company_name": company_name,
            "admin_email": admin_email,
            "industry": industry,
            "scale": scale,
            "status": "active",
            "created_at": now,
            "updated_at": now,
            "subscription_plan": "basic",
            "max_users": 10,
            "max_contracts": 100,
        }

        self._accounts[account_id] = account

        logger.info(
            f"Created enterprise account {account_id} for {company_name}")

        return {
            "account_id": account_id,
            "company_name": company_name,
            "status": "active",
            "created_at": now,
        }

    async def get_account(self, account_id: int) -> dict[str, Any] | None:
        """获取企业账号

        Args:
            account_id: 账号ID

        Returns:
            账号信息
        """
        return self._accounts.get(account_id)

    async def update_account(
        self,
        account_id: int,
        **kwargs,
    ) -> dict[str, Any]:
        """更新企业账号

        Args:
            account_id: 账号ID
            **kwargs: 更新字段

        Returns:
            更新结果
        """
        account = self._accounts.get(account_id)

        if not account:
            return {
                "success": False,
                "error": "企业账号不存在",
            }

        for key, value in kwargs.items():
            if key in ["company_name", "industry",
                       "scale", "subscription_plan"]:
                account[key] = value

        account["updated_at"] = datetime.now(timezone.utc).isoformat()

        return {
            "success": True,
            "account_id": account_id,
            "updated": kwargs,
        }

    async def list_users(
        self,
        account_id: int,
    ) -> list[dict[str, Any]]:
        """列出企业用户

        Args:
            account_id: 账号ID

        Returns:
            用户列表
        """
        return [
            u for u in self._users.values()
            if u["account_id"] == account_id
        ]

    async def add_user(
        self,
        account_id: int,
        email: str,
        name: str,
        role: str = "member",
    ) -> dict[str, Any]:
        """添加用户

        Args:
            account_id: 账号ID
            email: 邮箱
            name: 姓名
            role: 角色

        Returns:
            用户信息
        """
        account = self._accounts.get(account_id)

        if not account:
            return {
                "success": False,
                "error": "企业账号不存在",
            }

        current_users = sum(
            1 for u in self._users.values()
            if u["account_id"] == account_id
        )

        if current_users >= account["max_users"]:
            return {
                "success": False,
                "error": "用户数量已达上限",
            }

        user_id = len(self._users) + 1
        now = datetime.now(timezone.utc).isoformat()

        user = {
            "id": user_id,
            "account_id": account_id,
            "email": email,
            "name": name,
            "role": role,
            "status": "active",
            "created_at": now,
        }

        self._users[user_id] = user

        logger.info(f"Added user {user_id} to account {account_id}")

        return {
            "user_id": user_id,
            "email": email,
            "name": name,
            "role": role,
        }


class ContractReviewService:
    """合同审查服务"""

    def __init__(self):
        self._contracts: dict[int, dict[str, Any]] = {}
        self._review_results: dict[int, dict[str, Any]] = {}

    async def submit_contract(
        self,
        account_id: int,
        user_id: int,
        title: str,
        content: str,
        contract_type: str = "general",
    ) -> dict[str, Any]:
        """提交合同审查

        Args:
            account_id: 账号ID
            user_id: 用户ID
            title: 标题
            content: 内容
            contract_type: 合同类型

        Returns:
            合同信息
        """
        contract_id = len(self._contracts) + 1
        now = datetime.now(timezone.utc).isoformat()

        contract = {
            "id": contract_id,
            "account_id": account_id,
            "user_id": user_id,
            "title": title,
            "content": content,
            "contract_type": contract_type,
            "status": "pending",
            "created_at": now,
            "updated_at": now,
            "risk_level": None,
            "issues_count": 0,
        }

        self._contracts[contract_id] = contract

        logger.info(f"Submitted contract {contract_id} for review")

        return {
            "contract_id": contract_id,
            "status": "pending",
            "created_at": now,
        }

    async def review_contract(
        self,
        contract_id: int,
    ) -> dict[str, Any]:
        """审查合同

        Args:
            contract_id: 合同ID

        Returns:
            审查结果
        """
        contract = self._contracts.get(contract_id)

        if not contract:
            return {
                "success": False,
                "error": "合同不存在",
            }

        issues = []
        risk_level = "low"

        content = contract["content"]

        if "违约金" in content:
            issues.append({
                "type": "penalty",
                "severity": "medium",
                "message": "检测到违约金条款，建议明确计算方式",
            })

        if "无限责任" in content:
            issues.append({
                "type": "liability",
                "severity": "high",
                "message": "检测到无限责任条款，建议限制责任范围",
            })
            risk_level = "high"

        if "独家" in content:
            issues.append({
                "type": "exclusivity",
                "severity": "medium",
                "message": "检测到独家条款，建议评估商业影响",
            })

        if len(issues) > 3:
            risk_level = "medium"

        review_result = {
            "contract_id": contract_id,
            "reviewed_at": datetime.now(timezone.utc).isoformat(),
            "risk_level": risk_level,
            "issues": issues,
            "issues_count": len(issues),
            "recommendations": [
                "建议在签署前咨询专业法律顾问",
                "注意审查争议解决条款",
                "确认管辖权约定符合公司策略",
            ],
        }

        self._review_results[contract_id] = review_result

        contract["status"] = "reviewed"
        contract["risk_level"] = risk_level
        contract["issues_count"] = len(issues)
        contract["updated_at"] = datetime.now(timezone.utc).isoformat()

        logger.info(f"Reviewed contract {contract_id}, risk: {risk_level}")

        return {
            "success": True,
            "contract_id": contract_id,
            "risk_level": risk_level,
            "issues_count": len(issues),
        }

    async def get_review_result(
        self,
        contract_id: int,
    ) -> dict[str, Any]:
        """获取审查结果

        Args:
            contract_id: 合同ID

        Returns:
            审查结果
        """
        return self._review_results.get(contract_id, {})

    async def get_contracts(
        self,
        account_id: int,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        """获取合同列表

        Args:
            account_id: 账号ID
            status: 状态筛选

        Returns:
            合同列表
        """
        contracts = [
            c for c in self._contracts.values()
            if c["account_id"] == account_id
        ]

        if status:
            contracts = [c for c in contracts if c["status"] == status]

        return contracts

    async def get_stats(self, account_id: int) -> dict[str, Any]:
        """获取合同统计

        Args:
            account_id: 账号ID

        Returns:
            统计信息
        """
        contracts = await self.get_contracts(account_id)
        total = len(contracts)
        pending = sum(1 for c in contracts if c["status"] == "pending")
        reviewed = sum(1 for c in contracts if c["status"] == "reviewed")
        high_risk = sum(1 for c in contracts if c.get("risk_level") == "high")
        medium_risk = sum(
            1 for c in contracts if c.get("risk_level") == "medium")

        return {
            "total": total,
            "pending": pending,
            "reviewed": reviewed,
            "high_risk": high_risk,
            "medium_risk": medium_risk,
        }


class ComplianceTemplateLibrary:
    """合规模板库"""

    def __init__(self):
        self._templates: dict[str, dict[str, Any]] = {}
        self._categories: list[str] = [
            "劳动合同",
            "采购合同",
            "销售合同",
            "保密协议",
            "合作协议",
            "租赁合同",
        ]

    def add_template(
        self,
        name: str,
        category: str,
        content: str,
        description: str = "",
        risk_level: str = "low",
    ) -> dict[str, Any]:
        """添加合规模板

        Args:
            name: 模板名称
            category: 分类
            content: 内容
            description: 描述
            risk_level: 风险等级

        Returns:
            模板信息
        """
        template_id = f"TMPL-{len(self._templates) + 1:04d}"
        now = datetime.now(timezone.utc).isoformat()

        template = {
            "id": template_id,
            "name": name,
            "category": category,
            "content": content,
            "description": description,
            "risk_level": risk_level,
            "created_at": now,
            "updated_at": now,
            "usage_count": 0,
        }

        self._templates[template_id] = template

        logger.info(f"Added compliance template {template_id}: {name}")

        return {
            "template_id": template_id,
            "name": name,
            "category": category,
        }

    def get_templates(
        self,
        category: str | None = None,
        risk_level: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """获取模板列表

        Args:
            category: 分类筛选
            risk_level: 风险等级筛选
            limit: 限制数量

        Returns:
            模板列表
        """
        templates = list(self._templates.values())

        if category:
            templates = [t for t in templates if t["category"] == category]

        if risk_level:
            templates = [t for t in templates if t["risk_level"] == risk_level]

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
            or query in t["description"].lower()
        ]

        return results[:limit]

    def get_categories(self) -> list[str]:
        """获取分类列表

        Returns:
            分类列表
        """
        return self._categories

    async def list_templates(
        self,
        category: str | None = None,
    ) -> list[dict[str, Any]]:
        """列出模板

        Args:
            category: 分类筛选

        Returns:
            模板列表
        """
        return self.get_templates(category=category)

    async def get_template(
        self,
        template_id: int,
    ) -> dict[str, Any] | None:
        """获取模板

        Args:
            template_id: 模板ID

        Returns:
            模板信息
        """
        template_key = f"TMPL-{template_id:04d}"
        return self._templates.get(template_key)

    async def generate_contract(
        self,
        template_id: int,
        values: dict[str, Any],
    ) -> dict[str, Any]:
        """根据模板生成合同

        Args:
            template_id: 模板ID
            values: 填充值

        Returns:
            生成结果
        """
        template = await self.get_template(template_id)
        if not template:
            return {
                "success": False,
                "error": "模板不存在",
            }

        content = template["content"]
        for key, value in values.items():
            content = content.replace(f"{{{key}}}", str(value))

        return {
            "success": True,
            "content": content,
            "template_name": template["name"],
        }


# 别名
ComplianceTemplateService = ComplianceTemplateLibrary


class EnterpriseComplianceService:
    """企业合规服务"""

    def __init__(self):
        self.account_manager = EnterpriseAccountManager()
        self.contract_review_service = ContractReviewService()
        self.template_library = ComplianceTemplateLibrary()

    async def get_enterprise_dashboard(
        self,
        account_id: int,
    ) -> dict[str, Any]:
        """获取企业仪表盘

        Args:
            account_id: 账号ID

        Returns:
            仪表盘数据
        """
        account = await self.account_manager.get_account(account_id)
        contracts = await self.contract_review_service.get_contracts(account_id)
        templates = self.template_library.get_templates(limit=5)

        pending_review = sum(1 for c in contracts if c["status"] == "pending")
        reviewed = sum(1 for c in contracts if c["status"] == "reviewed")
        high_risk = sum(1 for c in contracts if c["risk_level"] == "high")

        return {
            "account": account,
            "contracts_summary": {
                "total": len(contracts),
                "pending": pending_review,
                "reviewed": reviewed,
                "high_risk": high_risk,
            },
            "recent_templates": templates,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }


# 单例实例
enterprise_compliance_service = EnterpriseComplianceService()


async def create_enterprise_account(
    company_name: str,
    admin_email: str,
    industry: str = "general",
    scale: str = "smb",
) -> dict[str, Any]:
    """便捷函数：创建企业账号

    Args:
        company_name: 公司名称
        admin_email: 管理员邮箱
        industry: 行业
        scale: 规模

    Returns:
        账号信息
    """
    return await enterprise_compliance_service.account_manager.create_enterprise_account(
        company_name=company_name,
        admin_email=admin_email,
        industry=industry,
        scale=scale,
    )


async def submit_contract_review(
    account_id: int,
    user_id: int,
    title: str,
    content: str,
    contract_type: str = "general",
) -> dict[str, Any]:
    """便捷函数：提交合同审查

    Args:
        account_id: 账号ID
        user_id: 用户ID
        title: 标题
        content: 内容
        contract_type: 合同类型

    Returns:
        合同信息
    """
    return await enterprise_compliance_service.contract_review_service.submit_contract(
        account_id=account_id,
        user_id=user_id,
        title=title,
        content=content,
        contract_type=contract_type,
    )


async def review_contract(
    contract_id: int,
) -> dict[str, Any]:
    """便捷函数：审查合同

    Args:
        contract_id: 合同ID

    Returns:
        审查结果
    """
    return await enterprise_compliance_service.contract_review_service.review_contract(
        contract_id=contract_id,
    )


def search_compliance_templates(
    query: str,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """便捷函数：搜索合规模板

    Args:
        query: 搜索词
        limit: 限制数量

    Returns:
        模板列表
    """
    return enterprise_compliance_service.template_library.search_templates(
        query=query,
        limit=limit,
    )


async def get_enterprise_dashboard(
    account_id: int,
) -> dict[str, Any]:
    """便捷函数：获取企业仪表盘

    Args:
        account_id: 账号ID

    Returns:
        仪表盘数据
    """
    return await enterprise_compliance_service.get_enterprise_dashboard(
        account_id=account_id,
    )
