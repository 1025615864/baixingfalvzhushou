"""密码策略 - 安全校验"""
import re
import logging

logger = logging.getLogger(__name__)

COMMON_PASSWORDS = {
    "123456", "password", "123456789", "12345678", "12345",
    "1234567", "1234567890", "qwerty", "abc123", "monkey",
    "123123", "letmein", "trustno1", "dragon", "baseball",
    "iloveyou", "master", "sunshine", "ashley", "fuckme",
    "passw0rd", "shadow", "123321", "princess", "password1",
}


class PasswordPolicy:
    """密码强度策略"""

    MIN_LENGTH = 8
    MAX_LENGTH = 128
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_DIGIT = True
    REQUIRE_SPECIAL = False
    COMMON_PASSWORD_CHECK = True

    @classmethod
    def validate(cls, password: str) -> tuple[bool, str]:
        """校验密码强度

        Returns:
            (is_valid, error_message)
        """
        if not password:
            return False, "密码不能为空"

        if len(password) < cls.MIN_LENGTH:
            return False, f"密码长度不能少于{cls.MIN_LENGTH}位"

        if len(password) > cls.MAX_LENGTH:
            return False, f"密码长度不能超过{cls.MAX_LENGTH}位"

        if cls.COMMON_PASSWORD_CHECK and password.lower() in COMMON_PASSWORDS:
            return False, "密码太简单，请使用更复杂的密码"

        if cls.REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
            return False, "密码需要包含大写字母"

        if cls.REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
            return False, "密码需要包含小写字母"

        if cls.REQUIRE_DIGIT and not re.search(r'\d', password):
            return False, "密码需要包含数字"

        if cls.REQUIRE_SPECIAL and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "密码需要包含特殊字符"

        return True, ""


password_policy = PasswordPolicy()
