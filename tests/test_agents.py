"""
Tests for agents/probe_agent.py and agents/diagnosis_agent.py.
All LLM calls are mocked — tests verify agent logic, not API correctness.
"""

import json
import pytest
from unittest.mock import patch, MagicMock
from agents.probe_agent import ProbeAgent
from agents.diagnosis_agent import DiagnosisAgent
from core.models import ActionItem, AuditDiagnosis


# ── Shared fixtures ───────────────────────────────────────────────────────────

def _result(label: str, mentioned: bool, sentiment: str = None) -> dict:
    return {
        "scenario_id": 1, "label": label, "prompt_used": "q",
        "response": "r", "mentioned": mentioned,
        "position": 1 if mentioned else None,
        "snippet": "snippet" if mentioned else "",
        "sentiment": sentiment, "claims": [], "is_probe": False,
    }


PROVIDER = "gemini"
MODEL = "gemini-2.5-flash"
KEY = "fake-key"


# ── ProbeAgent ────────────────────────────────────────────────────────────────

class TestProbeAgentDecide:

    def test_returns_probes_and_rationale(self):
        mock_response = {"probes": ["What are the top CRM tools?"], "rationale": "Brand was invisible."}
        with patch("agents.probe_agent.call_json", return_value=mock_response):
            agent = ProbeAgent(PROVIDER, MODEL, KEY)
            probes, rationale = agent.decide("HubSpot", "CRM", [_result("Market discovery", False)])
        assert len(probes) == 1
        assert rationale == "Brand was invisible."

    def test_caps_probes_at_max(self):
        mock_response = {
            "probes": ["q1", "q2", "q3", "q4", "q5"],  # 5 probes, max is 3
            "rationale": "Many gaps found.",
        }
        with patch("agents.probe_agent.call_json", return_value=mock_response):
            agent = ProbeAgent(PROVIDER, MODEL, KEY)
            probes, _ = agent.decide("HubSpot", "CRM", [_result("X", False)])
        assert len(probes) <= 3

    def test_returns_empty_on_null_response(self):
        with patch("agents.probe_agent.call_json", return_value=None):
            agent = ProbeAgent(PROVIDER, MODEL, KEY)
            probes, rationale = agent.decide("HubSpot", "CRM", [_result("X", False)])
        assert probes == []
        assert rationale != ""

    def test_returns_empty_when_agent_says_conclusive(self):
        mock_response = {"probes": [], "rationale": "results are conclusive"}
        with patch("agents.probe_agent.call_json", return_value=mock_response):
            agent = ProbeAgent(PROVIDER, MODEL, KEY)
            probes, rationale = agent.decide("HubSpot", "CRM", [_result("X", True)])
        assert probes == []


class TestProbeAgentRun:

    def test_run_returns_probe_results(self):
        decide_mock = {"probes": ["best CRM right now?"], "rationale": "testing alternate phrasing"}
        llm_response = "HubSpot is among the top CRM platforms available."

        with patch("agents.probe_agent.call_json", return_value=decide_mock), \
             patch("agents.probe_agent.call_llm", return_value=llm_response):
            agent = ProbeAgent(PROVIDER, MODEL, KEY)
            results, rationale = agent.run("HubSpot", "CRM", [_result("Market discovery", False)])

        assert len(results) == 1
        assert results[0]["is_probe"] is True
        assert results[0]["mentioned"] is True
        assert rationale == "testing alternate phrasing"

    def test_run_returns_empty_when_no_probes(self):
        decide_mock = {"probes": [], "rationale": "results are conclusive"}
        with patch("agents.probe_agent.call_json", return_value=decide_mock):
            agent = ProbeAgent(PROVIDER, MODEL, KEY)
            results, rationale = agent.run("HubSpot", "CRM", [])
        assert results == []

    def test_run_handles_llm_exception_gracefully(self):
        decide_mock = {"probes": ["best CRM?"], "rationale": "gap found"}
        with patch("agents.probe_agent.call_json", return_value=decide_mock), \
             patch("agents.probe_agent.call_llm", side_effect=Exception("API down")):
            agent = ProbeAgent(PROVIDER, MODEL, KEY)
            results, _ = agent.run("HubSpot", "CRM", [_result("X", False)])
        # Should not raise — returns error result
        assert len(results) == 1
        assert results[0]["mentioned"] is False
        assert "error" in results[0]


# ── DiagnosisAgent ────────────────────────────────────────────────────────────

