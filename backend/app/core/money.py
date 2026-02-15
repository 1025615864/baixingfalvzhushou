"""金额精度处理工具

提供精确的金融金额计算功能，防止浮点数精度问题。

功能特性:
    - 使用Decimal进行精确计算
    - 金额与分的双向转换
    - 舍入模式配置
    - 历史数据兼容处理

使用示例:
    ```python
    from app.core.money import (
        Money,
        amount_to_cents,
        cents_to_amount,
        quantize_amount,
    )

    # 创建Money对象
    price = Money(99.99)
    price_cents = price.to_cents()  # 9999

    # 安全计算
    total = Money("0.1") + Money("0.2")  # 0.30 而不是 0.30000000000000004
    ```
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Any


ROUNDING_MODE = ROUND_HALF_UP
PRECISION = Decimal("0.01")
CENT_PRECISION = Decimal("1")


@dataclass
class Money:
    """金额对象

    使用Decimal进行精确金额计算。

    Attributes:
        amount: 金额（Decimal类型）

    Examples:
        >>> price = Money(99.99)
        >>> price.to_cents()
        9999
        >>> price * 2
        Money(amount=Decimal('199.98'))
    """

    amount: Decimal

    def __init__(self, value: float | str | int | Decimal) -> None:
        if isinstance(value, float):
            self.amount = Decimal(str(value)).quantize(PRECISION, rounding=ROUNDING_MODE)
        else:
            self.amount = Decimal(value).quantize(PRECISION, rounding=ROUNDING_MODE)

    def __repr__(self) -> str:
        return f"Money(amount={self.amount!r})"

    def __str__(self) -> str:
        return f"{self.amount:.2f}"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        return self.amount == other.amount

    def __lt__(self, other: Money) -> bool:
        return self.amount < other.amount

    def __le__(self, other: Money) -> bool:
        return self.amount <= other.amount

    def __gt__(self, other: Money) -> bool:
        return self.amount > other.amount

    def __ge__(self, other: Money) -> bool:
        return self.amount >= other.amount

    def __add__(self, other: Money) -> Money:
        return Money(self.amount + other.amount)

    def __sub__(self, other: Money) -> Money:
        return Money(self.amount - other.amount)

    def __mul__(self, other: float | int | Decimal) -> Money:
        if isinstance(other, (float, int)):
            other = Decimal(str(other))
        return Money(self.amount * other)

    def __truediv__(self, other: float | int | Decimal | Money) -> Money:
        if isinstance(other, Money):
            return Money(self.amount / other.amount)
        if isinstance(other, (float, int)):
            other = Decimal(str(other))
        return Money(self.amount / other)

    def to_cents(self) -> int:
        """转换为分（整数）

        Returns:
            金额对应的分值
        """
        return int((self.amount * Decimal("100")).quantize(CENT_PRECISION, rounding=ROUNDING_MODE))

    def to_float(self) -> float:
        """转换为浮点数

        Returns:
            金额浮点值
        """
        return float(self.amount)

    def is_zero(self) -> bool:
        """检查是否为零"""
        return self.amount == Decimal("0")

    def is_positive(self) -> bool:
        """检查是否为正数"""
        return self.amount > Decimal("0")

    def abs(self) -> Money:
        """获取绝对值"""
        return Money(abs(self.amount))


def quantize_amount(amount: float | str | Decimal | int) -> Decimal:
    """金额舍入到2位小数

    Args:
        amount: 原始金额

    Returns:
        舍入后的Decimal金额

    Examples:
        >>> quantize_amount(99.999)
        Decimal('100.00')
        >>> quantize_amount("99.999")
        Decimal('100.00')
    """
    if isinstance(amount, float):
        return Decimal(str(amount)).quantize(PRECISION, rounding=ROUNDING_MODE)
    return Decimal(amount).quantize(PRECISION, rounding=ROUNDING_MODE)


def amount_to_cents(amount: float | str | Decimal | int) -> int:
    """将金额转换为分（整数）

    Args:
        amount: 金额

    Returns:
        金额对应的分值

    Examples:
        >>> amount_to_cents(99.99)
        9999
        >>> amount_to_cents("0.1")
        10
    """
    decimal_amount = quantize_amount(amount)
    return int((decimal_amount * Decimal("100")).quantize(CENT_PRECISION, rounding=ROUNDING_MODE))


def cents_to_amount(cents: int | str) -> Decimal:
    """将分转换为金额

    Args:
        cents: 分值

    Returns:
        金额Decimal

    Examples:
        >>> cents_to_amount(9999)
        Decimal('99.99')
        >>> cents_to_amount("100")
        Decimal('1.00')
    """
    if isinstance(cents, str):
        cents = int(cents)
    return (Decimal(cents) / Decimal("100")).quantize(PRECISION, rounding=ROUNDING_MODE)


def format_money(amount: float | str | Decimal | int, currency: str = "CNY") -> str:
    """格式化金额显示

    Args:
        amount: 金额
        currency: 货币符号

    Returns:
        格式化的金额字符串

    Examples:
        >>> format_money(99.99)
        '¥99.99'
        >>> format_money(99.99, "$")
        '$99.99'
    """
    decimal_amount = quantize_amount(amount)
    symbol = {"CNY": "¥", "USD": "$"}.get(currency.upper(), currency)
    return f"{symbol}{decimal_amount:.2f}"


def safe_add(*amounts: float | str | Decimal | int) -> Decimal:
    """安全加法（防止精度丢失）

    Args:
        amounts: 要相加的金额列表

    Returns:
        相加结果
    """
    result = Decimal("0")
    for amount in amounts:
        result += quantize_amount(amount)
    return result


def safe_subtract(a: float | str | Decimal | int, b: float | str | Decimal | int) -> Decimal:
    """安全减法（防止精度丢失）

    Args:
        a: 被减数
        b: 减数

    Returns:
        相减结果
    """
    return quantize_amount(a) - quantize_amount(b)


def safe_multiply(amount: float | str | Decimal | int, multiplier: float | int | Decimal) -> Decimal:
    """安全乘法（防止精度丢失）

    Args:
        amount: 金额
        multiplier: 乘数

    Returns:
        相乘结果
    """
    return quantize_amount(amount) * Decimal(str(multiplier))


def safe_divide(amount: float | str | Decimal | int, divisor: float | int | Decimal) -> Decimal:
    """安全除法（防止精度丢失）

    Args:
        amount: 被除数
        divisor: 除数

    Returns:
        相除结果
    """
    if isinstance(divisor, (float, int)):
        divisor = Decimal(str(divisor))
    if divisor == Decimal("0"):
        raise ValueError("Division by zero")
    return (quantize_amount(amount) / divisor).quantize(PRECISION, rounding=ROUNDING_MODE)


class MoneyCalculator:
    """金额计算器

    提供链式金额计算功能。

    Examples:
        >>> calc = MoneyCalculator(100)
        >>> calc.add(50).subtract(30).multiply(2).result()
        Decimal('240.00')
    """

    def __init__(self, initial: float | str | Decimal | int = 0) -> None:
        self.value = quantize_amount(initial)

    def reset(self, value: float | str | Decimal | int = 0) -> MoneyCalculator:
        """重置计算器"""
        self.value = quantize_amount(value)
        return self

    def add(self, amount: float | str | Decimal | int) -> MoneyCalculator:
        """加法"""
        self.value = self.value + quantize_amount(amount)
        return self

    def subtract(self, amount: float | str | Decimal | int) -> MoneyCalculator:
        """减法"""
        self.value = self.value - quantize_amount(amount)
        return self

    def multiply(self, multiplier: float | int | Decimal) -> MoneyCalculator:
        """乘法"""
        self.value = self.value * Decimal(str(multiplier))
        self.value = quantize_amount(self.value)
        return self

    def divide(self, divisor: float | int | Decimal) -> MoneyCalculator:
        """除法"""
        if isinstance(divisor, (float, int)):
            divisor = Decimal(str(divisor))
        if divisor == Decimal("0"):
            raise ValueError("Division by zero")
        self.value = self.value / divisor
        self.value = quantize_amount(self.value)
        return self

    def percentage(self, percent: float | int | Decimal) -> MoneyCalculator:
        """百分比计算"""
        self.value = self.value * Decimal(str(percent)) / Decimal("100")
        self.value = quantize_amount(self.value)
        return self

    def result(self) -> Decimal:
        """获取结果"""
        return self.value

    def to_money(self) -> Money:
        """获取Money对象"""
        return Money(self.value)

    def to_cents(self) -> int:
        """获取分值"""
        return amount_to_cents(self.value)


def validate_amount_range(
    amount: float | str | Decimal | int,
    min_amount: float | str | Decimal | int = Decimal("0.01"),
    max_amount: float | str | Decimal | int = Decimal("99999999.99"),
) -> tuple[bool, str | None]:
    """验证金额范围

    Args:
        amount: 要验证的金额
        min_amount: 最小金额
        max_amount: 最大金额

    Returns:
        (是否有效, 错误消息)
    """
    decimal_amount = quantize_amount(amount)
    min_decimal = quantize_amount(min_amount)
    max_decimal = quantize_amount(max_amount)

    if decimal_amount < min_decimal:
        return False, f"金额不能小于 {min_decimal:.2f}"

    if decimal_amount > max_decimal:
        return False, f"金额不能大于 {max_decimal:.2f}"

    return True, None
