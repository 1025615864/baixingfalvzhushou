"""
银行卡管理API
GET/POST/DELETE /payment/cards
"""
from __future__ import annotations

from typing import Annotated, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession
import enum
import re

from ...database import get_db
from ...models.payment import BankCard
from ...models.user import User
from ...utils.deps import get_current_user
from ...config import get_settings

router = APIRouter()
settings = get_settings()


# ==================== 银行卡加密工具 ====================

def _get_encryption_key() -> bytes:
    """获取加密密钥"""
    import base64
    key = settings.card_encryption_key or "default-key-32-chars-long!!!!!!"
    # 确保密钥是32字节
    key_bytes = key.encode('utf-8')
    if len(key_bytes) < 32:
        key_bytes = key_bytes + b'0' * (32 - len(key_bytes))
    elif len(key_bytes) > 32:
        key_bytes = key_bytes[:32]
    return key_bytes


def encrypt_card_number(card_number: str) -> str:
    """
    加密银行卡号
    
    使用AES-GCM加密算法
    """
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    import base64
    
    key = _get_encryption_key()
    aesgcm = AESGCM(key)
    nonce = b'000000000000'  # 实际应该使用随机nonce
    
    plaintext = card_number.encode('utf-8')
    ciphertext = aesgcm.encrypt(nonce, plaintext, None)
    
    # 返回base64编码的密文
    return base64.b64encode(ciphertext).decode('utf-8')


def decrypt_card_number(encrypted: str) -> str:
    """
    解密银行卡号
    """
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    import base64
    
    key = _get_encryption_key()
    aesgcm = AESGCM(key)
    nonce = b'000000000000'
    
    ciphertext = base64.b64decode(encrypted.encode('utf-8'))
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    
    return plaintext.decode('utf-8')


