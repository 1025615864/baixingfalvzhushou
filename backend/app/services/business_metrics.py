"""业务指标收集服务

提供业务指标收集和导出功能，包括：
- 咨询转化率指标
- 支付成功率指标
- 用户留存率指标
- 律师响应时间指标
- 内容审核效率指标

使用示例:
    ```python
    from app.services.business_metrics import get_business_metrics_collector

    collector = get_business_metrics_collector()

    # 记录咨询转化指标
    collector.record_consultation_funnel("view", user_id=123)
    collector.record_consultation_funnel("create", user_id=123)
    collector.record_consultation_funnel("pay", user_id=123)

    # 记录支付指标
    collector.record_payment_success(order_no="xxx", amount=100.0)
    collector.record_payment_fail(order_no="xxx", reason="balance_insufficient")

    # 记录律师响应时间
    collector.record_lawyer_response(lawyer_id=1, response_time_seconds=120.5)

    # 记录内容审核指标
    collector.record_content_moderation(content_type="post", action="approved", duration=30.0)

    # 获取指标数据
    metrics = collector.get_all_metrics()
    ```
"""
from __future__ import annotations

import time
import logging
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Deque
from enum import Enum

logger = logging.getLogger(__name__)


class ConsultationStage(str, Enum):
    """咨询转化阶段"""
    VIEW = "view"  # 浏览咨询页面
    START = "start"  # 开始填写咨询
    CREATE = "create"  # 创建咨询
    PAY = "pay"  # 完成支付
    COMPLETE = "complete"  # 咨询完成


class ModerationAction(str, Enum):
    """内容审核操作"""
    APPROVED = "approved"  # 通过
    REJECTED = "rejected"  # 拒绝
    PENDING = "pending"  # 待审核
    FLAGGED = "flagged"  # 标记为可疑


@dataclass
class ConsultationFunnelData:
    """咨询转化漏斗数据"""
    view_count: int = 0
    start_count: int = 0
    create_count: int = 0
    pay_count: int = 0
    complete_count: int = 0
    
    # 分阶段转化率
    view_to_start_rate: float = 0.0
    start_to_create_rate: float = 0.0
    create_to_pay_rate: float = 0.0
    pay_to_complete_rate: float = 0.0
    overall_conversion_rate: float = 0.0


@dataclass
class PaymentMetricsData:
    """支付指标数据"""
    total_orders: int = 0
    successful_orders: int = 0
    failed_orders: int = 0
    refunded_orders: int = 0
    
    total_amount: float = 0.0
    successful_amount: float = 0.0
    
    # 支付成功率
    success_rate: float = 0.0
    
    # 按支付方式统计
    by_method: Dict[str, Dict[str, int]] = field(default_factory=dict)
    
    # 按订单类型统计
    by_type: Dict[str, Dict[str, int]] = field(default_factory=dict)


@dataclass
class UserRetentionData:
    """用户留存数据"""
    # 日活跃用户
    dau: int = 0
    # 周活跃用户
    wau: int = 0
    # 月活跃用户
    mau: int = 0
    
    # 留存率
    day1_retention: float = 0.0  # 次日留存
    day7_retention: float = 0.0  # 7 日留存
    day30_retention: float = 0.0  # 30 日留存
    
    # 新增用户
    new_users_today: int = 0
    new_users_this_week: int = 0
    new_users_this_month: int = 0


@dataclass
class LawyerResponseData:
    """律师响应时间数据"""
    # 平均响应时间（秒）
    avg_response_time: float = 0.0
    # 中位数响应时间
    median_response_time: float = 0.0
    # P95 响应时间
    p95_response_time: float = 0.0
    # P99 响应时间
    p99_response_time: float = 0.0
    
    # 响应总数
    total_responses: int = 0
    
    # 按律师 ID 统计
    by_lawyer: Dict[int, Dict[str, float]] = field(default_factory=dict)