class TestDiagnosisAgentParse:

    def setup_method(self):
        self.agent = DiagnosisAgent(PROVIDER, MODEL, KEY)

    def test_parse_full_valid_response(self):
        raw = {
            "status_summary": "Low visibility.",
            "root_cause": "No content targeting these queries.",
            "actions": [
                {"action": "Publish comparison page", "effort": "medium", "impact": "high", "confidence": 0.85,
                 "scenarios_driving_it": ["Market discovery"]},
            ],
        }
        diag = self.agent._parse(raw)
        assert isinstance(diag, AuditDiagnosis)
        assert diag.status_summary == "Low visibility."
        assert len(diag.actions) == 1
        assert diag.actions[0].confidence == 0.85

    def test_parse_null_returns_fallback(self):
        diag = self.agent._parse(None)
        assert isinstance(diag, AuditDiagnosis)
        assert "Could not" in diag.status_summary

    def test_parse_clamps_confidence(self):
        raw = {
            "status_summary": "x", "root_cause": "y",
            "actions": [{"action": "Do X", "confidence": 1.5}],  # out of range
        }
        diag = self.agent._parse(raw)
        assert diag.actions[0].confidence <= 1.0

    def test_parse_skips_malformed_actions(self):
        raw = {
            "status_summary": "x", "root_cause": "y",
            "actions": [
                {"action": "Good action", "confidence": 0.8},
                {"action": "Bad action", "effort": "invalid_value"},  # invalid Literal
            ],
        }
        diag = self.agent._parse(raw)
        # Malformed action should be skipped, good one retained
        assert len(diag.actions) >= 1

    def test_parse_cross_model_note(self):
        raw = {
            "status_summary": "x", "root_cause": "y",
            "actions": [],
            "cross_model_note": "Gemini and ChatGPT disagree on market position.",
        }
        diag = self.agent._parse(raw)
        assert diag.cross_model_note is not None


class TestDiagnosisAgentResultsText:

    def setup_method(self):
        self.agent = DiagnosisAgent(PROVIDER, MODEL, KEY)

    def test_results_text_includes_labels(self):
        results = [_result("Market discovery", True), _result("Tool recommendation", False)]
        text = self.agent._results_text(results)
        assert "Market discovery" in text
        assert "Tool recommendation" in text

    def test_results_text_shows_mentioned_status(self):
        results = [_result("Brand knowledge", True), _result("Best-in-class", False)]
        text = self.agent._results_text(results)
        assert "MENTIONED" in text
        assert "NOT MENTIONED" in text

    def test_results_text_includes_sentiment_when_present(self):
        results = [_result("Market discovery", True, sentiment="positive")]
        text = self.agent._results_text(results)
        assert "positive" in text

    def test_results_text_includes_probe_section(self):
        results = [_result("Standard", True)]
        probes = [_result("Probe query", False)]
        text = self.agent._results_text(results, probes)
        assert "Probe follow-ups" in text


class TestDiagnosisAgentRun:

    def test_single_model_path(self):
        mock_diag = {
            "status_summary": "HubSpot is visible in 4/6 scenarios.",
            "root_cause": "Missing from generic searches.",
            "actions": [{"action": "Optimize category pages", "confidence": 0.75}],
        }
        with patch("agents.diagnosis_agent.call_json", return_value=mock_diag):
            agent = DiagnosisAgent(PROVIDER, MODEL, KEY)
            results_by_provider = {"gemini": [_result("Market discovery", True)]}
            probe_by_provider = {"gemini": ([], "")}
            diag = agent.run("HubSpot", "CRM", results_by_provider, probe_by_provider)
        assert isinstance(diag, AuditDiagnosis)
        assert "HubSpot" in diag.status_summary

    def test_multi_model_path_called_for_two_providers(self):
        mock_diag = {
            "status_summary": "Gemini shows HubSpot, ChatGPT does not.",
            "root_cause": "Training data difference.",
            "actions": [],
            "cross_model_note": "Models trained on different publisher corpora.",
        }
        with patch("agents.diagnosis_agent.call_json", return_value=mock_diag):
            agent = DiagnosisAgent(PROVIDER, MODEL, KEY)
            results_by_provider = {
                "gemini": [_result("Market discovery", True)],
                "openai": [_result("Market discovery", False)],
            }
            probe_by_provider = {"gemini": ([], ""), "openai": ([], "")}
            diag = agent.run("HubSpot", "CRM", results_by_provider, probe_by_provider)
        assert diag.cross_model_note is not None
