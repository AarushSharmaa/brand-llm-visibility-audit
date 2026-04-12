"""
Tests for agents/analyzer.py — mention detection and SOV counting.
All pure Python, no API calls.
"""

from agents.analyzer import detect_mention, count_competitor_mentions


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
    # Edge: brand is empty string — should not throw
    result = detect_mention("Any text here", "")
    # Empty string is technically always "in" any string, but shouldn't crash
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
    assert result["position"] is None  # not in a numbered list


def test_detect_mention_snippet_contains_brand():
    text = "Among the top tools, HubSpot stands out for its ease of use and integrations."
    result = detect_mention(text, "HubSpot")
    assert "HubSpot" in result["snippet"] or "hubspot" in result["snippet"].lower()


def test_detect_mention_snippet_truncation():
    long_text = "x" * 50 + "Notion" + "y" * 200
    result = detect_mention(long_text, "Notion")
    assert result["mentioned"] is True
    # Snippet should not be the entire text
    assert len(result["snippet"]) < len(long_text)


def test_detect_mention_position_extraction_paren_format():
    text = "1) Salesforce\n2) HubSpot\n3) Pipedrive"
    result = detect_mention(text, "HubSpot")
    assert result["mentioned"] is True
    assert result["position"] == 2


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
