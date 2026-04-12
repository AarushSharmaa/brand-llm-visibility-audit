"""
Reusable Streamlit render functions.
Each function takes data + calls st.markdown() — no business logic here.
"""

import streamlit as st
from core.models import ActionItem, AuditDiagnosis, CompetitorSOV
from core.config import PROVIDERS


# ── Utilities ────────────────────────────────────────────────────────────────

def score_color(score: int) -> str:
    return "#16a34a" if score >= 67 else "#d97706" if score >= 34 else "#dc2626"

def score_class(score: int) -> str:
    return "score-high" if score >= 67 else "score-mid" if score >= 34 else "score-low"

def section_label(text: str):
    st.markdown(f'<p class="section-label">{text}</p>', unsafe_allow_html=True)

def sentiment_html(sentiment: str | None) -> str:
    if not sentiment:
        return ""
    icons = {"positive": "↑", "neutral": "→", "cautious": "~", "negative": "↓"}
    icon = icons.get(sentiment, "")
    return f'<span class="sent-{sentiment}" style="font-family:Inter,sans-serif;font-size:11px;margin-left:8px">{icon} {sentiment}</span>'

def claims_html(claims: list[str]) -> str:
    if not claims:
        return ""
    pills = "".join(f'<span class="claim-pill">{c}</span>' for c in claims)
    return f'<div class="claims-row">{pills}</div>'


# ── Single scenario card ──────────────────────────────────────────────────────

def render_scenario_card(result: dict, model_dots: list[tuple[str, bool]] = None):
    """
    result: dict with mentioned, position, snippet, sentiment, claims, label, is_probe
    model_dots: [(provider_label, mentioned_bool), ...] for multi-model view
    """
    mentioned = result.get("mentioned", False)
    position = result.get("position")
    snippet = result.get("snippet", "")
    is_probe = result.get("is_probe", False)
    label = result.get("label", "")

    if is_probe:
        card_class = "result-card result-card-probe"
        prefix = '<span class="tag-probe">Probe</span> '
    elif mentioned:
        card_class = "result-card result-card-hit"
        prefix = ""
    else:
        card_class = "result-card result-card-miss"
        prefix = ""

    if mentioned:
        if position:
            tag = f'<span class="tag-yes">Mentioned — #{position}</span>'
        else:
            tag = '<span class="tag-pos">Mentioned</span>'
    else:
        tag = '<span class="tag-no">Not mentioned</span>'

    body = (
        f'<div class="snippet">"{snippet}"</div>'
        if snippet
        else '<p style="font-family:Inter,sans-serif;font-size:12px;color:#cbd5e1;font-style:italic;margin:0">Brand not found in response.</p>'
    )

    sent = sentiment_html(result.get("sentiment")) if mentioned else ""
    clms = claims_html(result.get("claims", [])) if mentioned else ""

    dots_html = ""
    if model_dots and len(model_dots) > 1:
        parts = []
        for provider_key, hit in model_dots:
            short = PROVIDERS.get(provider_key, {}).get("short", provider_key[0].upper())
            dot_class = "dot-hit" if hit else "dot-miss"
            parts.append(
                f'<span class="model-dot-label">{short}</span>'
                f'<span class="model-dot {dot_class}"></span>'
            )
        dots_html = f'<div style="display:flex;align-items:center;gap:4px;margin-top:10px">{"".join(parts)}</div>'

    st.markdown(f"""
    <div class="{card_class}">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:6px">
        <span style="font-size:13px;font-weight:500;color:#0f172a">{prefix}{label}</span>
        <div style="display:flex;align-items:center">{tag}{sent}</div>
      </div>
      {body}
      {clms}
      {dots_html}
    </div>
    """, unsafe_allow_html=True)


# ── Model comparison table ────────────────────────────────────────────────────

def render_model_table(model_audits: list[dict]):
    """
    model_audits: [{provider, score, mention_count, total, avg_position}]
    """
    rows_html = ""
    total_m = sum(a["mention_count"] for a in model_audits)
    total_s = sum(a["total"] for a in model_audits)

    for a in model_audits:
        label = PROVIDERS.get(a["provider"], {}).get("label", a["provider"])
        model_name = a.get("model_name", "")
        cls = score_class(a["score"])
        pos = f"#{a['avg_position']}" if a.get("avg_position") else "—"
        rows_html += f"""
        <tr>
          <td style="font-weight:500;color:#0f172a">{label}
            <span style="color:#94a3b8;font-size:10px;margin-left:6px;font-family:Inter,sans-serif">{model_name}</span></td>
          <td class="{cls}" style="font-size:15px;font-weight:500">{a['score']}%</td>
          <td>{a['mention_count']}/{a['total']}</td>
          <td>{pos}</td>
        </tr>"""

    if len(model_audits) > 1:
        combined = round((total_m / total_s) * 100) if total_s else 0
        cls = score_class(combined)
        rows_html += f"""
        <tr style="opacity:0.45">
          <td>Combined</td>
          <td class="{cls}">{combined}%</td>
          <td>{total_m}/{total_s}</td>
          <td>—</td>
        </tr>"""

    st.markdown(f"""
    <div style="margin:12px 0 20px 0;overflow-x:auto">
      <table class="model-table">
        <thead><tr>
          <th>Model</th><th>Score</th><th>Scenarios</th><th>Avg position</th>
        </tr></thead>
        <tbody>{rows_html}</tbody>
      </table>
    </div>
    """, unsafe_allow_html=True)


