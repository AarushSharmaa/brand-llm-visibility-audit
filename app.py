import streamlit as st
from google import genai
from google.genai import types
import re
import time

st.set_page_config(
    page_title="Brand LLM Visibility Audit",
    page_icon="◉",
    layout="centered"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&family=Lora:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'Lora', Georgia, serif;
}

.stApp {
    background-color: #0f0f0f;
    color: #e8e8e8;
}

h1, h2, h3 {
    font-family: 'Lora', Georgia, serif !important;
    font-weight: 400 !important;
    color: #e8e8e8 !important;
}

.stTextInput > div > div > input,
.stSelectbox > div > div > div,
.stTextArea > div > div > textarea {
    background-color: #1a1a1a !important;
    border: 1px solid #2e2e2e !important;
    border-radius: 6px !important;
    color: #e8e8e8 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 13px !important;
}

.stSelectbox > div > div > div {
    color: #e8e8e8 !important;
}

.stButton > button {
    background-color: #a3e635 !important;
    color: #0f0f0f !important;
    border: none !important;
    border-radius: 6px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    padding: 10px 28px !important;
    letter-spacing: 0.04em !important;
}

.stButton > button:hover {
    background-color: #bef264 !important;
    color: #0f0f0f !important;
}

label, .stSelectbox label, .stTextInput label {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 11px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
    color: #888 !important;
}

hr {
    border-color: #2e2e2e !important;
    margin: 24px 0 !important;
}

.metric-card {
    background: #1a1a1a;
    border: 1px solid #2e2e2e;
    border-radius: 8px;
    padding: 16px;
    text-align: left;
}

.metric-val {
    font-size: 26px;
    font-weight: 500;
    font-family: 'JetBrains Mono', monospace;
    margin-bottom: 4px;
}

.metric-lbl {
    font-size: 11px;
    font-family: 'JetBrains Mono', monospace;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #666;
}

.result-card {
    border: 0.5px solid #2e2e2e;
    border-radius: 8px;
    padding: 14px 16px;
    margin-bottom: 10px;
    background: #1a1a1a;
}

.result-card-hit {
    border-left: 3px solid #a3e635;
}

.result-card-miss {
    border-left: 3px solid #2e2e2e;
    opacity: 0.7;
}

.section-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #666;
    margin-bottom: 12px;
    padding-bottom: 8px;
    border-bottom: 0.5px solid #2e2e2e;
}

.tag-yes {
    background: rgba(163,230,53,0.15);
    color: #a3e635;
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    padding: 3px 8px;
    border-radius: 4px;
}

.tag-pos {
    background: rgba(251,191,36,0.1);
    color: #fbbf24;
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    padding: 3px 8px;
    border-radius: 4px;
}

.tag-no {
    background: #1e1e1e;
    color: #555;
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    padding: 3px 8px;
    border-radius: 4px;
}

.snippet {
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    color: #888;
    line-height: 1.7;
    border-left: 2px solid #2e2e2e;
    padding-left: 10px;
    margin-top: 8px;
}

.geo-box {
    background: #1a1a1a;
    border: 1px solid #2e2e2e;
    border-radius: 8px;
    padding: 20px;
    font-size: 14px;
    line-height: 1.85;
    color: #ccc;
}

.footer-note {
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    color: #444;
    text-align: center;
    margin-top: 40px;
}

div[data-testid="stStatusWidget"] { display: none; }
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

PRESET_BRANDS = {
    "Custom (type below)": {"brand": "", "category": ""},
    "Peec AI": {"brand": "Peec AI", "category": "generative engine optimization"},
    "Notion": {"brand": "Notion", "category": "productivity and note-taking software"},
    "Perplexity": {"brand": "Perplexity", "category": "AI-powered search"},
    "HubSpot": {"brand": "HubSpot", "category": "CRM and marketing automation"},
    "Salesforce": {"brand": "Salesforce", "category": "enterprise CRM"},
    "Intercom": {"brand": "Intercom", "category": "customer support and messaging"},
    "Linear": {"brand": "Linear", "category": "software project management"},
}

