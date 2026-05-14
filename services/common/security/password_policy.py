"""密码策略验证

提供强密码策略验证，符合 OWASP 标准。
支持：
- 最小长度要求
- 大小写字母、数字、特殊字符要求
- 常见弱密码检测
- 密码历史检查（禁止重复使用）
"""
import re
import hashlib
from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime, timezone


Base = DeclarativeBase()


class PasswordPolicyError(Exception):
    """密码策略验证错误"""
    pass


class PasswordHistory(Base):
    """密码历史表"""
    __tablename__ = "password_history"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    password_hash = Column(String(128), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


COMMON_WEAK_PASSWORDS = {
    "password", "123456", "12345678", "qwerty", "abc123",
    "monkey", "master", "dragon", "111111", "baseball",
    "iloveyou", "trustno1", "sunshine", "letmein", "welcome",
    "admin", "password1", "1234567", "123456789", "1234567890",
    "admin123", "root", "toor", "pass", "test", "guest",
    "baixing123", "falv123", "legal123", "admin888",
}


def validate_password(
    password: str,
    min_length: int = 8,
    max_length: int = 128,
    require_uppercase: bool = True,
    require_lowercase: bool = True,
    require_digit: bool = True,
    require_special: bool = True,
    username: Optional[str] = None,
    email: Optional[str] = None,
    previous_passwords: Optional[list[str]] = None,
    check_common: bool = True,
) -> bool:
    """
    验证密码是否符合策略要求

    Args:
        password: 待验证的密码
        min_length: 最小长度（默认 8）
        max_length: 最大长度（默认 128）
        require_uppercase: 是否需要大写字母
        require_lowercase: 是否需要小写字母
        require_digit: 是否需要数字
        require_special: 是否需要特殊字符
        username: 用户名（用于检测是否包含用户名）
        email: 邮箱（用于检测是否包含邮箱前缀）
        previous_passwords: 历史密码列表（用于检测重复）
        check_common: 是否检测常见弱密码

    Returns:
        True 如果密码符合要求

    Raises:
        PasswordPolicyError: 如果密码不符合要求
    """
    if not password:
        raise PasswordPolicyError("密码不能为空")

    if len(password) < min_length:
        raise PasswordPolicyError(f"密码长度至少为 {min_length} 个字符")

    if len(password) > max_length:
        raise PasswordPolicyError(f"密码长度不能超过 {max_length} 个字符")

    if require_uppercase and not re.search(r"[A-Z]", password):
        raise PasswordPolicyError("密码必须包含至少一个大写字母")

    if require_lowercase and not re.search(r"[a-z]", password):
        raise PasswordPolicyError("密码必须包含至少一个小写字母")

    if require_digit and not re.search(r"\d", password):
        raise PasswordPolicyError("密码必须包含至少一个数字")

    if require_special and not re.search(r"[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]", password):
        raise PasswordPolicyError("密码必须包含至少一个特殊字符 (!@#$%^&*...)")

    if check_common and password.lower() in COMMON_WEAK_PASSWORDS:
        raise PasswordPolicyError("密码过于常见，请选择更安全的密码")

    if username and username.lower() in password.lower():
        raise PasswordPolicyError("密码不能包含用户名")

    if email:
        email_prefix = email.split("@")[0].lower()
        if email_prefix and email_prefix in password.lower():
            raise PasswordPolicyError("密码不能包含邮箱前缀")

    if previous_passwords:
        for prev in previous_passwords:
            if _hash_password(password) == _hash_password(prev):
                raise PasswordPolicyError("不能使用最近使用过的密码")

    return True


def _hash_password(password: str) -> str:
    """简单哈希用于历史密码比对"""
    return hashlib.sha256(password.encode()).hexdigest()


def check_password_strength(password: str) -> dict:
    """
    检查密码强度评分

    Returns:
        包含强度评分和详细信息的字典
    """
    score = 0
    issues = []

    if len(password) >= 8:
        score += 1
    else:
        issues.append("长度不足8位")

    if len(password) >= 12:
        score += 1

    if re.search(r"[A-Z]", password):
        score += 1
    else:
        issues.append("缺少大写字母")

    if re.search(r"[a-z]", password):
        score += 1
    else:
        issues.append("缺少小写字母")

    if re.search(r"\d", password):
        score += 1
    else:
        issues.append("缺少数字")

    if re.search(r"[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]", password):
        score += 1
    else:
        issues.append("缺少特殊字符")

    if len(password) >= 16:
        score += 1

    levels = ["极弱", "弱", "一般", "强", "很强", "极强"]
    level = levels[min(score, len(levels) - 1)]

    return {
        "score": score,
        "max_score": 7,
        "level": level,
        "issues": issues,
        "is_strong": score >= 4,
    }
