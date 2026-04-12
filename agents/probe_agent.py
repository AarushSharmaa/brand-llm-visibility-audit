"""
Adaptive Probe Agent — the agentic core of the audit.

After 6 standard scenarios, an LLM orchestrator reviews what it found and
decides whether to run 1–3 targeted follow-up queries. This is genuinely
agentic: the model reasons about results and chooses its own next actions.

Decision logic (embedded in the prompt, not hardcoded):
  - Invisible brand (≤2/6): probe alternate phrasings
  - Negative/cautious mentions: dig into that framing
  - High scorer (5–6/6): test edge cases / niche angles
  - Mixed: target the gaps
"""

from llm.client import call_llm, call_json
from agents.analyzer import detect_mention


MAX_PROBES = 3


class ProbeAgent:
    def __init__(self, provider: str, model_name: str, api_key: str):
        self.provider = provider
        self.model_name = model_name
        self.api_key = api_key

    def decide(self, brand: str, category: str, results: list[dict]) -> tuple[list[str], str]:
        """
        Ask the orchestrator LLM to review results and return follow-up probe queries.
        Returns (probe_prompts, rationale).
        """
        results_summary = "\n".join(
            "- {}: {}{}".format(
                r["label"],
                "MENTIONED" if r.get("mentioned") else "NOT MENTIONED",
                f" [sentiment: {r['sentiment']}]" if r.get("sentiment") else "",
            )
            for r in results
        )

        prompt = f"""You are auditing AI visibility for a brand.

Brand: {brand}
Category: {category}

Initial audit results (6 standard scenarios):
{results_summary}

Decide whether 1–3 targeted follow-up queries would reveal meaningful additional signal.

Rules:
- Brand scored ≤2/6 → probe with alternate category phrasings (how real buyers ask, not just "top tools")
- Mentioned with negative or cautious sentiment → write a query that specifically surfaces that framing
- Brand scored 5–6/6 → test edge cases: niche segment, regional variant, persona-specific phrasing
- Mixed results → target the specific scenarios where the brand is absent

Return JSON:
{{
  "probes": ["exact query text 1", "exact query text 2"],
  "rationale": "one sentence explaining why these probes add signal"
}}

Return 1–3 probes. If no follow-up would meaningfully add signal, return {{"probes": [], "rationale": "results are conclusive"}}.
Write probe queries as a real user would type them — natural language, no formal structure."""

        result = call_json(self.provider, self.model_name, self.api_key, prompt)
        if not result:
            return [], "Agent could not determine follow-up probes."

        probes = result.get("probes", [])[:MAX_PROBES]
        rationale = result.get("rationale", "")
        return probes, rationale

    def run(self, brand: str, category: str, initial_results: list[dict]) -> tuple[list[dict], str]:
        """
        Full probe loop. Returns (probe_result_dicts, rationale).
        Each probe result has the same shape as a scenario result dict.
        """
        probes, rationale = self.decide(brand, category, initial_results)

        if not probes:
            return [], rationale

        probe_results = []
        for probe_prompt in probes:
            try:
                response = call_llm(self.provider, self.model_name, self.api_key, probe_prompt)
                analysis = detect_mention(response, brand)
                probe_results.append({
                    "scenario_id": 100 + len(probe_results),
                    "label": probe_prompt[:90] + ("…" if len(probe_prompt) > 90 else ""),
                    "prompt_used": probe_prompt,
                    "response": response,
                    "mentioned": analysis["mentioned"],
                    "position": analysis["position"],
                    "snippet": analysis["snippet"],
                    "sentiment": None,
                    "claims": [],
                    "is_probe": True,
                })
            except Exception as e:
                probe_results.append({
                    "scenario_id": 100 + len(probe_results),
                    "label": probe_prompt[:70] + "…",
                    "prompt_used": probe_prompt,
                    "response": "",
                    "mentioned": False,
                    "position": None,
                    "snippet": "",
                    "sentiment": None,
                    "claims": [],
                    "is_probe": True,
                    "error": str(e),
                })

        return probe_results, rationale
