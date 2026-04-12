"""
Design system CSS — light B2B SaaS with original character.

Philosophy:
- Light neutral base (Peec AI-aligned: clean, professional, legible)
- Original identity: Lora heading, JetBrains Mono for labels, lime-green data accent
- Dark button on light bg — premium B2B pattern (Notion, Linear, Vercel light mode)
- Color only on data signals (score, sentiment, hits)
- Sidebar for inputs, tabs for navigation
"""

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* ── ANIMATIONS ── */
@keyframes eye-scan {
    0%, 100% { opacity: 0.25; transform: scale(1); }
    50%       { opacity: 0.55; transform: scale(1.1); }
}
@keyframes logo-breathe {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0.45; }
}
@keyframes bar-fade-in {
    0%   { opacity: 0; transform: scaleX(0.6); transform-origin: left; }
    100% { opacity: 1; transform: scaleX(1);   transform-origin: left; }
}

/* ── BASE ── */
html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, sans-serif !important;
}

.stApp {
    background-color: #f8fafc !important;
    color: #0f172a;
}

div[data-testid="stAppViewContainer"],
div[data-testid="stMain"],
div[data-testid="block-container"] {
    background-color: transparent !important;
}

h1, h2, h3 {
    font-family: 'Inter', sans-serif !important;
    font-weight: 700 !important;
    color: #0f172a !important;
    letter-spacing: -0.02em !important;
}