SCENARIOS = [
    {
        "id": 1,
        "label": "Market discovery",
        "prompt": lambda b, c: f"List the top 5 companies in the {c} space. Rank them with a one-line description each."
    },
    {
        "id": 2,
        "label": "Tool recommendation",
        "prompt": lambda b, c: f"I need a {c} solution for my company. What are the best options right now and why?"
    },
    {
        "id": 3,
        "label": "Brand knowledge",
        "prompt": lambda b, c: f"Tell me about {b}. What do they do, what is their core product, and who is it for?"
    },
    {
        "id": 4,
        "label": "Competitive landscape",
        "prompt": lambda b, c: f"Who are the main players in the {c} market today? Give me a quick rundown."
    },
    {
        "id": 5,
        "label": "Best-in-class search",
        "prompt": lambda b, c: f"What is the best {c} tool right now? Give me your honest recommendation."
    },
    {
        "id": 6,
        "label": "Vendor comparison",
        "prompt": lambda b, c: f"How does {b} compare to its main competitors in {c}? What are the key tradeoffs?"
    },
]


def call_gemini(api_key: str, prompt: str, system: str = None) -> str:
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(
            system_instruction=system or "You are a helpful AI assistant. Answer questions naturally and concisely."
        ),
        contents=prompt
    )
    return response.text


def analyze_mention(text: str, brand: str) -> dict:
    if not text:
        return {"mentioned": False, "position": None, "snippet": ""}

    lower = text.lower()
    b_lower = brand.lower()
    mentioned = b_lower in lower

    position = None
    snippet = ""

    if mentioned:
        esc = re.escape(brand)
        m = re.search(r'(\d+)[.)]\s[^\n]{0,80}?' + esc, text, re.IGNORECASE)
        if m:
            position = int(m.group(1))

        idx = lower.index(b_lower)
        start = max(0, idx - 60)
        end = min(len(text), idx + len(brand) + 140)
        snippet = ("..." if start > 0 else "") + text[start:end].strip() + ("..." if end < len(text) else "")

    return {"mentioned": mentioned, "position": position, "snippet": snippet}


def render_section_label(text):
    st.markdown(f'<p class="section-label">{text}</p>', unsafe_allow_html=True)


def render_result_card(scenario_label, mentioned, position, snippet):
    card_class = "result-card result-card-hit" if mentioned else "result-card result-card-miss"

    if mentioned:
        if position:
            tag = f'<span class="tag-yes">Mentioned &mdash; #{position} in list</span>'
        else:
            tag = '<span class="tag-pos">Mentioned &mdash; no list rank</span>'
    else:
        tag = '<span class="tag-no">Not mentioned</span>'

    if snippet:
        body = f'<div class="snippet">"{snippet}"</div>'
    else:
        body = '<p style="font-family: JetBrains Mono, monospace; font-size:12px; color:#444; font-style:italic; margin:0">Brand not found in response.</p>'

    st.markdown(f"""
    <div class="{card_class}">
        <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:8px">
            <span style="font-size:13px; font-weight:500; color:#e8e8e8">{scenario_label}</span>
            {tag}
        </div>
        {body}
    </div>
    """, unsafe_allow_html=True)


# Header
st.markdown("## Brand LLM visibility audit")
st.markdown('<p style="font-family: JetBrains Mono, monospace; font-size:13px; color:#666; margin-bottom:28px">6 discovery scenarios. See how Gemini talks about your brand.</p>', unsafe_allow_html=True)

# API Key
api_key = st.text_input("Gemini API key", type="password", placeholder="AIza... (your key stays in this session only)")

st.markdown("<br>", unsafe_allow_html=True)

# Brand picker
preset = st.selectbox("Quick-pick a brand", options=list(PRESET_BRANDS.keys()))

col1, col2 = st.columns(2)
with col1:
    brand_default = PRESET_BRANDS[preset]["brand"]
    brand = st.text_input("Brand name", value=brand_default, placeholder="e.g. Notion")
with col2:
    cat_default = PRESET_BRANDS[preset]["category"]
    category = st.text_input("Category", value=cat_default, placeholder="e.g. productivity software")

st.markdown("<br>", unsafe_allow_html=True)
run = st.button("Run audit")

