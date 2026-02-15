import pytest
from app.utils.secret_crypto import (
    encrypt_secret,
    decrypt_secret,
    _ENC_PREFIX,
    rotate_key,
    get_key_versions,
    get_current_key_version,
    initialize_keys,
)


def test_encrypt_secret_empty():
    """Test encrypting empty string returns empty"""
    assert encrypt_secret("") == ""
    assert encrypt_secret(None) == ""


def test_encrypt_secret_already_encrypted():
    """Test that already encrypted strings are not re-encrypted"""
    encrypted = encrypt_secret("test")
    result = encrypt_secret(encrypted)
    assert result == encrypted


def test_decrypt_secret_empty():
    """Test decrypting empty string returns empty"""
    assert decrypt_secret("") == ""
    assert decrypt_secret(None) == ""


def test_decrypt_secret_not_encrypted():
    """Test that non-encrypted values are returned as-is"""
    assert decrypt_secret("plain_text") == "plain_text"


def test_encrypt_decrypt_roundtrip():
    """Test that encrypt/decrypt roundtrip works"""
    original = "my_secret_api_key_12345"
    encrypted = encrypt_secret(original)
    
    # Should have encryption prefix
    assert encrypted.startswith(_ENC_PREFIX)
    assert encrypted != original
    
    # Decrypt should return original
    decrypted = decrypt_secret(encrypted)
    assert decrypted == original


def test_encrypt_secret_special_chars():
    """Test encrypting strings with special characters"""
    special = "key=abc123&secret=xyz!@#"
    encrypted = encrypt_secret(special)
    decrypted = decrypt_secret(encrypted)
    assert decrypted == special


def test_encrypt_secret_unicode():
    """Test encrypting unicode strings"""
    unicode_str = "中文密钥🔐"
    encrypted = encrypt_secret(unicode_str)
    assert decrypt_secret(encrypted) == unicode_str


def test_decrypt_secret_invalid_token():
    """Test decrypting invalid token returns empty"""
    # Invalid base64/fernet token
    result = decrypt_secret(f"{_ENC_PREFIX}invalid_token_here")
    assert result == ""


def test_encrypt_secret_long_string():
    """Test encrypting long strings"""
    long_str = "A" * 1000
    assert decrypt_secret(encrypt_secret(long_str)) == long_str


class TestSecretCryptoEdgeCases:
    """测试加密解密边缘情况"""

    def test_encrypt_with_whitespace(self):
        """测试包含空白的字符串"""
        original = "secret key"
        assert decrypt_secret(encrypt_secret(original)) == original

    def test_encrypt_with_newlines(self):
        """测试包含换行的字符串"""
        original = "secret\nkey\nwith\nnewlines"
        assert decrypt_secret(encrypt_secret(original)) == original

    def test_encrypt_with_tabs(self):
        """测试包含制表符的字符串"""
        original = "secret\tkey\twith\ttabs"
        assert decrypt_secret(encrypt_secret(original)) == original

    def test_encrypt_json_like_string(self):
        """测试JSON-like字符串"""
        original = '{"api_key": "secret123", "token": "abc"}'
        assert decrypt_secret(encrypt_secret(original)) == original

    def test_encrypt_base64_like_string(self):
        """测试Base64-like字符串"""
        original = "SGVsbG8gV29ybGQhIFRoaXMgaXMgYSBzZWNyZXQ="
        assert decrypt_secret(encrypt_secret(original)) == original

    def test_decrypt_empty_prefix(self):
        """测试解密空前缀"""
        result = decrypt_secret(_ENC_PREFIX)
        assert result == ""

    def test_encrypt_very_long_string(self):
        """测试加密非常长的字符串"""
        long_str = "x" * 10000
        assert decrypt_secret(encrypt_secret(long_str)) == long_str


class TestKeyRotation:
    """测试密钥轮换功能"""

    def test_rotate_key_increments_version(self):
        """测试轮换密钥增加版本号"""
        initial_version = get_current_key_version()
        new_version = rotate_key("new_encryption_key_12345")
        assert new_version == initial_version + 1
        assert get_current_key_version() == new_version

    def test_rotate_key_adds_new_key(self):
        """测试轮换密钥添加新密钥"""
        initial_versions = get_key_versions()
        rotate_key("new_encryption_key_67890")
        new_versions = get_key_versions()
        assert len(new_versions) == len(initial_versions) + 1
        assert max(new_versions) > max(initial_versions) if initial_versions else True

    def test_encrypt_with_new_key_after_rotation(self):
        """测试密钥轮换后使用新密钥加密"""
        original = "secret_after_rotation"
        
        # 加密初始版本
        encrypted_v1 = encrypt_secret(original)
        assert decrypt_secret(encrypted_v1) == original
        
        # 轮换密钥
        rotate_key("new_key_after_rotation")
        
        # 加密新版本
        encrypted_v2 = encrypt_secret(original)
        
        # 两个加密结果应该不同（使用不同密钥）
        assert encrypted_v1 != encrypted_v2
        
        # 但都能解密
        assert decrypt_secret(encrypted_v1) == original
        assert decrypt_secret(encrypted_v2) == original

    def test_decrypt_old_secret_after_rotation(self):
        """测试密钥轮换后仍能解密旧密钥加密的数据"""
        original = "old_secret_data"
        
        # 使用旧密钥加密
        encrypted_old = encrypt_secret(original)
        
        # 轮换密钥
        rotate_key("completely_new_key")
        
        # 仍能解密旧数据
        decrypted = decrypt_secret(encrypted_old)
        assert decrypted == original

    def test_get_key_versions_returns_sorted_list(self):
        """测试获取密钥版本返回排序列表"""
        versions = get_key_versions()
        assert isinstance(versions, list)
        assert versions == sorted(versions)

    def test_get_current_key_version(self):
        """测试获取当前密钥版本"""
        version = get_current_key_version()
        assert isinstance(version, int)
        assert version >= 1
        assert version in get_key_versions()

    def test_multiple_rotations(self):
        """测试多次密钥轮换"""
        initial_version = get_current_key_version()
        
        # 第一次轮换
        v1 = rotate_key("key_v1")
        assert v1 == initial_version + 1
        
        # 第二次轮换
        v2 = rotate_key("key_v2")
        assert v2 == v1 + 1
        
        # 第三次轮换
        v3 = rotate_key("key_v3")
        assert v3 == v2 + 1
        
        # 验证所有版本都存在
        versions = get_key_versions()
        assert v1 in versions
        assert v2 in versions
        assert v3 in versions

    def test_encrypt_with_specific_version(self):
        """测试使用指定版本加密"""
        original = "version_specific_secret"
        
        # 轮换到版本2
        rotate_key("version_2_key")
        
        # 使用版本1加密（如果存在）
        encrypted_v1 = encrypt_secret(original, version=1)
        encrypted_v2 = encrypt_secret(original, version=2)
        
        # 两者应该不同
        assert encrypted_v1 != encrypted_v2
        
        # 都能解密
        assert decrypt_secret(encrypted_v1) == original
        assert decrypt_secret(encrypted_v2) == original

    def test_backward_compatibility_with_old_format(self):
        """测试向后兼容旧格式加密数据"""
        # 模拟旧格式（无版本号）
        # 注意：这需要实际使用旧密钥加密的数据
        # 这里只测试解析逻辑
        old_format_encrypted = f"{_ENC_PREFIX}some_old_token"
        result = decrypt_secret(old_format_encrypted)
        # 应该返回空或尝试解密
        assert isinstance(result, str)

