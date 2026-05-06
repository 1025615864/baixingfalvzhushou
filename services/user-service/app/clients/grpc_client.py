"""gRPC客户端"""
import logging
import os
from typing import Optional

import grpc

logger = logging.getLogger(__name__)

grpc_user_client = None


def init_grpc_clients(use_tls: bool = False):
    """初始化gRPC客户端"""
    global grpc_user_client

    user_service_host = os.getenv("USER_SERVICE_GRPC_HOST", "localhost")
    user_service_port = os.getenv("USER_SERVICE_GRPC_PORT", "50051")

    try:
        import user_service_pb2
        import user_service_pb2_grpc

        if use_tls:
            credentials = grpc.ssl_channel_credentials()
            channel = grpc.aio.secure_channel(
                f"{user_service_host}:{user_service_port}",
                credentials,
            )
        else:
            channel = grpc.aio.insecure_channel(
                f"{user_service_host}:{user_service_port}"
            )

        grpc_user_client = user_service_pb2_grpc.UserServiceStub(channel)
        logger.info(f"gRPC user client initialized (host={user_service_host}:{user_service_port})")
    except Exception as e:
        logger.warning(f"Failed to initialize gRPC user client: {e}")
        grpc_user_client = None


def close_grpc_clients():
    """关闭gRPC客户端"""
    global grpc_user_client
    grpc_user_client = None


async def grpc_get_user(user_id: int) -> Optional[dict]:
    """通过gRPC获取用户信息"""
    if not grpc_user_client:
        logger.warning("gRPC user client not initialized")
        return None

    try:
        import user_service_pb2

        request = user_service_pb2.GetUserRequest(user_id=user_id)
        response = await grpc_user_client.GetUser(request)
        return {
            "id": response.id,
            "username": response.username,
            "email": response.email,
            "role": response.role,
            "is_active": response.is_active,
        }
    except grpc.RpcError as e:
        logger.error(f"gRPC GetUser error: {e}")
        return None


async def grpc_validate_token(token: str) -> Optional[dict]:
    """通过gRPC验证Token"""
    if not grpc_user_client:
        logger.warning("gRPC user client not initialized")
        return None

    try:
        import user_service_pb2

        request = user_service_pb2.ValidateTokenRequest(token=token)
        response = await grpc_user_client.ValidateToken(request)
        if response.valid:
            return {
                "user_id": response.user_id,
                "role": response.role,
            }
        return None
    except grpc.RpcError as e:
        logger.error(f"gRPC ValidateToken error: {e}")
        return None


async def grpc_batch_get_users(user_ids: list[int]) -> dict:
    """批量通过gRPC获取用户信息

    Returns:
        {
            "users": [...],  # 用户列表
            "not_found_ids": [...]  # 未找到的ID列表
        }
    """
    if not grpc_user_client:
        logger.warning("gRPC user client not initialized")
        return {"users": [], "not_found_ids": user_ids}

    if not user_ids:
        return {"users": [], "not_found_ids": []}

    try:
        import user_service_pb2

        request = user_service_pb2.BatchGetUsersRequest(user_ids=user_ids)
        response = await grpc_user_client.BatchGetUsers(request)

        users = [
            {
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "phone": u.phone,
                "nickname": u.nickname,
                "role": u.role,
                "is_active": u.is_active,
                "avatar": u.avatar,
            }
            for u in response.users
        ]

        return {
            "users": users,
            "not_found_ids": list(response.not_found_ids),
        }
    except grpc.RpcError as e:
        logger.error(f"gRPC BatchGetUsers error: {e}")
        return {"users": [], "not_found_ids": user_ids}
