"""
Tests for agents/playbook_agent.py and GEOPlaybook/ContentBrief Pydantic models.
All LLM calls are mocked — no API keys required.
"""

import pytest
from unittest.mock import patch
from agents.playbook_agent import PlaybookAgent
from core.models import ContentBrief, GEOPlaybook, AuditDiagnosis, ActionItem


# ── Fixtures ──────────────────────────────────────────────────────────────────

PROVIDER = "groq"
MODEL = "llama-3.3-70b-versatile"
KEY = "fake-key"


def _diagnosis(actions=None) -> AuditDiagnosis:
    return AuditDiagnosis(
        status_summary="Notion is mentioned in 2/6 scenarios. Invisible in generic searches.",
        root_cause="No comparison content targeting head-to-head queries.",
        actions=actions or [
            ActionItem(
                action="Publish a Notion vs Obsidian comparison page",
                scenarios_driving_it=["Market discovery", "Tool recommendation"],
                effort="medium",
                impact="high",
                confidence=0.82,
            )
        ],
    )


def _results() -> dict:
    return {
        "groq": [
            {"label": "Market discovery", "mentioned": False, "sentiment": None, "claims": []},
            {"label": "Tool recommendation", "mentioned": True, "sentiment": "positive", "claims": ["easy to use"]},
        ]
    }


def _raw_playbook() -> dict:
    return {
        "executive_summary": "Notion is invisible in 4 of 6 scenarios. Publishing comparison content will close the gap.",
        "briefs": [
            {
                "title": "Notion vs Obsidian: Which Note-Taking App Is Right for Your Team? (2026)",
                "content_type": "comparison page",
                "target_queries": [
                    "What's the best note-taking app for teams?",
                    "Notion vs Obsidian for project management",
                ],
                "word_count": 1400,
                "outline": [
                    "What each tool does best",
                    "Side-by-side feature comparison",
                    "Pricing breakdown",
                    "Which team size fits which tool",
                    "Migration tips",
                ],
                "competitors_to_reference": ["Obsidian"],
                "priority": "this week",
                "why_this_matters": "Notion is absent from head-to-head queries where buyers make final decisions.",
            }
        ],
        "quick_wins": [
            "Add /llms.txt to notion.so listing your top use cases",
            "Update homepage meta description to include 'team knowledge base'",
        ],
        "estimated_timeline": "4-6 weeks to see initial LLM visibility improvement",
    }


# ── ContentBrief model ────────────────────────────────────────────────────────

class TestContentBriefModel:

    def test_valid_content_brief(self):
        brief = ContentBrief(
            title="Notion vs Obsidian: Full 2026 Comparison",
            content_type="comparison page",
            target_queries=["best note-taking app for teams?"],
            word_count=1200,
            outline=["Intro", "Features", "Pricing", "Verdict"],
            competitors_to_reference=["Obsidian"],
            priority="this week",
            why_this_matters="Fills the head-to-head gap.",
        )
        assert brief.title == "Notion vs Obsidian: Full 2026 Comparison"
        assert brief.content_type == "comparison page"
        assert brief.priority == "this week"
        assert brief.word_count == 1200

    def test_invalid_content_type_raises(self):
        with pytest.raises(Exception):
            ContentBrief(title="x", content_type="invalid_type")

    def test_invalid_priority_raises(self):
        with pytest.raises(Exception):
            ContentBrief(title="x", priority="yesterday")

    def test_defaults(self):
        brief = ContentBrief(title="x")
        assert brief.content_type == "how-to guide"
        assert brief.priority == "this month"
        assert brief.word_count == 800
        assert brief.outline == []
        assert brief.target_queries == []


# ── GEOPlaybook model ─────────────────────────────────────────────────────────

class TestGEOPlaybookModel:

    def test_valid_playbook(self):
        pb = GEOPlaybook(
            brand="Notion",
            category="productivity software",
            executive_summary="Notion is invisible in generic searches.",
            briefs=[ContentBrief(title="Notion for Teams Guide")],
            quick_wins=["Add llms.txt"],
            estimated_timeline="4-6 weeks",
        )
        assert pb.brand == "Notion"
        assert len(pb.briefs) == 1
        assert len(pb.quick_wins) == 1

    def test_empty_briefs_allowed(self):
        pb = GEOPlaybook(brand="x", category="y", executive_summary="z")
        assert pb.briefs == []
        assert pb.quick_wins == []


# ── PlaybookAgent._parse ──────────────────────────────────────────────────────

