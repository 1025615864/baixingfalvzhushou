"""计算器工具 - 费用计算、时效计算等"""

import logging
from typing import Any, Dict, Optional
from datetime import datetime, timedelta

from ..base import BaseTool, ToolResult, ToolCategory, ToolPermission

logger = logging.getLogger(__name__)


class CalculatorTool(BaseTool):
    """法律相关计算器工具

    支持:
    - 诉讼费用计算
    - 诉讼时效计算
    - 经济补偿金计算
    - 误工费计算
    """

    name = "calculator"
    description = """提供法律相关的计算功能:
    - 诉讼费用计算: 根据诉讼标的额计算案件受理费
    - 诉讼时效计算: 计算诉讼时效是否届满
    - 经济补偿金计算: 根据工作年限和工资计算经济补偿
    - 误工费计算: 根据收入和误工天数计算误工费

    使用场景:
    - 用户想了解诉讼成本
    - 用户想确认是否过了诉讼时效
    - 用户想计算赔偿金额
    """

    version = "1.0.0"
    category = ToolCategory.CALCULATOR
    tags = ["计算", "费用", "诉讼费", "时效", "补偿金"]
    permission = ToolPermission.PUBLIC

    def __init__(self):
        super().__init__()

    def _get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "calculation_type": {
                    "type": "string",
                    "enum": ["litigation_fee", "limitation", "severance", "missed_work"],
                    "description": "计算类型: litigation_fee(诉讼费), limitation(时效), severance(经济补偿金), missed_work(误工费)",
                },
                "amount": {
                    "type": "number",
                    "description": "金额（诉讼标的额/工资/月收入）",
                },
                "start_date": {
                    "type": "string",
                    "description": "开始日期（格式: YYYY-MM-DD），用于时效计算",
                },
                "end_date": {
                    "type": "string",
                    "description": "结束日期（格式: YYYY-MM-DD），用于时效/补偿计算",
                },
                "work_years": {
                    "type": "number",
                    "description": "工作年限，用于经济补偿金计算",
                },
                "daily_wage": {
                    "type": "number",
                    "description": "日工资，用于误工费计算",
                },
                "missed_days": {
                    "type": "number",
                    "description": "误工天数，用于误工费计算",
                },
                "case_type": {
                    "type": "string",
                    "description": "案件类型，用于诉讼费计算（civil/labor/administrative）",
                },
            },
            "required": ["calculation_type"],
        }

    async def execute(
        self,
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> ToolResult:
        """执行计算"""
        calculation_type = params.get("calculation_type")

        try:
            if calculation_type == "litigation_fee":
                return await self._calculate_litigation_fee(params)
            elif calculation_type == "limitation":
                return await self._calculate_limitation(params)
            elif calculation_type == "severance":
                return await self._calculate_severance(params)
            elif calculation_type == "missed_work":
                return await self._calculate_missed_work(params)
            else:
                return ToolResult(
                    success=False,
                    error=f"不支持的计算类型: {calculation_type}"
                )
        except Exception as e:
            logger.exception("计算失败")
            return ToolResult(
                success=False,
                error=f"计算失败: {str(e)}"
            )

    async def _calculate_litigation_fee(
            self, params: Dict[str, Any]) -> ToolResult:
        """计算诉讼费用（民事案件案件受理费）"""
        amount = float(params.get("amount", 0))
        case_type = params.get("case_type", "civil")

        if amount <= 0:
            return ToolResult(
                success=False,
                error="请输入有效的诉讼标的金额"
            )

        # 2022年最新的诉讼费用标准（民事案件）
        # 财产案件根据标的额分段累计计算
        if amount <= 10000:
            fee = 50
        elif amount <= 100000:
            fee = 50 + (amount - 10000) * 0.025
        elif amount <= 200000:
            fee = 50 + 90000 * 0.025 + (amount - 100000) * 0.02
        elif amount <= 500000:
            fee = 50 + 90000 * 0.025 + 100000 * \
                0.02 + (amount - 200000) * 0.015
        elif amount <= 1000000:
            fee = 50 + 90000 * 0.025 + 100000 * 0.02 + \
                300000 * 0.015 + (amount - 500000) * 0.01
        else:
            fee = 50 + 90000 * 0.025 + 100000 * 0.02 + 300000 * \
                0.015 + 500000 * 0.01 + (amount - 1000000) * 0.005

        # 劳动争议案件每件 10 元
        if case_type == "labor":
            fee = 10

        # 简化案件收费
        if amount < 1000:
            fee = min(fee, 30)

        fee = round(fee, 2)

        return ToolResult(
            success=True,
            data={
                "calculation_type": "litigation_fee",
                "amount": amount,
                "case_type": case_type,
                "fee": fee,
                "description": f"诉讼标的额 {amount:,.0f} 元的案件受理费约为 {fee:,.2f} 元",
                "note": "实际收费以法院为准，此为参考值",
            },
            metadata={
                "formula": "民事案件案件受理费分段累计计算",
                "standard_year": 2022,
            }
        )

    async def _calculate_limitation(
            self, params: Dict[str, Any]) -> ToolResult:
        """计算诉讼时效"""
        start_date_str = params.get("start_date")
        end_date_str = params.get("end_date")

        if not start_date_str:
            return ToolResult(
                success=False,
                error="请提供纠纷发生日期（start_date）"
            )

        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
            end_date = datetime.strptime(
                end_date_str, "%Y-%m-%d") if end_date_str else datetime.now()

            # 默认普通诉讼时效为 3 年
            limitation_period = 3 * 365  # 天数

            # 计算时效届满日期
            expiry_date = start_date + timedelta(days=limitation_period)

            # 判断是否已过时效
            days_elapsed = (end_date - start_date).days
            days_remaining = (expiry_date - end_date).days
            is_expired = days_remaining < 0

            result = {
                "calculation_type": "limitation",
                "dispute_date": start_date_str,
                "check_date": end_date.strftime("%Y-%m-%d"),
                "limitation_period_years": 3,
                "days_elapsed": days_elapsed,
                "days_remaining": max(0, days_remaining),
                "is_expired": is_expired,
                "expiry_date": expiry_date.strftime("%Y-%m-%d"),
            }

            if is_expired:
                result["advice"] = "已超过诉讼时效，建议咨询律师确认是否存在时效中断或中止的情形"
            else:
                result["advice"] = f"诉讼时效尚未届满，剩余 {days_remaining} 天"

            return ToolResult(
                success=True,
                data=result,
                metadata={
                    "note": "普通诉讼时效为3年，特殊情况可能有不同时效",
                }
            )

        except ValueError as e:
            return ToolResult(
                success=False,
                error=f"日期格式错误: {str(e)}，请使用 YYYY-MM-DD 格式"
            )

    async def _calculate_severance(self, params: Dict[str, Any]) -> ToolResult:
        """计算经济补偿金"""
        monthly_wage = float(params.get("amount", 0))
        work_years = float(params.get("work_years", 0))

        if monthly_wage <= 0:
            return ToolResult(
                success=False,
                error="请输入月工资数额"
            )

        if work_years <= 0:
            return ToolResult(
                success=False,
                error="请输入工作年限"
            )

        # 经济补偿金计算
        # 每满一年支付一个月工资
        # 六个月以上不满一年按一年计算
        # 不满六个月支付半个月工资
        # 月工资高于本地区上年度职工月平均工资3倍的，按3倍计算，最高年限12年

        monthly_compensation = monthly_wage
        years_count = int(work_years)
        months_extra = (work_years - years_count) * 12

        if months_extra > 6:
            years_count += 1
            months_compensation = 0
        elif months_extra > 0:
            months_compensation = 0.5
        else:
            months_compensation = 0

        total_months = years_count + months_compensation
        total_compensation = monthly_compensation * total_months

        return ToolResult(
            success=True,
            data={
                "calculation_type": "severance",
                "monthly_wage": monthly_wage,
                "work_years": work_years,
                "years_count": years_count,
                "months_compensation": months_compensation,
                "total_months": total_months,
                "total_compensation": round(
                    total_compensation,
                    2),
                "description": (
                    f"工作 {work_years:.1f} 年，月工资 {monthly_wage:,.0f} 元，"
                    f"经济补偿金约为 {total_compensation:,.2f} 元"
                ),
                "note": "此为单倍经济补偿金计算结果，实际补偿可能因具体情况而异",
            },
            metadata={
                "formula": "经济补偿金 = 月工资 × 工作年限（不足一年按比例计算）",
                "regulation": "《劳动合同法》第四十七条",
            })

    async def _calculate_missed_work(
            self, params: Dict[str, Any]) -> ToolResult:
        """计算误工费"""
        daily_wage = float(params.get("daily_wage", 0))
        missed_days = float(params.get("missed_days", 0))

        if daily_wage <= 0:
            return ToolResult(
                success=False,
                error="请输入日工资数额"
            )

        if missed_days <= 0:
            return ToolResult(
                success=False,
                error="请输入误工天数"
            )

        # 误工费 = 日工资 × 误工天数
        total_compensation = daily_wage * missed_days

        return ToolResult(
            success=True,
            data={
                "calculation_type": "missed_work",
                "daily_wage": daily_wage,
                "missed_days": missed_days,
                "total_compensation": round(
                    total_compensation,
                    2),
                "description": (
                    f"日工资 {daily_wage:,.0f} 元，误工 {missed_days:.0f} 天，"
                    f"误工费约为 {total_compensation:,.2f} 元"
                ),
                "note": "有固定收入的按实际减少计算，无固定收入的可参照行业平均工资",
            },
            metadata={
                "formula": "误工费 = 日工资 × 误工天数",
            })
