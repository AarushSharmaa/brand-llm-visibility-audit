"""
Tests for llm/client.py — JSON parsing, fence stripping, provider routing,
and API call shape verification for every supported provider.
All provider SDK calls are mocked — no real network calls.
"""

import json
import sys
import pytest
from unittest.mock import patch, MagicMock, call
from llm.client import call_json, call_llm


# ── Helpers ───────────────────────────────────────────────────────────────────

def _mock_call_llm(raw: str):
    return patch("llm.client.call_llm", return_value=raw)


# ── call_json: JSON cleaning ──────────────────────────────────────────────────

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


def test_call_json_empty_object_is_valid():
    with _mock_call_llm("{}"):
        result = call_json("groq", "llama-3.3-70b-versatile", "key", "prompt")
    assert result == {}


def test_call_json_empty_array_is_valid():
    with _mock_call_llm("[]"):
        result = call_json("groq", "llama-3.3-70b-versatile", "key", "prompt")
    assert result == []


def test_call_json_appends_json_instruction_to_prompt():
    """call_json must append the JSON instruction — missing it causes LLMs to return prose."""
    with patch("llm.client.call_llm", return_value="{}") as mock_call:
        call_json("groq", "model", "key", "my original prompt")
    prompt_sent = mock_call.call_args[0][3]
    assert "my original prompt" in prompt_sent
    assert "Return ONLY valid JSON" in prompt_sent


def test_call_json_uses_json_system_prompt():
    """call_json should send a system prompt that reinforces JSON-only output."""
    with patch("llm.client.call_llm", return_value="{}") as mock_call:
        call_json("groq", "model", "key", "prompt")
    # system is passed as a keyword argument
    system_sent = mock_call.call_args[1]["system"]
    assert "JSON" in system_sent


# ── call_llm: unknown provider ────────────────────────────────────────────────

def test_call_llm_unknown_provider_raises():
    with pytest.raises(ValueError, match="Unknown provider"):
        call_llm("unknown_provider", "model", "key", "prompt")


# ── call_llm: Groq — API shape ────────────────────────────────────────────────

def _groq_mock():
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "groq response"
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response
    return mock_client


def test_call_llm_groq_returns_content():
    mock_client = _groq_mock()
    with patch("groq.Groq", return_value=mock_client):
        result = call_llm("groq", "llama-3.3-70b-versatile", "gsk_test", "hello")
    assert result == "groq response"


def test_call_llm_groq_passes_api_key():
    mock_client = _groq_mock()
    with patch("groq.Groq", return_value=mock_client) as mock_cls:
        call_llm("groq", "llama-3.3-70b-versatile", "gsk_test", "hello")
    mock_cls.assert_called_once_with(api_key="gsk_test")


def test_call_llm_groq_passes_model_name():
    mock_client = _groq_mock()
    with patch("groq.Groq", return_value=mock_client):
        call_llm("groq", "llama-3.3-70b-versatile", "key", "hello")
    call_kwargs = mock_client.chat.completions.create.call_args[1]
    assert call_kwargs["model"] == "llama-3.3-70b-versatile"


def test_call_llm_groq_messages_include_system_and_user():
    """Groq uses OpenAI-compatible chat format — system role must be first."""
    mock_client = _groq_mock()
    with patch("groq.Groq", return_value=mock_client):
        call_llm("groq", "llama-3.3-70b-versatile", "key", "user prompt", "sys prompt")
    messages = mock_client.chat.completions.create.call_args[1]["messages"]
    assert messages[0]["role"] == "system"
    assert messages[0]["content"] == "sys prompt"
    assert messages[1]["role"] == "user"
    assert messages[1]["content"] == "user prompt"


def test_call_llm_groq_default_system_prompt_when_empty():
    mock_client = _groq_mock()
    with patch("groq.Groq", return_value=mock_client):
        call_llm("groq", "llama-3.3-70b-versatile", "key", "prompt")  # no system arg
    messages = mock_client.chat.completions.create.call_args[1]["messages"]
    assert messages[0]["role"] == "system"
    assert messages[0]["content"] != ""  # default is applied, not empty string


# ── call_llm: OpenAI — API shape ──────────────────────────────────────────────

def _openai_mock():
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "openai response"
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response
    return mock_client


def test_call_llm_openai_returns_content():
    mock_client = _openai_mock()
    with patch("openai.OpenAI", return_value=mock_client):
        result = call_llm("openai", "gpt-4o-mini", "sk-test", "hello")
    assert result == "openai response"


def test_call_llm_openai_passes_api_key():
    mock_client = _openai_mock()
    with patch("openai.OpenAI", return_value=mock_client) as mock_cls:
        call_llm("openai", "gpt-4o-mini", "sk-test", "hello")
    mock_cls.assert_called_once_with(api_key="sk-test")


def test_call_llm_openai_messages_format():
    mock_client = _openai_mock()
    with patch("openai.OpenAI", return_value=mock_client):
        call_llm("openai", "gpt-4o-mini", "key", "user msg", "system msg")
    messages = mock_client.chat.completions.create.call_args[1]["messages"]
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"


# ── call_llm: Perplexity — must use OpenAI with base_url ─────────────────────

def test_call_llm_perplexity_uses_perplexity_base_url():
    """Critical: Perplexity requires base_url — wrong or missing = silent failure."""
    mock_client = _openai_mock()
    with patch("openai.OpenAI", return_value=mock_client) as mock_cls:
        call_llm("perplexity", "sonar", "pplx-test", "prompt")
    _, kwargs = mock_cls.call_args
    assert kwargs.get("base_url") == "https://api.perplexity.ai"