@dataclass
class ModerationMetricsData:
    """内容审核指标数据"""
    # 总审核数
    total_moderations: int = 0
    # 审核通过数
    approved_count: int = 0
    # 审核拒绝数
    rejected_count: int = 0
    # 待审核数
    pending_count: int = 0
    
    # 平均审核时长（秒）
    avg_moderation_time: float = 0.0
    
    # 审核通过率
    approval_rate: float = 0.0
    
    # 按内容类型统计
    by_content_type: Dict[str, Dict[str, int]] = field(default_factory=dict)


class BusinessMetricsCollector:
    """业务指标收集器
    
    收集和统计各种业务指标，为监控和数据分析提供支持。
    
    Attributes:
        _consultation_funnel: 咨询转化漏斗数据
        _payment_metrics: 支付指标数据
        _user_retention: 用户留存数据
        _lawyer_response: 律师响应时间数据
        _moderation_metrics: 内容审核指标数据
        _start_time: 服务启动时间
    """
    
    def __init__(self, max_history_size: int = 10000):
        """初始化业务指标收集器
        
        Args:
            max_history_size: 历史数据最大大小，用于限制内存使用
        """
        self._start_time = time.time()
        self._max_history_size = max_history_size
        
        # 咨询转化漏斗 - 按天统计
        self._consultation_funnel: Dict[str, ConsultationFunnelData] = defaultdict(ConsultationFunnelData)
        
        # 支付指标
        self._payment_metrics = PaymentMetricsData()
        self._payment_history: Deque[Dict[str, Any]] = deque(maxlen=max_history_size)
        
        # 用户留存
        self._user_retention = UserRetentionData()
        self._daily_active_users: Deque[set] = deque(maxlen=365)
        self._new_users_by_date: Dict[str, int] = defaultdict(int)
        
        # 律师响应时间 - 使用 deque 限制大小
        self._lawyer_response_times: Deque[float] = deque(maxlen=max_history_size)
        self._lawyer_response_by_lawyer: Dict[int, Deque[float]] = defaultdict(lambda: deque(maxlen=1000))
        self._lawyer_metrics = LawyerResponseData()
        
        # 内容审核指标
        self._moderation_metrics = ModerationMetricsData()
        self._moderation_history: Deque[Dict[str, Any]] = deque(maxlen=max_history_size)
        
        # 用户行为计数器
        self._counters: Dict[str, int] = defaultdict(int)
        
        # 指标更新时间
        self._last_update_time = time.time()
    
    def _get_date_key(self, dt: Optional[datetime] = None) -> str:
        """获取日期键"""
        if dt is None:
            dt = datetime.now(timezone.utc)
        return dt.strftime("%Y-%m-%d")
    
    # ==================== 咨询转化指标 ====================
    
    def record_consultation_funnel(
        self,
        stage: ConsultationStage | str,
        user_id: Optional[int] = None,
        consultation_id: Optional[int] = None,
        extra_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """记录咨询转化漏斗
        
        Args:
            stage: 转化阶段
            user_id: 用户 ID
            consultation_id: 咨询 ID
            extra_data: 额外数据
        """
        date_key = self._get_date_key()
        stage_value = stage.value if isinstance(stage, ConsultationStage) else stage
        funnel = self._consultation_funnel[date_key]
        
        # 更新阶段计数
        if stage_value == "view":
            funnel.view_count += 1
        elif stage_value == "start":
            funnel.start_count += 1
        elif stage_value == "create":
            funnel.create_count += 1
        elif stage_value == "pay":
            funnel.pay_count += 1
        elif stage_value == "complete":
            funnel.complete_count += 1
        
        # 计算转化率
        self._update_consultation_conversion_rates(funnel)
        
        # 记录详细数据
        self._counters[f"consultation.{stage_value}"] += 1
        
        logger.debug(f"记录咨询转化：stage={stage_value}, user_id={user_id}")
    
    def _update_consultation_conversion_rates(self, funnel: ConsultationFunnelData) -> None:
        """更新咨询转化率"""
        if funnel.view_count > 0:
            funnel.view_to_start_rate = funnel.start_count / funnel.view_count
        if funnel.start_count > 0:
            funnel.start_to_create_rate = funnel.create_count / funnel.start_count
        if funnel.create_count > 0:
            funnel.create_to_pay_rate = funnel.pay_count / funnel.create_count
        if funnel.pay_count > 0:
            funnel.pay_to_complete_rate = funnel.complete_count / funnel.pay_count
        if funnel.view_count > 0:
            funnel.overall_conversion_rate = funnel.complete_count / funnel.view_count
    
    def get_consultation_funnel(self, date: Optional[str] = None) -> ConsultationFunnelData:
        """获取咨询转化漏斗数据
        
        Args:
            date: 日期，格式 YYYY-MM-DD，默认为今天
            
        Returns:
            咨询转化漏斗数据
        """
        if date is None:
            date = self._get_date_key()
        return self._consultation_funnel.get(date, ConsultationFunnelData())
    
    # ==================== 支付指标 ====================
    
    def record_payment_success(
        self,
        order_no: str,
        amount: float,
        payment_method: str = "unknown",
        order_type: str = "unknown",
        user_id: Optional[int] = None,
    ) -> None:
        """记录支付成功
        
        Args:
            order_no: 订单号
            amount: 支付金额
            payment_method: 支付方式
            order_type: 订单类型
            user_id: 用户 ID
        """
        self._payment_metrics.total_orders += 1
        self._payment_metrics.successful_orders += 1
        self._payment_metrics.total_amount += amount
        self._payment_metrics.successful_amount += amount
        
        # 按支付方式统计
        if payment_method not in self._payment_metrics.by_method:
            self._payment_metrics.by_method[payment_method] = {"success": 0, "fail": 0}
        self._payment_metrics.by_method[payment_method]["success"] += 1
        
        # 按订单类型统计
        if order_type not in self._payment_metrics.by_type:
            self._payment_metrics.by_type[order_type] = {"success": 0, "fail": 0}
        self._payment_metrics.by_type[order_type]["success"] += 1
        
        # 更新成功率
        if self._payment_metrics.total_orders > 0:
            self._payment_metrics.success_rate = (
                self._payment_metrics.successful_orders / self._payment_metrics.total_orders
            )
        
        # 记录历史
        self._payment_history.append({
            "order_no": order_no,
            "amount": amount,
            "payment_method": payment_method,
            "order_type": order_type,
            "user_id": user_id,
            "status": "success",
            "timestamp": time.time(),
        })
        
        logger.debug(f"记录支付成功：order_no={order_no}, amount={amount}")
    
    def record_payment_fail(
        self,
        order_no: str,
        reason: str,
        payment_method: str = "unknown",
        order_type: str = "unknown",
        user_id: Optional[int] = None,
        amount: float = 0.0,
    ) -> None:
        """记录支付失败
        
        Args:
            order_no: 订单号
            reason: 失败原因
            payment_method: 支付方式
            order_type: 订单类型
            user_id: 用户 ID
            amount: 订单金额
        """
        self._payment_metrics.total_orders += 1
        self._payment_metrics.failed_orders += 1
        self._payment_metrics.total_amount += amount
        
        # 按支付方式统计
        if payment_method not in self._payment_metrics.by_method:
            self._payment_metrics.by_method[payment_method] = {"success": 0, "fail": 0}
        self._payment_metrics.by_method[payment_method]["fail"] += 1
        
        # 按订单类型统计
        if order_type not in self._payment_metrics.by_type:
            self._payment_metrics.by_type[order_type] = {"success": 0, "fail": 0}
        self._payment_metrics.by_type[order_type]["fail"] += 1
        
        # 更新成功率
        if self._payment_metrics.total_orders > 0:
            self._payment_metrics.success_rate = (
                self._payment_metrics.successful_orders / self._payment_metrics.total_orders
            )
        
        # 记录历史
        self._payment_history.append({
            "order_no": order_no,
            "amount": amount,
            "payment_method": payment_method,
            "order_type": order_type,
            "user_id": user_id,
            "status": "fail",
            "reason": reason,
            "timestamp": time.time(),
        })
        
        logger.debug(f"记录支付失败：order_no={order_no}, reason={reason}")
    
    def record_refund(
        self,
        order_no: str,
        amount: float,
        user_id: Optional[int] = None,
    ) -> None:
        """记录退款
        
        Args:
            order_no: 订单号
            amount: 退款金额
            user_id: 用户 ID
        """
        self._payment_metrics.refunded_orders += 1
        
        self._payment_history.append({
            "order_no": order_no,
            "amount": amount,
            "user_id": user_id,
            "status": "refund",
            "timestamp": time.time(),
        })
        
        logger.debug(f"记录退款：order_no={order_no}, amount={amount}")
    
    def get_payment_metrics(self) -> PaymentMetricsData:
        """获取支付指标数据
        
        Returns:
            支付指标数据
        """
        return self._payment_metrics
    
    # ==================== 用户留存指标 ====================
    
    def record_daily_active_user(self, user_id: int) -> None:
        """记录日活跃用户
        
        Args:
            user_id: 用户 ID
        """
        today = self._get_date_key()
        
        # 如果今天的集合不存在，创建一个新的
        if len(self._daily_active_users) == 0 or self._daily_active_users[-1] is None:
            self._daily_active_users.append(set())
        
        self._daily_active_users[-1].add(user_id)
        self._user_retention.dau = len(self._daily_active_users[-1])
    
    def record_new_user(self, user_id: int) -> None:
        """记录新用户
        
        Args:
            user_id: 用户 ID
        """
        today = self._get_date_key()
        self._new_users_by_date[today] += 1
        self._user_retention.new_users_today = self._new_users_by_date[today]
    
    def update_retention_metrics(
        self,
        day1_retention: float,
        day7_retention: float,
        day30_retention: float,
    ) -> None:
        """更新留存率指标
        
        Args:
            day1_retention: 次日留存率
            day7_retention: 7 日留存率
            day30_retention: 30 日留存率
        """
        self._user_retention.day1_retention = day1_retention
        self._user_retention.day7_retention = day7_retention
        self._user_retention.day30_retention = day30_retention
    
    def get_user_retention(self) -> UserRetentionData:
        """获取用户留存数据
        
        Returns:
            用户留存数据
        """
        # 更新活跃用户统计
        if len(self._daily_active_users) >= 1:
            self._user_retention.dau = len(self._daily_active_users[-1])
        if len(self._daily_active_users) >= 7:
            # 简单计算周活跃（实际应该去重）
            wau_set = set()
            for day_set in list(self._daily_active_users)[-7:]:
                wau_set.update(day_set)
            self._user_retention.wau = len(wau_set)
        if len(self._daily_active_users) >= 30:
            mau_set = set()
            for day_set in list(self._daily_active_users)[-30:]:
                mau_set.update(day_set)
            self._user_retention.mau = len(mau_set)
        
        return self._user_retention
    
    # ==================== 律师响应时间指标 ====================
    
    def record_lawyer_response(
        self,
        lawyer_id: int,
        response_time_seconds: float,
        consultation_id: Optional[int] = None,
    ) -> None:
        """记录律师响应时间
        
        Args:
            lawyer_id: 律师 ID
            response_time_seconds: 响应时间（秒）
            consultation_id: 咨询 ID
        """
        self._lawyer_response_times.append(response_time_seconds)
        self._lawyer_response_by_lawyer[lawyer_id].append(response_time_seconds)
        self._lawyer_metrics.total_responses += 1
        
        # 更新统计数据
        self._update_lawyer_response_stats()
        
        logger.debug(f"记录律师响应：lawyer_id={lawyer_id}, response_time={response_time_seconds}s")
    
    def _update_lawyer_response_stats(self) -> None:
        """更新律师响应时间统计"""
        if not self._lawyer_response_times:
            return
        
        times = sorted(self._lawyer_response_times)
        n = len(times)
        
        # 平均值
        self._lawyer_metrics.avg_response_time = sum(times) / n
        
        # 中位数
        mid = n // 2
        if n % 2 == 0:
            self._lawyer_metrics.median_response_time = (times[mid - 1] + times[mid]) / 2
        else:
            self._lawyer_metrics.median_response_time = times[mid]
        
        # P95
        p95_idx = int(n * 0.95)
        self._lawyer_metrics.p95_response_time = times[min(p95_idx, n - 1)]
        
        # P99
        p99_idx = int(n * 0.99)
        self._lawyer_metrics.p99_response_time = times[min(p99_idx, n - 1)]
    
    def get_lawyer_response_metrics(self) -> LawyerResponseData:
        """获取律师响应时间指标
        
        Returns:
            律师响应时间指标数据
        """
        return self._lawyer_metrics
    
    # ==================== 内容审核指标 ====================
    
    def record_content_moderation(
        self,
        content_type: str,
        action: ModerationAction | str,
        duration: float,
        content_id: Optional[int] = None,
        moderator_id: Optional[int] = None,
    ) -> None:
        """记录内容审核
        
        Args:
            content_type: 内容类型 (post, comment, news, etc.)
            action: 审核操作
            duration: 审核耗时（秒）
            content_id: 内容 ID
            moderator_id: 审核员 ID
        """
        action_value = action.value if isinstance(action, ModerationAction) else action
        
        self._moderation_metrics.total_moderations += 1
        
        if action_value == "approved":
            self._moderation_metrics.approved_count += 1
        elif action_value == "rejected":
            self._moderation_metrics.rejected_count += 1
        elif action_value == "pending":
            self._moderation_metrics.pending_count += 1
        
        # 按内容类型统计
        if content_type not in self._moderation_metrics.by_content_type:
            self._moderation_metrics.by_content_type[content_type] = {
                "approved": 0,
                "rejected": 0,
                "pending": 0,
            }
        self._moderation_metrics.by_content_type[content_type][action_value] = (
            self._moderation_metrics.by_content_type[content_type].get(action_value, 0) + 1
        )
        
        # 更新平均审核时长
        total = self._moderation_metrics.total_moderations
        old_avg = self._moderation_metrics.avg_moderation_time
        self._moderation_metrics.avg_moderation_time = (
            (old_avg * (total - 1) + duration) / total
        )
        
        # 更新审核通过率
        if self._moderation_metrics.total_moderations > 0:
            self._moderation_metrics.approval_rate = (
                self._moderation_metrics.approved_count / self._moderation_metrics.total_moderations
            )
        
        # 记录历史
        self._moderation_history.append({
            "content_type": content_type,
            "action": action_value,
            "duration": duration,
            "content_id": content_id,
            "moderator_id": moderator_id,
            "timestamp": time.time(),
        })
        
        logger.debug(f"记录内容审核：content_type={content_type}, action={action_value}")
    
    def get_moderation_metrics(self) -> ModerationMetricsData:
        """获取内容审核指标
        
        Returns:
            内容审核指标数据
        """
        return self._moderation_metrics
    
    # ==================== 通用计数器 ====================
    
    def inc_counter(self, name: str, value: int = 1) -> None:
        """增加计数器
        
        Args:
            name: 计数器名称
            value: 增加的值
        """
        self._counters[name] += value
    
    def get_counter(self, name: str) -> int:
        """获取计数器值
        
        Args:
            name: 计数器名称
            
        Returns:
            计数器值
        """
        return self._counters.get(name, 0)
    
    # ==================== 综合指标 ====================
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """获取所有业务指标
        
        Returns:
            包含所有业务指标的字典
        """
        today = self._get_date_key()
        consultation_funnel = self.get_consultation_funnel(today)
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "uptime_seconds": time.time() - self._start_time,
            "consultation": {
                "funnel": {
                    "view_count": consultation_funnel.view_count,
                    "start_count": consultation_funnel.start_count,
                    "create_count": consultation_funnel.create_count,
                    "pay_count": consultation_funnel.pay_count,
                    "complete_count": consultation_funnel.complete_count,
                    "conversion_rates": {
                        "view_to_start": consultation_funnel.view_to_start_rate,
                        "start_to_create": consultation_funnel.start_to_create_rate,
                        "create_to_pay": consultation_funnel.create_to_pay_rate,
                        "pay_to_complete": consultation_funnel.pay_to_complete_rate,
                        "overall": consultation_funnel.overall_conversion_rate,
                    },
                }
            },
            "payment": {
                "total_orders": self._payment_metrics.total_orders,
                "successful_orders": self._payment_metrics.successful_orders,
                "failed_orders": self._payment_metrics.failed_orders,
                "refunded_orders": self._payment_metrics.refunded_orders,
                "total_amount": self._payment_metrics.total_amount,
                "successful_amount": self._payment_metrics.successful_amount,
                "success_rate": self._payment_metrics.success_rate,
                "by_method": self._payment_metrics.by_method,
                "by_type": self._payment_metrics.by_type,
            },
            "user": {
                "dau": self._user_retention.dau,
                "wau": self._user_retention.wau,
                "mau": self._user_retention.mau,
                "retention_rates": {
                    "day1": self._user_retention.day1_retention,
                    "day7": self._user_retention.day7_retention,
                    "day30": self._user_retention.day30_retention,
                },
                "new_users": {
                    "today": self._user_retention.new_users_today,
                    "this_week": self._user_retention.new_users_this_week,
                    "this_month": self._user_retention.new_users_this_month,
                },
            },
            "lawyer": {
                "total_responses": self._lawyer_metrics.total_responses,
                "avg_response_time": self._lawyer_metrics.avg_response_time,
                "median_response_time": self._lawyer_metrics.median_response_time,
                "p95_response_time": self._lawyer_metrics.p95_response_time,
                "p99_response_time": self._lawyer_metrics.p99_response_time,
            },
            "moderation": {
                "total_moderations": self._moderation_metrics.total_moderations,
                "approved_count": self._moderation_metrics.approved_count,
                "rejected_count": self._moderation_metrics.rejected_count,
                "pending_count": self._moderation_metrics.pending_count,
                "avg_moderation_time": self._moderation_metrics.avg_moderation_time,
                "approval_rate": self._moderation_metrics.approval_rate,
                "by_content_type": self._moderation_metrics.by_content_type,
            },
            "counters": dict(self._counters),
        }
    
    def get_uptime_seconds(self) -> float:
        """获取运行时间（秒）
        
        Returns:
            运行时间
        """
        return time.time() - self._start_time