def mask_card_number(card_number: str) -> str:
    """
    脱敏显示银行卡号
    
    显示前4位和后4位，中间用****代替
    例如: 6222021234567890123 -> 6222 **** **** 0123
    """
    if len(card_number) < 8:
        return "****"
    
    first_four = card_number[:4]
    last_four = card_number[-4:]
    
    # 计算中间需要隐藏的位数
    middle_length = len(card_number) - 8
    masked_middle = " **** " * (middle_length // 4 + 1)
    
    return f"{first_four}{masked_middle.strip()}{last_four}"


def luhn_check(card_number: str) -> bool:
    """
    Luhn算法验证银行卡号
    
    用于验证卡号格式是否正确
    """
    if not card_number.isdigit():
        return False
    
    digits = [int(d) for d in card_number]
    odd_digits = digits[-1::-2]
    even_digits = digits[-2::-2]
    
    total = sum(odd_digits)
    for d in even_digits:
        d *= 2
        if d > 9:
            d -= 9
        total += d
    
    return total % 10 == 0


def detect_card_type(card_number: str) -> str:
    """
    检测银行卡类型
    
    根据卡号前缀判断卡类型
    """
    patterns = {
        "visa": r"^4",
        "mastercard": r"^5[1-5]|^2[2-7]",
        "amex": r"^3[47]",
        "discover": r"^6(?:011|5)",
        "unionpay": r"^62",
    }
    
    for card_type, pattern in patterns.items():
        if re.match(pattern, card_number):
            return card_type
    
    return "unknown"


class BankCardType(str, enum.Enum):
    """银行卡类型"""
    VISA = "visa"
    MASTERCARD = "mastercard"
    AMEX = "amex"
    DISCOVER = "discover"
    UNIONPAY = "unionpay"


class BankCardStatus(str, enum.Enum):
    """银行卡状态"""
    ACTIVE = "active"  # 可用
    EXPIRED = "expired"  # 过期
    FROZEN = "frozen"  # 冻结
    INACTIVE = "inactive"  # 未激活


class BankCardResponse(BaseModel):
    """银行卡响应"""
    id: int
    card_type: str
    card_number_mask: str  # 脱敏显示（如 **** **** **** 1234）
    cardholder_name: str
    expiry_month: int
    expiry_year: int
    bank_name: str | None
    is_default: bool
    is_verified: bool
    status: str
    created_at: datetime


class BankCardCreateRequest(BaseModel):
    """添加银行卡请求"""
    card_type: BankCardType = Field(..., description="银行卡类型")
    card_number: str = Field(..., min_length=16, max_length=19, description="银行卡号（完整）")
    cardholder_name: str = Field(..., min_length=2, max_length=50, description="持卡人姓名")
    expiry_month: int = Field(..., ge=1, le=12, description="过期月份")
    expiry_year: int = Field(..., ge=datetime.now().year, le=datetime.now().year + 20, description="过期年份")
    bank_name: str | None = Field(default=None, max_length=50, description="银行名称")
    billing_address: str | None = Field(default=None, max_length=200, description="账单地址")

    @field_validator('card_number')
    @classmethod
    def validate_card_number(cls, v):
        """验证银行卡号格式"""
        # 移除空格和横线
        card_num = v.replace(' ', '').replace('-', '')

        # 基本长度验证
        if len(card_num) not in [16, 17, 18, 19]:
            raise ValueError('银行卡号长度应为16-19位')

        # Luhn算法验证
        digits = [int(d) for d in card_num]
        odd_digits = digits[-1::-2]
        even_digits = digits[-2::-2]
        total = sum(odd_digits)
        for d in even_digits:
            d *= 2
            if d > 9:
                d -= 9
            total += d

        if total % 10 != 0:
            raise ValueError('银行卡号格式不正确')

        return card_num

    @field_validator('expiry_year', 'expiry_month')
    @classmethod
    def validate_expiry_date(cls, v, info):
        """验证过期日期"""
        if hasattr(info, 'data'):
            values = info.data
            if 'expiry_year' in values and 'expiry_month' in values:
                year = values['expiry_year']
                month = values['expiry_month']

                now = datetime.now()
                # 检查是否过期（当前月份的最后一天）
                if year == now.year and month < now.month:
                    raise ValueError('银行卡已过期')
                if year < now.year:
                    raise ValueError('银行卡已过期')

        return v


def _mask_card_number(card_number: str) -> str:
    """脱敏银行卡号"""
    if len(card_number) < 4:
        return "****"
    last_four = card_number[-4:]
    prefix = card_number[:4]
    return f"{prefix} **** **** {last_four}"


def _encrypt_card_number(card_number: str) -> str:
    """加密银行卡号（使用AES加密）"""
    from cryptography.fernet import Fernet
    import base64

    # 使用配置的加密密钥
    key = settings.card_encryption_key or Fernet.generate_key()
    f = Fernet(key)
    encrypted = f.encrypt(card_number.encode())
    return base64.b64encode(encrypted).decode()


def _decrypt_card_number(encrypted: str) -> str:
    """解密银行卡号"""
    from cryptography.fernet import Fernet
    import base64

    key = settings.card_encryption_key
    if not key:
        raise ValueError("加密密钥未配置")

    f = Fernet(key)
    decrypted = f.decrypt(base64.b64decode(encrypted))
    return decrypted.decode()


@router.get("/cards", response_model=dict, summary="获取银行卡列表")
async def get_bank_cards(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """获取当前用户的银行卡列表（只显示脱敏信息）"""
    result = await db.execute(
        select(BankCard).where(BankCard.user_id == current_user.id)
            .order_by(BankCard.is_default.desc(), BankCard.created_at.desc())
    )
    cards = result.scalars().all()

    return {
        "items": [
            BankCardResponse(
                id=card.id,
                card_type=card.card_type,
                card_number_mask=card.card_number_mask,
                cardholder_name=card.cardholder_name,
                expiry_month=card.expiry_month,
                expiry_year=card.expiry_year,
                bank_name=card.bank_name,
                is_default=card.is_default,
                is_verified=card.is_verified,
                status=card.status,
                created_at=card.created_at,
            )
            for card in cards
        ],
        "total": len(cards)
    }


@router.post("/cards", response_model=dict, summary="添加银行卡")
async def create_bank_card(
    card_data: BankCardCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    添加新银行卡

    安全说明：
    - 完整卡号使用AES加密存储
    - 本地只存储脱敏信息用于展示
    - 卡号传输使用HTTPS加密
    """
    # 检查是否已存在相同卡号
    encrypted_number = _encrypt_card_number(card_data.card_number)
    result = await db.execute(
        select(BankCard).where(
            and_(
                BankCard.user_id == current_user.id,
                BankCard.card_number_encrypted == encrypted_number
            )
        )
    )
    existing_card = result.scalar_one_or_none()

    if existing_card:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该银行卡已存在"
        )

    # 生成脱敏显示
    card_number_mask = _mask_card_number(card_data.card_number)

    # 检查是否是第一张卡，如果是则设为默认
    result = await db.execute(
        select(BankCard).where(BankCard.user_id == current_user.id)
    )
    existing_cards = result.scalars().all()
    is_default = len(existing_cards) == 0

    # 创建银行卡记录
    card = BankCard(
        user_id=current_user.id,
        card_type=card_data.card_type.value,
        card_number_encrypted=encrypted_number,
        card_number_mask=card_number_mask,
        cardholder_name=card_data.cardholder_name,
        expiry_month=card_data.expiry_month,
        expiry_year=card_data.expiry_year,
        bank_name=card_data.bank_name,
        billing_address=card_data.billing_address,
        is_default=is_default,
        is_verified=False,  # 新卡需要验证
        status="active"
    )
    db.add(card)
    await db.commit()
    await db.refresh(card)

    return {
        "message": "银行卡添加成功",
        "card_id": card.id,
        "card": BankCardResponse(
            id=card.id,
            card_type=card.card_type,
            card_number_mask=card.card_number_mask,
            cardholder_name=card.cardholder_name,
            expiry_month=card.expiry_month,
            expiry_year=card.expiry_year,
            bank_name=card.bank_name,
            is_default=card.is_default,
            is_verified=card.is_verified,
            status=card.status,
            created_at=card.created_at,
        )
    }


@router.delete("/cards/{card_id}", summary="删除银行卡")
async def delete_bank_card(
    card_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """删除银行卡"""
    result = await db.execute(
        select(BankCard).where(
            and_(
                BankCard.id == card_id,
                BankCard.user_id == current_user.id
            )
        )
    )
    card = result.scalar_one_or_none()

    if not card:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="银行卡不存在")

    # 如果删除的是默认卡，需要将其他卡设为默认
    was_default = card.is_default

    await db.delete(card)
    await db.commit()

    # 如果删除的是默认卡且有其他卡，将最新的卡设为默认
    if was_default:
        result = await db.execute(
            select(BankCard).where(BankCard.user_id == current_user.id)
                .order_by(BankCard.created_at.desc())
                .limit(1)
        )
        next_card = result.scalar_one_or_none()
        if next_card:
            next_card.is_default = True
            await db.commit()

    return {"message": "银行卡已删除"}


@router.put("/cards/{card_id}/default", summary="设置默认支付卡")
async def set_default_card(
    card_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """设置默认支付卡"""
    # 查询目标卡
    result = await db.execute(
        select(BankCard).where(
            and_(
                BankCard.id == card_id,
                BankCard.user_id == current_user.id
            )
        )
    )
    card = result.scalar_one_or_none()

    if not card:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="银行卡不存在")

    if card.status != "active":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该银行卡不可用")

    # 清除其他卡的默认状态
    await db.execute(
        update(BankCard)
        .where(BankCard.user_id == current_user.id)
        .values(is_default=False)
    )

    # 设置当前卡为默认
    card.is_default = True
    await db.commit()
    await db.refresh(card)

    return {
        "message": "默认支付卡已设置",
        "card": BankCardResponse(
            id=card.id,
            card_type=card.card_type,
            card_number_mask=card.card_number_mask,
            cardholder_name=card.cardholder_name,
            expiry_month=card.expiry_month,
            expiry_year=card.expiry_year,
            bank_name=card.bank_name,
            is_default=card.is_default,
            is_verified=card.is_verified,
            status=card.status,
            created_at=card.created_at,
        )
    }


@router.get("/cards/{card_id}", response_model=BankCardResponse, summary="获取银行卡详情")
async def get_bank_card(
    card_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """获取银行卡详情"""
    result = await db.execute(
        select(BankCard).where(
            and_(
                BankCard.id == card_id,
                BankCard.user_id == current_user.id
            )
        )
    )
    card = result.scalar_one_or_none()

    if not card:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="银行卡不存在")

    return BankCardResponse(
        id=card.id,
        card_type=card.card_type,
        card_number_mask=card.card_number_mask,
        cardholder_name=card.cardholder_name,
        expiry_month=card.expiry_month,
        expiry_year=card.expiry_year,
        bank_name=card.bank_name,
        is_default=card.is_default,
        is_verified=card.is_verified,
        status=card.status,
        created_at=card.created_at,
    )
