"""客户端模块"""
from .http_client import user_service_client, backend_client, UserServiceClient, BackendClient
from .grpc_client import grpc_user_client

__all__ = [
    "user_service_client",
    "backend_client",
    "UserServiceClient",
    "BackendClient",
    "grpc_user_client",
]
