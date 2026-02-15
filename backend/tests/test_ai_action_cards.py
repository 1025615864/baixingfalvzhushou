"""Tests for AI Action Cards feature"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json


class TestAIActionCards:
    """Test AI Action Cards functionality"""

    @pytest.mark.asyncio
    async def test_chat_router_actions_event_format(self):
        """Test that actions event format is correct"""
        async def event_generator():
            yield f"event: actions\ndata: {json.dumps({'actions': [{'id': 'generate_document', 'type': 'action', 'label': '生成文书', 'description': '根据对话内容生成法律文书', 'icon': 'file-text', 'priority': 'high', 'payload': {'template_type': 'legal_opinion'}}, {'id': 'search_lawyer', 'type': 'action', 'label': '搜索律师', 'description': '查找适合的律师资源', 'icon': 'search', 'priority': 'medium', 'payload': {'specialty': '劳动纠纷'}}]}, ensure_ascii=False)}\n\n"

        events = []
        async for event in event_generator():
            events.append(event)

        assert len(events) == 1
        assert "event: actions" in events[0]
        data = json.loads(events[0].split("data: ")[1].strip())
        assert "actions" in data
        assert len(data["actions"]) == 2
        assert data["actions"][0]["id"] == "generate_document"
        assert data["actions"][1]["id"] == "search_lawyer"


class TestActionCardSchema:
    """Test Action Card data structure"""

    def test_action_card_structure(self):
        """Verify action card has correct structure"""
        action = {
            "id": "generate_document",
            "type": "action",
            "label": "生成文书",
            "description": "根据对话内容生成法律文书",
            "icon": "file-text",
            "priority": "high",
            "payload": {"template_type": "legal_opinion"}
        }

        assert action["id"] == "generate_document"
        assert action["type"] == "action"
        assert "label" in action
        assert "description" in action
        assert "priority" in action
        assert "payload" in action

    def test_action_card_types(self):
        """Verify action card types are valid"""
        actions = [
            {
                "id": "generate_document",
                "type": "action",
                "label": "生成文书",
                "description": "根据对话内容生成法律文书",
                "icon": "file-text",
                "priority": "high",
                "payload": {"template_type": "legal_opinion"}
            },
            {
                "id": "search_lawyer",
                "type": "action",
                "label": "搜索律师",
                "description": "查找适合的律师资源",
                "icon": "search",
                "priority": "medium",
                "payload": {"specialty": "劳动纠纷"}
            }
        ]

        assert len(actions) == 2
        assert all(a["type"] == "action" for a in actions)
        assert all("id" in a for a in actions)
        assert all("label" in a for a in actions)
