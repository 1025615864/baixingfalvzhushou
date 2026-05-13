"""gRPC 服务器 - Legal Service v3

提供 gRPC 服务，供其他微服务调用
支持 11 个接口：
- GetLawyer: 获取单个律师
- BatchGetLawyers: 批量获取律师
- SearchLawyers: 搜索律师
- GetLawyerSchedule: 获取律师排班
- CheckAvailability: 检查排班可用性
- GetLawyerStats: 获取律师统计
- GetConsultation: 获取咨询
- GetUserConsultations: 获取用户咨询列表
- GetAppointment: 获取预约
- GetUserAppointments: 获取用户预约列表
- HealthCheck: 健康检查
"""
import logging
import os
import time
from typing import Optional
from concurrent import futures

import grpc
from sqlalchemy import select, func

logger = logging.getLogger(__name__)

_start_time = time.time()


class LegalServiceServicer:
    """Legal Service gRPC 服务实现"""

    def __init__(self, session_factory, redis_client=None):
        self._session_factory = session_factory
        self._redis = redis_client

    async def _get_cached(self, key: str) -> Optional[str]:
        """从 Redis 获取缓存"""
        if not self._redis:
            return None
        try:
            return await self._redis.get(key)
        except Exception:
            logger.error("获取Redis缓存失败")
            return None

    async def _set_cached(self, key: str, value: str, ttl: int = 300):
        """设置 Redis 缓存"""
        if not self._redis:
            return
        try:
            await self._redis.set(key, value, ex=ttl)
        except Exception:
            logger.error("设置Redis缓存失败")

    async def _get_lawyer_by_id(self, lawyer_id: int):
        """从数据库获取律师信息"""
        from ..models import Lawyer
        async with self._session_factory() as session:
            result = await session.execute(
                select(Lawyer).where(Lawyer.id == lawyer_id)
            )
            return result.scalar_one_or_none()

    async def _get_lawyer_schedule(self, lawyer_id: int, date: str = None):
        """从数据库获取律师排班"""
        from ..models import LawyerSchedule
        from datetime import datetime
        async with self._session_factory() as session:
            query = select(LawyerSchedule).where(
                LawyerSchedule.lawyer_id == lawyer_id
            )
            if date:
                try:
                    filter_date = datetime.strptime(date, "%Y-%m-%d").date()
                    query = query.where(LawyerSchedule.date >= datetime.combine(filter_date, datetime.min.time()))
                except ValueError:
                    pass
            result = await session.execute(
                query.order_by(LawyerSchedule.date, LawyerSchedule.start_time)
            )
            return list(result.scalars().all())

    async def _lawyer_to_proto(self, lawyer) -> dict:
        """将律师模型转换为 proto dict"""
        return {
            "lawyer_id": str(lawyer.id),
            "name": lawyer.name,
            "firm_id": str(lawyer.lawfirm_id) if lawyer.lawfirm_id else "",
            "title": lawyer.title or "",
            "expertise": lawyer.specialties or [],
            "rating": int((lawyer.rating or 0) * 10),
            "consultation_count": lawyer.consultation_count or 0,
            "price_per_hour": 0,
            "city": lawyer.city or "",
            "status": lawyer.status or "pending",
        }

    def _schedule_to_proto(self, schedule, common_pb2) -> dict:
        """将排班模型转换为 proto dict"""
        return {
            "slot_id": str(schedule.id),
            "start_time": common_pb2.Timestamp(
                seconds=int(schedule.date.timestamp()) if schedule.date else 0
            ),
            "end_time": common_pb2.Timestamp(
                seconds=int(schedule.date.timestamp()) if schedule.date else 0
            ),
            "is_available": bool(schedule.is_available),
        }