# 全局业务指标收集器实例
_business_metrics_collector: Optional[BusinessMetricsCollector] = None


def get_business_metrics_collector() -> BusinessMetricsCollector:
    """获取业务指标收集器单例
    
    Returns:
        业务指标收集器实例
    """
    global _business_metrics_collector
    if _business_metrics_collector is None:
        _business_metrics_collector = BusinessMetricsCollector()
    return _business_metrics_collector


# 便捷函数
def record_consultation_metric(
    stage: ConsultationStage | str,
    user_id: Optional[int] = None,
    consultation_id: Optional[int] = None,
) -> None:
    """记录咨询指标的便捷函数"""
    get_business_metrics_collector().record_consultation_funnel(stage, user_id, consultation_id)


def record_payment_metric(
    success: bool,
    order_no: str,
    amount: float,
    payment_method: str = "unknown",
    order_type: str = "unknown",
    user_id: Optional[int] = None,
    reason: Optional[str] = None,
) -> None:
    """记录支付指标的便捷函数"""
    collector = get_business_metrics_collector()
    if success:
        collector.record_payment_success(order_no, amount, payment_method, order_type, user_id)
    else:
        collector.record_payment_fail(order_no, reason or "unknown", payment_method, order_type, user_id, amount)


def record_lawyer_response_metric(
    lawyer_id: int,
    response_time_seconds: float,
    consultation_id: Optional[int] = None,
) -> None:
    """记录律师响应指标的便捷函数"""
    get_business_metrics_collector().record_lawyer_response(lawyer_id, response_time_seconds, consultation_id)


def record_moderation_metric(
    content_type: str,
    action: ModerationAction | str,
    duration: float,
    content_id: Optional[int] = None,
    moderator_id: Optional[int] = None,
) -> None:
    """记录内容审核指标的便捷函数"""
    get_business_metrics_collector().record_content_moderation(
        content_type, action, duration, content_id, moderator_id
    )