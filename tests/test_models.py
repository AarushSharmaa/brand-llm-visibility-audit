"""
Tests for core/models.py — Pydantic model properties and validation.
All pure, no API calls.
"""

import pytest
from core.models import ScenarioResult, ModelAudit, ActionItem, AuditDiagnosis, CompetitorSOV


# ── ScenarioResult ────────────────────────────────────────────────────────────

def make_result(mentioned: bool, position: int = None, is_probe: bool = False) -> dict:
    return dict(
        scenario_id=1, label="Test", prompt_used="q", response="r",
        mentioned=mentioned, position=position, is_probe=is_probe,
    )


def test_scenario_result_defaults():
    r = ScenarioResult(**make_result(False))
    assert r.sentiment is None
    assert r.claims == []
    assert r.is_probe is False


def test_scenario_result_mentioned_with_position():
    r = ScenarioResult(**make_result(True, position=2))
    assert r.mentioned is True
    assert r.position == 2


# ── ModelAudit computed properties ───────────────────────────────────────────

def _sr(mentioned: bool, position: int = None, is_probe: bool = False) -> ScenarioResult:
    return ScenarioResult(**make_result(mentioned, position, is_probe))


def test_model_audit_score_zero():
    audit = ModelAudit(provider="gemini", model_name="gemini-2.5-flash")
    assert audit.score == 0
    assert audit.mention_count == 0
    assert audit.total_scenarios == 0


def test_model_audit_score_full():
    audit = ModelAudit(
        provider="gemini", model_name="gemini-2.5-flash",
        results=[_sr(True), _sr(True), _sr(True)],
    )
    assert audit.score == 100
    assert audit.mention_count == 3


def test_model_audit_score_partial():
    audit = ModelAudit(
        provider="gemini", model_name="gemini-2.5-flash",
        results=[_sr(True), _sr(False), _sr(True), _sr(False)],
    )
    assert audit.score == 50
    assert audit.mention_count == 2


def test_model_audit_includes_probes_in_score():
    audit = ModelAudit(
        provider="gemini", model_name="gemini-2.5-flash",
        results=[_sr(True), _sr(False)],
        probe_results=[_sr(True, is_probe=True)],
    )
    assert audit.total_scenarios == 3
    assert audit.mention_count == 2
    assert audit.score == 67


def test_model_audit_avg_position_none_when_no_positions():
    audit = ModelAudit(
        provider="gemini", model_name="gemini-2.5-flash",
        results=[_sr(True), _sr(True)],  # mentioned but no position extracted
    )
    assert audit.avg_position is None


def test_model_audit_avg_position_computed():
    audit = ModelAudit(
        provider="gemini", model_name="gemini-2.5-flash",
        results=[_sr(True, position=1), _sr(True, position=3)],
    )
    assert audit.avg_position == 2.0


# ── ActionItem ────────────────────────────────────────────────────────────────

def test_action_item_defaults():
    a = ActionItem(action="Publish comparison page")
    assert a.effort == "medium"
    assert a.impact == "medium"
    assert a.confidence == 0.7


def test_action_item_confidence_range():
    a = ActionItem(action="Do something", confidence=0.95)
    assert a.confidence == 0.95


def test_action_item_invalid_effort():
    with pytest.raises(Exception):
        ActionItem(action="X", effort="ultra")


# ── AuditDiagnosis ────────────────────────────────────────────────────────────

def test_audit_diagnosis_empty_actions():
    d = AuditDiagnosis(status_summary="Low visibility.", root_cause="No content.")
    assert d.actions == []
    assert d.cross_model_note is None


def test_audit_diagnosis_with_actions():
    a = ActionItem(action="Write case studies", effort="low", impact="high", confidence=0.85)
    d = AuditDiagnosis(status_summary="OK", root_cause="Gaps", actions=[a])
    assert len(d.actions) == 1
    assert d.actions[0].confidence == 0.85


# ── CompetitorSOV ─────────────────────────────────────────────────────────────

def test_sov_share_pct_basic():
    c = CompetitorSOV(name="Notion", mentions=3, total_responses=10)
    assert c.share_pct == 30.0


def test_sov_share_pct_zero_responses():
    c = CompetitorSOV(name="Notion", mentions=0, total_responses=0)
    assert c.share_pct == 0.0


def test_sov_share_pct_full():
    c = CompetitorSOV(name="Notion", mentions=6, total_responses=6)
    assert c.share_pct == 100.0
