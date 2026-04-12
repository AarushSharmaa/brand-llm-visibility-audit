"""
Tests for ui/components.py — pure render-helper functions only.
No Streamlit calls (those require a live session). Tests cover all
functions that return strings or do pure computation.
"""

import pytest
from ui.components import score_color, score_class, sentiment_html, claims_html


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
