"""模块联动服务

提供跨模块的业务流程联动，如 咨询→文书→律师 闭环。
"""

from .module_integration import (
    ModuleIntegrationService,
    ConsultationDocumentIntegration,
    ConsultationLawyerIntegration,
    NewsForumIntegration,
    WorkflowContext,
    WorkflowType,
    get_integration_service,
)

__all__ = [
    "ModuleIntegrationService",
    "ConsultationDocumentIntegration",
    "ConsultationLawyerIntegration",
    "NewsForumIntegration",
    "WorkflowContext",
    "WorkflowType",
    "get_integration_service",
]