def test_call_llm_perplexity_passes_api_key():
    mock_client = _openai_mock()
    with patch("openai.OpenAI", return_value=mock_client) as mock_cls:
        call_llm("perplexity", "sonar", "pplx-key", "prompt")
    _, kwargs = mock_cls.call_args
    assert kwargs.get("api_key") == "pplx-key"


def test_call_llm_perplexity_returns_content():
    mock_client = _openai_mock()
    with patch("openai.OpenAI", return_value=mock_client):
        result = call_llm("perplexity", "sonar", "pplx-test", "prompt")
    assert result == "openai response"


# ── call_llm: Anthropic — API shape ──────────────────────────────────────────

def _anthropic_mock():
    mock_response = MagicMock()
    mock_response.content[0].text = "anthropic response"
    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response
    return mock_client


def test_call_llm_anthropic_returns_content():
    mock_client = _anthropic_mock()
    with patch("anthropic.Anthropic", return_value=mock_client):
        result = call_llm("anthropic", "claude-haiku-4-5-20251001", "sk-ant-test", "prompt")
    assert result == "anthropic response"


def test_call_llm_anthropic_passes_api_key():
    mock_client = _anthropic_mock()
    with patch("anthropic.Anthropic", return_value=mock_client) as mock_cls:
        call_llm("anthropic", "claude-haiku-4-5-20251001", "sk-ant-key", "prompt")
    mock_cls.assert_called_once_with(api_key="sk-ant-key")


def test_call_llm_anthropic_system_is_top_level_param():
    """Anthropic API: system must be a top-level param, NOT inside messages array."""
    mock_client = _anthropic_mock()
    with patch("anthropic.Anthropic", return_value=mock_client):
        call_llm("anthropic", "claude-haiku-4-5-20251001", "key", "user msg", "system msg")
    kwargs = mock_client.messages.create.call_args[1]
    assert kwargs["system"] == "system msg"
    # system must NOT appear in the messages array
    for msg in kwargs["messages"]:
        assert msg["role"] != "system"


def test_call_llm_anthropic_messages_only_user_role():
    """Anthropic messages array should only contain user-role messages."""
    mock_client = _anthropic_mock()
    with patch("anthropic.Anthropic", return_value=mock_client):
        call_llm("anthropic", "claude-haiku-4-5-20251001", "key", "user prompt")
    kwargs = mock_client.messages.create.call_args[1]
    assert len(kwargs["messages"]) == 1
    assert kwargs["messages"][0]["role"] == "user"
    assert kwargs["messages"][0]["content"] == "user prompt"


def test_call_llm_anthropic_max_tokens_sufficient_for_json():
    """max_tokens must be >= 2048 — playbook JSON can easily hit 1000+ tokens."""
    mock_client = _anthropic_mock()
    with patch("anthropic.Anthropic", return_value=mock_client):
        call_llm("anthropic", "claude-haiku-4-5-20251001", "key", "prompt")
    kwargs = mock_client.messages.create.call_args[1]
    assert kwargs["max_tokens"] >= 2048


# ── call_llm: Gemini — API shape ──────────────────────────────────────────────

def _gemini_mocks():
    mock_genai = MagicMock()
    mock_types = MagicMock()
    mock_google = MagicMock()
    mock_google.genai = mock_genai

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value.text = "gemini response"
    mock_genai.Client.return_value = mock_client

    return mock_google, mock_genai, mock_types, mock_client


def test_call_llm_gemini_returns_content():
    mock_google, mock_genai, mock_types, mock_client = _gemini_mocks()
    with patch.dict(sys.modules, {
        "google": mock_google,
        "google.genai": mock_genai,
        "google.genai.types": mock_types,
    }):
        result = call_llm("gemini", "gemini-2.5-flash", "AIza-key", "prompt")
    assert result == "gemini response"


def test_call_llm_gemini_passes_api_key():
    mock_google, mock_genai, mock_types, mock_client = _gemini_mocks()
    with patch.dict(sys.modules, {
        "google": mock_google,
        "google.genai": mock_genai,
        "google.genai.types": mock_types,
    }):
        call_llm("gemini", "gemini-2.5-flash", "AIza-key", "prompt")
    mock_genai.Client.assert_called_once_with(api_key="AIza-key")


def test_call_llm_gemini_passes_model_name():
    mock_google, mock_genai, mock_types, mock_client = _gemini_mocks()
    with patch.dict(sys.modules, {
        "google": mock_google,
        "google.genai": mock_genai,
        "google.genai.types": mock_types,
    }):
        call_llm("gemini", "gemini-2.5-flash", "key", "prompt")
    call_kwargs = mock_client.models.generate_content.call_args[1]
    assert call_kwargs["model"] == "gemini-2.5-flash"


def test_call_llm_gemini_system_via_generate_content_config():
    """Gemini uses GenerateContentConfig(system_instruction=...), not messages array."""
    mock_google, mock_genai, mock_types, mock_client = _gemini_mocks()
    with patch.dict(sys.modules, {
        "google": mock_google,
        "google.genai": mock_genai,
        "google.genai.types": mock_types,
    }):
        call_llm("gemini", "gemini-2.5-flash", "key", "prompt", "sys instruction")
    # `from google.genai import types` resolves types as mock_genai.types attribute
    mock_genai.types.GenerateContentConfig.assert_called_once_with(system_instruction="sys instruction")
