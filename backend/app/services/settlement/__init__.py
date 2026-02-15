"""结算服务模块

该模块已重构，核心组件已拆分到 settlement/ 目录：
- from ..settlement.core import SettlementService  # 核心结算服务
- from ..settlement.wallet import WalletService  # 钱包操作服务
- from ..settlement.income import IncomeService  # 收入记录服务
- from ..settlement.withdrawal import WithdrawalService  # 提现服务

向后兼容导入仍然可用。
"""

# 重新导出核心组件（向后兼容）
from .core import (
    SettlementService,
    _now,
    _quantize_amount,
    _decimal_to_cents,
    _mask_account_no,
    SETTLEMENT_PLATFORM_FEE_RATE,
    SETTLEMENT_FREEZE_DAYS,
    SETTLEMENT_WITHDRAW_MIN_AMOUNT,
    SETTLEMENT_WITHDRAW_MAX_AMOUNT,
    SETTLEMENT_WITHDRAW_FEE,
    SETTLEMENT_VERIFIED_MIN_COMPLETED,
    SETTLEMENT_VERIFIED_MIN_RATING,
    SETTLEMENT_VERIFIED_PLATFORM_FEE_RATE,
    SETTLEMENT_VERIFIED_FREEZE_DAYS,
    SETTLEMENT_GOLD_MIN_COMPLETED,
    SETTLEMENT_GOLD_MIN_RATING,
    SETTLEMENT_GOLD_PLATFORM_FEE_RATE,
    SETTLEMENT_GOLD_FREEZE_DAYS,
    SETTLEMENT_PARTNER_LAWYER_IDS,
    SETTLEMENT_PARTNER_PLATFORM_FEE_RATE,
    SETTLEMENT_PARTNER_FREEZE_DAYS,
)

# 导出子服务
from .income import IncomeService
from .withdrawal import WithdrawalService

# 保持原有文件的完整内容（向后兼容）
# 这样可以确保向后兼容，不需要修改任何调用方

_settlement_service = None


def get_settlement_service() -> SettlementService:
    """获取结算服务实例（懒加载）"""
    global _settlement_service
    if _settlement_service is None:
        _settlement_service = SettlementService()
    return _settlement_service


# 实例化单例（保持原有使用方式）
settlement_service = SettlementService()
