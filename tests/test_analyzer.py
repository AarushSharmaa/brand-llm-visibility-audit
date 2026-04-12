"""
Tests for agents/analyzer.py — mention detection, SOV counting,
and enrichment (sentiment + claims via LLM).
"""

import pytest
from unittest.mock import patch
from agents.analyzer import detect_mention, count_competitor_mentions, enrich_with_claims


# ── detect_mention ────────────────────────────────────────────────────────────

def test_detect_mention_basic_hit():
    result = detect_mention("Notion is a great tool for notes.", "Notion")
    assert result["mentioned"] is True
    assert result["snippet"] != ""


def test_detect_mention_case_insensitive():
    result = detect_mention("We recommend NOTION for teams.", "Notion")
    assert result["mentioned"] is True


def test_detect_mention_miss():
    result = detect_mention("Try Obsidian or Roam Research.", "Notion")
    assert result["mentioned"] is False
    assert result["position"] is None
    assert result["snippet"] == ""


def test_detect_mention_empty_response():
    result = detect_mention("", "Notion")
    assert result["mentioned"] is False


def test_detect_mention_empty_brand_not_crash():
    result = detect_mention("Any text here", "")
    assert isinstance(result, dict)


def test_detect_mention_extracts_position_from_numbered_list():
    text = "1. Salesforce — enterprise CRM\n2. HubSpot — SMB CRM\n3. Zoho CRM — budget option"
    result = detect_mention(text, "HubSpot")
    assert result["mentioned"] is True
    assert result["position"] == 2


def test_detect_mention_position_none_when_not_in_list():
    text = "HubSpot is a solid marketing platform worth considering."
    result = detect_mention(text, "HubSpot")
    assert result["mentioned"] is True
    assert result["position"] is None


def test_detect_mention_snippet_contains_brand():
    text = "Among the top tools, HubSpot stands out for its ease of use and integrations."
    result = detect_mention(text, "HubSpot")
    assert "HubSpot" in result["snippet"] or "hubspot" in result["snippet"].lower()


def test_detect_mention_snippet_truncation():
    long_text = "x" * 50 + "Notion" + "y" * 200
    result = detect_mention(long_text, "Notion")
    assert result["mentioned"] is True
    assert len(result["snippet"]) < len(long_text)


def test_detect_mention_position_extraction_paren_format():
    text = "1) Salesforce\n2) HubSpot\n3) Pipedrive"
    result = detect_mention(text, "HubSpot")
    assert result["mentioned"] is True
    assert result["position"] == 2


def test_detect_mention_position_large_number():
    text = "\n".join(f"{i}. Brand{i}" for i in range(1, 12))
    text += "\n11. TargetBrand"
    result = detect_mention(text, "TargetBrand")
    assert result["mentioned"] is True
    assert result["position"] == 11


def test_detect_mention_brand_at_start_of_text():
    result = detect_mention("Notion is the best productivity tool.", "Notion")
    assert result["mentioned"] is True
    # No leading ellipsis since brand is near start
    assert not result["snippet"].startswith("...")


def test_detect_mention_brand_with_alphanumeric_name():
    """Brand names like 'n8n' (no special regex chars) should work fine."""
    result = detect_mention("I recommend n8n for workflow automation.", "n8n")
    assert result["mentioned"] is True


def test_detect_mention_returns_correct_keys():
    result = detect_mention("Some text", "SomeBrand")
    assert "mentioned" in result
    assert "position" in result
    assert "snippet" in result


def test_detect_mention_none_response_handled():
    # None text should not crash — empty text path
    result = detect_mention("", "Notion")
    assert result["mentioned"] is False
    assert result["snippet"] == ""


# ── count_competitor_mentions ─────────────────────────────────────────────────

def test_count_competitor_basic():
    responses = [
        "Notion is great for teams.",
        "I prefer Obsidian over Notion.",
        "No mention of anything relevant.",
    ]
    assert count_competitor_mentions(responses, "Notion") == 2


def test_count_competitor_case_insensitive():
    responses = ["NOTION is the best", "notion wins"]
    assert count_competitor_mentions(responses, "Notion") == 2


def test_count_competitor_none():
    responses = ["Obsidian", "Roam", "Logseq"]
    assert count_competitor_mentions(responses, "Notion") == 0


def test_count_competitor_empty_responses():
    assert count_competitor_mentions([], "Notion") == 0


def test_count_competitor_one_response_per_count():
    # Even if a brand appears 5 times in one response, it counts as 1
    responses = ["Notion Notion Notion Notion Notion"]
    assert count_competitor_mentions(responses, "Notion") == 1


