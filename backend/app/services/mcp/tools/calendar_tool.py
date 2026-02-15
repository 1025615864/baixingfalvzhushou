"""日历工具 - 律师日程查询和预约"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, date, timedelta

from ..base import BaseTool, ToolResult, ToolCategory, ToolPermission

logger = logging.getLogger(__name__)


class CalendarTool(BaseTool):
    """律师日程管理工具

    功能:
    - 查询律师可预约时间
    - 创建预约日程
    - 查询用户预约历史
    """

    name = "calendar"
    description = """管理法律咨询日程:
    - 查询律师可预约时间段
    - 创建咨询预约
    - 查看预约历史
    - 取消预约

    使用场景:
    - 用户想预约律师咨询
    - AI 帮助用户安排咨询时间
    - 查询律师空闲时间
    """

    version = "1.0.0"
    category = ToolCategory.UTILITY
    tags = ["日历", "预约", "日程", "咨询"]
    permission = ToolPermission.USER_REQUIRED

    def _get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": [
                        "check_availability",
                        "create_appointment",
                        "list_appointments",
                        "cancel_appointment"],
                    "description": "操作类型",
                },
                "lawyer_id": {
                    "type": "integer",
                    "description": "律师ID",
                },
                "date": {
                    "type": "string",
                    "description": "日期（格式: YYYY-MM-DD）",
                },
                "time_slot": {
                    "type": "string",
                    "description": "时间段（如: 09:00-10:00）",
                },
                "appointment_id": {
                    "type": "integer",
                    "description": "预约ID（取消时使用）",
                },
                "topic": {
                    "type": "string",
                    "description": "咨询主题",
                },
                "notes": {
                    "type": "string",
                    "description": "备注说明",
                },
                "limit": {
                    "type": "integer",
                    "description": "返回数量限制",
                },
            },
            "required": ["action"],
        }

    async def execute(
        self,
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> ToolResult:
        """执行日历操作"""
        action = params.get("action")
        user_id = context.get("user_id") if context else None

        if action in ["create_appointment",
                      "list_appointments", "cancel_appointment"]:
            if not user_id:
                return ToolResult(
                    success=False,
                    error="请先登录后再进行此操作"
                )

        try:
            if action == "check_availability":
                return await self._check_availability(params)
            elif action == "create_appointment":
                return await self._create_appointment(params, user_id)
            elif action == "list_appointments":
                return await self._list_appointments(params, user_id)
            elif action == "cancel_appointment":
                return await self._cancel_appointment(params, user_id)
            else:
                return ToolResult(
                    success=False,
                    error=f"不支持的操作: {action}"
                )
        except Exception as e:
            logger.exception("日历操作失败")
            return ToolResult(
                success=False,
                error=f"操作失败: {str(e)}"
            )

    async def _check_availability(self, params: Dict[str, Any]) -> ToolResult:
        """检查律师可预约时间"""
        lawyer_id = params.get("lawyer_id")
        date_str = params.get("date")

        if not lawyer_id:
            return ToolResult(
                success=False,
                error="请提供律师ID"
            )

        # 生成可用时间段
        time_slots = self._generate_time_slots(date_str)

        return ToolResult(
            success=True,
            data={
                "lawyer_id": lawyer_id,
                "date": date_str or datetime.now().strftime("%Y-%m-%d"),
                "available_slots": time_slots,
                "total_slots": len(time_slots),
                "note": "示例数据，实际可用时间段请以系统显示为准",
            }
        )

    async def _create_appointment(
            self, params: Dict[str, Any], user_id: Optional[int]) -> ToolResult:
        """创建预约"""
        lawyer_id = params.get("lawyer_id")
        date_str = params.get("date")
        time_slot = params.get("time_slot")
        topic = params.get("topic", "")
        notes = params.get("notes", "")

        if not all([lawyer_id, date_str, time_slot]):
            return ToolResult(
                success=False,
                error="请提供律师ID、日期和时间段"
            )

        if not user_id:
            return ToolResult(
                success=False,
                error="请先登录"
            )

        # 模拟创建预约
        appointment_id = int(datetime.now().timestamp())

        return ToolResult(
            success=True,
            data={
                "appointment_id": appointment_id,
                "lawyer_id": lawyer_id,
                "date": date_str,
                "time_slot": time_slot,
                "topic": topic,
                "status": "pending",
                "message": "预约申请已提交，等待律师确认",
                "created_at": datetime.now().isoformat(),
            },
            metadata={
                "note": "示例数据，实际预约请通过正式渠道操作",
            }
        )

    async def _list_appointments(
            self, params: Dict[str, Any], user_id: Optional[int]) -> ToolResult:
        """列出用户预约"""
        limit = min(int(params.get("limit", 10)), 50)

        if not user_id:
            return ToolResult(
                success=False,
                error="请先登录"
            )

        # 模拟预约列表
        appointments = [{"id": 1001,
                         "lawyer_name": "张律师",
                         "lawyer_firm": "XX律师事务所",
                         "date": (datetime.now().strftime("%Y-%m-%d")),
                         "time_slot": "10:00-11:00",
                         "status": "confirmed",
                         "topic": "劳动纠纷咨询",
                         },
                        {"id": 1002,
                         "lawyer_name": "李律师",
                         "lawyer_firm": "YY律师事务所",
                         "date": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
                         "time_slot": "14:00-15:00",
                         "status": "pending",
                         "topic": "合同审查",
                         },
                        ]

        return ToolResult(
            success=True,
            data={
                "appointments": appointments[:limit],
                "total": len(appointments),
            }
        )

    async def _cancel_appointment(
            self, params: Dict[str, Any], user_id: Optional[int]) -> ToolResult:
        """取消预约"""
        appointment_id = params.get("appointment_id")

        if not appointment_id:
            return ToolResult(
                success=False,
                error="请提供预约ID"
            )

        if not user_id:
            return ToolResult(
                success=False,
                error="请先登录"
            )

        return ToolResult(
            success=True,
            data={
                "appointment_id": appointment_id,
                "status": "cancelled",
                "cancelled_at": datetime.now().isoformat(),
                "message": "预约已取消",
            }
        )

    def _generate_time_slots(
            self, date_str: Optional[str] = None) -> List[Dict[str, str]]:
        """生成时间段列表"""
        slots = []
        for hour in [9, 10, 11, 14, 15, 16, 17]:
            slots.append({
                "time": f"{hour:02d}:00-{hour:02d}:00",
                "available": True,
                "fee": "¥100-300",
            })
        return slots
