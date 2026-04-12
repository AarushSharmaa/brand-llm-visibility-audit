# Roadmap

## The problem

Search is shifting. When someone asks ChatGPT or Perplexity "what's the best CRM right now?", the brands that show up win the click — and most companies have no idea where they stand.

Two audiences feel this acutely:

- **Early-stage startups** trying to break into a category where incumbents already dominate AI responses
- **Established brands** that spent years perfecting SEO, now discovering AI plays by entirely different rules — their Google rankings mean nothing here

This tool gives both a clear answer in 2 minutes: here's where you stand, here's who's beating you, here's what to fix.

---

## What's built

- 6 discovery scenarios covering the full buyer journey (market discovery → recommendation → comparison)
- Visibility score, list position, and response snippets per scenario
- GEO diagnosis: a direct, opinionated read on why the brand is invisible and what to do

---

## What's next — and why in this order

### 1. Sentiment tagging
**The insight that turns a mention into signal.** "X is an option, but it's expensive" and "X is the go-to tool" both count as mentions — but they're completely different positions. Every paid GEO tool ($29–$500/mo) sells this. We do it with one extra classification per scenario.

- Label each mention: positive, neutral, cautious, or negative
- Show the sentiment tag alongside the mention status on each result card
- Factor sentiment into the GEO diagnosis

### 2. Multi-LLM comparison
**The real picture is across all the models that matter.** Gemini, ChatGPT, and Claude each have different training data and surface different brands. A legacy brand might rank well on Gemini but be invisible on Claude. That variance is where the story lives — averaging it away hides the signal.

- Run the same 6 prompts across all models the user has keys for
- Show a score-per-model comparison table — make variance visible, not smoothed out
- Only activate models the user provides keys for

### 3. Competitor share of voice
**Context turns a score into a decision.** "You have 83% visibility" is forgettable. "You have 12% share of voice vs. your main competitor's 41%" is a budget conversation. This is the number a CMO actually acts on.

- Up to 3 competitor inputs, same category as primary brand
- Run the full audit on each, show side-by-side scores
- Calculate share of voice: % of total category mentions going to each brand

### 5. Agentic & reasoning depth
**The leap from audit to analyst.** The current tool runs 6 fixed prompts and synthesizes a diagnosis in one pass. That's a reporter, not an analyst. These capabilities turn it into something that reasons about what it finds, adapts as it goes, and explains its conclusions — the difference between a dashboard and an actual consultant.

#### A. Chain-of-thought diagnosis with visible reasoning trace
Replace the GEO diagnosis call with a reasoning model (Gemini 2.5 Flash `thinking_config` or Claude extended thinking). The model reasons step-by-step — weighing contradictions across scenarios, inferring root causes, and stress-testing its own conclusions — before writing the final diagnosis. Surface the reasoning chain as a collapsible "show thinking" block so users can audit the logic, not just trust the output.

- **Why it matters:** "Mentioned in 1 scenario, invisible in 5" requires genuine reasoning to diagnose correctly. A standard LLM call describes the pattern; a CoT model explains the *mechanism* — why training data, content framing, or positioning gaps are causing it. That's actionable; a description isn't.
- **What the reasoning trace shows:** Which scenarios contradict each other → what that implies about the brand's positioning → which competitor is winning each gap and why → the root cause hypothesis the model settled on and what it ruled out.
- **Implementation:** `thinking_config={"thinking_budget": 8000}` for Gemini 2.5 Flash; `betas=["thinking"]` for Claude. The reasoning chain is returned as a separate field and rendered collapsed by default.

#### B. Adaptive agentic probe loop
After the initial 6 scenarios, an orchestrator agent reviews the results and decides whether to run 1–3 targeted follow-up probes based on what it found:
- Invisible brand (≤2 mentions): probe alternate phrasings of the category query — "best tools for X" vs "what does everyone use for X" vs "X software recommendations"
- Mentioned with caveats or negatively: dig into the specific framing — is the negative association consistent or query-dependent?
- Strong score: test edge cases — niche segments, regional queries, persona-specific variants

The agent runs these autonomously, folds results into the final score and diagnosis, and surfaces which follow-up queries it chose and why. Users see the probe rationale, not just the result.

- **Why it matters:** Fixed prompts miss how real buyers actually phrase questions. An adaptive agent surfaces a more accurate picture *and* tells you which query angles you're winning or losing — information no fixed-prompt tool can give you.
- **Implementation:** Orchestration loop where an LLM returns structured JSON `{"probes": [...], "rationale": "..."}`. Max 2 rounds, ~3–6 extra calls. Configurable depth.

#### C. Claim extraction and framing analysis
Go beyond mention detection — extract *what the LLM actually says* about the brand. For each mention, the model identifies the claims being made: "expensive," "best for enterprises," "limited integrations," "founder-led," "recently acquired." Then a reasoning pass flags which claims are accurate, which are outdated, and which are wrong or missing — giving the brand a content brief, not just a score.

- **Why it matters:** Every serious GEO tool sells mention rate. None of them tell you *what the model says when it mentions you*. A brand can have 83% visibility with uniformly weak framing ("Notion is an option") and lose to a competitor at 50% with strong framing ("Notion is the go-to for teams"). Claim extraction is what turns visibility data into a content strategy.
- **Implementation:** Structured output on each scenario call: `{"mentioned": bool, "claims": [...], "framing": "positive|neutral|cautious|negative"}`. Claim list rendered as pills on the result card.

#### D. Cross-model disagreement reasoning
When two or more models disagree (one mentions the brand, another doesn't), a reasoning agent hypothesizes *why* — training data cutoff, category framing differences, how the brand is represented in the sources each model weights. This is surfaced as a one-paragraph "why models disagree" note on any scenario where variance exists.

- **Why it matters:** Variance is the most valuable signal in a multi-model audit. Showing "Gemini ✓, ChatGPT ✗" is data; explaining "ChatGPT appears to associate this category with Atlassian products — your brand doesn't appear in the enterprise content it learned from" is insight. No current GEO tool offers this.
- **Implementation:** Per-scenario reasoning call triggered only when models disagree. Light — one extra call per disagreement scenario, using the reasoning model.

#### E. Reasoning-backed action plan with confidence scores
Replace the 3-paragraph diagnosis with structured output: diagnosis → root cause → prioritized actions. Each action includes: what to do, which scenarios drove it, effort estimate (low/med/high), expected impact (low/med/high), and a confidence score (0–1) reflecting how strongly the evidence supports it. Low-confidence actions are shown with a caveat — "this is a hypothesis, not a confirmed pattern."

- **Why it matters:** "Write more authoritative content" is forgettable. "Add a comparison page vs. Obsidian — they appear in 5/6 scenarios you don't, comparison queries are your biggest gap, and this is a low-effort, high-impact fix [confidence: 0.91]" is a decision. Confidence scoring is what separates an analyst's recommendation from a generic suggestion.
- **Implementation:** Structured output schema. Action cards rendered as styled components. Confidence score shown as a subtle bar under each action.

### 6. Shareable PDF report
**The loop closer.** The person running this audit is rarely the final decision-maker. Give them something to send — not a screenshot.

- One-click export: score, sentiment breakdown, model comparison, GEO diagnosis
- Styled to match the app — something you'd attach to a deck

---

## Intentionally out of scope
No user accounts, no database, no automated monitoring, no trend tracking (useful only after repeat usage — not the core value). This is a fast, on-demand audit. Keeping it manual is a deliberate product choice.
