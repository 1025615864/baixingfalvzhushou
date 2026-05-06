import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.knowledge import LegalKnowledge


class TestKnowledgeAPI:

    def test_create_knowledge_api(self, client: TestClient):
        response = client.post(
            "/api/v1/knowledge",
            json={
                "knowledge_type": "law",
                "title": "API测试知识",
                "content": "这是API测试的内容"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["id"] is not None
        assert data["title"] == "API测试知识"
        assert data["status"] == "draft"
        assert data["version"] == 1

    def test_get_knowledge_api(self, client: TestClient, sample_knowledge: LegalKnowledge):
        response = client.get(f"/api/v1/knowledge/{sample_knowledge.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_knowledge.id
        assert data["title"] == sample_knowledge.title

    def test_get_knowledge_not_found_api(self, client: TestClient):
        response = client.get("/api/v1/knowledge/9999")
        assert response.status_code == 404

    def test_update_knowledge_api(self, client: TestClient, sample_knowledge: LegalKnowledge):
        response = client.put(
            f"/api/v1/knowledge/{sample_knowledge.id}",
            json={"title": "API更新后的标题"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "API更新后的标题"
        assert data["version"] == sample_knowledge.version + 1

    def test_update_knowledge_not_found_api(self, client: TestClient):
        response = client.put(
            "/api/v1/knowledge/9999",
            json={"title": "新标题"}
        )
        assert response.status_code == 404

    def test_delete_knowledge_api(self, client: TestClient, sample_knowledge: LegalKnowledge):
        response = client.delete(f"/api/v1/knowledge/{sample_knowledge.id}")
        assert response.status_code == 204

    def test_delete_knowledge_not_found_api(self, client: TestClient):
        response = client.delete("/api/v1/knowledge/9999")
        assert response.status_code == 404

    def test_publish_knowledge_api(self, client: TestClient, sample_knowledge: LegalKnowledge):
        response = client.post(f"/api/v1/knowledge/{sample_knowledge.id}/publish?reviewed_by=1")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "published"
        assert data["reviewed_by"] == 1

    def test_publish_knowledge_from_pending_review_api(self, client: TestClient, sample_knowledge: LegalKnowledge):
        client.post(f"/api/v1/knowledge/{sample_knowledge.id}/submit-review")

        response = client.post(f"/api/v1/knowledge/{sample_knowledge.id}/publish")
        assert response.status_code == 200
        assert response.json()["status"] == "published"

    def test_publish_knowledge_invalid_status_api(self, client: TestClient, published_knowledge: LegalKnowledge):
        response = client.post(f"/api/v1/knowledge/{published_knowledge.id}/publish")
        assert response.status_code == 400

    def test_publish_knowledge_not_found_api(self, client: TestClient):
        response = client.post("/api/v1/knowledge/9999/publish")
        assert response.status_code == 404

    def test_unpublish_knowledge_api(self, client: TestClient, published_knowledge: LegalKnowledge):
        response = client.post(f"/api/v1/knowledge/{published_knowledge.id}/unpublish")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "archived"

    def test_unpublish_knowledge_invalid_status_api(self, client: TestClient, sample_knowledge: LegalKnowledge):
        response = client.post(f"/api/v1/knowledge/{sample_knowledge.id}/unpublish")
        assert response.status_code == 400

    def test_submit_for_review_api(self, client: TestClient, sample_knowledge: LegalKnowledge):
        response = client.post(f"/api/v1/knowledge/{sample_knowledge.id}/submit-review")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending_review"

    def test_submit_for_review_invalid_status_api(self, client: TestClient, published_knowledge: LegalKnowledge):
        response = client.post(f"/api/v1/knowledge/{published_knowledge.id}/submit-review")
        assert response.status_code == 400

    def test_submit_for_review_not_found_api(self, client: TestClient):
        response = client.post("/api/v1/knowledge/9999/submit-review")
        assert response.status_code == 404

    def test_state_machine_api_flow(self, client: TestClient):
        create_response = client.post(
            "/api/v1/knowledge",
            json={
                "knowledge_type": "law",
                "title": "状态机测试",
                "content": "测试状态转换"
            }
        )
        knowledge_id = create_response.json()["id"]
        assert create_response.json()["status"] == "draft"

        submit_response = client.post(f"/api/v1/knowledge/{knowledge_id}/submit-review")
        assert submit_response.json()["status"] == "pending_review"

        publish_response = client.post(f"/api/v1/knowledge/{knowledge_id}/publish")
        assert publish_response.json()["status"] == "published"

        unpublish_response = client.post(f"/api/v1/knowledge/{knowledge_id}/unpublish")
        assert unpublish_response.json()["status"] == "archived"

    def test_health_check(self, client: TestClient):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_root_endpoint(self, client: TestClient):
        response = client.get("/")
        assert response.status_code == 200
        assert "service" in response.json()
