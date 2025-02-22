"""Tests for specification parsers."""

import pytest

from aica.core.parsers import parse_markdown_list, parse_markdown_spec, parse_spec_file


def test_parse_markdown_list():
    """Test parsing markdown lists."""
    markdown = [
        "- Simple item",
        "- **Key** Value",
        "- **List** with items",
        "  - Item 1",
        "  - Item 2",
        "- Another item"
    ]
    
    expected = [
        "Simple item",
        {"key": "Value"},
        {"list": ["Item 1", "Item 2"]},
        "Another item"
    ]
    
    assert parse_markdown_list(markdown) == expected


def test_parse_markdown_spec():
    """Test parsing a complete markdown spec."""
    markdown = """# Project Title

## Section One
- **Key1** Value1
- **Key2** Value2
  - Nested1
  - Nested2

## Section Two
- Simple item
- **List** Items
  - Item1
  - Item2
"""
    
    expected = {
        "section_one": [
            {"key1": "Value1"},
            {"key2": ["Nested1", "Nested2"]}
        ],
        "section_two": [
            "Simple item",
            {"list": ["Item1", "Item2"]}
        ]
    }
    
    assert parse_markdown_spec(markdown) == expected


def test_parse_spec_file_yaml():
    """Test parsing YAML spec files."""
    yaml_content = """
section_one:
  - key1: value1
  - key2:
    - nested1
    - nested2
"""
    
    expected = {
        "section_one": [
            {"key1": "value1"},
            {"key2": ["nested1", "nested2"]}
        ]
    }
    
    assert parse_spec_file(yaml_content, "yaml") == expected


def test_parse_spec_file_markdown():
    """Test parsing Markdown spec files."""
    markdown = """# Title

## Section
- **Key** Value
- Simple item
"""
    
    expected = {
        "section": [
            {"key": "Value"},
            "Simple item"
        ]
    }
    
    assert parse_spec_file(markdown, "markdown") == expected


def test_parse_spec_file_invalid_format():
    """Test handling invalid format."""
    with pytest.raises(ValueError, match="Unsupported format"):
        parse_spec_file("content", "invalid")
