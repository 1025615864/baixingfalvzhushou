"""domains package - 业务领域隔离"""
from .firm import models as firm_models, services as firm_services, routers as firm_routers
from .consultation import models as consultation_models, services as consultation_services, routers as consultation_routers
from .lawyer import models as lawyer_models, services as lawyer_services, routers as lawyer_routers
from .appointment import models as appointment_models, services as appointment_services, routers as appointment_routers
from .review import models as review_models, services as review_services, routers as review_routers
from .document import models as document_models, services as document_services, routers as document_routers
from .admin import models as admin_models, services as admin_services, routers as admin_routers

__all__ = [
    "firm",
    "consultation",
    "lawyer",
    "appointment",
    "review",
    "document",
    "admin",
]

DOMAIN_MODULES = {
    "firm": {
        "models": firm_models,
        "services": firm_services,
        "routers": firm_routers,
    },
    "consultation": {
        "models": consultation_models,
        "services": consultation_services,
        "routers": consultation_routers,
    },
    "lawyer": {
        "models": lawyer_models,
        "services": lawyer_services,
        "routers": lawyer_routers,
    },
    "appointment": {
        "models": appointment_models,
        "services": appointment_services,
        "routers": appointment_routers,
    },
    "review": {
        "models": review_models,
        "services": review_services,
        "routers": review_routers,
    },
    "document": {
        "models": document_models,
        "services": document_services,
        "routers": document_routers,
    },
    "admin": {
        "models": admin_models,
        "services": admin_services,
        "routers": admin_routers,
    },
}
