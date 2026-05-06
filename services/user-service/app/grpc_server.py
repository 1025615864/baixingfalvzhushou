"""gRPC服务器实现"""
import logging
from concurrent import futures
import asyncio
import os

import grpc
from grpc import aio

from app.clients import user_service_pb2, user_service_pb2_grpc
from app.database import AsyncSessionLocal
from app.models import User, UserProfile
from app.services.auth_service import AuthService
from sqlalchemy import select

logger = logging.getLogger(__name__)

GRPC_PORT = int(os.getenv("GRPC_PORT", "50051"))


class UserServiceServicer(user_service_pb2_grpc.UserServiceServicer):
    """gRPC用户服务实现"""

    async def GetUser(self, request, context):
        """获取用户信息（支持uid查询）"""
        try:
            async with AsyncSessionLocal() as session:
                if request.uid:
                    result = await session.execute(
                        select(User).where(User.uid == request.uid)
                    )
                elif request.user_id:
                    result = await session.execute(
                        select(User).where(User.id == request.user_id)
                    )
                else:
                    return user_service_pb2.GetUserResponse()

                user = result.scalar_one_or_none()

                if not user:
                    return user_service_pb2.GetUserResponse()

                profile_result = await session.execute(
                    select(UserProfile).where(UserProfile.user_id == user.id)
                )
                profile = profile_result.scalar_one_or_none()

                return user_service_pb2.GetUserResponse(
                    id=user.id,
                    uid=user.uid,
                    username=user.username or "",
                    email=user.email or "",
                    phone=user.phone or "",
                    nickname=profile.nickname if profile else "",
                    role=user.role,
                    status=user.status,
                    is_active=user.is_active,
                    email_verified=user.email_verified,
                    phone_verified=user.phone_verified,
                    avatar=profile.avatar if profile else "",
                    created_at=int(user.created_at.timestamp()) if user.created_at else 0,
                    updated_at=int(user.updated_at.timestamp()) if user.updated_at else 0,
                )
        except Exception as e:
            logger.error(f"gRPC GetUser error: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details("Internal server error")
            return user_service_pb2.GetUserResponse()

    async def GetUserByUsername(self, request, context):
        """通过用户名获取用户"""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(User).where(User.username == request.username)
                )
                user = result.scalar_one_or_none()

                if not user:
                    return user_service_pb2.GetUserResponse()

                profile_result = await session.execute(
                    select(UserProfile).where(UserProfile.user_id == user.id)
                )
                profile = profile_result.scalar_one_or_none()

                return user_service_pb2.GetUserResponse(
                    id=user.id,
                    uid=user.uid,
                    username=user.username or "",
                    email=user.email or "",
                    phone=user.phone or "",
                    nickname=profile.nickname if profile else "",
                    role=user.role,
                    status=user.status,
                    is_active=user.is_active,
                    email_verified=user.email_verified,
                    phone_verified=user.phone_verified,
                    avatar=profile.avatar if profile else "",
                    created_at=int(user.created_at.timestamp()) if user.created_at else 0,
                    updated_at=int(user.updated_at.timestamp()) if user.updated_at else 0,
                )
        except Exception as e:
            logger.error(f"gRPC GetUserByUsername error: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details("Internal server error")
            return user_service_pb2.GetUserResponse()

    async def BatchGetUsers(self, request, context):
        """批量获取用户信息"""
        try:
            user_ids = list(request.user_ids)
            if not user_ids:
                return user_service_pb2.BatchGetUsersResponse()

            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(User).where(User.id.in_(user_ids))
                )
                users = result.scalars().all()

                found_ids = {user.id for user in users}
                not_found_ids = [uid for uid in user_ids if uid not in found_ids]

                pb_users = []
                for user in users:
                    profile_result = await session.execute(
                        select(UserProfile).where(UserProfile.user_id == user.id)
                    )
                    profile = profile_result.scalar_one_or_none()

                    pb_users.append(
                        user_service_pb2.User(
                            id=user.id,
                            uid=user.uid,
                            username=user.username or "",
                            email=user.email or "",
                            phone=user.phone or "",
                            nickname=profile.nickname if profile else "",
                            role=user.role,
                            status=user.status,
                            is_active=user.is_active,
                            email_verified=user.email_verified,
                            phone_verified=user.phone_verified,
                            avatar=profile.avatar if profile else "",
                            created_at=int(user.created_at.timestamp()) if user.created_at else 0,
                            updated_at=int(user.updated_at.timestamp()) if user.updated_at else 0,
                        )
                    )

                return user_service_pb2.BatchGetUsersResponse(
                    users=pb_users,
                    not_found_ids=not_found_ids,
                )
        except Exception as e:
            logger.error(f"gRPC BatchGetUsers error: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details("Internal server error")
            return user_service_pb2.BatchGetUsersResponse()

    async def ValidateToken(self, request, context):
        """验证Token"""
        try:
            async with AsyncSessionLocal() as session:
                auth_service = AuthService(session)
                result = await auth_service.verify_token(request.token)

                if result:
                    return user_service_pb2.ValidateTokenResponse(
                        valid=True,
                        user_id=result["user_id"],
                        uid=result.get("uid", ""),
                        role=result["role"],
                    )
                else:
                    return user_service_pb2.ValidateTokenResponse(
                        valid=False,
                        error="Invalid or expired token",
                    )
        except Exception as e:
            logger.error(f"gRPC ValidateToken error: {e}")
            return user_service_pb2.ValidateTokenResponse(
                valid=False,
                error=str(e),
            )

    async def CheckPermission(self, request, context):
        """检查用户权限"""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(User).where(User.id == request.user_id)
                )
                user = result.scalar_one_or_none()

                if not user:
                    return user_service_pb2.CheckPermissionResponse(
                        allowed=False,
                        reason="User not found",
                    )

                role_hierarchy = {"admin": 3, "svip": 2, "vip": 2, "user": 1}
                user_level = role_hierarchy.get(user.role, 0)
                required_level = role_hierarchy.get(request.required_role, 0)

                if user_level >= required_level and user.is_active:
                    return user_service_pb2.CheckPermissionResponse(
                        allowed=True,
                    )
                else:
                    return user_service_pb2.CheckPermissionResponse(
                        allowed=False,
                        reason=f"Insufficient permissions (user: {user.role}, required: {request.required_role})",
                    )
        except Exception as e:
            logger.error(f"gRPC CheckPermission error: {e}")
            return user_service_pb2.CheckPermissionResponse(
                allowed=False,
                reason=str(e),
            )

    async def GetUserProfile(self, request, context):
        """获取用户画像"""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(UserProfile).where(UserProfile.user_id == request.user_id)
                )
                profile = result.scalar_one_or_none()

                if not profile:
                    return user_service_pb2.GetUserProfileResponse()

                return user_service_pb2.GetUserProfileResponse(
                    id=profile.id,
                    user_id=profile.user_id,
                    nickname=profile.nickname or "",
                    avatar=profile.avatar or "",
                    bio=profile.bio or "",
                    gender=profile.gender or "",
                    birthday=str(profile.birthday) if profile.birthday else "",
                    province=profile.province or "",
                    city=profile.city or "",
                )
        except Exception as e:
            logger.error(f"gRPC GetUserProfile error: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details("Internal server error")
            return user_service_pb2.GetUserProfileResponse()

    async def UpdateUserProfile(self, request, context):
        """更新用户画像"""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(UserProfile).where(UserProfile.user_id == request.user_id)
                )
                profile = result.scalar_one_or_none()

                if profile:
                    if request.nickname:
                        profile.nickname = request.nickname
                    if request.avatar:
                        profile.avatar = request.avatar
                    if request.bio:
                        profile.bio = request.bio
                    if request.gender:
                        profile.gender = request.gender
                    if request.birthday:
                        profile.birthday = request.birthday
                    if request.province:
                        profile.province = request.province
                    if request.city:
                        profile.city = request.city
                else:
                    profile = UserProfile(
                        user_id=request.user_id,
                        nickname=request.nickname or "",
                        avatar=request.avatar or "",
                        bio=request.bio or "",
                        gender=request.gender or "",
                        province=request.province or "",
                        city=request.city or "",
                    )
                    session.add(profile)

                await session.commit()
                return user_service_pb2.UpdateUserProfileResponse(
                    success=True,
                    message="Profile updated successfully",
                )
        except Exception as e:
            logger.error(f"gRPC UpdateUserProfile error: {e}")
            return user_service_pb2.UpdateUserProfileResponse(
                success=False,
                message="Internal server error",
            )

    async def UpdateUserRole(self, request, context):
        """更新用户角色（律师认证通过后回调）"""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(User).where(User.id == request.user_id)
                )
                user = result.scalar_one_or_none()

                if not user:
                    return user_service_pb2.UpdateUserRoleResponse(
                        success=False,
                        message="User not found",
                        old_role="",
                        new_role="",
                    )

                old_role = user.role
                user.role = request.new_role
                await session.commit()

                try:
                    from .events.kafka_producer import publish_role_changed
                    await publish_role_changed(
                        user_id=str(user.uid),
                        old_role=old_role,
                        new_role=request.new_role,
                        operator_id=request.operator_id or "",
                    )
                except Exception as e:
                    logger.warning(f"Failed to publish role change event: {e}")

                return user_service_pb2.UpdateUserRoleResponse(
                    success=True,
                    message="Role updated successfully",
                    old_role=old_role,
                    new_role=request.new_role,
                )
        except Exception as e:
            logger.error(f"gRPC UpdateUserRole error: {e}")
            return user_service_pb2.UpdateUserRoleResponse(
                success=False,
                message=str(e),
                old_role="",
                new_role="",
            )

    async def BanUser(self, request, context):
        """封禁用户（管理后台回调）"""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(User).where(User.id == request.user_id)
                )
                user = result.scalar_one_or_none()

                if not user:
                    return user_service_pb2.BanUserResponse(
                        success=False,
                        message="User not found",
                        ban_end_at="",
                    )

                user.status = "banned"
                user.is_active = False

                from datetime import datetime, timedelta
                ban_end = None
                if request.ban_duration_hours > 0:
                    ban_end = datetime.utcnow() + timedelta(hours=request.ban_duration_hours)
                    user.banned_until = ban_end

                await session.commit()

                from .services.token_service import token_manager
                await token_manager.revoke_all_user_tokens(user.id)

                try:
                    from .events.kafka_producer import publish_account_banned
                    await publish_account_banned(
                        user_id=str(user.uid),
                        banned_by=request.operator_id or "",
                        reason=request.reason or "",
                    )
                except Exception as e:
                    logger.warning(f"Failed to publish ban event: {e}")

                return user_service_pb2.BanUserResponse(
                    success=True,
                    message="User banned successfully",
                    ban_end_at=ban_end.isoformat() if ban_end else "",
                )
        except Exception as e:
            logger.error(f"gRPC BanUser error: {e}")
            return user_service_pb2.BanUserResponse(
                success=False,
                message=str(e),
                ban_end_at="",
            )

    async def UpdateMembership(self, request, context):
        """更新会员等级（支付服务回调）"""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(User).where(User.id == request.user_id)
                )
                user = result.scalar_one_or_none()

                if not user:
                    return user_service_pb2.UpdateMembershipResponse(
                        success=False,
                        message="User not found",
                        old_tier="",
                        new_tier="",
                    )

                old_tier = user.membership_tier or "free"
                user.membership_tier = request.tier

                if request.vip_expires_at > 0:
                    user.vip_expires_at = datetime.fromtimestamp(request.vip_expires_at)

                await session.commit()

                try:
                    from .events.kafka_producer import publish_membership_upgraded
                    await publish_membership_upgraded(
                        user_id=str(user.uid),
                        old_tier=old_tier,
                        new_tier=request.tier,
                        operator_id=request.operator_id or "",
                    )
                except Exception as e:
                    logger.warning(f"Failed to publish membership event: {e}")

                return user_service_pb2.UpdateMembershipResponse(
                    success=True,
                    message="Membership updated successfully",
                    old_tier=old_tier,
                    new_tier=request.tier,
                )
        except Exception as e:
            logger.error(f"gRPC UpdateMembership error: {e}")
            return user_service_pb2.UpdateMembershipResponse(
                success=False,
                message=str(e),
                old_tier="",
                new_tier="",
            )

    async def HealthCheck(self, request, context):
        """gRPC健康检查"""
        try:
            import time
            from sqlalchemy import text

            async with AsyncSessionLocal() as session:
                await session.execute(text("SELECT 1"))

            return user_service_pb2.HealthCheckResponse(
                healthy=True,
                status="healthy",
                timestamp=int(time.time()),
                metadata={
                    "service": "user-service",
                    "database": "connected",
                    "grpc_port": str(GRPC_PORT),
                },
            )
        except Exception as e:
            logger.error(f"gRPC HealthCheck error: {e}")
            return user_service_pb2.HealthCheckResponse(
                healthy=False,
                status=f"unhealthy: {str(e)}",
                timestamp=int(time.time()),
                metadata={
                    "service": "user-service",
                    "error": str(e),
                },
            )


async def serve_grpc(port: int = None):
    """启动gRPC服务器

    Args:
        port: gRPC端口，默认从环境变量GRPC_PORT读取
    """
    if port is None:
        port = GRPC_PORT

    server = aio.server(futures.ThreadPoolExecutor(max_workers=10))
    user_service_pb2_grpc.add_UserServiceServicer_to_server(
        UserServiceServicer(), server
    )
    listen_addr = f"[::]:{port}"
    server.add_insecure_port(listen_addr)
    logger.info(f"Starting gRPC server on {listen_addr}")
    await server.start()
    await server.wait_for_termination()
