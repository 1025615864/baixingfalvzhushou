import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_funnel_workflow():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Create
        funnel_data = {
            "funnel_id": "test_funnel_1",
            "name": "Test Funnel",
            "steps": [
                {"step_id": "step1", "name": "Step 1", "event_type": "view"},
                {"step_id": "step2", "name": "Step 2", "event_type": "click"}
            ]
        }
        response = await ac.post("/api/funnel/funnels", json=funnel_data)
        assert response.status_code == 200
        assert response.json()["id"] == "test_funnel_1"

        # List
        response = await ac.get("/api/funnel/funnels")
        assert response.status_code == 200
        assert len(response.json()["funnels"]) >= 1

        # Track
        track_data = {
            "funnel_id": "test_funnel_1",
            "step_id": "step1",
            "properties": {"source": "mobile"}
        }
        response = await ac.post("/api/funnel/track", json=track_data)
        assert response.status_code == 200

        # Stats
        response = await ac.get("/api/funnel/stats")
        assert response.status_code == 200
