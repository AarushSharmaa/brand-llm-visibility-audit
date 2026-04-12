"""
Playbook Agent — turns a GEO diagnosis into writer-ready content briefs.

Takes AuditDiagnosis + audit context, produces GEOPlaybook with specific
content briefs (real titles, target queries, outlines) and quick wins.
Single call_json() call — stays within Groq free tier limits.
"""

from llm.client import call_json
from core.models import ContentBrief, GEOPlaybook


_VALID_TYPES = {
    "comparison page", "how-to guide", "listicle",
    "case study", "community post", "llms.txt update", "product page update",
}
_VALID_PRIORITIES = {"this week", "this month", "next quarter"}


class PlaybookAgent:
    def __init__(self, provider: str, model_name: str, api_key: str):
        self.provider = provider
        self.model_name = model_name
        self.api_key = api_key

    def run(
        self,
        brand: str,
        category: str,
        diagnosis,               # AuditDiagnosis
        results_by_provider: dict,
        competitors: list[str],
    ) -> GEOPlaybook:
        prompt = self._build_prompt(brand, category, diagnosis, results_by_provider, competitors)
        raw = call_json(self.provider, self.model_name, self.api_key, prompt)
        return self._parse(brand, category, raw)

    # ── prompt ────────────────────────────────────────────────────────────────

    def _build_prompt(
        self, brand: str, category: str, diagnosis, results_by_provider: dict, competitors: list[str]
    ) -> str:
        # Summarise what was/wasn't mentioned across scenarios
        all_results = []
        for results in results_by_provider.values():
            all_results.extend(results)
        missed = [r["label"] for r in all_results if not r.get("mentioned")]
        hit = [r["label"] for r in all_results if r.get("mentioned")]
        missed_str = ", ".join(dict.fromkeys(missed)) or "none"
        hit_str = ", ".join(dict.fromkeys(hit)) or "none"

        # Summarise diagnosis actions
        actions_text = "\n".join(
            f"- {a.action} (confidence {round(a.confidence * 100)}%, effort={a.effort}, impact={a.impact})"
            for a in diagnosis.actions
        ) or "No specific actions identified."

        comp_str = ", ".join(competitors) if competitors else "none provided"

        return f"""You are a GEO strategist. Turn an AI visibility diagnosis into specific, writer-ready content briefs.

Brand: {brand}
Category: {category}
Competitors known: {comp_str}

Visibility gaps (NOT mentioned in these scenarios): {missed_str}
Already visible in: {hit_str}

Diagnosis summary: {diagnosis.status_summary}
Root cause: {diagnosis.root_cause}

Recommended actions from diagnosis:
{actions_text}

---

Rules (read carefully before generating):
- Every title must name the brand AND be a real, publishable article title.
  BAD: "Write a comparison page." GOOD: "{brand} vs [Competitor]: Which {category} tool is right for [use case]? (2026)"
- Target queries must be natural-language questions a real person types into ChatGPT.
  BAD: "best {category} software" GOOD: "What's the best {category} tool for a 20-person team?"
- Outlines must have 4-6 concrete section headings — not "Introduction" / "Conclusion" filler.
- Quick wins must be completable in under 1 hour (e.g. add /llms.txt, update homepage meta description).
- Be honest about timeline — LLM training data changes take weeks to months.
- Generate one brief per diagnosis action (2-3 briefs total). If an action maps naturally to a quick win instead of a full article, put it in quick_wins.

Return ONLY this JSON structure:
{{
  "executive_summary": "2-3 sentences: where {brand} is invisible, what the fix is, expected outcome.",
  "briefs": [
    {{
      "title": "exact, publishable article/page title",
      "content_type": "comparison page|how-to guide|listicle|case study|community post|llms.txt update|product page update",
      "target_queries": ["natural language query 1", "natural language query 2"],
      "word_count": 1200,
      "outline": ["Section heading 1", "Section heading 2", "Section heading 3", "Section heading 4"],
      "competitors_to_reference": ["Competitor A", "Competitor B"],
      "priority": "this week|this month|next quarter",
      "why_this_matters": "1-2 sentences connecting this brief to the specific visibility gap."
    }}
  ],
  "quick_wins": ["Specific thing to do in under 1 hour", "Another quick win"],
  "estimated_timeline": "X-Y weeks to see initial visibility improvement"
}}"""

    # ── parser ────────────────────────────────────────────────────────────────

    def _parse(self, brand: str, category: str, raw: dict | None) -> GEOPlaybook:
        if not raw:
            return GEOPlaybook(
                brand=brand,
                category=category,
                executive_summary="Could not generate playbook. Try running the diagnosis first.",
                briefs=[],
                quick_wins=[],
                estimated_timeline="",
            )

        briefs = []
        for b in raw.get("briefs", []):
            try:
                content_type = b.get("content_type", "how-to guide")
                if content_type not in _VALID_TYPES:
                    content_type = "how-to guide"
                priority = b.get("priority", "this month")
                if priority not in _VALID_PRIORITIES:
                    priority = "this month"
                word_count = b.get("word_count", 800)
                try:
                    word_count = int(word_count)
                except (TypeError, ValueError):
                    word_count = 800
                briefs.append(ContentBrief(
                    title=b.get("title", ""),
                    content_type=content_type,
                    target_queries=b.get("target_queries", []),
                    word_count=word_count,
                    outline=b.get("outline", []),
                    competitors_to_reference=b.get("competitors_to_reference", []),
                    priority=priority,
                    why_this_matters=b.get("why_this_matters", ""),
                ))
            except Exception:
                continue

        return GEOPlaybook(
            brand=brand,
            category=category,
            executive_summary=raw.get("executive_summary", ""),
            briefs=briefs,
            quick_wins=raw.get("quick_wins", []),
            estimated_timeline=raw.get("estimated_timeline", ""),
        )
