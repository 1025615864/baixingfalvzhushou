"""Lawfirm services - 律所相关服务模块"""

from .firms import LawFirmService
from .lawyers import LawyerService
from .consultations import (
    LawyerConsultationService,
    ConsultationMessageService,
    ConsultationStatus
)
from .reviews import ReviewService
from .stats import LawyerStatsService
from .schedules import LawyerScheduleService
from .verification import LawyerVerificationService

# 创建全局实例（向后兼容）
lawfirm_service = LawFirmService()
lawyer_service = LawyerService()
consultation_service = LawyerConsultationService()
review_service = ReviewService()
lawyer_stats_service = LawyerStatsService()
schedule_service = LawyerScheduleService()
verification_service = LawyerVerificationService()

__all__ = [
    "LawFirmService",
    "LawyerService",
    "LawyerConsultationService",
    "ConsultationMessageService",
    "ConsultationStatus",
    "ReviewService",
    "LawyerStatsService",
    "LawyerScheduleService",
    "LawyerVerificationService",
    # 全局实例（向后兼容）
    "lawfirm_service",
    "lawyer_service",
    "consultation_service",
    "review_service",
    "lawyer_stats_service",
    "schedule_service",
    "verification_service",
]
