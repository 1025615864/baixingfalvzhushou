"""案例 API 路由单元测试"""
import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.archive import LegalCase


class TestArchiveAPI:
    """Archive API 端点测试"""

    def test_create_case_api(self, client: TestClient, sample_case_request):
        """测试 POST /api/v1/archive 创建案例"""
        response = client.post("/api/v1/archive", json=sample_case_request.model_dump(mode="json"))

        assert response.status_code == 201
        data = response.json()
        assert data["id"] is not None
        assert data["title"] == sample_case_request.title
        assert data["status"] == "draft"

    def test_create_case_with_duplicate_case_number(self, client: TestClient, sample_case: LegalCase, sample_case_request):
        """测试案号重复时返回 400"""
        response = client.post("/api/v1/archive", json=sample_case_request.model_dump(mode="json"))

        assert response.status_code == 400
        assert "案号已存在" in response.json()["detail"]

    def test_get_case_api(self, client: TestClient, sample_case: LegalCase):
        """测试 GET /api/v1/archive/{case_id} 获取案例"""
        response = client.get(f"/api/v1/archive/{sample_case.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_case.id
        assert data["title"] == sample_case.title

    def test_get_case_not_found_api(self, client: TestClient):
        """测试获取不存在的案例返回 404"""
        response = client.get("/api/v1/archive/99999")

        assert response.status_code == 404
        assert "案例不存在" in response.json()["detail"]

    def test_update_case_api(self, client: TestClient, sample_case: LegalCase):
        """测试 PUT /api/v1/archive/{case_id} 更新案例"""
        update_data = {"title": "更新后的标题"}
        response = client.put(f"/api/v1/archive/{sample_case.id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "更新后的标题"
        assert data["version"] == sample_case.version + 1

    def test_update_case_not_found_api(self, client: TestClient):
        """测试更新不存在的案例返回 404"""
        update_data = {"title": "新标题"}
        response = client.put("/api/v1/archive/99999", json=update_data)

        assert response.status_code == 404

    def test_delete_case_api(self, client: TestClient, sample_case: LegalCase):
        """测试 DELETE /api/v1/archive/{case_id} 软删除案例"""
        response = client.delete(f"/api/v1/archive/{sample_case.id}")

        assert response.status_code == 204

        get_response = client.get(f"/api/v1/archive/{sample_case.id}")
        assert get_response.status_code == 404

    def test_delete_case_not_found_api(self, client: TestClient):
        """测试删除不存在的案例返回 404"""
        response = client.delete("/api/v1/archive/99999")

        assert response.status_code == 404

    def test_publish_case_api(self, client: TestClient, sample_case: LegalCase):
        """测试 POST /api/v1/archive/{case_id}/publish 发布案例"""
        response = client.post(f"/api/v1/archive/{sample_case.id}/publish?reviewed_by=1")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "published"
        assert data["is_active"] is True
        assert data["reviewed_by"] == 1

    def test_publish_case_from_pending_review_api(self, client: TestClient, sample_case: LegalCase):
        """测试从待审核状态发布案例"""
        client.post(f"/api/v1/archive/{sample_case.id}/submit-review")
        response = client.post(f"/api/v1/archive/{sample_case.id}/publish")

        assert response.status_code == 200
        assert response.json()["status"] == "published"

    def test_publish_case_invalid_status_api(self, client: TestClient, sample_case: LegalCase):
        """测试从无效状态发布案例返回 400"""
        client.post(f"/api/v1/archive/{sample_case.id}/publish")
        response = client.post(f"/api/v1/archive/{sample_case.id}/publish")

        assert response.status_code == 400

    def test_publish_case_not_found_api(self, client: TestClient):
        """测试发布不存在的案例返回 400"""
        response = client.post("/api/v1/archive/99999/publish")

        assert response.status_code == 400

    def test_unpublish_case_api(self, client: TestClient, sample_case: LegalCase):
        """测试 POST /api/v1/archive/{case_id}/unpublish 下线案例"""
        client.post(f"/api/v1/archive/{sample_case.id}/publish")
        response = client.post(f"/api/v1/archive/{sample_case.id}/unpublish")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "archived"
        assert data["is_active"] is False

    def test_unpublish_case_invalid_status_api(self, client: TestClient, sample_case: LegalCase):
        """测试从非发布状态下线案例返回 400"""
        response = client.post(f"/api/v1/archive/{sample_case.id}/unpublish")

        assert response.status_code == 400
        assert "只能下线已发布的案例" in response.json()["detail"]

    def test_unpublish_case_not_found_api(self, client: TestClient):
        """测试下线不存在的案例返回 400"""
        response = client.post("/api/v1/archive/99999/unpublish")

        assert response.status_code == 400

    def test_submit_for_review_api(self, client: TestClient, sample_case: LegalCase):
        """测试 POST /api/v1/archive/{case_id}/submit-review 提交审核"""
        response = client.post(f"/api/v1/archive/{sample_case.id}/submit-review")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending_review"

    def test_submit_for_review_invalid_status_api(self, client: TestClient, sample_case: LegalCase):
        """测试从非草稿状态提交审核返回 400"""
        client.post(f"/api/v1/archive/{sample_case.id}/publish")
        response = client.post(f"/api/v1/archive/{sample_case.id}/submit-review")

        assert response.status_code == 400
        assert "只能提交草稿状态的案例" in response.json()["detail"]

    def test_submit_for_review_not_found_api(self, client: TestClient):
        """测试提交审核不存在的案例返回 400"""
        response = client.post("/api/v1/archive/99999/submit-review")

        assert response.status_code == 400

    def test_create_case_minimal_fields_api(self, client: TestClient):
        """测试仅提供必填字段创建案例"""
        minimal_data = {
            "case_type": "civil",
            "title": "最小字段案例",
            "facts": "事实描述"
        }
        response = client.post("/api/v1/archive", json=minimal_data)

        assert response.status_code == 201
        data = response.json()
        assert data["id"] is not None
        assert data["case_number"] is None
