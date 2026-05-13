"""Calculator tool for legal fee computations."""
from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from typing import Any

from app.services.mcp.base import BaseTool, ToolCategory, ToolPermission, ToolResult


class CalculatorTool(BaseTool):
    name = "calculator"
    description = "法律费用计算工具，支持诉讼费用计算、诉讼时效计算、经济补偿金计算、误工费计算等"
    version = "1.0.0"
    category = ToolCategory.CALCULATOR
    permission = ToolPermission.PUBLIC
    tags = ["计算", "费用", "诉讼费", "时效", "补偿金", "误工费"]

    def _get_parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "calculation_type": {
                    "type": "string",
                    "enum": [
                        "litigation_fee",
                        "limitation",
                        "severance",
                        "missed_work",
                    ],
                    "description": "计算类型",
                },
                "amount": {
                    "type": "number",
                    "description": "金额",
                },
                "start_date": {
                    "type": "string",
                    "description": "开始日期 (YYYY-MM-DD)",
                },
                "end_date": {
                    "type": "string",
                    "description": "结束日期 (YYYY-MM-DD)",
                },
                "work_years": {
                    "type": "number",
                    "description": "工作年限",
                },
                "daily_wage": {
                    "type": "number",
                    "description": "日工资",
                },
                "missed_days": {
                    "type": "number",
                    "description": "误工天数",
                },
                "case_type": {
                    "type": "string",
                    "description": "案件类型",
                },
            },
            "required": ["calculation_type"],
        }

    async def execute(self, params: dict, context: dict) -> ToolResult:
        calc_type = params.get("calculation_type")
        try:
            if calc_type == "litigation_fee":
                return await self._calculate_litigation_fee(params)
            elif calc_type == "limitation":
                return await self._calculate_limitation(params)
            elif calc_type == "severance":
                return await self._calculate_severance(params)
            elif calc_type == "missed_work":
                return await self._calculate_missed_work(params)
            else:
                return ToolResult(success=False, error=f"不支持的计算类型: {calc_type}")
        except Exception as e:
            return ToolResult(success=False, error=f"计算失败: {str(e)}")

    async def _calculate_litigation_fee(self, params: dict) -> ToolResult:
        amount = params.get("amount")
        if amount is None or amount <= 0:
            return ToolResult(success=False, error="请输入有效的诉讼标的金额")

        case_type = params.get("case_type", "")

        if case_type == "labor":
            return ToolResult(success=True, data={"fee": 10, "amount": amount, "case_type": case_type})

        fee = 0.0
        if amount <= 10000:
            fee = 50
        elif amount <= 100000:
            fee = 50 + (amount - 10000) * 0.025
        elif amount <= 200000:
            fee = 50 + 90000 * 0.025 + (amount - 100000) * 0.02
        elif amount <= 500000:
            fee = 50 + 90000 * 0.025 + 100000 * 0.02 + (amount - 200000) * 0.015
        elif amount <= 1000000:
            fee = 50 + 90000 * 0.025 + 100000 * 0.02 + 300000 * 0.015 + (amount - 500000) * 0.01
        else:
            fee = 50 + 90000 * 0.025 + 100000 * 0.02 + 300000 * 0.015 + 500000 * 0.01 + (amount - 1000000) * 0.005

        fee = min(fee, 30) if amount <= 1000 and fee > 30 else fee
        fee = round(fee, 2)

        return ToolResult(success=True, data={"fee": fee, "amount": amount})

    async def _calculate_limitation(self, params: dict) -> ToolResult:
        start_date_str = params.get("start_date")
        if not start_date_str:
            return ToolResult(success=False, error="请提供纠纷发生日期")

        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            return ToolResult(success=False, error="日期格式错误，请使用 YYYY-MM-DD 格式")

        end_date_str = params.get("end_date")
        if end_date_str:
            try:
                check_date = datetime.strptime(end_date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            except ValueError:
                return ToolResult(success=False, error="日期格式错误，请使用 YYYY-MM-DD 格式")
        else:
            check_date = datetime.now(timezone.utc)

        limitation_end = start_date + timedelta(days=3 * 365)
        is_expired = check_date > limitation_end
        days_remaining = max(0, (limitation_end - check_date).days)

        result_data = {
            "dispute_date": start_date_str,
            "check_date": end_date_str or check_date.strftime("%Y-%m-%d"),
            "limitation_end": limitation_end.strftime("%Y-%m-%d"),
            "is_expired": is_expired,
            "days_remaining": days_remaining,
        }

        if is_expired:
            result_data["advice"] = "诉讼时效已过，建议咨询专业律师了解是否有中断、中止情形"

        return ToolResult(success=True, data=result_data)

    async def _calculate_severance(self, params: dict) -> ToolResult:
        amount = params.get("amount")
        work_years = params.get("work_years")

        if not amount or amount <= 0:
            return ToolResult(success=False, error="请输入月工资数额")
        if work_years is None or work_years <= 0:
            return ToolResult(success=False, error="请输入工作年限")

        years_count = int(work_years)
        fractional = work_years - years_count

        months_compensation = 0.0
        if fractional > 0.5:
            years_count += 1
        elif fractional > 0:
            months_compensation = fractional

        total_months = years_count + months_compensation if months_compensation else years_count
        total_compensation = round(amount * total_months, 2)

        return ToolResult(success=True, data={
            "monthly_wage": amount,
            "years_count": years_count,
            "months_compensation": months_compensation,
            "total_months": total_months,
            "total_compensation": total_compensation,
        })

    async def _calculate_missed_work(self, params: dict) -> ToolResult:
        daily_wage = params.get("daily_wage")
        missed_days = params.get("missed_days")

        if not daily_wage or daily_wage <= 0:
            return ToolResult(success=False, error="请输入日工资数额")
        if missed_days is None or missed_days <= 0:
            return ToolResult(success=False, error="请输入误工天数")

        total_compensation = round(daily_wage * missed_days, 2)

        return ToolResult(success=True, data={
            "daily_wage": daily_wage,
            "missed_days": missed_days,
            "total_compensation": total_compensation,
        })
