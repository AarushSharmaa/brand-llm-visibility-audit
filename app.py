"""
Brand LLM Visibility Audit — main entry point.

Architecture:
  core/       — config, Pydantic data models
  llm/        — unified LLM client (Gemini, Groq, OpenAI, Perplexity, Claude)
  agents/     — analyzer, probe agent (agentic loop), diagnosis agent
  ui/         — CSS + reusable render components
  app.py      — thin Streamlit orchestrator (UI state + agent calls only)
"""

import time
import streamlit as st

from core.config import PROVIDERS, PRIMARY_PROVIDERS, OPTIONAL_PROVIDERS, SCENARIOS, PRESET_BRANDS
from core.models import CompetitorSOV
from llm.client import call_llm
from agents.analyzer import detect_mention, enrich_with_claims, count_competitor_mentions
from agents.probe_agent import ProbeAgent
from agents.diagnosis_agent import DiagnosisAgent
from ui.styles import CSS
from ui.components import (
    section_label, render_scenario_card, render_model_table,
    render_metric_cards, render_probe_box, render_diagnosis, render_sov_table,
)

st.set_page_config(page_title="Brand LLM Visibility", page_icon="◉", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)


# ── Sidebar — all inputs ───────────────────────────────────────────────────────

with st.sidebar:
    st.markdown(
        '<div class="sidebar-logo">'
        '<span class="sidebar-logo-dot">◉</span>'
        '<span class="sidebar-logo-text">LLM Visibility</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="sidebar-section-label">Brand</div>', unsafe_allow_html=True)
    preset = st.selectbox("Quick-pick", options=list(PRESET_BRANDS.keys()), label_visibility="collapsed")
    brand = st.text_input("Brand name", value=PRESET_BRANDS[preset]["brand"], placeholder="e.g. Notion")
    category = st.text_input(
        "Category",
        value=PRESET_BRANDS[preset]["category"],
        placeholder="e.g. productivity software",
        help="The product space your brand competes in — e.g. CRM, note-taking, AI search.",
    )

    st.markdown('<div class="sidebar-section-label" style="margin-top:20px">Model</div>', unsafe_allow_html=True)
    primary_options = {
        pk: f"{PROVIDERS[pk]['label']}"
        for pk in PRIMARY_PROVIDERS
    }
    primary_provider_key = st.selectbox(
        "Primary provider",
        options=list(primary_options.keys()),
        format_func=lambda k: primary_options[k],
        label_visibility="collapsed",
    )
    primary_provider = PROVIDERS[primary_provider_key]
    primary_model_options = primary_provider["models"]
    selected_model = st.selectbox(
        "Model variant",
        options=list(primary_model_options.keys()),
        format_func=lambda k: primary_model_options[k],
        help="Higher quality models give more nuanced results. Default is fine for most audits.",
    )
    primary_api_key = st.text_input(
        f"{primary_provider['label']} API key",
        type="password",
        placeholder=primary_provider["key_hint"],
    )

    with st.expander("Add more models — optional"):
        st.markdown(
            '<p style="font-size:11px;color:#52525b;margin-bottom:12px;font-family:Inter,sans-serif">'
            "Compare visibility across ChatGPT, Perplexity, Claude."
            "</p>",
            unsafe_allow_html=True,
        )
        extra_keys: dict[str, tuple[str, str]] = {}
        for pk in OPTIONAL_PROVIDERS:
            p = PROVIDERS[pk]
            k = st.text_input(
                f"{p['label']}",
                type="password",
                placeholder=p["key_hint"],
                key=f"key_{pk}",
            )
            m = st.selectbox(
                "Model",
                options=list(p["models"].keys()),
                format_func=lambda x, p=p: p["models"][x],
                key=f"model_{pk}",
                label_visibility="collapsed",
            )
            if k:
                extra_keys[pk] = (k, m)

    st.markdown('<div class="sidebar-section-label" style="margin-top:20px">Competitors</div>', unsafe_allow_html=True)
    competitors_input = []
    for i in range(3):
        c = st.text_input(f"Competitor {i+1}", placeholder="e.g. Notion", key=f"comp_{i}", label_visibility="collapsed")
        if c.strip():
            competitors_input.append(c.strip())

    st.markdown("<br>", unsafe_allow_html=True)
    run = st.button("Run audit", use_container_width=True)

    st.markdown("""
    <div class="sidebar-footer">
        Built by
        <a href="https://aarushsharmaa.github.io/aarush-sharma/" target="_blank" class="sidebar-footer-link">Aarush Sharma</a>
    </div>
    """, unsafe_allow_html=True)


# ── Main content ───────────────────────────────────────────────────────────────

