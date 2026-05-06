#!/usr/bin/env python3
"""生成JWT RSA密钥对"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.jwt_keys import JWTKeyManager


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    keys_dir = os.path.join(base_dir, "keys")

    os.makedirs(keys_dir, exist_ok=True)

    private_path = os.path.join(keys_dir, "jwt_private.pem")
    public_path = os.path.join(keys_dir, "jwt_public.pem")

    if os.path.exists(private_path) or os.path.exists(public_path):
        print(f"Keys already exist at {keys_dir}")
        print("To regenerate, delete the existing keys first.")
        return

    JWTKeyManager.generate_key_pair(private_path, public_path)
    print(f"Generated RSA key pair:")
    print(f"  Private key: {private_path}")
    print(f"  Public key: {public_path}")
    print(f"\nSet environment variables:")
    print(f"  export JWT_PRIVATE_KEY_PATH={private_path}")
    print(f"  export JWT_PUBLIC_KEY_PATH={public_path}")


if __name__ == "__main__":
    main()
