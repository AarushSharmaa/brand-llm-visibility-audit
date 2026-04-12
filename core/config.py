"""
Provider registry, model lists, and scenario definitions.
Add new providers or models here — no other files need changing.
"""

PROVIDERS: dict = {
    "gemini": {
        "label": "Gemini",
        "color": "#4285f4",
        "short": "G",
        "free_tier": True,
        "models": {
            "gemini-2.5-flash": "Gemini 2.5 Flash (recommended)",
            "gemini-1.5-flash": "Gemini 1.5 Flash",
        },
        "default_model": "gemini-2.5-flash",
        "key_hint": "AIza... — free key at aistudio.google.com",
    },
    "groq": {
        "label": "Groq",
        "color": "#f97316",
        "short": "Q",
        "free_tier": True,
        "models": {
            "llama-3.3-70b-versatile": "Llama 3.3 70B (best quality)",
            "llama-3.1-8b-instant": "Llama 3.1 8B (fastest)",
            "mixtral-8x7b-32768": "Mixtral 8x7B",
        },
        "default_model": "llama-3.3-70b-versatile",
        "key_hint": "gsk_... — free key at console.groq.com",
    },
    "openai": {
        "label": "ChatGPT",
        "color": "#10a37f",
        "short": "O",
        "free_tier": False,
        "models": {
            "gpt-4o-mini": "GPT-4o Mini",
            "gpt-4o": "GPT-4o",
        },
        "default_model": "gpt-4o-mini",
        "key_hint": "sk-...",
    },
    "perplexity": {
        "label": "Perplexity",
        "color": "#a78bfa",
        "short": "P",
        "free_tier": False,
        "models": {
            "sonar": "Sonar",
            "sonar-pro": "Sonar Pro",
        },
        "default_model": "sonar",
        "key_hint": "pplx-...",
    },
    "anthropic": {
        "label": "Claude",
        "color": "#d97706",
        "short": "C",
        "free_tier": False,
        "models": {
            "claude-haiku-4-5-20251001": "Claude Haiku (fast)",
            "claude-sonnet-4-5": "Claude Sonnet",
        },
        "default_model": "claude-haiku-4-5-20251001",
        "key_hint": "sk-ant-...",
    },
}

# Order for display: free-tier providers first
PRIMARY_PROVIDERS = ["gemini", "groq"]
OPTIONAL_PROVIDERS = ["openai", "perplexity", "anthropic"]

SCENARIOS = [
    {
        "id": 1,
        "label": "Market discovery",
        "prompt": lambda b, c: f"List the top 5 companies in the {c} space. Rank them with a one-line description each.",
    },
    {
        "id": 2,
        "label": "Tool recommendation",
        "prompt": lambda b, c: f"I need a {c} solution for my company. What are the best options right now and why?",
    },
    {
        "id": 3,
        "label": "Brand knowledge",
        "prompt": lambda b, c: f"Tell me about {b}. What do they do, what is their core product, and who is it for?",
    },
    {
        "id": 4,
        "label": "Competitive landscape",
        "prompt": lambda b, c: f"Who are the main players in the {c} market today? Give me a quick rundown.",
    },
    {
        "id": 5,
        "label": "Best-in-class search",
        "prompt": lambda b, c: f"What is the best {c} tool right now? Give me your honest recommendation.",
    },
    {
        "id": 6,
        "label": "Vendor comparison",
        "prompt": lambda b, c: f"How does {b} compare to its main competitors in {c}? What are the key tradeoffs?",
    },
]

PRESET_BRANDS = {
    "Custom (type below)": {"brand": "", "category": ""},
    "Peec AI": {"brand": "Peec AI", "category": "generative engine optimization"},
    "Notion": {"brand": "Notion", "category": "productivity and note-taking software"},
    "Perplexity": {"brand": "Perplexity", "category": "AI-powered search"},
    "HubSpot": {"brand": "HubSpot", "category": "CRM and marketing automation"},
    "Salesforce": {"brand": "Salesforce", "category": "enterprise CRM"},
    "Intercom": {"brand": "Intercom", "category": "customer support and messaging"},
    "Linear": {"brand": "Linear", "category": "software project management"},
    "Cursor": {"brand": "Cursor", "category": "AI code editor"},
}
