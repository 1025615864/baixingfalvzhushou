"""预约服务领域"""
from .services import AppointmentDomainService
from .routers import router as appointment_router

__all__ = ["AppointmentDomainService", "appointment_router"]