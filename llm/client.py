"""
Unified LLM client. All providers speak through call_llm() and call_json().
Adding a new provider = one new elif block here.
"""

import json
import re
from typing import Optional


def call_llm(provider: str, model_name: str, api_key: str, prompt: str, system: str = "") -> str:
    """Call any supported LLM provider. Raises on API error."""
    system = system or "You are a helpful AI assistant. Answer questions naturally and concisely."

    if provider == "gemini":
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model_name,
            config=types.GenerateContentConfig(system_instruction=system),
            contents=prompt,
        )
        return response.text

    if provider == "groq":
        from groq import Groq
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content

    if provider == "openai":
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content

    if provider == "perplexity":
        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url="https://api.perplexity.ai")
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content

    if provider == "anthropic":
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=model_name,
            max_tokens=1024,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text

    raise ValueError(f"Unknown provider: {provider}")


def call_json(provider: str, model_name: str, api_key: str, prompt: str) -> Optional[dict | list]:
    """
    Call LLM and parse the response as JSON.
    Returns None on failure — callers should handle gracefully.
    """
    json_prompt = (
        prompt
        + "\n\nReturn ONLY valid JSON. No markdown fences, no explanation outside JSON."
    )
    try:
        raw = call_llm(
            provider, model_name, api_key, json_prompt,
            system="You are a precise analyst. Return only valid JSON, nothing else.",
        )
        # Strip markdown code fences if present
        raw = re.sub(r"^```(?:json)?\s*", "", raw.strip())
        raw = re.sub(r"\s*```$", "", raw.strip())
        return json.loads(raw)
    except Exception:
        return None
