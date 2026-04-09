# Brand LLM Visibility Audit

When someone asks ChatGPT or Perplexity "what's the best CRM right now?", the brands that show up win the click. Most companies have no idea where they stand. This tool gives them a clear answer in under 2 minutes.

## What it does

Runs 6 buyer-journey scenarios across one or more AI models, then tells you exactly where your brand appears, how it is framed, and what to fix.

**Scenarios:** market discovery, tool recommendation, brand knowledge, competitive landscape, best-in-class search, vendor comparison.

**Output:**
- Visibility score per model (% of scenarios where brand is mentioned)
- List position and response snippet per scenario
- Sentiment tag and extracted claims per mention (what the LLM actually says about you)
- Adaptive follow-up probes chosen by an agent based on your results
- Confidence-scored action plan with effort and impact ratings
- Competitor share of voice computed from existing responses (no extra API calls)
- Cross-model disagreement analysis when multiple models are used

## Providers supported

| Provider | Free tier | Models |
|---|---|---|
| Groq | Yes (high limits) | Llama 3.3 70B, Llama 3.1 8B, Mixtral 8x7B |
| Gemini | Yes | Gemini 2.5 Flash, 1.5 Flash |
| OpenAI | No | GPT-4o Mini, GPT-4o |
| Perplexity | No | Sonar, Sonar Pro |
| Anthropic | No | Claude Haiku, Claude Sonnet |

Only a Groq or Gemini key is required to run the full audit. Additional keys unlock multi-model comparison.

## Running locally

```bash
git clone <repo-url>
cd brand-llm-visibility-audit
pip install -r requirements.txt
streamlit run app.py
```

Get a free Groq key at [console.groq.com](https://console.groq.com) or a free Gemini key at [aistudio.google.com](https://aistudio.google.com).

## What makes it agentic

The probe agent reviews the initial 6 results and decides whether to run targeted follow-up queries. The decision logic is LLM-driven, not hardcoded:

- Brand invisible (2/6 or fewer mentions): probe alternate category phrasings
- Negative or cautious sentiment: surface that framing specifically
- High score (5-6/6): test edge cases and niche segments
- Mixed results: target the specific gaps

The diagnosis agent produces structured JSON output with per-action confidence scores (0 to 1). Actions under 0.6 are flagged as hypotheses.

## Tech stack

Python, Streamlit, Pydantic, google-genai, groq, openai, anthropic SDKs.
