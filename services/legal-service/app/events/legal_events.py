"""Legal Service Kafka 事件定义"""
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Optional, Any, Dict
import json
import uuid


@dataclass
class LegalEvent:
    event_id: str
    event_type: str
    timestamp: str
    version: str
    source: str
    lawyer_id: Optional[str] = None
    consultation_id: Optional[str] = None
    user_id: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, data: str) -> "LegalEvent":
        return cls(**json.loads(data))

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class LegalEventTypes:
    CONSULTATION_CREATED = "legal.consultation.created"
    CONSULTATION_ASSIGNED = "legal.consultation.assigned"
    CONSULTATION_COMPLETED = "legal.consultation.completed"
    CONSULTATION_CANCELLED = "legal.consultation.cancelled"
    CONSULTATION_MESSAGE_ADDED = "legal.consultation.message_added"

    LAWYER_VERIFIED = "legal.lawyer.verified"
    LAWYER_RATING_UPDATED = "legal.lawyer.rating_updated"
    LAWYER_STATUS_CHANGED = "legal.lawyer.status_changed"

    FIRM_REGISTERED = "legal.firm.registered"
    FIRM_STATUS_CHANGED = "legal.firm.status_changed"

    APPOINTMENT_CREATED = "legal.appointment.created"
    APPOINTMENT_CONFIRMED = "legal.appointment.confirmed"
    APPOINTMENT_CANCELLED = "legal.appointment.cancelled"

    REVIEW_SUBMITTED = "legal.review.submitted"


def create_legal_event(
    event_type: str,
    lawyer_id: Optional[str] = None,
    consultation_id: Optional[str] = None,
    user_id: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
    source: str = "legal-service",
) -> LegalEvent:
    return LegalEvent(
        event_id=str(uuid.uuid4()),
        event_type=event_type,
        timestamp=datetime.now(timezone.utc).isoformat(),
        version="1.0",
        source=source,
        lawyer_id=lawyer_id,
        consultation_id=consultation_id,
        user_id=user_id,
        payload=payload or {},
    )