# Project Background

## What it does
Runs 6 standardised discovery prompts against LLMs and scores how visible a brand is. Simulates how real users find products through AI — market discovery, tool recommendation, brand knowledge, competitive landscape, best-in-class search, vendor comparison.

## Run
```
streamlit run app.py
```

## Stack
- Python + Streamlit (single-page app, `app.py`)
- Google GenAI SDK (`google-genai`), Gemini 2.5 Flash
- No database — session-based; audit history saved locally to `audit_history.json`

## Key internals
- `SCENARIOS` — list of dicts with `id`, `label`, `prompt` (lambda: `brand, category → str`)
- `call_gemini(api_key, prompt, system)` — single Gemini call, returns text
- `analyze_mention(text, brand)` — returns `{mentioned, position, snippet}`
- GEO diagnosis = 7th LLM call synthesising all snippets into 3 paragraphs

## Important constraints
- API keys are session-only — never persist them anywhere
- Split `app.py` into `audit.py` + `app.py` only if it exceeds ~600 lines
- See `docs/roadmap.md` for what features to build next
