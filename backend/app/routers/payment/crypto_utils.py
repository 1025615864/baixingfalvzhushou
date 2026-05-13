from __future__ import annotations

import hashlib
from urllib.parse import urlencode


def _ikunpay_sign_md5(params: dict, key: str) -> str:
    filtered = {k: v for k, v in params.items() if k not in ("sign", "sign_type") and v != ""}
    sorted_items = sorted(filtered.items(), key=lambda x: x[0])
    raw = "&".join(f"{k}={v}" for k, v in sorted_items)
    raw += key
    return hashlib.md5(raw.encode("utf-8")).hexdigest().lower()


def _alipay_sign_rsa2(params: dict, private_key_pem: str) -> str:
    filtered = {k: v for k, v in params.items() if k not in ("sign", "sign_type") and v != ""}
    sorted_items = sorted(filtered.items(), key=lambda x: x[0])
    raw = "&".join(f"{k}={v}" for k, v in sorted_items)

    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding
    import base64

    if isinstance(private_key_pem, str):
        private_key = serialization.load_pem_private_key(
            private_key_pem.encode("utf-8"), password=None,
        )
    else:
        private_key = private_key_pem

    signature = private_key.sign(
        raw.encode("utf-8"),
        padding.PKCS1v15(),
        hashes.SHA256(),
    )
    return base64.b64encode(signature).decode("utf-8")


def _alipay_verify_rsa2(params: dict, public_key_pem: str, sign: str) -> bool:
    filtered = {k: v for k, v in params.items() if k not in ("sign", "sign_type") and v != ""}
    sorted_items = sorted(filtered.items(), key=lambda x: x[0])
    raw = "&".join(f"{k}={v}" for k, v in sorted_items)

    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding
    import base64

    if isinstance(public_key_pem, str):
        public_key = serialization.load_pem_public_key(
            public_key_pem.encode("utf-8"),
        )
    else:
        public_key = public_key_pem

    try:
        public_key.verify(
            base64.b64decode(sign),
            raw.encode("utf-8"),
            padding.PKCS1v15(),
            hashes.SHA256(),
        )
        return True
    except Exception:
        return False


def _ikunpay_verify_md5(params: dict, key: str, sign: str) -> bool:
    expected = _ikunpay_sign_md5(params, key)
    return expected == sign.lower()