# ── Single-model metric cards ─────────────────────────────────────────────────

def render_metric_cards(score: int, mention_count: int, total: int, avg_pos):
    sc = score_color(score)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f'<div class="metric-card"><div class="metric-val" style="color:{sc}">{score}%</div><div class="metric-lbl">◉ Visibility score</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="metric-card"><div class="metric-val">{mention_count} / {total}</div><div class="metric-lbl">Scenarios mentioned</div></div>', unsafe_allow_html=True)
    with c3:
        pos_display = f"#{avg_pos}" if avg_pos else "N/A"
        st.markdown(f'<div class="metric-card"><div class="metric-val">{pos_display}</div><div class="metric-lbl">Avg list position</div></div>', unsafe_allow_html=True)


# ── Probe agent info box ──────────────────────────────────────────────────────

def render_probe_box(rationale: str, probe_count: int):
    if not rationale:
        return
    verb = f"Ran {probe_count} follow-up probe{'s' if probe_count != 1 else ''}" if probe_count else "No follow-up probes needed"
    st.markdown(f"""
    <div class="probe-box">
      <span style="font-family:Inter,sans-serif;font-size:10px;font-weight:500;text-transform:uppercase;letter-spacing:0.08em;color:#6366f1">◈ Probe agent — agent-selected follow-up queries based on your results</span><br>
      <strong style="font-size:13px">{verb}.</strong> {rationale}
    </div>
    """, unsafe_allow_html=True)


# ── Diagnosis ────────────────────────────────────────────────────────────────

def render_diagnosis(diagnosis: AuditDiagnosis, multi_model: bool = False):
    box_class = "cross-model-box" if multi_model else "geo-box"

    # Status + root cause
    st.markdown(f"""
    <div class="{box_class}">
      <p style="margin:0 0 12px 0;color:#0f172a">{diagnosis.status_summary}</p>
      <p style="margin:0;color:#64748b;font-size:13px">{diagnosis.root_cause}</p>
    </div>
    """, unsafe_allow_html=True)

    # Cross-model note
    if diagnosis.cross_model_note:
        st.markdown(f"""
        <div style="background:#eef2ff;border:1px solid #c7d2fe;border-radius:6px;padding:12px 16px;margin-top:10px;font-size:13px;color:#3730a3;line-height:1.6">
          <span style="font-family:Inter,sans-serif;font-size:10px;font-weight:500;text-transform:uppercase;letter-spacing:0.08em;color:#6366f1">Why models disagree</span><br>{diagnosis.cross_model_note}
        </div>
        """, unsafe_allow_html=True)

    if not diagnosis.actions:
        return

    st.markdown(
        '<p style="font-family:Inter,sans-serif;font-size:10px;text-transform:uppercase;letter-spacing:0.1em;color:#94a3b8;margin:20px 0 4px 0">Recommended actions</p>'
        '<p style="font-family:Inter,sans-serif;font-size:10px;color:#cbd5e1;margin:0 0 12px 0">Confidence reflects how strongly the evidence supports each action. Under 60% is a hypothesis, not a confirmed pattern.</p>',
        unsafe_allow_html=True,
    )

    for action in diagnosis.actions:
        conf = action.confidence
        conf_pct = round(conf * 100)
        if conf >= 0.75:
            card_cls = "action-card action-card-high-conf"
            bar_color = "#84cc16"
        elif conf >= 0.55:
            card_cls = "action-card action-card-mid-conf"
            bar_color = "#f59e0b"
        else:
            card_cls = "action-card action-card-low-conf"
            bar_color = "#e2e8f0"

        caveat = (
            '<span style="font-family:Inter,sans-serif;font-size:10px;color:#94a3b8;font-style:italic"> — hypothesis, needs validation</span>'
            if conf < 0.6 else ""
        )

        scenarios_text = ", ".join(action.scenarios_driving_it) if action.scenarios_driving_it else "—"
        effort_color = {"low": "#16a34a", "medium": "#d97706", "high": "#dc2626"}.get(action.effort, "#94a3b8")
        impact_color = {"low": "#94a3b8", "medium": "#d97706", "high": "#16a34a"}.get(action.impact, "#94a3b8")

        st.markdown(f"""
        <div class="{card_cls}">
          <p style="margin:0 0 8px 0;font-size:13px;color:#0f172a">{action.action}{caveat}</p>
          <div style="display:flex;gap:16px;flex-wrap:wrap">
            <span style="font-family:Inter,sans-serif;font-size:10px;color:#94a3b8">Driven by: <span style="color:#64748b">{scenarios_text}</span></span>
            <span style="font-family:Inter,sans-serif;font-size:10px;color:#94a3b8">Effort: <span style="color:{effort_color}">{action.effort}</span></span>
            <span style="font-family:Inter,sans-serif;font-size:10px;color:#94a3b8">Impact: <span style="color:{impact_color}">{action.impact}</span></span>
          </div>
          <div class="confidence-bar-bg" style="margin-top:10px">
            <div class="confidence-bar" style="width:{conf_pct}%;background:{bar_color}"></div>
          </div>
          <p style="font-family:Inter,sans-serif;font-size:10px;color:#94a3b8;margin:3px 0 0 0">confidence {conf_pct}%</p>
        </div>
        """, unsafe_allow_html=True)


