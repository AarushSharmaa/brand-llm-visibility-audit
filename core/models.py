"""
Pydantic data models for the entire audit pipeline.
All agent outputs are typed — no raw dicts crossing module boundaries.
"""

from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional, Literal


class ScenarioResult(BaseModel):
    scenario_id: int
    label: str
    prompt_used: str
    response: str
    mentioned: bool
    position: Optional[int] = None
    snippet: str = ""
    sentiment: Optional[Literal["positive", "neutral", "cautious", "negative"]] = None
    claims: list[str] = Field(default_factory=list)
    is_probe: bool = False  # True for adaptive follow-up queries


class ModelAudit(BaseModel):
    """Full audit results for a single model/provider."""
    provider: str          # e.g. "gemini"
    model_name: str        # e.g. "gemini-2.5-flash"
    results: list[ScenarioResult] = Field(default_factory=list)
    probe_results: list[ScenarioResult] = Field(default_factory=list)
    probe_rationale: str = ""

    @property
    def all_results(self) -> list[ScenarioResult]:
        return self.results + self.probe_results

    @property
    def mention_count(self) -> int:
        return sum(1 for r in self.all_results if r.mentioned)

    @property
    def total_scenarios(self) -> int:
        return len(self.all_results)

    @property
    def score(self) -> int:
        if not self.total_scenarios:
            return 0
        return round((self.mention_count / self.total_scenarios) * 100)

    @property
    def avg_position(self) -> Optional[float]:
        positions = [r.position for r in self.all_results if r.position is not None]
        return round(sum(positions) / len(positions), 1) if positions else None


class ActionItem(BaseModel):
    action: str
    scenarios_driving_it: list[str] = Field(default_factory=list)
    effort: Literal["low", "medium", "high"] = "medium"
    impact: Literal["low", "medium", "high"] = "medium"
    confidence: float = 0.7  # 0.0 – 1.0


class AuditDiagnosis(BaseModel):
    status_summary: str
    root_cause: str
    actions: list[ActionItem] = Field(default_factory=list)
    cross_model_note: Optional[str] = None


class ContentBrief(BaseModel):
    """A single writer-ready content brief derived from a GEO diagnosis action."""
    title: str
    content_type: Literal[
        "comparison page", "how-to guide", "listicle",
        "case study", "community post", "llms.txt update", "product page update"
    ] = "how-to guide"
    target_queries: list[str] = Field(default_factory=list)
    word_count: int = 800
    outline: list[str] = Field(default_factory=list)
    competitors_to_reference: list[str] = Field(default_factory=list)
    priority: Literal["this week", "this month", "next quarter"] = "this month"
    why_this_matters: str = ""


class GEOPlaybook(BaseModel):
    """Full content playbook generated from audit diagnosis."""
    brand: str
    category: str
    executive_summary: str
    briefs: list[ContentBrief] = Field(default_factory=list)
    quick_wins: list[str] = Field(default_factory=list)
    estimated_timeline: str = ""


class CompetitorSOV(BaseModel):
    """Share-of-voice computed from existing response text — no extra API calls."""
    name: str
    mentions: int
    total_responses: int

    @property
    def share_pct(self) -> float:
        return round((self.mentions / self.total_responses) * 100, 1) if self.total_responses else 0.0
