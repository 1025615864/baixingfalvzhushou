"""JWT密钥管理 - 支持RSA RS256"""
import os
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class JWTKeyManager:
    """JWT密钥管理器

    支持RS256非对称加密:
    - 私钥用于签发Token
    - 公钥用于验证Token
    """

    def __init__(
        self,
        private_key_path: Optional[str] = None,
        public_key_path: Optional[str] = None,
        jwt_secret_key: Optional[str] = None,
    ):
        self.jwt_algorithm = "RS256"
        self._private_key = None
        self._public_key = None
        self._secret_key = jwt_secret_key

        if private_key_path and public_key_path:
            self.private_key_path = Path(private_key_path)
            self.public_key_path = Path(public_key_path)
            self._load_keys()
        else:
            self.jwt_algorithm = "HS256"
            logger.warning("RSA keys not configured, falling back to HS256")

    def _load_keys(self):
        """加载RSA密钥对"""
        try:
            if self.private_key_path.exists():
                self._private_key = self.private_key_path.read_text()
                logger.info(f"Loaded private key from {self.private_key_path}")
            else:
                logger.warning(f"Private key not found at {self.private_key_path}")

            if self.public_key_path.exists():
                self._public_key = self.public_key_path.read_text()
                logger.info(f"Loaded public key from {self.public_key_path}")
            else:
                logger.warning(f"Public key not found at {self.public_key_path}")

            if self._private_key and self._public_key:
                self.jwt_algorithm = "RS256"
                logger.info("RSA keys loaded successfully, using RS256")
        except Exception as e:
            logger.error(f"Failed to load RSA keys: {e}")
            self.jwt_algorithm = "HS256"

    @property
    def private_key(self) -> Optional[str]:
        return self._private_key

    @property
    def public_key(self) -> Optional[str]:
        return self._public_key

    @property
    def secret_key(self) -> Optional[str]:
        return self._secret_key

    @property
    def algorithm(self) -> str:
        return self.jwt_algorithm

    def is_using_rsa(self) -> bool:
        return self.jwt_algorithm == "RS256"

    def get_public_key_pem(self) -> Optional[str]:
        """获取公钥PEM格式（用于JWKS）"""
        if self._public_key:
            return self._public_key
        if self._private_key:
            try:
                from cryptography.hazmat.primitives import serialization
                from cryptography.hazmat.primitives.asymmetric import rsa, padding
                from cryptography.hazmat.backends import default_backend
                import base64

                private_key = serialization.load_pem_private_key(
                    self._private_key.encode(),
                    password=None,
                    backend=default_backend()
                )
                public_key = private_key.public_key()
                public_key_pem = public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                )

                pem_str = public_key_pem.decode()
                pem_str = pem_str.replace("-----BEGIN PUBLIC KEY-----", "")
                pem_str = pem_str.replace("-----END PUBLIC KEY-----", "")
                pem_str = pem_str.replace("\n", "")

                return pem_str
            except Exception as e:
                logger.error(f"Failed to extract public key from private key: {e}")
        return None

    @staticmethod
    def generate_key_pair(private_path: str, public_path: str):
        """生成RSA密钥对

        Args:
            private_path: 私钥文件路径
            public_path: 公钥文件路径
        """
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.backends import default_backend

        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )

        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )

        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        Path(private_path).write_bytes(private_pem)
        Path(public_path).write_bytes(public_pem)

        os.chmod(private_path, 0o600)

        logger.info(f"Generated RSA key pair: {private_path}, {public_path}")


def create_jwt_key_manager() -> JWTKeyManager:
    """创建JWT密钥管理器"""
    settings_module = None
    try:
        from ..config.settings import get_settings
        settings_module = get_settings()
    except ImportError:
        pass

    if settings_module:
        return JWTKeyManager(
            private_key_path=os.getenv("JWT_PRIVATE_KEY_PATH"),
            public_key_path=os.getenv("JWT_PUBLIC_KEY_PATH"),
            jwt_secret_key=getattr(settings_module, "jwt_secret_key", None),
        )

    return JWTKeyManager(
        private_key_path=os.getenv("JWT_PRIVATE_KEY_PATH"),
        public_key_path=os.getenv("JWT_PUBLIC_KEY_PATH"),
        jwt_secret_key=os.getenv("JWT_SECRET_KEY"),
    )


jwt_key_manager = create_jwt_key_manager()
