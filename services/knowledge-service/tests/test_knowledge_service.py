import pytest
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.knowledge import LegalKnowledge
from app.services.knowledge_service import KnowledgeService
from app.routers.knowledge import KnowledgeCreateRequest, KnowledgeUpdateRequest


class TestKnowledgeService:

    def test_create_knowledge(self, db_session: Session, sample_knowledge_request: KnowledgeCreateRequest):
        service = KnowledgeService(db_session)
        knowledge = service.create_knowledge(sample_knowledge_request)

        assert knowledge.id is not None
        assert knowledge.knowledge_type == "law"
        assert knowledge.title == "测试知识标题"
        assert knowledge.content == "这是测试内容，包含了详细的法律条款描述。"
        assert knowledge.status == "draft"
        assert knowledge.version == 1
        assert knowledge.is_deleted is False
        assert knowledge.is_active is True

    def test_get_knowledge(self, db_session: Session, sample_knowledge: LegalKnowledge):
        service = KnowledgeService(db_session)
        fetched = service.get_knowledge(sample_knowledge.id)

        assert fetched is not None
        assert fetched.id == sample_knowledge.id
        assert fetched.title == sample_knowledge.title

    def test_get_knowledge_not_found(self, db_session: Session):
        service = KnowledgeService(db_session)
        fetched = service.get_knowledge(9999)

        assert fetched is None

    def test_get_knowledge_soft_deleted(self, db_session: Session, sample_knowledge: LegalKnowledge):
        import asyncio
        service = KnowledgeService(db_session)
        asyncio.get_event_loop().run_until_complete(service.delete_knowledge(sample_knowledge.id))

        fetched = service.get_knowledge(sample_knowledge.id)
        assert fetched is None

    def test_update_knowledge(self, db_session: Session, sample_knowledge: LegalKnowledge):
        service = KnowledgeService(db_session)
        original_version = sample_knowledge.version

        update_request = KnowledgeUpdateRequest(
            title="更新后的标题",
            content="更新后的内容"
        )
        updated = service.update_knowledge(sample_knowledge.id, update_request)

        assert updated is not None
        assert updated.title == "更新后的标题"
        assert updated.content == "更新后的内容"
        assert updated.version == original_version + 1

    def test_update_knowledge_version_increment(self, db_session: Session, sample_knowledge: LegalKnowledge):
        service = KnowledgeService(db_session)
        initial_version = sample_knowledge.version

        update_request = KnowledgeUpdateRequest(title="新标题")
        updated = service.update_knowledge(sample_knowledge.id, update_request)

        assert updated.version == initial_version + 1

        update_request2 = KnowledgeUpdateRequest(title="又一个新标题")
        updated2 = service.update_knowledge(sample_knowledge.id, update_request2)

        assert updated2.version == initial_version + 2

    def test_delete_knowledge(self, db_session: Session, sample_knowledge: LegalKnowledge):
        service = KnowledgeService(db_session)
        import asyncio
        result = asyncio.get_event_loop().run_until_complete(service.delete_knowledge(sample_knowledge.id))

        assert result is True

        deleted = db_session.query(LegalKnowledge).filter(LegalKnowledge.id == sample_knowledge.id).first()
        assert deleted.is_deleted is True
        assert deleted.is_active is False
        assert deleted.deleted_at is not None

    def test_delete_knowledge_not_found(self, db_session: Session):
        service = KnowledgeService(db_session)
        import asyncio
        result = asyncio.get_event_loop().run_until_complete(service.delete_knowledge(9999))

        assert result is False

    def test_publish_knowledge(self, db_session: Session, sample_knowledge: LegalKnowledge):
        service = KnowledgeService(db_session)
        import asyncio
        published = asyncio.get_event_loop().run_until_complete(
            service.publish_knowledge(sample_knowledge.id, reviewed_by=1)
        )

        assert published is not None
        assert published.status == "published"
        assert published.is_active is True
        assert published.reviewed_by == 1
        assert published.reviewed_at is not None

    def test_publish_knowledge_from_pending_review(self, db_session: Session, sample_knowledge: LegalKnowledge):
        service = KnowledgeService(db_session)
        sample_knowledge.status = "pending_review"
        db_session.commit()

        import asyncio
        published = asyncio.get_event_loop().run_until_complete(
            service.publish_knowledge(sample_knowledge.id, reviewed_by=1)
        )

        assert published.status == "published"

    def test_publish_knowledge_invalid_status(self, db_session: Session, sample_knowledge: LegalKnowledge):
        service = KnowledgeService(db_session)
        sample_knowledge.status = "archived"
        db_session.commit()

        import asyncio
        with pytest.raises(ValueError, match="无法从状态"):
            asyncio.get_event_loop().run_until_complete(
                service.publish_knowledge(sample_knowledge.id)
            )

    def test_unpublish_knowledge(self, db_session: Session, published_knowledge: LegalKnowledge):
        service = KnowledgeService(db_session)
        import asyncio
        unpublished = asyncio.get_event_loop().run_until_complete(
            service.unpublish_knowledge(published_knowledge.id)
        )

        assert unpublished is not None
        assert unpublished.status == "archived"
        assert unpublished.is_active is False

    def test_unpublish_knowledge_invalid_status(self, db_session: Session, sample_knowledge: LegalKnowledge):
        service = KnowledgeService(db_session)

        import asyncio
        with pytest.raises(ValueError, match="只能下线已发布的知识"):
            asyncio.get_event_loop().run_until_complete(
                service.unpublish_knowledge(sample_knowledge.id)
            )

    def test_submit_for_review(self, db_session: Session, sample_knowledge: LegalKnowledge):
        service = KnowledgeService(db_session)
        submitted = service.submit_for_review(sample_knowledge.id)

        assert submitted is not None
        assert submitted.status == "pending_review"

    def test_submit_for_review_invalid_status(self, db_session: Session, published_knowledge: LegalKnowledge):
        service = KnowledgeService(db_session)

        with pytest.raises(ValueError, match="只能提交草稿状态"):
            service.submit_for_review(published_knowledge.id)

    def test_state_machine_transitions(self, db_session: Session, sample_knowledge: LegalKnowledge):
        service = KnowledgeService(db_session)

        assert sample_knowledge.status == "draft"

        submitted = service.submit_for_review(sample_knowledge.id)
        assert submitted.status == "pending_review"

        import asyncio
        published = asyncio.get_event_loop().run_until_complete(
            service.publish_knowledge(sample_knowledge.id, reviewed_by=1)
        )
        assert published.status == "published"

        unpublished = asyncio.get_event_loop().run_until_complete(
            service.unpublish_knowledge(sample_knowledge.id)
        )
        assert unpublished.status == "archived"

    def test_invalid_publish_from_archived(self, db_session: Session, published_knowledge: LegalKnowledge):
        service = KnowledgeService(db_session)
        import asyncio

        asyncio.get_event_loop().run_until_complete(
            service.unpublish_knowledge(published_knowledge.id)
        )

        with pytest.raises(ValueError, match="无法从状态"):
            asyncio.get_event_loop().run_until_complete(
                service.publish_knowledge(published_knowledge.id)
            )

    def test_full_lifecycle(self, db_session: Session, sample_knowledge_request: KnowledgeCreateRequest):
        service = KnowledgeService(db_session)

        created = service.create_knowledge(sample_knowledge_request)
        assert created.status == "draft"
        assert created.version == 1

        import asyncio

        updated = service.update_knowledge(created.id, KnowledgeUpdateRequest(title="修改后标题"))
        assert updated.version == 2

        submitted = service.submit_for_review(created.id)
        assert submitted.status == "pending_review"

        published = asyncio.get_event_loop().run_until_complete(
            service.publish_knowledge(created.id, reviewed_by=1)
        )
        assert published.status == "published"

        unpublished = asyncio.get_event_loop().run_until_complete(
            service.unpublish_knowledge(created.id)
        )
        assert unpublished.status == "archived"

        deleted = asyncio.get_event_loop().run_until_complete(
            service.delete_knowledge(created.id)
        )
        assert deleted is True

        final = service.get_knowledge(created.id)
        assert final is None