if run:
    if not api_key:
        st.error("Paste your Gemini API key above to run the audit.")
    elif not brand or not category:
        st.error("Fill in both brand name and category.")
    else:
        st.markdown("---")
        render_section_label("Running scenarios")

        progress_placeholder = st.empty()
        results = []

        def render_progress(current_id, done_ids):
            lines = []
            for s in SCENARIOS:
                if s["id"] in done_ids:
                    lines.append(f'<div style="display:flex;align-items:center;gap:8px;padding:4px 0"><div style="width:7px;height:7px;border-radius:50%;background:#a3e635;flex-shrink:0"></div><span style="font-family:JetBrains Mono,monospace;font-size:12px;color:#a3e635">{s["label"]}</span></div>')
                elif s["id"] == current_id:
                    lines.append(f'<div style="display:flex;align-items:center;gap:8px;padding:4px 0"><div style="width:7px;height:7px;border-radius:50%;background:#fbbf24;flex-shrink:0"></div><span style="font-family:JetBrains Mono,monospace;font-size:12px;color:#fbbf24">{s["label"]} &mdash; running...</span></div>')
                else:
                    lines.append(f'<div style="display:flex;align-items:center;gap:8px;padding:4px 0"><div style="width:7px;height:7px;border-radius:50%;background:#2e2e2e;flex-shrink:0"></div><span style="font-family:JetBrains Mono,monospace;font-size:12px;color:#555">{s["label"]}</span></div>')
            progress_placeholder.markdown("".join(lines), unsafe_allow_html=True)

        done_ids = []
        error_occurred = False

        for scenario in SCENARIOS:
            render_progress(scenario["id"], done_ids)
            try:
                prompt = scenario["prompt"](brand, category)
                response_text = call_gemini(api_key, prompt)
                analysis = analyze_mention(response_text, brand)
                results.append({
                    "label": scenario["label"],
                    "mentioned": analysis["mentioned"],
                    "position": analysis["position"],
                    "snippet": analysis["snippet"],
                    "response": response_text
                })
            except Exception as e:
                st.error(f"Error on '{scenario['label']}': {str(e)}")
                error_occurred = True
                break
            done_ids.append(scenario["id"])
            time.sleep(0.3)

        render_progress(None, done_ids)

        if not error_occurred and results:
            mention_count = sum(1 for r in results if r["mentioned"])
            score = round((mention_count / len(results)) * 100)
            positioned = [r["position"] for r in results if r["position"] is not None]
            avg_pos = round(sum(positioned) / len(positioned), 1) if positioned else None

            score_color = "#a3e635" if score >= 67 else "#fbbf24" if score >= 34 else "#f87171"

            st.markdown("---")
            render_section_label("Summary")

            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-val" style="color:{score_color}">{score}%</div>
                    <div class="metric-lbl">Visibility score</div>
                </div>""", unsafe_allow_html=True)
            with c2:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-val">{mention_count} / {len(results)}</div>
                    <div class="metric-lbl">Scenarios mentioned</div>
                </div>""", unsafe_allow_html=True)
            with c3:
                pos_display = f"#{avg_pos}" if avg_pos else "N/A"
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-val">{pos_display}</div>
                    <div class="metric-lbl">Avg list position</div>
                </div>""", unsafe_allow_html=True)

            st.markdown("---")
            render_section_label("Scenario breakdown")

            for r in results:
                render_result_card(r["label"], r["mentioned"], r["position"], r["snippet"])

            st.markdown("---")
            render_section_label("GEO diagnosis")

            with st.spinner("Generating diagnosis..."):
                snippets = "\n\n".join(
                    f"[{r['label']}]: {r['snippet']}"
                    for r in results if r["mentioned"] and r["snippet"]
                )
                synth_prompt = f"""You are a GEO (Generative Engine Optimization) analyst.

Brand: {brand}
Category: {category}
Mentioned in {mention_count} out of {len(results)} Gemini responses across different user query types.

Mentions found:
{snippets if snippets else "(Brand was not mentioned in any response)"}

Write a short GEO diagnosis. Three paragraphs:
1. Current LLM visibility status. Be honest and direct.
2. The most likely root cause of the gap (or strength, if visibility is high).
3. One specific, actionable thing to improve LLM presence.

No bullet points. No filler phrases. No "Furthermore" or "Moreover". Write like a consultant who respects the reader's time."""

                try:
                    diagnosis = call_gemini(
                        api_key,
                        synth_prompt,
                        system="You are a direct, no-nonsense GEO analyst. Plain English only. Short sentences. Be specific."
                    )
                    st.markdown(f'<div class="geo-box">{diagnosis}</div>', unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Could not generate diagnosis: {str(e)}")

        st.markdown('<p class="footer-note">Prototype by Aarush Sharma &mdash; demonstrating GEO audit thinking</p>', unsafe_allow_html=True)