class TestPlaybookAgentParse:

    def setup_method(self):
        self.agent = PlaybookAgent(PROVIDER, MODEL, KEY)

    def test_parse_full_valid_response(self):
        pb = self.agent._parse("Notion", "productivity software", _raw_playbook())
        assert isinstance(pb, GEOPlaybook)
        assert pb.brand == "Notion"
        assert pb.executive_summary != ""
        assert len(pb.briefs) == 1
        assert pb.briefs[0].title == "Notion vs Obsidian: Which Note-Taking App Is Right for Your Team? (2026)"
        assert pb.briefs[0].content_type == "comparison page"
        assert pb.briefs[0].priority == "this week"
        assert pb.briefs[0].word_count == 1400
        assert len(pb.briefs[0].outline) == 5
        assert len(pb.quick_wins) == 2
        assert pb.estimated_timeline != ""

    def test_parse_null_returns_fallback(self):
        pb = self.agent._parse("Notion", "productivity software", None)
        assert isinstance(pb, GEOPlaybook)
        assert "Could not" in pb.executive_summary
        assert pb.briefs == []

    def test_parse_invalid_content_type_coerced(self):
        raw = _raw_playbook()
        raw["briefs"][0]["content_type"] = "random gibberish"
        pb = self.agent._parse("Notion", "productivity software", raw)
        assert pb.briefs[0].content_type == "how-to guide"

    def test_parse_invalid_priority_coerced(self):
        raw = _raw_playbook()
        raw["briefs"][0]["priority"] = "urgently"
        pb = self.agent._parse("Notion", "productivity software", raw)
        assert pb.briefs[0].priority == "this month"

    def test_parse_word_count_coerced_on_invalid(self):
        raw = _raw_playbook()
        raw["briefs"][0]["word_count"] = "not a number"
        pb = self.agent._parse("Notion", "productivity software", raw)
        assert pb.briefs[0].word_count == 800

    def test_parse_skips_malformed_brief(self):
        raw = _raw_playbook()
        raw["briefs"].append({"title": None})  # will fail ContentBrief validation
        # Should not raise — just skip bad brief or include good one
        pb = self.agent._parse("Notion", "productivity software", raw)
        assert isinstance(pb, GEOPlaybook)

    def test_parse_empty_briefs_list(self):
        raw = _raw_playbook()
        raw["briefs"] = []
        pb = self.agent._parse("Notion", "productivity software", raw)
        assert pb.briefs == []

    def test_parse_missing_quick_wins(self):
        raw = _raw_playbook()
        del raw["quick_wins"]
        pb = self.agent._parse("Notion", "productivity software", raw)
        assert pb.quick_wins == []


# ── PlaybookAgent.run ─────────────────────────────────────────────────────────

class TestPlaybookAgentRun:

    def test_run_returns_geo_playbook(self):
        with patch("agents.playbook_agent.call_json", return_value=_raw_playbook()):
            agent = PlaybookAgent(PROVIDER, MODEL, KEY)
            pb = agent.run("Notion", "productivity software", _diagnosis(), _results(), [])
        assert isinstance(pb, GEOPlaybook)
        assert pb.brand == "Notion"
        assert len(pb.briefs) >= 1

    def test_run_with_competitors_passes_them_through(self):
        with patch("agents.playbook_agent.call_json", return_value=_raw_playbook()) as mock_cj:
            agent = PlaybookAgent(PROVIDER, MODEL, KEY)
            agent.run("Notion", "productivity software", _diagnosis(), _results(), ["Obsidian", "Roam"])
            prompt_used = mock_cj.call_args[0][3]
        assert "Obsidian" in prompt_used
        assert "Roam" in prompt_used

    def test_run_handles_null_llm_response_gracefully(self):
        with patch("agents.playbook_agent.call_json", return_value=None):
            agent = PlaybookAgent(PROVIDER, MODEL, KEY)
            pb = agent.run("Notion", "productivity software", _diagnosis(), _results(), [])
        assert isinstance(pb, GEOPlaybook)
        assert pb.briefs == []

    def test_run_prompt_includes_brand(self):
        with patch("agents.playbook_agent.call_json", return_value=_raw_playbook()) as mock_cj:
            agent = PlaybookAgent(PROVIDER, MODEL, KEY)
            agent.run("Notion", "productivity software", _diagnosis(), _results(), [])
            prompt_used = mock_cj.call_args[0][3]
        assert "Notion" in prompt_used

    def test_run_prompt_includes_missed_scenarios(self):
        with patch("agents.playbook_agent.call_json", return_value=_raw_playbook()) as mock_cj:
            agent = PlaybookAgent(PROVIDER, MODEL, KEY)
            agent.run("Notion", "productivity software", _diagnosis(), _results(), [])
            prompt_used = mock_cj.call_args[0][3]
        assert "Market discovery" in prompt_used  # was not mentioned

    def test_run_no_competitors(self):
        with patch("agents.playbook_agent.call_json", return_value=_raw_playbook()):
            agent = PlaybookAgent(PROVIDER, MODEL, KEY)
            pb = agent.run("Notion", "productivity software", _diagnosis(), _results(), [])
        assert isinstance(pb, GEOPlaybook)

    def test_run_empty_diagnosis_actions(self):
        diag = _diagnosis(actions=[])
        with patch("agents.playbook_agent.call_json", return_value=_raw_playbook()):
            agent = PlaybookAgent(PROVIDER, MODEL, KEY)
            pb = agent.run("Notion", "productivity software", diag, _results(), [])
        assert isinstance(pb, GEOPlaybook)
