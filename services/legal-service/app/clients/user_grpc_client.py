"""User Service gRPC Client"""
import os
import logging
from typing import Optional, List, Dict, Any

import grpc

from services.common.proto import user_pb2, user_pb2_grpc

logger = logging.getLogger(__name__)


class UserGrpcClient:
    def __init__(self):
        self.channel: Optional[grpc.Channel] = None
        self.stub: Optional[user_pb2_grpc.UserServiceStub] = None
        self._enabled = os.getenv("USER_SERVICE_GRPC_ENABLED", "false").lower() in {"1", "true", "yes"}

    def connect(self):
        if not self._enabled:
            logger.info("User gRPC client is disabled")
            return
        user_service_addr = os.getenv("USER_SERVICE_ADDR", "localhost:50051")
        try:
            self.channel = grpc.insecure_channel(user_service_addr)
            self.stub = user_pb2_grpc.UserServiceStub(self.channel)
            logger.info(f"Connected to User Service gRPC at {user_service_addr}")
        except Exception as e:
            logger.error(f"Failed to connect to User Service gRPC: {e}")
            self.stub = None

    def close(self):
        if self.channel:
            self.channel.close()
            self.channel = None
            self.stub = None

    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        if not self.stub:
            return None
        try:
            request = user_pb2.GetUserRequest(user_id=str(user_id))
            response = self.stub.GetUser(request, timeout=5.0)
            if response.HasField('user'):
                return {
                    "id": int(response.user.id) if response.user.id else None,
                    "email": response.user.email,
                    "phone": response.user.phone,
                    "username": response.user.username,
                    "status": response.user.status,
                }
            return None
        except grpc.RpcError as e:
            logger.warning(f"gRPC GetUser failed: {e.code()} - {e.details()}")
            return None
        except Exception as e:
            logger.warning(f"GetUser failed: {e}")
            return None

    async def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        if not self.stub:
            return None
        try:
            request = user_pb2.ValidateTokenRequest(token=token)
            response = self.stub.ValidateToken(request, timeout=5.0)
            if response.valid:
                return {
                    "user_id": int(response.user_id) if response.user_id else None,
                    "roles": list(response.roles),
                    "valid": True,
                }
            return None
        except grpc.RpcError as e:
            logger.warning(f"gRPC ValidateToken failed: {e.code()} - {e.details()}")
            return None
        except Exception as e:
            logger.warning(f"ValidateToken failed: {e}")
            return None

    async def batch_get_users(self, user_ids: List[int]) -> List[Dict[str, Any]]:
        if not self.stub:
            return []
        results = []
        for user_id in user_ids:
            user = await self.get_user(user_id)
            if user:
                results.append(user)
        return results

    async def get_user_profile(self, user_id: int) -> Optional[Dict[str, Any]]:
        if not self.stub:
            return None
        try:
            request = user_pb2.GetUserProfileRequest(user_id=str(user_id))
            response = self.stub.GetUserProfile(request, timeout=5.0)
            return {
                "user_id": response.user_id,
                "nickname": response.nickname,
                "avatar_url": response.avatar_url,
                "bio": response.bio,
                "membership": {
                    "membership_type": response.membership.membership_type,
                } if response.HasField('membership') else None,
            }
        except grpc.RpcError as e:
            logger.warning(f"gRPC GetUserProfile failed: {e.code()} - {e.details()}")
            return None
        except Exception as e:
            logger.warning(f"GetUserProfile failed: {e}")
            return None

    async def get_user_quota(self, user_id: int) -> Optional[Dict[str, Any]]:
        if not self.stub:
            return None
        try:
            request = user_pb2.GetUserQuotaRequest(user_id=str(user_id))
            response = self.stub.GetUserQuota(request, timeout=5.0)
            return {
                "consultation_quota": response.consultation_quota,
                "consultation_used": response.consultation_used,
                "document_quota": response.document_quota,
                "document_used": response.document_used,
            }
        except grpc.RpcError as e:
            logger.warning(f"gRPC GetUserQuota failed: {e.code()} - {e.details()}")
            return None
        except Exception as e:
            logger.warning(f"GetUserQuota failed: {e}")
            return None


user_grpc_client = UserGrpcClient()