# ── Competitor score table ────────────────────────────────────────────────────

def render_competitor_score_table(
    brand: str, brand_score: int, brand_mc: int, brand_total: int,
    competitor_rows: list[dict],
):
    """
    Renders a ranked score table comparing the main brand against competitors.
    competitor_rows: [{"name": str, "score": int, "mention_count": int, "total": int}]
    """
    all_rows = [{"name": brand, "score": brand_score, "mention_count": brand_mc, "total": brand_total, "is_brand": True}]
    for r in competitor_rows:
        all_rows.append({**r, "is_brand": False})
    all_rows.sort(key=lambda x: x["score"], reverse=True)

    rows_html = ""
    for row in all_rows:
        cls = score_class(row["score"])
        you_badge = ' <span style="font-size:10px;color:#94a3b8;font-family:Inter,sans-serif;font-weight:400">you</span>' if row["is_brand"] else ""
        name_style = "font-weight:600;color:#0f172a" if row["is_brand"] else "color:#475569"
        rows_html += f"""
        <tr>
          <td style="{name_style};font-family:Inter,sans-serif">{row["name"]}{you_badge}</td>
          <td class="{cls}" style="font-size:15px;font-weight:600;font-family:Inter,sans-serif">{row["score"]}%</td>
          <td style="color:#64748b;font-family:Inter,sans-serif">{row["mention_count"]} / {row["total"]}</td>
        </tr>"""

    st.markdown(f"""
    <div style="margin:0 0 24px 0;overflow-x:auto">
      <table class="model-table">
        <thead><tr>
          <th>Brand</th><th>Score</th><th>Mentioned in</th>
        </tr></thead>
        <tbody>{rows_html}</tbody>
      </table>
    </div>
    <p style="font-family:Inter,sans-serif;font-size:10px;color:#94a3b8;margin-top:-16px">Each competitor audited independently across the same 6 scenarios.</p>
    """, unsafe_allow_html=True)


# ── Competitor SOV ────────────────────────────────────────────────────────────

def render_sov_table(brand: str, brand_mentions: int, competitors: list[CompetitorSOV], total_responses: int):
    all_entries = [(brand, brand_mentions, round(brand_mentions / total_responses * 100, 1) if total_responses else 0)]
    for c in competitors:
        all_entries.append((c.name, c.mentions, c.share_pct))

    all_entries.sort(key=lambda x: x[2], reverse=True)

    rows_html = ""
    for name, mentions, share in all_entries:
        is_brand = name == brand
        name_style = "color:#0f172a;font-weight:600" if is_brand else "color:#475569"
        bar_color = "#84cc16" if is_brand else "#e2e8f0"
        rows_html += f"""
        <tr>
          <td style="{name_style}">{name}{"  ←" if is_brand else ""}</td>
          <td style="color:#666;font-size:11px">{mentions}/{total_responses}</td>
          <td style="width:40%">
            <div class="sov-bar-bg">
              <div class="sov-bar" style="width:{min(share, 100)}%;background:{bar_color}"></div>
            </div>
          </td>
          <td style="color:#ccc;font-size:12px">{share}%</td>
        </tr>"""

    st.markdown(f"""
    <div style="overflow-x:auto;margin-top:8px">
      <table class="sov-table">
        <thead><tr>
          <th>Brand</th><th>Mentions</th><th>Share of voice</th><th>%</th>
        </tr></thead>
        <tbody>{rows_html}</tbody>
      </table>
    </div>
    <p style="font-family:Inter,sans-serif;font-size:10px;color:#94a3b8;margin-top:6px">Computed from {total_responses} AI responses — no extra API calls.</p>
    """, unsafe_allow_html=True)
