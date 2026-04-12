"""
Tests for ui/components.py — pure render-helper functions and HTML-generating
render functions (st.markdown mocked so no Streamlit session required).
"""

import pytest
from unittest.mock import patch, call
from ui.components import score_color, score_class, sentiment_html, claims_html, render_competitor_score_table


# ── score_color ───────────────────────────────────────────────────────────────

def test_score_color_high():
    assert score_color(100) == "#16a34a"
    assert score_color(67) == "#16a34a"


def test_score_color_mid():
    assert score_color(66) == "#d97706"
    assert score_color(34) == "#d97706"


def test_score_color_low():
    assert score_color(33) == "#dc2626"
    assert score_color(0) == "#dc2626"


def test_score_color_boundary_exactly_67():
    assert score_color(67) == "#16a34a"


def test_score_color_boundary_exactly_34():
    assert score_color(34) == "#d97706"


# ── score_class ───────────────────────────────────────────────────────────────

def test_score_class_high():
    assert score_class(80) == "score-high"
    assert score_class(67) == "score-high"


def test_score_class_mid():
    assert score_class(50) == "score-mid"
    assert score_class(34) == "score-mid"


def test_score_class_low():
    assert score_class(10) == "score-low"
    assert score_class(0) == "score-low"


def test_score_class_returns_string():
    assert isinstance(score_class(50), str)


# ── sentiment_html ────────────────────────────────────────────────────────────

def test_sentiment_html_positive():
    html = sentiment_html("positive")
    assert "sent-positive" in html
    assert "↑" in html
    assert "positive" in html


def test_sentiment_html_negative():
    html = sentiment_html("negative")
    assert "sent-negative" in html
    assert "↓" in html


def test_sentiment_html_neutral():
    html = sentiment_html("neutral")
    assert "sent-neutral" in html
    assert "→" in html


def test_sentiment_html_cautious():
    html = sentiment_html("cautious")
    assert "sent-cautious" in html
    assert "~" in html


def test_sentiment_html_none_returns_empty():
    assert sentiment_html(None) == ""


def test_sentiment_html_unknown_sentiment():
    # Unknown sentiment → icon defaults to "" but should not crash
    html = sentiment_html("unknown_value")
    assert isinstance(html, str)
    assert "sent-unknown_value" in html


# ── claims_html ───────────────────────────────────────────────────────────────

def test_claims_html_basic():
    html = claims_html(["easy to use", "enterprise-ready"])
    assert "easy to use" in html
    assert "enterprise-ready" in html
    assert "claim-pill" in html


def test_claims_html_empty_returns_empty():
    assert claims_html([]) == ""


def test_claims_html_single_claim():
    html = claims_html(["affordable"])
    assert "affordable" in html
    assert "claims-row" in html


def test_claims_html_special_characters():
    html = claims_html(["best-in-class", "50M+ users"])
    assert "best-in-class" in html
    assert "50M+ users" in html


# ── render_competitor_score_table ─────────────────────────────────────────────

def _captured_html(brand, brand_score, brand_mc, brand_total, competitor_rows):
    """Run render_competitor_score_table with st.markdown mocked, return HTML string."""
    with patch("ui.components.st") as mock_st:
        render_competitor_score_table(brand, brand_score, brand_mc, brand_total, competitor_rows)
        assert mock_st.markdown.called
        return mock_st.markdown.call_args[0][0]


def test_competitor_table_contains_brand():
    html = _captured_html("Notion", 67, 4, 6, [{"name": "Obsidian", "score": 50, "mention_count": 3, "total": 6}])
    assert "Notion" in html


def test_competitor_table_contains_competitors():
    html = _captured_html("Notion", 67, 4, 6, [{"name": "Obsidian", "score": 50, "mention_count": 3, "total": 6}])
    assert "Obsidian" in html


def test_competitor_table_shows_you_badge_on_brand():
    html = _captured_html("Notion", 67, 4, 6, [])
    assert "you" in html


def test_competitor_table_shows_scores():
    html = _captured_html("Notion", 67, 4, 6, [{"name": "Obsidian", "score": 83, "mention_count": 5, "total": 6}])
    assert "67%" in html
    assert "83%" in html


def test_competitor_table_shows_mention_counts():
    html = _captured_html("Notion", 67, 4, 6, [{"name": "Obsidian", "score": 83, "mention_count": 5, "total": 6}])
    assert "4 / 6" in html
    assert "5 / 6" in html


def test_competitor_table_sorted_by_score_descending():
    # Competitor has higher score — should appear before brand in the table
    html = _captured_html(
        "Notion", 33, 2, 6,
        [{"name": "Obsidian", "score": 83, "mention_count": 5, "total": 6}],
    )
    obsidian_pos = html.index("Obsidian")
    notion_pos = html.index("Notion")
    assert obsidian_pos < notion_pos


def test_competitor_table_no_competitors():
    # Just the brand, no competitors — should not crash
    html = _captured_html("Notion", 67, 4, 6, [])
    assert "Notion" in html
    assert "you" in html


def test_competitor_table_multiple_competitors():
    rows = [
        {"name": "Obsidian", "score": 83, "mention_count": 5, "total": 6},
        {"name": "Roam", "score": 17, "mention_count": 1, "total": 6},
    ]
    html = _captured_html("Notion", 50, 3, 6, rows)
    assert "Obsidian" in html
    assert "Roam" in html


def test_competitor_table_score_class_applied():
    # High score should get score-high class
    html = _captured_html("Notion", 100, 6, 6, [])
    assert "score-high" in html


def test_competitor_table_zero_score():
    rows = [{"name": "Ghost", "score": 0, "mention_count": 0, "total": 6}]
    html = _captured_html("Notion", 67, 4, 6, rows)
    assert "0%" in html
    assert "score-low" in html
