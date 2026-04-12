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


# ── ProbeAgent.decide ─────────────────────────────────────────────────────────

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

    def test_decide_prompt_includes_brand(self):
        with patch("agents.probe_agent.call_json", return_value={"probes": [], "rationale": ""}) as mock_cj:
            agent = ProbeAgent(PROVIDER, MODEL, KEY)
            agent.decide("HubSpot", "CRM", [_result("Market discovery", False)])
        prompt = mock_cj.call_args[0][3]
        assert "HubSpot" in prompt

    def test_decide_prompt_includes_category(self):
        with patch("agents.probe_agent.call_json", return_value={"probes": [], "rationale": ""}) as mock_cj:
            agent = ProbeAgent(PROVIDER, MODEL, KEY)
            agent.decide("HubSpot", "enterprise CRM software", [_result("Market discovery", False)])
        prompt = mock_cj.call_args[0][3]
        assert "enterprise CRM software" in prompt

    def test_decide_prompt_includes_sentiment_in_results_summary(self):
        """Sentiment must appear in the results summary so the agent can reason about it."""
        results = [_result("Market discovery", True, sentiment="negative")]
        with patch("agents.probe_agent.call_json", return_value={"probes": [], "rationale": ""}) as mock_cj:
            agent = ProbeAgent(PROVIDER, MODEL, KEY)
            agent.decide("HubSpot", "CRM", results)
        prompt = mock_cj.call_args[0][3]
        assert "negative" in prompt

    def test_decide_returns_only_up_to_max_probes_constant(self):
        """Verify the cap matches MAX_PROBES (3) — not hardcoded to a different value."""
        from agents.probe_agent import MAX_PROBES
        assert MAX_PROBES == 3
        mock_response = {"probes": ["q1", "q2", "q3", "q4"], "rationale": "many gaps"}
        with patch("agents.probe_agent.call_json", return_value=mock_response):
            agent = ProbeAgent(PROVIDER, MODEL, KEY)
            probes, _ = agent.decide("HubSpot", "CRM", [])
        assert len(probes) == MAX_PROBES


# ── ProbeAgent.run ────────────────────────────────────────────────────────────

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
        assert len(results) == 1
        assert results[0]["mentioned"] is False
        assert "error" in results[0]

    def test_run_probe_label_truncated_at_90_chars(self):
        long_probe = "a" * 120  # 120 chars
        decide_mock = {"probes": [long_probe], "rationale": "testing"}
        with patch("agents.probe_agent.call_json", return_value=decide_mock), \
             patch("agents.probe_agent.call_llm", return_value="no mention here"):
            agent = ProbeAgent(PROVIDER, MODEL, KEY)
            results, _ = agent.run("HubSpot", "CRM", [])
        # label is truncated to 90 + "…"
        assert len(results[0]["label"]) <= 92  # 90 + "…" = 91 chars

    def test_run_probe_error_label_truncated_at_70_chars(self):
        long_probe = "b" * 100
        decide_mock = {"probes": [long_probe], "rationale": "testing"}
        with patch("agents.probe_agent.call_json", return_value=decide_mock), \
             patch("agents.probe_agent.call_llm", side_effect=Exception("fail")):
            agent = ProbeAgent(PROVIDER, MODEL, KEY)
            results, _ = agent.run("HubSpot", "CRM", [])
        assert len(results[0]["label"]) <= 72  # 70 + "…"

    def test_run_probe_result_has_all_required_keys(self):
        decide_mock = {"probes": ["query?"], "rationale": "r"}
        with patch("agents.probe_agent.call_json", return_value=decide_mock), \
             patch("agents.probe_agent.call_llm", return_value="HubSpot response"):
            agent = ProbeAgent(PROVIDER, MODEL, KEY)
            results, _ = agent.run("HubSpot", "CRM", [])
        required = {"scenario_id", "label", "prompt_used", "response", "mentioned",
                    "position", "snippet", "sentiment", "claims", "is_probe"}
        assert required.issubset(results[0].keys())

    def test_run_probe_scenario_ids_start_at_100(self):
        decide_mock = {"probes": ["q1", "q2"], "rationale": "r"}
        with patch("agents.probe_agent.call_json", return_value=decide_mock), \
             patch("agents.probe_agent.call_llm", return_value="no mention"):
            agent = ProbeAgent(PROVIDER, MODEL, KEY)
            results, _ = agent.run("HubSpot", "CRM", [])
        assert results[0]["scenario_id"] == 100
        assert results[1]["scenario_id"] == 101

    def test_run_multiple_probes_all_execute(self):
        decide_mock = {"probes": ["q1", "q2", "q3"], "rationale": "3 gaps"}
        with patch("agents.probe_agent.call_json", return_value=decide_mock), \
             patch("agents.probe_agent.call_llm", return_value="no mention"):
            agent = ProbeAgent(PROVIDER, MODEL, KEY)
            results, _ = agent.run("HubSpot", "CRM", [])
        assert len(results) == 3