if not run:
    # Empty state
    st.markdown("""
    <div class="empty-state">
        <div class="empty-state-icon">◉</div>
        <h2 class="empty-state-title">Brand LLM Visibility Audit</h2>
        <p class="empty-state-sub">
            See how your brand appears across AI models — ChatGPT, Gemini, Perplexity, and more. Configure your brand and API key in the sidebar, then run the audit.
        </p>
        <div class="empty-state-pills">
            <span class="empty-pill">Visibility score</span>
            <span class="empty-pill">Position tracking</span>
            <span class="empty-pill">Sentiment analysis</span>
            <span class="empty-pill">Adaptive probe agent</span>
            <span class="empty-pill">Competitor share of voice</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()


# ── Validate ───────────────────────────────────────────────────────────────────

if not primary_api_key:
    st.error(f"Paste your {primary_provider['label']} API key in the sidebar to run the audit.")
    st.stop()
if not brand or not category:
    st.error("Fill in brand name and category in the sidebar.")
    st.stop()

# ── Run audit ──────────────────────────────────────────────────────────────────

active_models: dict[str, tuple[str, str]] = {primary_provider_key: (primary_api_key, selected_model)}
active_models.update(extra_keys)
multi = len(active_models) > 1

# Context bar
st.markdown(
    f'<div class="context-bar">'
    f'<span class="context-brand">{brand}</span>'
    f'<span class="context-sep">/</span>'
    f'<span class="context-category">{category}</span>'
    f'<span class="context-sep">·</span>'
    f'<span class="context-models">{len(active_models)} model{"s" if multi else ""} · {len(SCENARIOS)} scenarios</span>'
    f'</div>',
    unsafe_allow_html=True,
)

# Progress tracking
results_by_provider: dict[str, list[dict]] = {}
probe_by_provider: dict[str, tuple[list[dict], str]] = {}
progress = st.empty()


def render_progress(current_provider: str, current_scenario_idx: int, done: list[str]):
    lines = []
    for pk in active_models:
        label = PROVIDERS[pk]["label"]
        if pk in done:
            lines.append(f'<span style="font-size:12px;color:#16a34a;font-family:Inter,sans-serif;margin-right:16px">✓ {label}</span>')
        elif pk == current_provider:
            s_label = SCENARIOS[current_scenario_idx]["label"] if current_scenario_idx < len(SCENARIOS) else "probing..."
            lines.append(f'<span style="font-size:12px;color:#d97706;font-family:Inter,sans-serif;margin-right:16px">⟳ {label} — {s_label}</span>')
        else:
            lines.append(f'<span style="font-size:12px;color:#cbd5e1;font-family:Inter,sans-serif;margin-right:16px">◌ {label}</span>')
    progress.markdown(
        f'<div style="padding:12px 0;border-bottom:1px solid #e2e8f0;margin-bottom:20px">{"".join(lines)}</div>',
        unsafe_allow_html=True,
    )


done_providers: list[str] = []
error_occurred = False

for pk, (api_key_val, model_name) in active_models.items():
    provider_results: list[dict] = []

    for idx, scenario in enumerate(SCENARIOS):
        render_progress(pk, idx, done_providers)
        try:
            prompt = scenario["prompt"](brand, category)
            response_text = call_llm(pk, model_name, api_key_val, prompt)
            analysis = detect_mention(response_text, brand)
            provider_results.append({
                "scenario_id": scenario["id"],
                "label": scenario["label"],
                "prompt_used": prompt,
                "response": response_text,
                "mentioned": analysis["mentioned"],
                "position": analysis["position"],
                "snippet": analysis["snippet"],
                "sentiment": None,
                "claims": [],
                "is_probe": False,
            })
        except Exception as e:
            st.error(f"{PROVIDERS[pk]['label']} / {scenario['label']}: {e}")
            error_occurred = True
            break
        time.sleep(0.15)

    if error_occurred:
        break

    try:
        provider_results = enrich_with_claims(pk, model_name, api_key_val, brand, provider_results)
    except Exception:
        pass

    results_by_provider[pk] = provider_results

    render_progress(pk, len(SCENARIOS), done_providers)
    if pk == primary_provider_key:
        try:
            probe_agent = ProbeAgent(pk, model_name, api_key_val)
            probe_results, probe_rationale = probe_agent.run(brand, category, provider_results)
            probe_by_provider[pk] = (probe_results, probe_rationale)
        except Exception:
            probe_by_provider[pk] = ([], "")
    else:
        probe_by_provider[pk] = ([], "")

    done_providers.append(pk)
    render_progress(None, 0, done_providers)

if error_occurred or not results_by_provider:
    st.stop()

progress.empty()

# ── Compute summary stats ─────────────────────────────────────────────────────

pk_primary = primary_provider_key
primary_results = results_by_provider[pk_primary]
probe_results, probe_rationale = probe_by_provider.get(pk_primary, ([], ""))
all_primary = primary_results + probe_results
mc = sum(1 for r in all_primary if r["mentioned"])
total = len(all_primary)
positions = [r["position"] for r in all_primary if r.get("position") is not None]
avg_pos = round(sum(positions) / len(positions), 1) if positions else None
score = round((mc / total) * 100) if total else 0

sentiments = [r.get("sentiment") for r in all_primary if r.get("mentioned") and r.get("sentiment")]
pos_count = sentiments.count("positive")
neg_count = sentiments.count("negative")
dominant_sentiment = "positive" if pos_count > neg_count else ("negative" if neg_count > pos_count else "neutral")

# ── Tabs — Peec AI section structure ─────────────────────────────────────────

tab_labels = ["Overview", "Scenarios", "Diagnosis"]
if competitors_input:
    tab_labels.append("Competitors")
if multi:
    tab_labels.insert(1, "Model comparison")

tabs = st.tabs(tab_labels)
tab_map = {label: tab for label, tab in zip(tab_labels, tabs)}


# ── Tab: Overview ─────────────────────────────────────────────────────────────

with tab_map["Overview"]:
    st.markdown("<br>", unsafe_allow_html=True)

    if multi:
        model_audit_data = []
        for pk, results in results_by_provider.items():
            probe_r, _ = probe_by_provider.get(pk, ([], ""))
            all_r = results + probe_r
            mc_p = sum(1 for r in all_r if r.get("mentioned"))
            total_p = len(all_r)
            pos_p = [r["position"] for r in all_r if r.get("position") is not None]
            avg_p = round(sum(pos_p) / len(pos_p), 1) if pos_p else None
            model_audit_data.append({
                "provider": pk,
                "model_name": active_models[pk][1],
                "score": round((mc_p / total_p) * 100) if total_p else 0,
                "mention_count": mc_p,
                "total": total_p,
                "avg_position": avg_p,
            })
        render_metric_cards(score, mc, total, avg_pos)
        st.markdown("<br>", unsafe_allow_html=True)
        section_label("Across models")
        render_model_table(model_audit_data)
    else:
        render_metric_cards(score, mc, total, avg_pos)

    if probe_rationale or probe_results:
        st.markdown("<br>", unsafe_allow_html=True)
        section_label("Probe agent")
        render_probe_box(probe_rationale, len(probe_results))


# ── Tab: Model comparison (multi only) ───────────────────────────────────────

if multi and "Model comparison" in tab_map:
    with tab_map["Model comparison"]:
        st.markdown("<br>", unsafe_allow_html=True)
        render_model_table(model_audit_data)


# ── Tab: Scenarios ────────────────────────────────────────────────────────────

with tab_map["Scenarios"]:
    st.markdown("<br>", unsafe_allow_html=True)
    section_label(f"{len(SCENARIOS)} standard scenarios")
    for idx, scenario in enumerate(SCENARIOS):
        primary_r = primary_results[idx] if idx < len(primary_results) else {}
        model_dots = None
        if multi:
            model_dots = [
                (pk, results_by_provider[pk][idx].get("mentioned", False))
                for pk in active_models
                if idx < len(results_by_provider.get(pk, []))
            ]
        render_scenario_card(primary_r, model_dots=model_dots)

    if probe_results:
        st.markdown("<br>", unsafe_allow_html=True)
        section_label("Follow-up probes — agent-selected")
        for pr in probe_results:
            render_scenario_card(pr)


# ── Tab: Diagnosis ────────────────────────────────────────────────────────────

with tab_map["Diagnosis"]:
    st.markdown("<br>", unsafe_allow_html=True)
    with st.spinner("Generating diagnosis..."):
        try:
            api_key_val, model_name = active_models[pk_primary]
            diag_agent = DiagnosisAgent(pk_primary, model_name, api_key_val)
            diagnosis = diag_agent.run(brand, category, results_by_provider, probe_by_provider)
            render_diagnosis(diagnosis, multi_model=multi)
        except Exception as e:
            st.error(f"Could not generate diagnosis: {e}")


# ── Tab: Competitors ──────────────────────────────────────────────────────────

if competitors_input and "Competitors" in tab_map:
    with tab_map["Competitors"]:
        st.markdown("<br>", unsafe_allow_html=True)
        all_responses = []
        for pk, results in results_by_provider.items():
            all_responses.extend(r.get("response", "") for r in results)
            probe_r, _ = probe_by_provider.get(pk, ([], ""))
            all_responses.extend(r.get("response", "") for r in probe_r)

        total_responses = len(all_responses)
        brand_mentions = count_competitor_mentions(all_responses, brand)
        competitor_sovs = []
        for comp_name in competitors_input:
            mentions = count_competitor_mentions(all_responses, comp_name)
            competitor_sovs.append(CompetitorSOV(
                name=comp_name,
                mentions=mentions,
                total_responses=total_responses,
            ))
        render_sov_table(brand, brand_mentions, competitor_sovs, total_responses)
