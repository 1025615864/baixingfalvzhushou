"""Tests for JSON field parser utilities."""
import pytest

from app.utils.json_parser import (
    parse_json_field,
    parse_images_field,
    parse_attachments_field,
)


class TestParseJsonField:
    """Tests for parse_json_field function."""

    def test_parse_none_value(self):
        """Test parsing None value returns None."""
        result = parse_json_field(None)
        assert result is None

    def test_parse_empty_string(self):
        """Test parsing empty string returns None."""
        result = parse_json_field("")
        assert result is None

    def test_parse_valid_json_object(self):
        """Test parsing valid JSON object."""
        result = parse_json_field('{"key": "value"}')
        assert result == {"key": "value"}

    def test_parse_valid_json_array(self):
        """Test parsing valid JSON array."""
        result = parse_json_field('[1, 2, 3]')
        assert result == [1, 2, 3]

    def test_parse_invalid_json(self):
        """Test parsing invalid JSON returns None."""
        result = parse_json_field('not valid json')
        assert result is None

    def test_parse_with_field_name(self):
        """Test parsing with custom field name."""
        result = parse_json_field('{"test": 1}', "custom_field")
        assert result == {"test": 1}


class TestParseImagesField:
    """Tests for parse_images_field function."""

    def test_parse_none_images(self):
        """Test parsing None images returns empty list."""
        result = parse_images_field(None)
        assert result == []

    def test_parse_empty_string_images(self):
        """Test parsing empty string returns empty list."""
        result = parse_images_field("")
        assert result == []

    def test_parse_valid_images_array(self):
        """Test parsing valid images array."""
        result = parse_images_field('["image1.jpg", "image2.png"]')
        assert result == ["image1.jpg", "image2.png"]

    def test_parse_images_with_none_elements(self):
        """Test parsing images with None elements filters them out."""
        result = parse_images_field('["image1.jpg", null, "image2.png"]')
        assert result == ["image1.jpg", "image2.png"]

    def test_parse_images_with_empty_strings(self):
        """Test parsing images with empty strings filters them out."""
        result = parse_images_field('["image1.jpg", "", "image2.png"]')
        assert result == ["image1.jpg", "image2.png"]

    def test_parse_images_with_non_string_elements(self):
        """Test parsing images with non-string elements converts to string."""
        result = parse_images_field('["image1.jpg", 123, "image2.png"]')
        assert result == ["image1.jpg", "123", "image2.png"]

    def test_parse_images_non_array(self):
        """Test parsing non-array JSON returns empty list."""
        result = parse_images_field('{"not": "array"}')
        assert result == []

    def test_parse_images_invalid_json(self):
        """Test parsing invalid JSON returns empty list."""
        result = parse_images_field('not valid json')
        assert result == []


class TestParseAttachmentsField:
    """Tests for parse_attachments_field function."""

    def test_parse_none_attachments(self):
        """Test parsing None attachments returns empty list."""
        result = parse_attachments_field(None)
        assert result == []

    def test_parse_empty_string_attachments(self):
        """Test parsing empty string returns empty list."""
        result = parse_attachments_field("")
        assert result == []

    def test_parse_valid_attachments(self):
        """Test parsing valid attachments."""
        json_str = '[{"name": "doc.pdf", "url": "http://example.com/doc.pdf"}]'
        result = parse_attachments_field(json_str)
        assert len(result) == 1
        assert result[0] == {"name": "doc.pdf", "url": "http://example.com/doc.pdf"}

    def test_parse_multiple_attachments(self):
        """Test parsing multiple attachments."""
        json_str = '[{"name": "doc1.pdf", "url": "http://example.com/doc1.pdf"}, {"name": "doc2.pdf", "url": "http://example.com/doc2.pdf"}]'
        result = parse_attachments_field(json_str)
        assert len(result) == 2

    def test_parse_attachments_non_dict_elements(self):
        """Test parsing attachments with non-dict elements filters them out."""
        json_str = '[{"name": "doc.pdf", "url": "http://example.com/doc.pdf"}, "not a dict", 123]'
        result = parse_attachments_field(json_str)
        assert len(result) == 1
        assert result[0]["name"] == "doc.pdf"

    def test_parse_attachments_missing_name(self):
        """Test parsing attachments missing name field filters them out."""
        json_str = '[{"url": "http://example.com/doc.pdf"}]'
        result = parse_attachments_field(json_str)
        assert result == []

    def test_parse_attachments_missing_url(self):
        """Test parsing attachments missing url field filters them out."""
        json_str = '[{"name": "doc.pdf"}]'
        result = parse_attachments_field(json_str)
        assert result == []

    def test_parse_attachments_empty_name_or_url(self):
        """Test parsing attachments with empty name or url filters them out."""
        json_str = '[{"name": "", "url": "http://example.com/doc.pdf"}, {"name": "doc.pdf", "url": ""}]'
        result = parse_attachments_field(json_str)
        assert result == []

    def test_parse_attachments_non_array(self):
        """Test parsing non-array JSON returns empty list."""
        result = parse_attachments_field('{"not": "array"}')
        assert result == []

    def test_parse_attachments_invalid_json(self):
        """Test parsing invalid JSON returns empty list."""
        result = parse_attachments_field('not valid json')
        assert result == []
