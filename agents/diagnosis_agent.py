"""
Diagnosis Agent — produces a structured, confidence-scored GEO action plan.

Single-model: status + root cause + 2-3 prioritized actions with confidence scores.
Multi-model: same, plus cross-model disagreement note that names specific models
and hypothesizes *why* they differ (training data, framing, content gaps).
"""

from llm.client import call_json
from core.models import ActionItem, AuditDiagnosis


class DiagnosisAgent:
    def __init__(self, provider: str, model_name: str, api_key: str):
        self.provider = provider
        self.model_name = model_name
        self.api_key = api_key

    def run(
        self,
        brand: str,
        category: str,
        results_by_provider: dict,   # {provider_key: [result_dicts]}
        probe_by_provider: dict,     # {provider_key: ([probe_dicts], rationale)}
    ) -> AuditDiagnosis:
        if len(results_by_provider) > 1:
            return self._multi_model(brand, category, results_by_provider, probe_by_provider)
        provider_key = list(results_by_provider.keys())[0]
        results = results_by_provider[provider_key]
        probe_results, _ = probe_by_provider.get(provider_key, ([], ""))
        return self._single_model(brand, category, results, probe_results)

    # ── helpers ──────────────────────────────────────────────────────────────

    def _results_text(self, results: list[dict], probes: list[dict] = None) -> str:
        lines = []
        for r in results:
            status = "MENTIONED" if r.get("mentioned") else "NOT MENTIONED"
            extras = ""
            if r.get("mentioned"):
                if r.get("sentiment"):
                    extras += f", sentiment={r['sentiment']}"
                if r.get("claims"):
                    extras += f", claims: {', '.join(r['claims'])}"
            lines.append(f"- {r['label']}: {status}{extras}")
        if probes:
            lines.append("Probe follow-ups:")
            for p in probes:
                status = "MENTIONED" if p.get("mentioned") else "NOT MENTIONED"
                lines.append(f"  - [{p['label'][:70]}]: {status}")
        return "\n".join(lines)

    def _parse(self, raw: dict | None) -> AuditDiagnosis:
        if not raw:
            return AuditDiagnosis(
                status_summary="Could not generate structured diagnosis.",
                root_cause="",
                actions=[],
            )
        actions = []
        for a in raw.get("actions", []):
            try:
                conf = max(0.0, min(1.0, float(a.get("confidence", 0.7))))
                actions.append(ActionItem(
                    action=a.get("action", ""),
                    scenarios_driving_it=a.get("scenarios_driving_it", []),
                    effort=a.get("effort", "medium"),
                    impact=a.get("impact", "medium"),
                    confidence=conf,
                ))
            except Exception:
                continue
        return AuditDiagnosis(
            status_summary=raw.get("status_summary", ""),
            root_cause=raw.get("root_cause", ""),
            actions=actions,
            cross_model_note=raw.get("cross_model_note"),
        )

    # ── single-model path ─────────────────────────────────────────────────────

    def _single_model(
        self, brand: str, category: str, results: list[dict], probes: list[dict]
    ) -> AuditDiagnosis:
        mention_count = sum(1 for r in results if r.get("mentioned"))
        results_text = self._results_text(results, probes)

        prompt = f"""You are a GEO (Generative Engine Optimization) analyst.

Brand: {brand}
Category: {category}
Visibility: {mention_count}/{len(results)} scenarios

{results_text}

Produce a structured GEO diagnosis as JSON:
{{
  "status_summary": "2-3 sentences. Current LLM visibility status. Be direct and specific — name scenarios.",
  "root_cause": "2-3 sentences. The most likely root cause: content gaps, training data, weak positioning, etc.",
  "actions": [
    {{
      "action": "specific, concrete thing to do — not 'write more content'",
      "scenarios_driving_it": ["Market discovery", "Tool recommendation"],
      "effort": "low|medium|high",
      "impact": "low|medium|high",
      "confidence": 0.85
    }}
  ]
}}

Include 2-3 prioritized actions. Confidence (0–1): how strongly the evidence supports this action.
Under 0.6 = hypothesis. Over 0.8 = well-supported. Be specific — bad: "create blog posts". Good: "publish a head-to-head comparison page vs [main competitor] targeting '[category] vs [competitor]' queries"."""

        return self._parse(call_json(self.provider, self.model_name, self.api_key, prompt))

    # ── multi-model path ──────────────────────────────────────────────────────

    def _multi_model(
        self, brand: str, category: str,
        results_by_provider: dict, probe_by_provider: dict
    ) -> AuditDiagnosis:
        # Build per-model summary
        model_blocks = []
        for pk, results in results_by_provider.items():
            probes, _ = probe_by_provider.get(pk, ([], ""))
            mc = sum(1 for r in results if r.get("mentioned"))
            text = self._results_text(results, probes)
            model_blocks.append(f"=== {pk.upper()} ({mc}/{len(results)}) ===\n{text}")

        # Find scenario-level disagreements
        provider_keys = list(results_by_provider.keys())
        disagreements = []
        base_results = results_by_provider[provider_keys[0]]
        for i, base_r in enumerate(base_results):
            label = base_r.get("label", "")
            per_model = {}
            for pk in provider_keys:
                r_list = results_by_provider[pk]
                if i < len(r_list):
                    per_model[pk] = r_list[i].get("mentioned", False)
            if len(set(per_model.values())) > 1:
                detail = ", ".join(f"{k}={'✓' if v else '✗'}" for k, v in per_model.items())
                disagreements.append(f"- {label}: {detail}")

        disagreement_block = (
            "\nScenarios where models disagree:\n" + "\n".join(disagreements)
            if disagreements
            else "\nAll models agree on mention/no-mention for every scenario."
        )

        prompt = f"""You are a GEO analyst. A brand was audited across multiple AI models.

Brand: {brand}
Category: {category}

{chr(10).join(model_blocks)}
{disagreement_block}

Produce a structured cross-model GEO diagnosis as JSON:
{{
  "status_summary": "2-3 sentences comparing visibility across models. Name specific models and their scores.",
  "root_cause": "2-3 sentences on root cause of variance or consistent gaps.",
  "actions": [
    {{
      "action": "specific concrete action",
      "scenarios_driving_it": ["scenario label"],
      "effort": "low|medium|high",
      "impact": "low|medium|high",
      "confidence": 0.8
    }}
  ],
  "cross_model_note": "1-2 sentences explaining WHY disagreeing models differ — training data cutoff, category framing, which publishers/sources each model weights heavily."
}}

Include 2-3 prioritized actions. Confidence 0–1."""

        return self._parse(call_json(self.provider, self.model_name, self.api_key, prompt))
