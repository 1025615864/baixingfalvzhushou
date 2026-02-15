from datetime import datetime, timezone

import pytest

from app.main import app
from app.models.user import User
from app.utils.deps import get_current_user


@pytest.mark.asyncio
async def test_analytics_router_flow(client, test_session):
    now_utc = datetime.now(timezone.utc)

    user = User(
        username="analytics_user",
        email="analytics_user@example.com",
        nickname="analytics_user",
        hashed_password="x",
        created_at=now_utc,
        updated_at=now_utc,
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)

    async def override_user():
        return user

    app.dependency_overrides[get_current_user] = override_user

    try:
        payload = {
            "action": "page_view",
            "resource_type": "news",
            "resource_id": 1,
            "metadata": {"source": "landing", "score": 1},
            "session_id": "sess-1",
        }
        resp = await client.post("/api/analytics/log", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["user_id"] == user.id
        assert data["action"] == payload["action"]
        assert data["resource_type"] == payload["resource_type"]
        assert data["resource_id"] == payload["resource_id"]
        assert "source" in (data.get("metadata") or "")

        history = await client.get("/api/analytics/history")
        assert history.status_code == 200
        history_data = history.json()
        assert history_data["total"] == 1
        assert history_data["items"][0]["action"] == payload["action"]

        view = await client.get("/api/analytics/resource/news/1/view-count")
        assert view.status_code == 200
        assert view.json()["view_count"] == 1

        date_utc = now_utc.date().isoformat()
        stats = await client.get(
            "/api/analytics/statistics/actions",
            params={"start_date": date_utc, "end_date": date_utc},
        )
        assert stats.status_code == 200
        items = {item["action"]: item["count"] for item in stats.json()["items"]}
        assert items.get("page_view") == 1

        funnel = await client.post(
            "/api/analytics/funnel/conversion",
            json={
                "start_date": date_utc,
                "end_date": date_utc,
                "funnel_steps": [
                    {"name": "view", "action": "page_view", "resource_type": "news"},
                    {"name": "click", "action": "click", "resource_type": "news"},
                ],
            },
        )
        assert funnel.status_code == 200
        steps = funnel.json()["steps"]
        assert steps[0]["count"] == 1
        assert steps[0]["conversion_rate"] == 100
        assert steps[1]["count"] == 0
        assert steps[1]["drop_rate"] == 100

        retention = await client.post(
            "/api/analytics/retention",
            json={"cohort_date": now_utc.date().isoformat(), "retention_days": []},
        )
        assert retention.status_code == 200
        retention_data = retention.json()
        assert retention_data["cohort_count"] == 1
        assert retention_data["retention"] == []
    finally:
        app.dependency_overrides.pop(get_current_user, None)