class SyncLegalServiceServicer:
    """同步包装器，用于 gRPC ThreadPool"""

    def __init__(self, session_factory, redis_client=None):
        self._session_factory = session_factory
        self._redis = redis_client
        self._impl = LegalServiceServicer(session_factory, redis_client)

    async def _async_get_lawyer(self, request, context):
        from services.common.proto import legal_pb2
        try:
            lawyer_id = int(request.lawyer_id)
            lawyer = await self._impl._get_lawyer_by_id(lawyer_id)
            if not lawyer:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Lawyer {lawyer_id} not found")
                return legal_pb2.LawyerResponse()
            lawyer_data = await self._impl._lawyer_to_proto(lawyer)
            return legal_pb2.LawyerResponse(**lawyer_data)
        except Exception as e:
            logger.error(f"GetLawyer error: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return legal_pb2.LawyerResponse()

    async def _async_batch_get_lawyers(self, request, context):
        from services.common.proto import legal_pb2
        try:
            lawyers = []
            for lawyer_id_str in request.lawyer_ids:
                lawyer_id = int(lawyer_id_str)
                lawyer = await self._impl._get_lawyer_by_id(lawyer_id)
                if lawyer:
                    lawyer_data = await self._impl._lawyer_to_proto(lawyer)
                    lawyers.append(legal_pb2.LawyerResponse(**lawyer_data))
            return legal_pb2.BatchLawyersResponse(lawyers=lawyers)
        except Exception as e:
            logger.error(f"BatchGetLawyers error: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return legal_pb2.BatchLawyersResponse()

    async def _async_search_lawyers(self, request, context):
        from services.common.proto import legal_pb2
        from ..models import Lawyer
        try:
            async with self._session_factory() as session:
                query = select(Lawyer).where(Lawyer.status == "verified")
                if request.city:
                    query = query.where(Lawyer.city == request.city)
                if request.specialty:
                    query = query.where(Lawyer.specialties.contains([request.specialty]))
                count_query = select(func.count()).select_from(query.subquery())
                total = (await session.execute(count_query)).scalar() or 0
                query = query.offset((request.page - 1) * request.page_size).limit(request.page_size)
                result = await session.execute(query)
                lawyers = result.scalars().all()
                lawyer_responses = []
                for lawyer in lawyers:
                    lawyer_data = await self._impl._lawyer_to_proto(lawyer)
                    lawyer_responses.append(legal_pb2.LawyerResponse(**lawyer_data))
                return legal_pb2.SearchLawyersResponse(
                    lawyers=lawyer_responses,
                    total=total,
                    page=request.page,
                    page_size=request.page_size,
                )
        except Exception as e:
            logger.error(f"SearchLawyers error: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return legal_pb2.SearchLawyersResponse()

    async def _async_get_lawyer_schedule(self, request, context):
        from services.common.proto import legal_pb2, common_pb2
        try:
            lawyer_id = int(request.lawyer_id)
            schedules = await self._impl._get_lawyer_schedule(lawyer_id, request.date)
            time_slots = []
            for schedule in schedules:
                time_slots.append(legal_pb2.TimeSlot(
                    slot_id=str(schedule.id),
                    start_time=common_pb2.Timestamp(
                        seconds=int(schedule.date.timestamp()) if schedule.date else 0
                    ),
                    end_time=common_pb2.Timestamp(
                        seconds=int(schedule.date.timestamp()) if schedule.date else 0
                    ),
                    is_available=bool(schedule.is_available),
                ))
            return legal_pb2.LawyerScheduleResponse(
                lawyer_id=str(lawyer_id),
                available_slots=time_slots,
            )
        except Exception as e:
            logger.error(f"GetLawyerSchedule error: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return legal_pb2.LawyerScheduleResponse()

    async def _async_check_availability(self, request, context):
        from services.common.proto import legal_pb2, common_pb2
        try:
            lawyer_id = int(request.lawyer_id)
            schedules = await self._impl._get_lawyer_schedule(lawyer_id, request.date)
            available_slots = []
            is_available = False
            for schedule in schedules:
                if schedule.is_available:
                    is_available = True
                    available_slots.append(legal_pb2.TimeSlot(
                        slot_id=str(schedule.id),
                        start_time=common_pb2.Timestamp(
                            seconds=int(schedule.date.timestamp()) if schedule.date else 0
                        ),
                        end_time=common_pb2.Timestamp(
                            seconds=int(schedule.date.timestamp()) if schedule.date else 0
                        ),
                        is_available=True,
                    ))
            return legal_pb2.CheckAvailabilityResponse(
                lawyer_id=str(lawyer_id),
                date=request.date,
                is_available=is_available,
                slots=available_slots,
            )
        except Exception as e:
            logger.error(f"CheckAvailability error: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return legal_pb2.CheckAvailabilityResponse()

    async def _async_get_lawyer_stats(self, request, context):
        from services.common.proto import legal_pb2
        from ..models import Lawyer, LawyerConsultation
        try:
            lawyer_id = int(request.lawyer_id)
            async with self._session_factory() as session:
                lawyer_result = await session.execute(
                    select(Lawyer).where(Lawyer.id == lawyer_id)
                )
                lawyer = lawyer_result.scalar_one_or_none()
                if not lawyer:
                    context.set_code(grpc.StatusCode.NOT_FOUND)
                    context.set_details(f"Lawyer {lawyer_id} not found")
                    return legal_pb2.LawyerStatsResponse()
                count_query = select(func.count()).where(
                    LawyerConsultation.lawyer_id == lawyer_id,
                    LawyerConsultation.status == "completed"
                )
                completed_count = (await session.execute(count_query)).scalar() or 0
                return legal_pb2.LawyerStatsResponse(
                    lawyer_id=str(lawyer_id),
                    total_consultations=lawyer.consultation_count or 0,
                    completed_consultations=completed_count,
                    average_rating=int((lawyer.rating or 0) * 10),
                    response_time_minutes=30,
                )
        except Exception as e:
            logger.error(f"GetLawyerStats error: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return legal_pb2.LawyerStatsResponse()

    async def _async_get_consultation(self, request, context):
        from services.common.proto import legal_pb2, common_pb2
        from ..models import Consultation
        try:
            consultation_id = int(request.consultation_id)
            async with self._session_factory() as session:
                result = await session.execute(
                    select(Consultation).where(Consultation.id == consultation_id)
                )
                consultation = result.scalar_one_or_none()
                if not consultation:
                    context.set_code(grpc.StatusCode.NOT_FOUND)
                    context.set_details(f"Consultation {consultation_id} not found")
                    return legal_pb2.ConsultationResponse()
                return legal_pb2.ConsultationResponse(
                    consultation_id=str(consultation.id),
                    user_id=str(consultation.user_id),
                    lawyer_id=str(consultation.lawyer_id) if consultation.lawyer_id else "",
                    category=consultation.category or "",
                    title=consultation.title or "",
                    status=consultation.status or "pending",
                    created_at=common_pb2.Timestamp(
                        seconds=int(consultation.created_at.timestamp()) if consultation.created_at else 0
                    ),
                    updated_at=common_pb2.Timestamp(
                        seconds=int(consultation.updated_at.timestamp()) if consultation.updated_at else 0
                    ),
                )
        except Exception as e:
            logger.error(f"GetConsultation error: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return legal_pb2.ConsultationResponse()

    async def _async_get_user_consultations(self, request, context):
        from services.common.proto import legal_pb2, common_pb2
        from ..models import Consultation
        try:
            user_id = int(request.user_id)
            async with self._session_factory() as session:
                query = select(Consultation).where(Consultation.user_id == user_id)
                if request.status:
                    query = query.where(Consultation.status == request.status)
                count_query = select(func.count()).select_from(query.subquery())
                total = (await session.execute(count_query)).scalar() or 0
                query = query.offset((request.page - 1) * request.page_size).limit(request.page_size)
                result = await session.execute(query)
                consultations = result.scalars().all()
                responses = []
                for c in consultations:
                    responses.append(legal_pb2.ConsultationResponse(
                        consultation_id=str(c.id),
                        user_id=str(c.user_id),
                        lawyer_id=str(c.lawyer_id) if c.lawyer_id else "",
                        category=c.category or "",
                        title=c.title or "",
                        status=c.status or "pending",
                        created_at=common_pb2.Timestamp(
                            seconds=int(c.created_at.timestamp()) if c.created_at else 0
                        ),
                        updated_at=common_pb2.Timestamp(
                            seconds=int(c.updated_at.timestamp()) if c.updated_at else 0
                        ),
                    ))
                return legal_pb2.UserConsultationsResponse(
                    consultations=responses,
                    total=total,
                    page=request.page,
                    page_size=request.page_size,
                )
        except Exception as e:
            logger.error(f"GetUserConsultations error: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return legal_pb2.UserConsultationsResponse()

    async def _async_get_appointment(self, request, context):
        from services.common.proto import legal_pb2, common_pb2
        from ..models import LawyerConsultation
        try:
            appointment_id = int(request.appointment_id)
            async with self._session_factory() as session:
                result = await session.execute(
                    select(LawyerConsultation).where(LawyerConsultation.id == appointment_id)
                )
                appointment = result.scalar_one_or_none()
                if not appointment:
                    context.set_code(grpc.StatusCode.NOT_FOUND)
                    context.set_details(f"Appointment {appointment_id} not found")
                    return legal_pb2.AppointmentResponse()
                return legal_pb2.AppointmentResponse(
                    appointment_id=str(appointment.id),
                    consultation_id=str(appointment.consultation_id) if appointment.consultation_id else "",
                    user_id=str(appointment.user_id) if appointment.user_id else "",
                    lawyer_id=str(appointment.lawyer_id) if appointment.lawyer_id else "",
                    appointment_type=appointment.appointment_type or "video",
                    scheduled_at=common_pb2.Timestamp(
                        seconds=int(appointment.scheduled_at.timestamp()) if appointment.scheduled_at else 0
                    ),
                    status=appointment.status or "pending",
                    price=int(appointment.price or 0),
                )
        except Exception as e:
            logger.error(f"GetAppointment error: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return legal_pb2.AppointmentResponse()

    async def _async_get_user_appointments(self, request, context):
        from services.common.proto import legal_pb2, common_pb2
        from ..models import LawyerConsultation
        try:
            user_id = int(request.user_id)
            async with self._session_factory() as session:
                query = select(LawyerConsultation).where(LawyerConsultation.user_id == user_id)
                if request.status:
                    query = query.where(LawyerConsultation.status == request.status)
                count_query = select(func.count()).select_from(query.subquery())
                total = (await session.execute(count_query)).scalar() or 0
                query = query.offset((request.page - 1) * request.page_size).limit(request.page_size)
                result = await session.execute(query)
                appointments = result.scalars().all()
                responses = []
                for a in appointments:
                    responses.append(legal_pb2.AppointmentResponse(
                        appointment_id=str(a.id),
                        consultation_id=str(a.consultation_id) if a.consultation_id else "",
                        user_id=str(a.user_id) if a.user_id else "",
                        lawyer_id=str(a.lawyer_id) if a.lawyer_id else "",
                        appointment_type=a.appointment_type or "video",
                        scheduled_at=common_pb2.Timestamp(
                            seconds=int(a.scheduled_at.timestamp()) if a.scheduled_at else 0
                        ),
                        status=a.status or "pending",
                        price=int(a.price or 0),
                    ))
                return legal_pb2.UserAppointmentsResponse(
                    appointments=responses,
                    total=total,
                    page=request.page,
                    page_size=request.page_size,
                )
        except Exception as e:
            logger.error(f"GetUserAppointments error: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return legal_pb2.UserAppointmentsResponse()

    async def _async_health_check(self, request, context):
        from services.common.proto import legal_pb2
        return legal_pb2.HealthCheckResponse(
            status="healthy",
            version="1.0.0",
            uptime_seconds=int(time.time() - _start_time),
        )

    def GetLawyer(self, request, context):
        import asyncio
        try:
            loop = asyncio.new_event_loop()
            result = loop.run_until_complete(self._async_get_lawyer(request, context))
            loop.close()
            return result
        except Exception as e:
            logger.error(f"GetLawyer sync error: {e}")
            from services.common.proto import legal_pb2
            return legal_pb2.LawyerResponse()

    def BatchGetLawyers(self, request, context):
        import asyncio
        try:
            loop = asyncio.new_event_loop()
            result = loop.run_until_complete(self._async_batch_get_lawyers(request, context))
            loop.close()
            return result
        except Exception as e:
            logger.error(f"BatchGetLawyers sync error: {e}")
            from services.common.proto import legal_pb2
            return legal_pb2.BatchLawyersResponse()

    def SearchLawyers(self, request, context):
        import asyncio
        try:
            loop = asyncio.new_event_loop()
            result = loop.run_until_complete(self._async_search_lawyers(request, context))
            loop.close()
            return result
        except Exception as e:
            logger.error(f"SearchLawyers sync error: {e}")
            from services.common.proto import legal_pb2
            return legal_pb2.SearchLawyersResponse()

    def GetLawyerSchedule(self, request, context):
        import asyncio
        try:
            loop = asyncio.new_event_loop()
            result = loop.run_until_complete(self._async_get_lawyer_schedule(request, context))
            loop.close()
            return result
        except Exception as e:
            logger.error(f"GetLawyerSchedule sync error: {e}")
            from services.common.proto import legal_pb2
            return legal_pb2.LawyerScheduleResponse()

    def CheckAvailability(self, request, context):
        import asyncio
        try:
            loop = asyncio.new_event_loop()
            result = loop.run_until_complete(self._async_check_availability(request, context))
            loop.close()
            return result
        except Exception as e:
            logger.error(f"CheckAvailability sync error: {e}")
            from services.common.proto import legal_pb2
            return legal_pb2.CheckAvailabilityResponse()

    def GetLawyerStats(self, request, context):
        import asyncio
        try:
            loop = asyncio.new_event_loop()
            result = loop.run_until_complete(self._async_get_lawyer_stats(request, context))
            loop.close()
            return result
        except Exception as e:
            logger.error(f"GetLawyerStats sync error: {e}")
            from services.common.proto import legal_pb2
            return legal_pb2.LawyerStatsResponse()

    def GetConsultation(self, request, context):
        import asyncio
        try:
            loop = asyncio.new_event_loop()
            result = loop.run_until_complete(self._async_get_consultation(request, context))
            loop.close()
            return result
        except Exception as e:
            logger.error(f"GetConsultation sync error: {e}")
            from services.common.proto import legal_pb2
            return legal_pb2.ConsultationResponse()

    def GetUserConsultations(self, request, context):
        import asyncio
        try:
            loop = asyncio.new_event_loop()
            result = loop.run_until_complete(self._async_get_user_consultations(request, context))
            loop.close()
            return result
        except Exception as e:
            logger.error(f"GetUserConsultations sync error: {e}")
            from services.common.proto import legal_pb2
            return legal_pb2.UserConsultationsResponse()

    def GetAppointment(self, request, context):
        import asyncio
        try:
            loop = asyncio.new_event_loop()
            result = loop.run_until_complete(self._async_get_appointment(request, context))
            loop.close()
            return result
        except Exception as e:
            logger.error(f"GetAppointment sync error: {e}")
            from services.common.proto import legal_pb2
            return legal_pb2.AppointmentResponse()

    def GetUserAppointments(self, request, context):
        import asyncio
        try:
            loop = asyncio.new_event_loop()
            result = loop.run_until_complete(self._async_get_user_appointments(request, context))
            loop.close()
            return result
        except Exception as e:
            logger.error(f"GetUserAppointments sync error: {e}")
            from services.common.proto import legal_pb2
            return legal_pb2.UserAppointmentsResponse()

    def HealthCheck(self, request, context):
        import asyncio
        try:
            loop = asyncio.new_event_loop()
            result = loop.run_until_complete(self._async_health_check(request, context))
            loop.close()
            return result
        except Exception as e:
            logger.error(f"HealthCheck sync error: {e}")
            from services.common.proto import legal_pb2
            return legal_pb2.HealthCheckResponse()


def serve(port: int = 50052, session_factory=None, redis_client=None, max_workers: int = 10):
    """启动 gRPC 服务器"""
    from services.common.proto import legal_pb2_grpc

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=max_workers))

    if session_factory:
        servicer = SyncLegalServiceServicer(session_factory, redis_client)
        legal_pb2_grpc.add_LegalServiceServicer_to_server(servicer, server)
        logger.info("gRPC LegalService started with real database connection")
    else:
        logger.warning("gRPC server starting without database connection")

    server.add_insecure_port(f"[::]:{port}")
    logger.info(f"Legal Service gRPC server started on port {port}")
    server.start()
    return server
