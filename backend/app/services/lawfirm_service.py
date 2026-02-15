"""法律咨询所服务层

此模块已重构到 services/lawfirm/ 目录。
保留此文件用于向后兼容导入。
请使用 app.services.lawfirm 中的服务类。
"""

# 重新导出所有服务类（从模块化目录导入）
from app.services.lawfirm import (
    LawFirmService,
    LawyerService,
    LawyerConsultationService,
    ConsultationMessageService,
    ConsultationStatus,
    ReviewService,
    LawyerStatsService,
    LawyerScheduleService,
    LawyerVerificationService,
)

# 创建全局实例供向后兼容（所有方法都是静态方法，实例仅用于兼容）
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
