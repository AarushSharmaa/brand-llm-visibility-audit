"""
Mention analyzer: detects brand in LLM response text, then enriches
with sentiment + claims via a single batch LLM call per model run.
"""

import re
from typing import Optional
from llm.client import call_json


def detect_mention(text: str, brand: str) -> dict:
    """
    Fast regex-based mention detection. No API call.
    Returns {mentioned, position, snippet}.
    """
    if not text:
        return {"mentioned": False, "position": None, "snippet": ""}

    lower = text.lower()
    b_lower = brand.lower()
    mentioned = b_lower in lower
    position = None
    snippet = ""

    if mentioned:
        esc = re.escape(brand)
        m = re.search(r"(\d+)[.)]\s[^\n]{0,80}?" + esc, text, re.IGNORECASE)
        if m:
            position = int(m.group(1))

        idx = lower.index(b_lower)
        start = max(0, idx - 60)
        end = min(len(text), idx + len(brand) + 140)
        snippet = (
            ("..." if start > 0 else "")
            + text[start:end].strip()
            + ("..." if end < len(text) else "")
        )

    return {"mentioned": mentioned, "position": position, "snippet": snippet}


def enrich_with_claims(
    provider: str,
    model_name: str,
    api_key: str,
    brand: str,
    results: list[dict],
) -> list[dict]:
    """
    One batch LLM call to extract sentiment + claims for all mentioned scenarios.
    Mutates results in-place (adds 'sentiment' and 'claims').
    Falls back silently — never crashes the audit.
    """
    mentioned = [r for r in results if r.get("mentioned")]
    if not mentioned:
        return results

    scenarios_text = "\n\n".join(
        f"SCENARIO: {r['label']}\nRESPONSE EXCERPT: {r.get('response', '')[:600]}"
        for r in mentioned
    )

    prompt = f"""Brand being audited: {brand}

For each scenario below where {brand} is mentioned, extract:
1. sentiment: how the brand is portrayed ("positive", "neutral", "cautious", "negative")
2. claims: 2-4 short phrases describing exactly what the response says about this brand
   Examples of good claims: "expensive", "best for enterprises", "easy to set up",
   "limited integrations", "recently raised $50M", "founder-led", "niche tool"

{scenarios_text}

Return a JSON array:
[
  {{
    "scenario": "<exact scenario label>",
    "sentiment": "positive|neutral|cautious|negative",
    "claims": ["claim 1", "claim 2"]
  }}
]"""

    parsed = call_json(provider, model_name, api_key, prompt)
    if not parsed or not isinstance(parsed, list):
        return results

    enrichment = {item["scenario"]: item for item in parsed if isinstance(item, dict)}
    for r in results:
        if r.get("mentioned") and r["label"] in enrichment:
            e = enrichment[r["label"]]
            r["sentiment"] = e.get("sentiment", "neutral")
            r["claims"] = e.get("claims", [])[:5]

    return results


def count_competitor_mentions(responses: list[str], competitor: str) -> int:
    """Count how many responses mention a competitor brand. Used for SOV."""
    c_lower = competitor.lower()
    return sum(1 for r in responses if c_lower in r.lower())