# ── enrich_with_claims ────────────────────────────────────────────────────────

def _result(label: str, mentioned: bool) -> dict:
    return {
        "scenario_id": 1, "label": label, "prompt_used": "q",
        "response": f"Response mentioning {label}." if mentioned else "No mention.",
        "mentioned": mentioned, "position": None, "snippet": "",
        "sentiment": None, "claims": [], "is_probe": False,
    }


def test_enrich_with_claims_adds_sentiment_and_claims():
    results = [_result("Market discovery", True)]
    mock_response = [{"scenario": "Market discovery", "sentiment": "positive", "claims": ["easy to use"]}]
    with patch("agents.analyzer.call_json", return_value=mock_response):
        out = enrich_with_claims("groq", "model", "key", "Notion", results)
    assert out[0]["sentiment"] == "positive"
    assert "easy to use" in out[0]["claims"]


def test_enrich_with_claims_returns_unchanged_when_none_mentioned():
    results = [_result("Market discovery", False), _result("Tool recommendation", False)]
    with patch("agents.analyzer.call_json") as mock_cj:
        out = enrich_with_claims("groq", "model", "key", "Notion", results)
    mock_cj.assert_not_called()
    assert out[0]["sentiment"] is None
    assert out[1]["sentiment"] is None


def test_enrich_with_claims_handles_null_from_call_json():
    results = [_result("Market discovery", True)]
    with patch("agents.analyzer.call_json", return_value=None):
        out = enrich_with_claims("groq", "model", "key", "Notion", results)
    assert out[0]["sentiment"] is None  # unchanged


def test_enrich_with_claims_handles_non_list_response():
    results = [_result("Market discovery", True)]
    with patch("agents.analyzer.call_json", return_value={"error": "bad format"}):
        out = enrich_with_claims("groq", "model", "key", "Notion", results)
    assert out[0]["sentiment"] is None  # non-list response silently ignored


def test_enrich_with_claims_limits_claims_to_5():
    results = [_result("Market discovery", True)]
    mock_response = [{
        "scenario": "Market discovery",
        "sentiment": "positive",
        "claims": ["c1", "c2", "c3", "c4", "c5", "c6", "c7"],  # 7 claims
    }]
    with patch("agents.analyzer.call_json", return_value=mock_response):
        out = enrich_with_claims("groq", "model", "key", "Notion", results)
    assert len(out[0]["claims"]) <= 5


def test_enrich_with_claims_only_enriches_mentioned_results():
    results = [_result("Market discovery", True), _result("Tool recommendation", False)]
    mock_response = [
        {"scenario": "Market discovery", "sentiment": "positive", "claims": ["great"]},
    ]
    with patch("agents.analyzer.call_json", return_value=mock_response):
        out = enrich_with_claims("groq", "model", "key", "Notion", results)
    assert out[0]["sentiment"] == "positive"
    assert out[1]["sentiment"] is None  # not mentioned → untouched


def test_enrich_with_claims_unmatched_label_leaves_result_unchanged():
    results = [_result("Market discovery", True)]
    mock_response = [
        {"scenario": "Different label", "sentiment": "negative", "claims": ["bad"]},
    ]
    with patch("agents.analyzer.call_json", return_value=mock_response):
        out = enrich_with_claims("groq", "model", "key", "Notion", results)
    assert out[0]["sentiment"] is None  # no match, unchanged


def test_enrich_with_claims_multiple_scenarios():
    results = [
        _result("Market discovery", True),
        _result("Tool recommendation", True),
        _result("Brand knowledge", False),
    ]
    mock_response = [
        {"scenario": "Market discovery", "sentiment": "positive", "claims": ["affordable"]},
        {"scenario": "Tool recommendation", "sentiment": "neutral", "claims": ["solid"]},
    ]
    with patch("agents.analyzer.call_json", return_value=mock_response):
        out = enrich_with_claims("groq", "model", "key", "Notion", results)
    assert out[0]["sentiment"] == "positive"
    assert out[1]["sentiment"] == "neutral"
    assert out[2]["sentiment"] is None


def test_enrich_with_claims_prompt_includes_brand():
    results = [_result("Market discovery", True)]
    with patch("agents.analyzer.call_json", return_value=[]) as mock_cj:
        enrich_with_claims("groq", "model", "key", "HubSpot", results)
    prompt_used = mock_cj.call_args[0][3]
    assert "HubSpot" in prompt_used


def test_enrich_with_claims_returns_list():
    results = [_result("Market discovery", True)]
    with patch("agents.analyzer.call_json", return_value=[]):
        out = enrich_with_claims("groq", "model", "key", "Notion", results)
    assert isinstance(out, list)
