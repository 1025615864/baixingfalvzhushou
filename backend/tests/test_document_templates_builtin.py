"""Tests for builtin document templates."""
from __future__ import annotations

import pytest

from app.services.document_templates_builtin import (
    BUILTIN_DOCUMENT_TEMPLATES,
    BuiltinDocumentTemplate,
)


class TestBuiltinDocumentTemplate:
    """Test BuiltinDocumentTemplate TypedDict."""

    def test_builtin_document_template_is_typeddict(self) -> None:
        """Test that BuiltinDocumentTemplate is a TypedDict."""
        template = BuiltinDocumentTemplate(
            title="Test",
            description="Test description",
            template="Test template content",
        )
        assert template["title"] == "Test"
        assert template["description"] == "Test description"
        assert template["template"] == "Test template content"


class TestBuiltinDocumentTemplates:
    """Test BUILTIN_DOCUMENT_TEMPLATES dictionary."""

    def test_builtin_templates_exists(self) -> None:
        """Test that BUILTIN_DOCUMENT_TEMPLATES exists."""
        assert BUILTIN_DOCUMENT_TEMPLATES is not None
        assert isinstance(BUILTIN_DOCUMENT_TEMPLATES, dict)

    def test_builtin_templates_not_empty(self) -> None:
        """Test that BUILTIN_DOCUMENT_TEMPLATES is not empty."""
        assert len(BUILTIN_DOCUMENT_TEMPLATES) > 0

    def test_complaint_template_exists(self) -> None:
        """Test that complaint template exists."""
        assert "complaint" in BUILTIN_DOCUMENT_TEMPLATES
        template = BUILTIN_DOCUMENT_TEMPLATES["complaint"]
        assert template["title"] == "民事起诉状"
        assert "起诉状" in template["template"]

    def test_defense_template_exists(self) -> None:
        """Test that defense template exists."""
        assert "defense" in BUILTIN_DOCUMENT_TEMPLATES
        template = BUILTIN_DOCUMENT_TEMPLATES["defense"]
        assert template["title"] == "民事答辩状"
        assert "答辩状" in template["template"]

    def test_agreement_template_exists(self) -> None:
        """Test that agreement template exists."""
        assert "agreement" in BUILTIN_DOCUMENT_TEMPLATES
        template = BUILTIN_DOCUMENT_TEMPLATES["agreement"]
        assert template["title"] == "和解协议书"
        assert "和解协议" in template["template"]

    def test_letter_template_exists(self) -> None:
        """Test that letter template exists."""
        assert "letter" in BUILTIN_DOCUMENT_TEMPLATES
        template = BUILTIN_DOCUMENT_TEMPLATES["letter"]
        assert template["title"] == "律师函"
        assert "律师函" in template["template"]

    def test_all_templates_have_required_fields(self) -> None:
        """Test that all templates have title, description, and template."""
        for key, template in BUILTIN_DOCUMENT_TEMPLATES.items():
            assert "title" in template, f"Template '{key}' missing 'title'"
            assert "description" in template, f"Template '{key}' missing 'description'"
            assert "template" in template, f"Template '{key}' missing 'template'"
            assert isinstance(template["title"], str)
            assert isinstance(template["description"], str)
            assert isinstance(template["template"], str)

    def test_all_templates_are_non_empty(self) -> None:
        """Test that all template fields are non-empty strings."""
        for key, template in BUILTIN_DOCUMENT_TEMPLATES.items():
            assert len(template["title"]) > 0, f"Template '{key}' has empty title"
            assert len(template["description"]) > 0, f"Template '{key}' has empty description"
            assert len(template["template"]) > 0, f"Template '{key}' has empty template"

    def test_templates_contain_expected_placeholders(self) -> None:
        """Test that templates contain expected placeholders."""
        complaint = BUILTIN_DOCUMENT_TEMPLATES["complaint"]
        assert "{plaintiff_name}" in complaint["template"]
        assert "{defendant_name}" in complaint["template"]
        assert "{court_name}" in complaint["template"]

    def test_templates_have_content(self) -> None:
        """Test that templates have sufficient content."""
        for key, template in BUILTIN_DOCUMENT_TEMPLATES.items():
            # Check that templates contain reasonable content
            assert len(template["template"]) > 50, f"Template '{key}' is too short"
            # Templates should contain common legal document elements
            assert "{" in template["template"], f"Template '{key}' missing placeholders"

    def test_all_templates_have_placeholders(self) -> None:
        """Test that all templates use placeholders for dynamic content."""
        for key, template in BUILTIN_DOCUMENT_TEMPLATES.items():
            # Templates should use {placeholders} for dynamic content
            assert "{" in template["template"], f"Template '{key}' missing placeholders"
            assert "}" in template["template"], f"Template '{key}' has unclosed placeholders"


class TestTemplateStructure:
    """Test structure of individual templates."""

    def test_complaint_has_required_sections(self) -> None:
        """Test that complaint template has proper legal document structure."""
        template = BUILTIN_DOCUMENT_TEMPLATES["complaint"]["template"]
        # Should have plaintiff and defendant sections
        assert "plaintiff_name" in template
        assert "defendant_name" in template
        # Should have court section
        assert "court_name" in template
        # Should have evidence section
        assert "evidence" in template

    def test_defense_has_response_structure(self) -> None:
        """Test that defense template has proper response structure."""
        template = BUILTIN_DOCUMENT_TEMPLATES["defense"]["template"]
        assert "defendant_name" in template
        assert "plaintiff_name" in template

    def test_agreement_has_signatures(self) -> None:
        """Test that agreement template has signature sections."""
        template = BUILTIN_DOCUMENT_TEMPLATES["agreement"]["template"]
        assert "甲方" in template or "party_a" in template.lower() or "plaintiff_name" in template
        assert "乙方" in template or "party_b" in template.lower() or "defendant_name" in template
        assert "签字" in template or "signature" in template.lower()

    def test_letter_has_formal_structure(self) -> None:
        """Test that letter template has formal legal structure."""
        template = BUILTIN_DOCUMENT_TEMPLATES["letter"]["template"]
        # Should have recipient and sender placeholders
        assert "defendant_name" in template or "recipient" in template.lower()
        assert "plaintiff_name" in template or "sender" in template.lower()
