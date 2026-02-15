#!/usr/bin/env python3
"""
生成生产环境安全密钥和密码
运行此脚本生成所有必需的安全配置
"""

import secrets
import string
import sys
from pathlib import Path


def generate_jwt_secret(length: int = 64) -> str:
    """生成JWT密钥"""
    return secrets.token_urlsafe(length)


def generate_password(length: int = 32) -> str:
    """生成强密码"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_payment_webhook_secret(length: int = 64) -> str:
    """生成支付回调密钥"""
    return secrets.token_urlsafe(length)


def generate_database_password(length: int = 32) -> str:
    """生成数据库密码"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_redis_password(length: int = 24) -> str:
    """生成Redis密码"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_grafana_password(length: int = 24) -> str:
    """生成Grafana管理员密码"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_alipay_private_key() -> str:
    """生成支付宝私钥占位符（实际需要从支付宝获取）"""
    return "REPLACE_WITH_ALIPAY_PRIVATE_KEY_FROM_ALIPAY_PLATFORM"


def generate_wechatpay_private_key() -> str:
    """生成微信支付私钥占位符（实际需要从微信支付获取）"""
    return "REPLACE_WITH_WECHATPAY_PRIVATE_KEY_FROM_WECHAT_PLATFORM"


def main():
    """生成所有密钥和密码"""
    print("=" * 80)
    print("生产环境安全密钥和密码生成器")
    print("=" * 80)
    print()

    config = {
        "JWT_SECRET_KEY": generate_jwt_secret(),
        "PAYMENT_WEBHOOK_SECRET": generate_payment_webhook_secret(),
        "POSTGRES_PASSWORD": generate_database_password(),
        "REDIS_PASSWORD": generate_redis_password(),
        "GRAFANA_ADMIN_PASSWORD": generate_grafana_password(),
        "ALIPAY_PRIVATE_KEY": generate_alipay_private_key(),
        "WECHATPAY_PRIVATE_KEY": generate_wechatpay_private_key(),
    }

    print("生成的安全配置：")
    print("-" * 80)
    for key, value in config.items():
        print(f"{key}={value}")
    print()

    print("=" * 80)
    print("重要提示：")
    print("=" * 80)
    print("1. 请将这些配置保存到安全的地方（如密码管理器）")
    print("2. 不要将这些配置提交到代码库")
    print("3. 支付宝和微信支付的密钥需要从对应平台获取")
    print("4. 定期轮换这些密钥（建议每90天）")
    print()

    print("=" * 80)
    print("Docker Compose 环境变量格式：")
    print("=" * 80)
    print(f"JWT_SECRET_KEY={config['JWT_SECRET_KEY']}")
    print(f"PAYMENT_WEBHOOK_SECRET={config['PAYMENT_WEBHOOK_SECRET']}")
    print(f"POSTGRES_PASSWORD={config['POSTGRES_PASSWORD']}")
    print(f"REDIS_PASSWORD={config['REDIS_PASSWORD']}")
    print(f"GRAFANA_ADMIN_PASSWORD={config['GRAFANA_ADMIN_PASSWORD']}")
    print()

    print("=" * 80)
    print("Backend .env 文件格式：")
    print("=" * 80)
    print(f"SECRET_KEY={config['JWT_SECRET_KEY']}")
    print(f"PAYMENT_WEBHOOK_SECRET={config['PAYMENT_WEBHOOK_SECRET']}")
    print()

    print("=" * 80)
    print("是否保存到文件？(y/n): ", end="")
    choice = input().strip().lower()

    if choice == 'y':
        output_file = Path(".env.production")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# 生产环境配置 - 请妥善保管\n")
            f.write(f"# 生成时间: {secrets.SystemRandom().randint(1000000000, 9999999999)}\n\n")
            f.write(f"# JWT配置\n")
            f.write(f"SECRET_KEY={config['JWT_SECRET_KEY']}\n")
            f.write(f"ALGORITHM=HS256\n")
            f.write(f"ACCESS_TOKEN_EXPIRE_MINUTES=60\n\n")
            f.write(f"# 支付配置\n")
            f.write(f"PAYMENT_WEBHOOK_SECRET={config['PAYMENT_WEBHOOK_SECRET']}\n")
            f.write(f"ALIPAY_PRIVATE_KEY={config['ALIPAY_PRIVATE_KEY']}\n")
            f.write(f"WECHATPAY_PRIVATE_KEY={config['WECHATPAY_PRIVATE_KEY']}\n\n")
            f.write(f"# 数据库配置\n")
            f.write(f"DATABASE_URL=postgresql+asyncpg://postgres:{config['POSTGRES_PASSWORD']}@db:5432/baixing_law\n\n")
            f.write(f"# Redis配置\n")
            f.write(f"REDIS_URL=redis://:{config['REDIS_PASSWORD']}@redis:6379/0\n\n")
            f.write(f"# 应用配置\n")
            f.write(f"DEBUG=false\n")
            f.write(f"CORS_ALLOW_ORIGINS=[\"https://yourdomain.com\"]\n")
        
        print(f"配置已保存到: {output_file.absolute()}")
        print(f"请将此文件添加到 .gitignore")
    else:
        print("配置未保存到文件")


if __name__ == "__main__":
    main()
