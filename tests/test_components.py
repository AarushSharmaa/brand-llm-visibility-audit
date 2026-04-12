"""
Tests for ui/components.py — pure render-helper functions and HTML-generating
render functions (st.markdown mocked so no Streamlit session required).
"""

import pytest
from unittest.mock import patch, call
from ui.components import (
    score_color, score_class, sentiment_html, claims_html,
    render_competitor_score_table, render_scenario_card,
    render_probe_box, render_playbook,
)
from core.models import GEOPlaybook, ContentBrief


# ── Helpers ───────────────────────────────────────────────────────────────────

def _all_html(fn, *args, **kwargs) -> str:
    """Call a render function with st mocked; return all HTML passed to st.markdown joined."""
    with patch("ui.components.st") as mock_st:
        fn(*args, **kwargs)
        return " ".join(
            c[0][0]
            for c in mock_st.markdown.call_args_list
            if c[0]
        )


def _scenario_result(
    label="Market discovery", mentioned=True, position=2,
    snippet="Notion is #2 on the list.", sentiment="positive",
    claims=None, is_probe=False,
) -> dict:
    return {
        "label": label, "mentioned": mentioned, "position": position,
        "snippet": snippet, "sentiment": sentiment,
        "claims": claims or [], "is_probe": is_probe,
    }


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
    html = _captured_html(
        "Notion", 33, 2, 6,
        [{"name": "Obsidian", "score": 83, "mention_count": 5, "total": 6}],
    )
    obsidian_pos = html.index("Obsidian")
    notion_pos = html.index("Notion")
    assert obsidian_pos < notion_pos


def test_competitor_table_no_competitors():
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
    html = _captured_html("Notion", 100, 6, 6, [])
    assert "score-high" in html


def test_competitor_table_zero_score():
    rows = [{"name": "Ghost", "score": 0, "mention_count": 0, "total": 6}]
    html = _captured_html("Notion", 67, 4, 6, rows)
    assert "0%" in html
    assert "score-low" in html


# ── render_scenario_card ──────────────────────────────────────────────────────

def test_scenario_card_hit_has_hit_class():
    html = _all_html(render_scenario_card, _scenario_result(mentioned=True))
    assert "result-card-hit" in html


def test_scenario_card_miss_has_miss_class():
    html = _all_html(render_scenario_card, _scenario_result(
        mentioned=False, position=None, snippet="", sentiment=None
    ))
    assert "result-card-miss" in html


def test_scenario_card_probe_has_probe_class():
    html = _all_html(render_scenario_card, _scenario_result(is_probe=True))
    assert "result-card-probe" in html
    assert "Probe" in html


def test_scenario_card_shows_label():
    html = _all_html(render_scenario_card, _scenario_result(label="Vendor comparison"))
    assert "Vendor comparison" in html


def test_scenario_card_shows_snippet():
    html = _all_html(render_scenario_card, _scenario_result(snippet="Notion is ranked #2."))
    assert "Notion is ranked #2." in html


def test_scenario_card_shows_tag_mentioned_with_position():
    html = _all_html(render_scenario_card, _scenario_result(mentioned=True, position=3))
    assert "#3" in html


def test_scenario_card_shows_tag_not_mentioned():
    html = _all_html(render_scenario_card, _scenario_result(
        mentioned=False, position=None, snippet="", sentiment=None
    ))
    assert "Not mentioned" in html


def test_scenario_card_shows_sentiment_when_mentioned():
    html = _all_html(render_scenario_card, _scenario_result(mentioned=True, sentiment="positive"))
    assert "positive" in html


def test_scenario_card_no_sentiment_on_miss():
    r = _scenario_result(mentioned=False, position=None, snippet="", sentiment="positive")
    html = _all_html(render_scenario_card, r)
    # sentiment should not be shown for a miss
    assert "sent-positive" not in html


def test_scenario_card_shows_claims_when_mentioned():
    r = _scenario_result(mentioned=True, claims=["affordable", "easy setup"])
    html = _all_html(render_scenario_card, r)
    assert "affordable" in html
    assert "easy setup" in html


def test_scenario_card_no_snippet_shows_fallback():
    r = _scenario_result(mentioned=False, position=None, snippet="", sentiment=None)
    html = _all_html(render_scenario_card, r)
    assert "Brand not found" in html


def test_scenario_card_multi_model_dots():
    r = _scenario_result(mentioned=True)
    model_dots = [("gemini", True), ("openai", False)]
    html = _all_html(render_scenario_card, r, model_dots=model_dots)
    assert "dot-hit" in html
    assert "dot-miss" in html


def test_scenario_card_single_model_dot_not_shown():
    """With only 1 model, dots section should not render."""
    r = _scenario_result(mentioned=True)
    model_dots = [("gemini", True)]
    html = _all_html(render_scenario_card, r, model_dots=model_dots)
    assert "dot-hit" not in html


# ── render_probe_box ──────────────────────────────────────────────────────────

def test_probe_box_shows_rationale():
    html = _all_html(render_probe_box, "The brand was invisible in generic queries.", 2)
    assert "invisible" in html


def test_probe_box_empty_rationale_returns_without_render():
    with patch("ui.components.st") as mock_st:
        render_probe_box("", 2)
    mock_st.markdown.assert_not_called()


