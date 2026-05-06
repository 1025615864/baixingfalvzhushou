"""用户服务入口 - 使用.env.dev配置"""
from dotenv import load_dotenv
load_dotenv('.env.dev')

from app.main import app