# ── DiagnosisAgent._parse ─────────────────────────────────────────────────────

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
            "actions": [{"action": "Do X", "confidence": 1.5}],
        }
        diag = self.agent._parse(raw)
        assert diag.actions[0].confidence <= 1.0

    def test_parse_confidence_clamped_at_zero(self):
        raw = {
            "status_summary": "x", "root_cause": "y",
            "actions": [{"action": "Do X", "confidence": -0.5}],
        }
        diag = self.agent._parse(raw)
        assert diag.actions[0].confidence >= 0.0

    def test_parse_skips_malformed_actions(self):
        raw = {
            "status_summary": "x", "root_cause": "y",
            "actions": [
                {"action": "Good action", "confidence": 0.8},
                {"action": "Bad action", "effort": "invalid_value"},
            ],
        }
        diag = self.agent._parse(raw)
        assert len(diag.actions) >= 1

    def test_parse_cross_model_note(self):
        raw = {
            "status_summary": "x", "root_cause": "y",
            "actions": [],
            "cross_model_note": "Gemini and ChatGPT disagree on market position.",
        }
        diag = self.agent._parse(raw)
        assert diag.cross_model_note is not None

    def test_parse_missing_actions_key_returns_empty_list(self):
        raw = {"status_summary": "OK", "root_cause": "gaps"}
        # No "actions" key at all
        diag = self.agent._parse(raw)
        assert isinstance(diag, AuditDiagnosis)
        assert diag.actions == []

    def test_parse_empty_actions_list(self):
        raw = {"status_summary": "x", "root_cause": "y", "actions": []}
        diag = self.agent._parse(raw)
        assert diag.actions == []

    def test_parse_cross_model_note_none_by_default(self):
        raw = {"status_summary": "x", "root_cause": "y", "actions": []}
        diag = self.agent._parse(raw)
        assert diag.cross_model_note is None


# ── DiagnosisAgent._results_text ──────────────────────────────────────────────

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

    def test_results_text_with_claims(self):
        r = _result("Market discovery", True)
        r["claims"] = ["affordable", "easy setup"]
        text = self.agent._results_text([r])
        assert "affordable" in text
        assert "easy setup" in text

    def test_results_text_no_sentiment_no_extra_text(self):
        """If no sentiment, the extras string should be empty — no orphan commas."""
        results = [_result("Market discovery", True, sentiment=None)]
        text = self.agent._results_text(results)
        assert "sentiment=" not in text


# ── DiagnosisAgent.run ────────────────────────────────────────────────────────

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

    def test_multi_model_prompt_contains_disagreement_block(self):
        """Multi-model prompt must highlight where models disagree — that's the key insight."""
        mock_diag = {"status_summary": "x", "root_cause": "y", "actions": []}
        with patch("agents.diagnosis_agent.call_json", return_value=mock_diag) as mock_cj:
            agent = DiagnosisAgent(PROVIDER, MODEL, KEY)
            # Gemini mentions brand, OpenAI does not — disagreement on "Market discovery"
            results_by_provider = {
                "gemini": [_result("Market discovery", True)],
                "openai": [_result("Market discovery", False)],
            }
            probe_by_provider = {"gemini": ([], ""), "openai": ([], "")}
            agent.run("HubSpot", "CRM", results_by_provider, probe_by_provider)
        prompt = mock_cj.call_args[0][3]
        assert "Market discovery" in prompt
        assert "disagree" in prompt.lower() or "✓" in prompt or "✗" in prompt

    def test_multi_model_no_disagreements_included_in_prompt(self):
        """When all models agree, the prompt should note that too."""
        mock_diag = {"status_summary": "x", "root_cause": "y", "actions": []}
        with patch("agents.diagnosis_agent.call_json", return_value=mock_diag) as mock_cj:
            agent = DiagnosisAgent(PROVIDER, MODEL, KEY)
            # Both models agree: mentioned
            results_by_provider = {
                "gemini": [_result("Market discovery", True)],
                "openai": [_result("Market discovery", True)],
            }
            probe_by_provider = {"gemini": ([], ""), "openai": ([], "")}
            agent.run("HubSpot", "CRM", results_by_provider, probe_by_provider)
        prompt = mock_cj.call_args[0][3]
        assert "agree" in prompt.lower()