p { color: #475569; line-height: 1.6; }
hr { border-color: #e2e8f0 !important; margin: 24px 0 !important; }

/* ── SIDEBAR ── */
section[data-testid="stSidebar"] {
    background-color: #ffffff !important;
    border-right: 1px solid #e8edf2 !important;
    min-width: 300px !important;
    max-width: 320px !important;
}
section[data-testid="stSidebar"] > div {
    padding: 28px 22px !important;
}

.sidebar-logo {
    display: flex;
    align-items: center;
    gap: 8px;
    padding-bottom: 24px;
    margin-bottom: 24px;
    border-bottom: 1px solid #f1f5f9;
}
.sidebar-logo-dot { font-size: 14px; color: #0f172a; animation: logo-breathe 4s ease-in-out infinite; }
.sidebar-logo-text {
    font-family: 'Inter', sans-serif;
    font-size: 15px;
    font-weight: 600;
    color: #0f172a;
    letter-spacing: -0.02em;
}
.sidebar-section-label {
    font-family: 'Inter', sans-serif;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #94a3b8;
    margin-bottom: 10px;
}
.sidebar-footer {
    font-family: 'Inter', sans-serif;
    font-size: 12px;
    color: #cbd5e1;
    padding-top: 18px;
    border-top: 1px solid #f1f5f9;
    margin-top: 12px;
}
.sidebar-footer-link { color: #94a3b8; text-decoration: none; }
.sidebar-footer-link:hover { color: #475569; }

/* ── INPUTS ── */
.stTextInput > div > div > input,
.stSelectbox > div > div > div,
.stTextArea > div > div > textarea {
    background-color: #f8fafc !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 6px !important;
    color: #0f172a !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 13px !important;
    transition: border-color 0.12s, box-shadow 0.12s !important;
}
.stTextInput > div > div > input::placeholder { color: #cbd5e1 !important; }
.stTextInput > div > div > input:focus {
    border-color: #94a3b8 !important;
    box-shadow: 0 0 0 3px rgba(148,163,184,0.1) !important;
    outline: none !important;
}

label, .stSelectbox label, .stTextInput label {
    font-family: 'Inter', sans-serif !important;
    font-size: 11px !important;
    font-weight: 500 !important;
    color: #64748b !important;
}

/* ── BUTTON — dark on light, premium pattern ── */
.stButton > button {
    background-color: #0f172a !important;
    color: #f8fafc !important;
    border: none !important;
    border-radius: 6px !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    padding: 10px 20px !important;
    letter-spacing: -0.01em !important;
    transition: background-color 0.12s, transform 0.1s, box-shadow 0.12s !important;
    box-shadow: 0 1px 2px rgba(15,23,42,0.15) !important;
}
.stButton > button:hover {
    background-color: #1e293b !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 10px rgba(15,23,42,0.2) !important;
    color: #f8fafc !important;
}

/* ── EXPANDER ── */
.streamlit-expanderHeader {
    background-color: #f8fafc !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 6px !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 12px !important;
    font-weight: 500 !important;
    color: #94a3b8 !important;
}
.streamlit-expanderHeader:hover { color: #475569 !important; border-color: #cbd5e1 !important; }
.streamlit-expanderContent {
    background-color: #f8fafc !important;
    border: 1px solid #e2e8f0 !important;
    border-top: none !important;
    border-radius: 0 0 6px 6px !important;
}

/* ── TABS ── */
.stTabs [data-baseweb="tab-list"] {
    background-color: transparent !important;
    border-bottom: 1px solid #e2e8f0 !important;
    gap: 0 !important;
    padding: 0 !important;
}
.stTabs [data-baseweb="tab"] {
    background-color: transparent !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    padding: 10px 18px !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    color: #94a3b8 !important;
    transition: color 0.12s !important;
}
.stTabs [data-baseweb="tab"]:hover { color: #475569 !important; }
.stTabs [aria-selected="true"] {
    color: #0f172a !important;
    border-bottom: 2px solid #0f172a !important;
    background-color: transparent !important;
}
.stTabs [data-baseweb="tab-panel"] {
    padding: 0 !important;
    background-color: transparent !important;
}

/* ── CONTEXT BAR ── */
.context-bar {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 0 4px 0;
    margin-bottom: 4px;
}
.context-brand {
    font-family: 'Inter', sans-serif;
    font-size: 15px;
    font-weight: 700;
    color: #0f172a;
    letter-spacing: -0.02em;
}
.context-sep { font-size: 12px; color: #e2e8f0; }
.context-category { font-family: 'Inter', sans-serif; font-size: 13px; color: #64748b; }
.context-models { font-family: 'Inter', sans-serif; font-size: 12px; color: #94a3b8; }

/* ── EMPTY STATE ── */
.empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 80px 24px;
    text-align: center;
    max-width: 560px;
    margin: 0 auto;
}
.empty-state-icon { font-size: 32px; color: #cbd5e1; margin-bottom: 20px; animation: eye-scan 3.5s ease-in-out infinite; display: inline-block; }
.empty-state-title {
    font-family: 'Inter', sans-serif;
    font-size: 22px;
    font-weight: 700;
    color: #0f172a;
    letter-spacing: -0.03em;
    margin-bottom: 10px;
    line-height: 1.3;
}
.empty-state-sub {
    font-family: 'Inter', sans-serif;
    font-size: 14px;
    color: #94a3b8;
    line-height: 1.7;
    max-width: 440px;
    margin: 0 auto 28px auto;
}
.empty-state-pills { display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; }
.empty-pill {
    font-family: 'Inter', sans-serif;
    font-size: 12px;
    font-weight: 500;
    color: #94a3b8;
    border: 1px solid #e8edf2;
    border-radius: 20px;
    padding: 5px 14px;
    background: #ffffff;
}

/* ── SECTION LABEL ── */
.section-label {
    font-family: 'Inter', sans-serif;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #94a3b8;
    margin-bottom: 14px;
    padding-bottom: 8px;
    border-bottom: 1px solid #f1f5f9;
}

/* ── METRIC CARDS ── */
.metric-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 20px 18px;
    box-shadow: 0 1px 3px rgba(15,23,42,0.04);
    transition: transform 0.15s, box-shadow 0.15s;
}
.metric-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(15,23,42,0.08);
    border-color: #cbd5e1;
}
.metric-val {
    font-size: 30px; font-weight: 700;
    font-family: 'Inter', sans-serif;
    letter-spacing: -0.04em;
    margin-bottom: 4px;
    color: #0f172a;
}
.metric-lbl {
    font-size: 11px;
    font-family: 'Inter', sans-serif;
    font-weight: 500;
    color: #94a3b8;
}

/* ── RESULT CARDS ── */
.result-card {
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 14px 16px;
    margin-bottom: 6px;
    background: #ffffff;
    transition: border-color 0.12s, box-shadow 0.12s;
    box-shadow: 0 1px 2px rgba(15,23,42,0.03);
}
.result-card:hover { border-color: #cbd5e1; box-shadow: 0 2px 6px rgba(15,23,42,0.06); }
.result-card-hit  { border-left: 3px solid #84cc16; }
.result-card-miss { border-left: 3px solid #e2e8f0; }
.result-card-probe { border-left: 3px solid #6366f1; }

/* ── TAGS ── */
.tag-yes   { background: #f7fee7; color: #3f6212; font-family:'Inter',sans-serif; font-size:11px; padding:2px 8px; border-radius:4px; white-space:nowrap; border: 1px solid #d9f99d; }
.tag-pos   { background: #fffbeb; color: #92400e; font-family:'Inter',sans-serif; font-size:11px; padding:2px 8px; border-radius:4px; white-space:nowrap; border: 1px solid #fde68a; }
.tag-no    { background: #f8fafc; color: #94a3b8; font-family:'Inter',sans-serif; font-size:11px; padding:2px 8px; border-radius:4px; white-space:nowrap; border: 1px solid #e2e8f0; }
.tag-probe { background: #eef2ff; color: #4338ca; font-family:'Inter',sans-serif; font-size:11px; padding:2px 8px; border-radius:4px; white-space:nowrap; border: 1px solid #c7d2fe; }

/* sentiment */
.sent-positive { color: #16a34a; font-size:11px; font-family:'Inter',sans-serif; }
.sent-neutral  { color: #94a3b8; font-size:11px; font-family:'Inter',sans-serif; }
.sent-cautious { color: #d97706; font-size:11px; font-family:'Inter',sans-serif; }
.sent-negative { color: #dc2626; font-size:11px; font-family:'Inter',sans-serif; }

/* ── SNIPPET + CLAIMS ── */
.snippet {
    font-family: 'Inter', sans-serif;
    font-size: 12px; color: #64748b;
    line-height: 1.7; border-left: 2px solid #e2e8f0;
    padding-left: 12px; margin-top: 8px;
}
.result-card-hit  .snippet { border-left-color: #84cc16; }
.result-card-miss .snippet { border-left-color: #fca5a5; }
.result-card-probe .snippet { border-left-color: #a5b4fc; }
.claims-row { display:flex; flex-wrap:wrap; gap:6px; margin-top:8px; }
.claim-pill {
    font-family: 'Inter', sans-serif; font-size: 11px; font-weight: 500;
    padding: 2px 10px; border-radius: 20px;
    background: #f8fafc; color: #64748b; border: 1px solid #e2e8f0;
}

/* ── MODEL DOTS + TABLE ── */
.model-dot       { display:inline-block; width:6px; height:6px; border-radius:50%; margin-right:2px; }
.dot-hit         { background: #84cc16; }
.dot-miss        { background: #e2e8f0; }
.model-dot-label { font-family:'Inter',sans-serif; font-size:10px; color:#94a3b8; margin-right:3px; }

.model-table     { width:100%; border-collapse:collapse; font-family:'Inter',sans-serif; font-size:13px; }
.model-table th  { text-align:left; color:#94a3b8; font-size:10px; font-weight:600; text-transform:uppercase; letter-spacing:0.07em; padding:8px 12px; border-bottom:1px solid #f1f5f9; font-family:'Inter',sans-serif; }
.model-table td  { padding:10px 12px; border-bottom:1px solid #f8fafc; color:#475569; }
.model-table tr:hover td { background: #f8fafc; }
.model-table tr:last-child td { border-bottom:none; }

.score-high { color: #16a34a !important; font-weight: 600 !important; }
.score-mid  { color: #d97706 !important; font-weight: 600 !important; }
.score-low  { color: #dc2626 !important; font-weight: 600 !important; }

/* ── DIAGNOSIS + PROBE BOXES ── */
.geo-box {
    background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px;
    padding: 20px; font-size: 14px; line-height: 1.9; color: #475569;
    font-family: 'Inter', sans-serif;
    box-shadow: 0 1px 3px rgba(15,23,42,0.04);
}
.cross-model-box {
    background: #eef2ff; border: 1px solid #c7d2fe; border-radius: 8px;
    padding: 20px; font-size: 14px; line-height: 1.9; color: #3730a3;
    font-family: 'Inter', sans-serif;
}
.probe-box {
    background: #f0f9ff; border: 1px solid #bae6fd; border-radius: 8px;
    padding: 14px 18px; font-size: 13px; line-height: 1.75; color: #0369a1;
    font-family: 'Inter', sans-serif;
    margin-bottom: 10px;
}

/* ── ACTION CARDS ── */
.action-card {
    background: #ffffff; border: 1px solid #e2e8f0;
    border-radius: 8px; padding: 14px 16px; margin-bottom: 8px;
    transition: border-color 0.12s, box-shadow 0.12s;
    box-shadow: 0 1px 2px rgba(15,23,42,0.03);
}
.action-card:hover { border-color: #cbd5e1; box-shadow: 0 2px 6px rgba(15,23,42,0.06); }
.action-card-high-conf { border-left: 3px solid #84cc16; }
.action-card-mid-conf  { border-left: 3px solid #f59e0b; }
.action-card-low-conf  { border-left: 3px solid #e2e8f0; }
.confidence-bar-bg { background: #f1f5f9; border-radius: 4px; height: 3px; margin-top: 10px; }
.confidence-bar    { height: 3px; border-radius: 4px; animation: bar-fade-in 0.6s ease-out both; }

/* ── SOV TABLE ── */
.sov-table    { width:100%; border-collapse:collapse; font-family:'Inter',sans-serif; font-size:13px; }
.sov-table th { text-align:left; color:#94a3b8; font-size:10px; font-weight:500; text-transform:uppercase; letter-spacing:0.07em; padding:8px 12px; border-bottom:1px solid #f1f5f9; font-family:'Inter',sans-serif; }
.sov-table td { padding:10px 12px; border-bottom:1px solid #f8fafc; color:#475569; }
.sov-bar-bg   { background:#f1f5f9; border-radius:4px; height:4px; }
.sov-bar      { height:4px; border-radius:4px; background:#84cc16; }

/* ── HIDE STREAMLIT CHROME ── */
div[data-testid="stStatusWidget"] { display: none; }
#MainMenu { visibility: hidden; }
footer    { visibility: hidden; }
header    { visibility: hidden; }

/* ── PLAYBOOK ── */
.playbook-summary {
    background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px;
    padding: 18px 20px; font-size: 14px; line-height: 1.8; color: #166534;
    margin-bottom: 16px;
}
.playbook-quick-wins {
    background: #fffbeb; border: 1px solid #fde68a; border-radius: 8px;
    padding: 14px 20px; margin-bottom: 20px;
}
.brief-card {
    background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px;
    padding: 18px 20px; margin-bottom: 12px;
    box-shadow: 0 1px 3px rgba(15,23,42,0.04);
    transition: border-color 0.15s, box-shadow 0.15s;
}
.brief-card:hover { border-color: #cbd5e1; box-shadow: 0 3px 8px rgba(15,23,42,0.07); }
.brief-title { font-size: 14px; font-weight: 600; color: #0f172a; margin: 0 0 10px 0; line-height: 1.4; }
.brief-badge {
    display: inline-block; font-size: 10px; font-weight: 500; text-transform: uppercase;
    letter-spacing: 0.06em; border-radius: 4px; padding: 2px 8px; margin-right: 6px;
    font-family: 'Inter', sans-serif;
}
.badge-type { background: #f1f5f9; color: #64748b; }
.badge-week { background: #dcfce7; color: #166534; }
.badge-month { background: #fef9c3; color: #854d0e; }
.badge-quarter { background: #f1f5f9; color: #64748b; }
.brief-outline li { font-size: 12px; color: #475569; margin-bottom: 3px; line-height: 1.5; }
</style>
"""