def test_probe_box_none_rationale_returns_without_render():
    with patch("ui.components.st") as mock_st:
        render_probe_box(None, 2)
    mock_st.markdown.assert_not_called()


def test_probe_box_plural_probes():
    html = _all_html(render_probe_box, "Found gaps.", 3)
    assert "3" in html
    assert "probes" in html


def test_probe_box_singular_probe():
    html = _all_html(render_probe_box, "Found gap.", 1)
    assert "1" in html
    assert "probe" in html


def test_probe_box_zero_probes():
    html = _all_html(render_probe_box, "No follow-up needed.", 0)
    assert "No follow-up probes needed" in html


def test_probe_box_shows_agent_label():
    html = _all_html(render_probe_box, "Some rationale.", 1)
    assert "Probe agent" in html


# ── render_playbook ───────────────────────────────────────────────────────────

def _playbook(**kwargs) -> GEOPlaybook:
    defaults = dict(
        brand="Notion",
        category="productivity software",
        executive_summary="Notion is invisible in generic searches. Publishing comparison content will close the gap.",
        briefs=[
            ContentBrief(
                title="Notion vs Obsidian: Complete 2026 Comparison for Teams",
                content_type="comparison page",
                target_queries=["best note-taking app for teams?", "Notion vs Obsidian 2026"],
                word_count=1400,
                outline=["What each tool does best", "Feature comparison", "Pricing", "Verdict"],
                competitors_to_reference=["Obsidian"],
                priority="this week",
                why_this_matters="Notion is absent from head-to-head queries where buyers decide.",
            )
        ],
        quick_wins=["Add /llms.txt to notion.so", "Update homepage meta description"],
        estimated_timeline="4-6 weeks to see initial improvement",
    )
    defaults.update(kwargs)
    return GEOPlaybook(**defaults)


def test_render_playbook_shows_executive_summary():
    html = _all_html(render_playbook, _playbook())
    assert "invisible in generic searches" in html


def test_render_playbook_empty_executive_summary_returns_early():
    pb = _playbook(executive_summary="")
    with patch("ui.components.st") as mock_st:
        render_playbook(pb)
    mock_st.markdown.assert_not_called()


def test_render_playbook_shows_quick_wins():
    html = _all_html(render_playbook, _playbook())
    assert "Add /llms.txt" in html
    assert "Update homepage meta description" in html


def test_render_playbook_no_quick_wins_no_quick_wins_section():
    html = _all_html(render_playbook, _playbook(quick_wins=[]))
    assert "Quick wins" not in html


def test_render_playbook_shows_brief_title():
    html = _all_html(render_playbook, _playbook())
    assert "Notion vs Obsidian: Complete 2026 Comparison for Teams" in html


def test_render_playbook_shows_content_type_badge():
    html = _all_html(render_playbook, _playbook())
    assert "comparison page" in html


def test_render_playbook_shows_priority_badge():
    html = _all_html(render_playbook, _playbook())
    assert "this week" in html


def test_render_playbook_shows_target_queries():
    html = _all_html(render_playbook, _playbook())
    assert "best note-taking app for teams?" in html
    assert "Notion vs Obsidian 2026" in html


def test_render_playbook_shows_outline_items():
    html = _all_html(render_playbook, _playbook())
    assert "Feature comparison" in html
    assert "Pricing" in html


def test_render_playbook_shows_word_count():
    html = _all_html(render_playbook, _playbook())
    assert "1,400" in html or "1400" in html


def test_render_playbook_shows_competitors_to_reference():
    html = _all_html(render_playbook, _playbook())
    assert "Obsidian" in html


def test_render_playbook_shows_why_it_matters():
    html = _all_html(render_playbook, _playbook())
    assert "head-to-head queries" in html


def test_render_playbook_shows_timeline():
    html = _all_html(render_playbook, _playbook())
    assert "4-6 weeks" in html


def test_render_playbook_no_briefs_no_brief_cards():
    html = _all_html(render_playbook, _playbook(briefs=[]))
    assert "brief-card" not in html


def test_render_playbook_no_briefs_still_shows_summary():
    html = _all_html(render_playbook, _playbook(briefs=[]))
    assert "invisible in generic searches" in html


def test_render_playbook_month_priority_badge():
    pb = _playbook(briefs=[
        ContentBrief(title="X", priority="this month")
    ])
    html = _all_html(render_playbook, pb)
    assert "this month" in html


def test_render_playbook_quarter_priority_badge():
    pb = _playbook(briefs=[
        ContentBrief(title="X", priority="next quarter")
    ])
    html = _all_html(render_playbook, pb)
    assert "next quarter" in html


def test_render_playbook_multiple_briefs():
    pb = _playbook(briefs=[
        ContentBrief(title="Brief One", content_type="how-to guide"),
        ContentBrief(title="Brief Two", content_type="listicle"),
    ])
    html = _all_html(render_playbook, pb)
    assert "Brief One" in html
    assert "Brief Two" in html


def test_render_playbook_no_timeline_no_timeline_text():
    pb = _playbook(estimated_timeline="")
    html = _all_html(render_playbook, pb)
    assert "Timeline:" not in html
