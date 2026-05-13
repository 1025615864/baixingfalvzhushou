import pytest
from pydantic import ValidationError
from app.schemas.user import UserCreate, UserUpdate, PasswordChange, PasswordResetConfirm
from tests.conftest import TEST_PASSWORD

class TestUserValidationEnhancement:
    
    def test_username_validation_basic(self):
        """Test basic username validation logic via schema"""
        # Valid
        valid_username = "user123_test"
        model = UserCreate(
            username=valid_username, 
            email="test@example.com", 
            password=TEST_PASSWORD,
            agree_terms=True,
            agree_privacy=True,
            agree_ai_disclaimer=True
        )
        assert model.username == valid_username

    def test_username_invalid_chars(self):
        with pytest.raises(ValidationError) as exc:
            UserCreate(
                username="invalid@user",
                email="test@example.com",
                password=TEST_PASSWORD,
                agree_terms=True,
                agree_privacy=True,
                agree_ai_disclaimer=True
            )
        assert "用户名只能包含中文、英文、数字和下划线" in str(exc.value)

    def test_username_length(self):
        """Test strict username length limits (2-20)"""
        # Too short (1 char) should fail
        with pytest.raises(ValidationError) as exc:
            UserCreate(
                username="u", 
                email="test@example.com", 
                password=TEST_PASSWORD,
                agree_terms=True,
                agree_privacy=True,
                agree_ai_disclaimer=True
            )
        errors = exc.value.errors()
        # Message might be standard pydantic min_length or custom validator
        assert any("String should have at least 2 characters" in e['msg'] or "用户名至少2个字符" in e['msg'] for e in errors)
    
    def test_password_complexity_valid(self):
        """Test valid password complexity"""
        model = UserCreate(
            username="validUser", 
            email="test@example.com", 
            password=TEST_PASSWORD,
            agree_terms=True,
            agree_privacy=True,
            agree_ai_disclaimer=True
        )
        assert model.password == TEST_PASSWORD

    def test_password_complexity_weak(self):
        """Test weak passwords"""
        # No digit
        with pytest.raises(ValidationError) as exc:
            UserCreate(
                username="validUser", 
                email="test@example.com", 
                password="PasswordOnly", 
                agree_terms=True,
                agree_privacy=True,
                agree_ai_disclaimer=True
            )
        assert "密码需包含大小写字母和数字" in str(exc.value)
        
        # No uppercase
        with pytest.raises(ValidationError):
            UserCreate(
                username="validUser", 
                email="test@example.com", 
                password="password1", 
                agree_terms=True,
                agree_privacy=True,
                agree_ai_disclaimer=True
            )

    def test_change_password_validation(self):
        """Test password complexity in PasswordChange schema"""
        with pytest.raises(ValidationError) as exc:
            PasswordChange(
                old_password="any",
                new_password="weak"
            )
        # Note: Pydantic 2.0+ standard error message for min_length
        assert "String should have at least 8 characters" in str(exc.value) or "密码长度至少8位" in str(exc.value)

    def test_phone_validation(self):
        """Test phone validation in UserUpdate"""
        # Valid
        model = UserUpdate(phone="13800138000")
        assert model.phone == "13800138000"
        
        # Invalid
        with pytest.raises(ValidationError) as exc:
            UserUpdate(phone="123456")
        assert "手机号格式不正确" in str(exc.value)
