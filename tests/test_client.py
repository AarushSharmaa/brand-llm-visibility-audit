"""
Tests for llm/client.py — JSON parsing, fence stripping, error handling.
Provider API calls are mocked — no real network calls.
"""

import json
import pytest
from unittest.mock import patch
from llm.client import call_json


# ── call_json JSON cleaning ───────────────────────────────────────────────────

def _mock_call_llm(raw: str):
    """Patch call_llm to return a fixed string."""
    return patch("llm.client.call_llm", return_value=raw)


def test_call_json_clean_json():
    with _mock_call_llm('{"key": "value"}'):
        result = call_json("gemini", "gemini-2.5-flash", "fake-key", "prompt")
    assert result == {"key": "value"}


def test_call_json_strips_markdown_fences():
    raw = "```json\n{\"key\": \"value\"}\n```"
    with _mock_call_llm(raw):
        result = call_json("gemini", "gemini-2.5-flash", "fake-key", "prompt")
    assert result == {"key": "value"}


def test_call_json_strips_plain_code_fences():
    raw = "```\n{\"key\": \"value\"}\n```"
    with _mock_call_llm(raw):
        result = call_json("gemini", "gemini-2.5-flash", "fake-key", "prompt")
    assert result == {"key": "value"}


def test_call_json_returns_list():
    raw = '[{"a": 1}, {"b": 2}]'
    with _mock_call_llm(raw):
        result = call_json("gemini", "gemini-2.5-flash", "fake-key", "prompt")
    assert isinstance(result, list)
    assert len(result) == 2


def test_call_json_returns_none_on_invalid_json():
    with _mock_call_llm("this is not json at all"):
        result = call_json("gemini", "gemini-2.5-flash", "fake-key", "prompt")
    assert result is None


def test_call_json_returns_none_on_exception():
    with patch("llm.client.call_llm", side_effect=Exception("API error")):
        result = call_json("gemini", "gemini-2.5-flash", "fake-key", "prompt")
    assert result is None


def test_call_json_handles_whitespace_around_fences():
    raw = "  ```json\n  {\"x\": 1}\n  ```  "
    with _mock_call_llm(raw):
        result = call_json("gemini", "gemini-2.5-flash", "fake-key", "prompt")
    assert result == {"x": 1}


def test_call_json_nested_json():
    data = {"actions": [{"action": "Write content", "confidence": 0.8}]}
    with _mock_call_llm(json.dumps(data)):
        result = call_json("gemini", "gemini-2.5-flash", "fake-key", "prompt")
    assert result["actions"][0]["confidence"] == 0.8


# ── call_llm provider routing ─────────────────────────────────────────────────

def test_call_llm_unknown_provider_raises():
    from llm.client import call_llm
    with pytest.raises(ValueError, match="Unknown provider"):
        call_llm("unknown_provider", "model", "key", "prompt")
