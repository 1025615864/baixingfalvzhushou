"""测试密钥加密轮换策略"""
import pytest
from app.utils.secret_crypto import (
    encrypt_secret,
    decrypt_secret,
    rotate_key,
    initialize_keys,
    get_key_versions,
    get_current_key_version,
)


class TestSecretCryptoKeyRotation:
    """测试密钥加密轮换策略"""

    @pytest.fixture(autouse=True)
    def setup_keys(self):
        """每个测试前清理密钥状态"""
        from app.utils.secret_crypto import _key_manager
        _key_manager._keys.clear()
        _key_manager._current_version = 1
        yield
        _key_manager._keys.clear()
        _key_manager._current_version = 1

    def test_encrypt_with_version(self):
        """测试带版本号的加密"""
        initialize_keys("test-key-1")
        
        encrypted = encrypt_secret("my-secret")
        
        # 应该包含版本号
        assert "v1:" in encrypted
        assert encrypted.startswith("enc:")

    def test_decrypt_with_version(self):
        """测试带版本号的解密"""
        initialize_keys("test-key-1")
        
        original = "my-secret"
        encrypted = encrypt_secret(original)
        decrypted = decrypt_secret(encrypted)
        
        assert decrypted == original

    def test_backward_compatibility_old_format(self):
        """测试向后兼容旧格式（无版本号）"""
        initialize_keys("test-key-1")
        
        # 模拟旧格式加密
        from cryptography.fernet import Fernet
        import base64
        import hashlib
        
        secret = "test-key-1"
        digest = hashlib.sha256(secret.encode("utf-8")).digest()
        key = base64.urlsafe_b64encode(digest)
        fernet = Fernet(key)
        
        original = "my-secret"
        token = fernet.encrypt(original.encode("utf-8")).decode("utf-8")
        old_format = f"enc:{token}"
        
        decrypted = decrypt_secret(old_format)
        
        assert decrypted == original

    def test_key_rotation(self):
        """测试密钥轮换"""
        initialize_keys("old-key")
        
        # 使用旧密钥加密
        encrypted_v1 = encrypt_secret("secret-v1")
        assert "v1:" in encrypted_v1
        
        # 轮换密钥
        new_version = rotate_key("new-key")
        assert new_version == 2
        assert get_current_key_version() == 2
        
        # 使用新密钥加密
        encrypted_v2 = encrypt_secret("secret-v2")
        assert "v2:" in encrypted_v2
        
        # 解密v1加密的数据（应该成功）
        decrypted_v1 = decrypt_secret(encrypted_v1)
        assert decrypted_v1 == "secret-v1"
        
        # 解密v2加密的数据
        decrypted_v2 = decrypt_secret(encrypted_v2)
        assert decrypted_v2 == "secret-v2"

    def test_multiple_key_rotations(self):
        """测试多次密钥轮换"""
        # 清理全局状态，确保测试隔离
        from app.utils.secret_crypto import _key_manager
        _key_manager._keys.clear()
        _key_manager._current_version = 1
        
        initialize_keys("key-v1")
        
        # 第一次轮换
        rotate_key("key-v2")
        assert get_current_key_version() == 2
        assert get_key_versions() == [1, 2]
        
        # 第二次轮换
        rotate_key("key-v3")
        assert get_current_key_version() == 3
        assert get_key_versions() == [1, 2, 3]
        
        # 验证所有版本都能解密
        encrypted_v1 = encrypt_secret("secret-1")
        encrypted_v2 = encrypt_secret("secret-2")
        encrypted_v3 = encrypt_secret("secret-3")
        
        assert decrypt_secret(encrypted_v1) == "secret-1"
        assert decrypt_secret(encrypted_v2) == "secret-2"
        assert decrypt_secret(encrypted_v3) == "secret-3"

    def test_get_key_versions(self):
        """测试获取密钥版本列表"""
        # 清理全局状态
        from app.utils.secret_crypto import _key_manager
        _key_manager._keys.clear()
        _key_manager._current_version = 1
        
        initialize_keys("key-1")
        
        versions = get_key_versions()
        assert versions == [1]
        
        rotate_key("key-2")
        versions = get_key_versions()
        assert versions == [1, 2]
        
        rotate_key("key-3")
        versions = get_key_versions()
        assert versions == [1, 2, 3]

    def test_get_current_key_version(self):
        """测试获取当前密钥版本"""
        initialize_keys("key-1")
        assert get_current_key_version() == 1
        
        rotate_key("key-2")
        assert get_current_key_version() == 2
        
        rotate_key("key-3")
        assert get_current_key_version() == 3

    def test_empty_secret_handling(self):
        """测试空密钥处理"""
        initialize_keys("test-key")
        
        # 加密空字符串
        encrypted = encrypt_secret("")
        assert encrypted == ""
        
        # 解密空字符串
        decrypted = decrypt_secret("")
        assert decrypted == ""

    def test_non_encrypted_secret(self):
        """测试非加密密钥"""
        initialize_keys("test-key")
        
        # 非加密密钥应该原样返回
        decrypted = decrypt_secret("plain-text")
        assert decrypted == "plain-text"

    def test_encrypted_secret_passthrough(self):
        """测试已加密密钥的透传"""
        initialize_keys("test-key")
        
        # 加密后的密钥再次加密应该保持不变
        encrypted1 = encrypt_secret("my-secret")
        encrypted2 = encrypt_secret(encrypted1)
        
        assert encrypted1 == encrypted2
