"""案例服务层单元测试"""
import pytest
from datetime import datetime
from sqlalchemy.orm import Session

from app.services.archive_service import ArchiveService
from app.routers.archive import CaseCreateRequest, CaseUpdateRequest
from app.models.archive import LegalCase


class TestArchiveService:
    """ArchiveService 业务逻辑测试"""

    def test_create_case(self, db_session: Session, sample_case_request: CaseCreateRequest):
        """测试创建案例"""
        service = ArchiveService(db_session)
        case = service.create_case(sample_case_request)

        assert case.id is not None
        assert case.case_number == sample_case_request.case_number
        assert case.case_type == sample_case_request.case_type
        assert case.title == sample_case_request.title
        assert case.status == "draft"
        assert case.version == 1
        assert case.is_deleted is False
        assert case.is_active is True

    def test_get_case(self, db_session: Session, sample_case: LegalCase):
        """测试获取案例详情"""
        service = ArchiveService(db_session)
        retrieved_case = service.get_case(sample_case.id)

        assert retrieved_case is not None
        assert retrieved_case.id == sample_case.id
        assert retrieved_case.title == sample_case.title

    def test_get_case_not_found(self, db_session: Session):
        """测试获取不存在的案例"""
        service = ArchiveService(db_session)
        retrieved_case = service.get_case(99999)
        assert retrieved_case is None

    def test_update_case(self, db_session: Session, sample_case: LegalCase):
        """测试更新案例，version 递增"""
        service = ArchiveService(db_session)
        original_version = sample_case.version

        update_request = CaseUpdateRequest(title="更新后的标题")
        updated_case = service.update_case(sample_case.id, update_request)

        assert updated_case.title == "更新后的标题"
        assert updated_case.version == original_version + 1

    def test_update_case_not_found(self, db_session: Session):
        """测试更新不存在的案例"""
        service = ArchiveService(db_session)
        update_request = CaseUpdateRequest(title="新标题")

        with pytest.raises(ValueError, match="案例不存在"):
            service.update_case(99999, update_request)

    def test_delete_case(self, db_session: Session, sample_case: LegalCase):
        """测试软删除案例"""
        service = ArchiveService(db_session)
        service.delete_case(sample_case.id)

        deleted_case = service.get_case(sample_case.id)
        assert deleted_case is None

        db_session.expire_all()
        case_from_db = db_session.query(LegalCase).filter(LegalCase.id == sample_case.id).first()
        assert case_from_db.is_deleted is True
        assert case_from_db.deleted_at is not None

    def test_delete_case_not_found(self, db_session: Session):
        """测试删除不存在的案例"""
        service = ArchiveService(db_session)
        with pytest.raises(ValueError, match="案例不存在"):
            service.delete_case(99999)

    def test_publish_case(self, db_session: Session, sample_case: LegalCase):
        """测试发布案例"""
        service = ArchiveService(db_session)
        published_case = service.publish_case(sample_case.id, reviewed_by=1)

        assert published_case.status == "published"
        assert published_case.is_active is True
        assert published_case.reviewed_by == 1
        assert published_case.reviewed_at is not None

    def test_publish_case_from_pending_review(self, db_session: Session, sample_case: LegalCase):
        """测试从待审核状态发布案例"""
        service = ArchiveService(db_session)
        service.submit_for_review(sample_case.id)
        published_case = service.publish_case(sample_case.id)

        assert published_case.status == "published"

    def test_publish_case_invalid_status(self, db_session: Session, sample_case: LegalCase):
        """测试从无效状态发布案例"""
        service = ArchiveService(db_session)
        service.publish_case(sample_case.id)

        with pytest.raises(ValueError, match="无法从状态"):
            service.publish_case(sample_case.id)

    def test_publish_case_not_found(self, db_session: Session):
        """测试发布不存在的案例"""
        service = ArchiveService(db_session)
        with pytest.raises(ValueError, match="案例不存在"):
            service.publish_case(99999)

    def test_unpublish_case(self, db_session: Session, sample_case: LegalCase):
        """测试下线案例"""
        service = ArchiveService(db_session)
        service.publish_case(sample_case.id)
        archived_case = service.unpublish_case(sample_case.id)

        assert archived_case.status == "archived"
        assert archived_case.is_active is False

    def test_unpublish_case_invalid_status(self, db_session: Session, sample_case: LegalCase):
        """测试从非发布状态下线案例"""
        service = ArchiveService(db_session)
        with pytest.raises(ValueError, match="只能下线已发布的案例"):
            service.unpublish_case(sample_case.id)

    def test_unpublish_case_not_found(self, db_session: Session):
        """测试下线不存在的案例"""
        service = ArchiveService(db_session)
        with pytest.raises(ValueError, match="案例不存在"):
            service.unpublish_case(99999)

    def test_duplicate_case_number(self, db_session: Session, sample_case_request: CaseCreateRequest):
        """测试案号唯一性检查"""
        service = ArchiveService(db_session)
        service.create_case(sample_case_request)

        duplicate_request = CaseCreateRequest(
            case_number=sample_case_request.case_number,
            case_type="criminal",
            title="另一个案例",
            facts="其他事实"
        )

        with pytest.raises(ValueError, match="案号已存在"):
            service.create_case(duplicate_request)

    def test_duplicate_case_number_allowed_without_case_number(self, db_session: Session, sample_case_request: CaseCreateRequest):
        """测试不提供案号时可以创建多个案例"""
        service = ArchiveService(db_session)
        sample_case_request.case_number = None
        case1 = service.create_case(sample_case_request)
        case2 = service.create_case(sample_case_request)

        assert case1.id != case2.id

    def test_submit_for_review(self, db_session: Session, sample_case: LegalCase):
        """测试提交审核"""
        service = ArchiveService(db_session)
        reviewed_case = service.submit_for_review(sample_case.id)

        assert reviewed_case.status == "pending_review"

    def test_submit_for_review_invalid_status(self, db_session: Session, sample_case: LegalCase):
        """测试从非草稿状态提交审核"""
        service = ArchiveService(db_session)
        service.publish_case(sample_case.id)

        with pytest.raises(ValueError, match="只能提交草稿状态的案例"):
            service.submit_for_review(sample_case.id)

    def test_state_machine_transitions(self, db_session: Session, sample_case: LegalCase):
        """测试状态机转换: draft -> pending_review -> published -> archived"""
        service = ArchiveService(db_session)
        case_id = sample_case.id

        assert service.get_case(case_id).status == "draft"

        case = service.submit_for_review(case_id)
        assert case.status == "pending_review"

        case = service.publish_case(case_id, reviewed_by=1)
        assert case.status == "published"

        case = service.unpublish_case(case_id)
        assert case.status == "archived"

    def test_state_machine_invalid_publish_from_archived(self, db_session: Session, sample_case: LegalCase):
        """测试从 archived 状态不能直接发布"""
        service = ArchiveService(db_session)
        service.submit_for_review(sample_case.id)
        service.publish_case(sample_case.id)
        service.unpublish_case(sample_case.id)

        with pytest.raises(ValueError, match="无法从状态"):
            service.publish_case(sample_case.id)

    def test_get_deleted_case_returns_none(self, db_session: Session, sample_case: LegalCase):
        """测试 get_case 不会返回已删除的案例"""
        service = ArchiveService(db_session)
        service.delete_case(sample_case.id)

        result = service.get_case(sample_case.id)
        assert result is None

    def test_case_preserves_version_on_soft_delete(self, db_session: Session, sample_case: LegalCase):
        """测试软删除不改变 version"""
        service = ArchiveService(db_session)
        version_before_delete = sample_case.version
        service.delete_case(sample_case.id)

        db_session.expire_all()
        case_from_db = db_session.query(LegalCase).filter(LegalCase.id == sample_case.id).first()
        assert case_from_db.version == version_before_delete

    def test_get_published_cases(self, db_session: Session, sample_case: LegalCase):
        """测试获取所有已发布案例"""
        service = ArchiveService(db_session)
        service.publish_case(sample_case.id)

        published_cases = service.get_published_cases()
        assert len(published_cases) == 1
        assert published_cases[0].id == sample_case.id

    def test_get_published_cases_excludes_unpublished(self, db_session: Session, sample_case: LegalCase):
        """测试 get_published_cases 不包含未发布案例"""
        service = ArchiveService(db_session)

        published_cases = service.get_published_cases()
        assert len(published_cases) == 0

    def test_batch_create_cases(self, db_session: Session):
        """测试批量创建案例"""
        service = ArchiveService(db_session)
        items = [
            CaseCreateRequest(case_type="civil", title=f"案例{i}", facts=f"事实{i}")
            for i in range(5)
        ]

        success, failed, errors = service.batch_create_cases(items)

        assert success == 5
        assert failed == 0
        assert len(errors) == 0

        all_cases = db_session.query(LegalCase).all()
        assert len(all_cases) == 5

    def test_batch_create_cases_with_duplicates_skip(self, db_session: Session, sample_case: LegalCase):
        """测试批量创建时跳过重复案号"""
        service = ArchiveService(db_session)
        items = [
            CaseCreateRequest(
                case_number=sample_case.case_number,
                case_type="civil",
                title="重复案例",
                facts="事实"
            ),
            CaseCreateRequest(
                case_type="civil",
                title="新案例",
                facts="事实"
            )
        ]

        success, failed, errors = service.batch_create_cases(items, skip_duplicates=True)

        assert success == 1
        assert failed == 0

    def test_batch_create_cases_with_duplicates_raise(self, db_session: Session, sample_case: LegalCase):
        """测试批量创建时重复案号抛出异常"""
        service = ArchiveService(db_session)
        items = [
            CaseCreateRequest(
                case_number=sample_case.case_number,
                case_type="civil",
                title="重复案例",
                facts="事实"
            )
        ]

        with pytest.raises(ValueError, match="案号"):
            service.batch_create_cases(items, skip_duplicates=False)
