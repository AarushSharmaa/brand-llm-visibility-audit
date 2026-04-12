"""
Tests for core/config.py — structural integrity of provider registry and scenarios.
Catches accidental misconfiguration (missing keys, broken lambdas, etc.).
"""

import pytest
from core.config import PROVIDERS, PRIMARY_PROVIDERS, OPTIONAL_PROVIDERS, SCENARIOS, PRESET_BRANDS


# ── Provider registry ─────────────────────────────────────────────────────────

REQUIRED_PROVIDER_KEYS = {"label", "color", "short", "free_tier", "models", "default_model", "key_hint"}

def test_all_providers_have_required_keys():
    for name, cfg in PROVIDERS.items():
        missing = REQUIRED_PROVIDER_KEYS - set(cfg.keys())
        assert not missing, f"Provider '{name}' missing keys: {missing}"


def test_provider_models_not_empty():
    for name, cfg in PROVIDERS.items():
        assert cfg["models"], f"Provider '{name}' has empty models dict"


def test_default_model_exists_in_models():
    for name, cfg in PROVIDERS.items():
        assert cfg["default_model"] in cfg["models"], (
            f"Provider '{name}' default_model '{cfg['default_model']}' not in models"
        )


def test_primary_providers_exist_in_registry():
    for pk in PRIMARY_PROVIDERS:
        assert pk in PROVIDERS, f"Primary provider '{pk}' not in PROVIDERS"


def test_optional_providers_exist_in_registry():
    for pk in OPTIONAL_PROVIDERS:
        assert pk in PROVIDERS, f"Optional provider '{pk}' not in PROVIDERS"


def test_no_overlap_between_primary_and_optional():
    overlap = set(PRIMARY_PROVIDERS) & set(OPTIONAL_PROVIDERS)
    assert not overlap, f"Providers appear in both primary and optional: {overlap}"


def test_free_tier_providers_are_primary():
    """Free-tier providers should be primary (lowest friction for users)."""
    free_providers = {k for k, v in PROVIDERS.items() if v.get("free_tier")}
    for pk in free_providers:
        assert pk in PRIMARY_PROVIDERS, f"Free-tier provider '{pk}' is not in PRIMARY_PROVIDERS"


# ── Scenarios ─────────────────────────────────────────────────────────────────

REQUIRED_SCENARIO_KEYS = {"id", "label", "prompt"}

def test_scenarios_not_empty():
    assert len(SCENARIOS) > 0


def test_scenarios_have_required_keys():
    for s in SCENARIOS:
        missing = REQUIRED_SCENARIO_KEYS - set(s.keys())
        assert not missing, f"Scenario '{s.get('id')}' missing keys: {missing}"


def test_scenario_ids_unique():
    ids = [s["id"] for s in SCENARIOS]
    assert len(ids) == len(set(ids)), "Scenario IDs are not unique"


def test_scenario_prompts_are_callable():
    for s in SCENARIOS:
        assert callable(s["prompt"]), f"Scenario '{s['label']}' prompt is not callable"


def test_scenario_prompts_include_brand_and_category():
    """Each prompt should interpolate brand and/or category."""
    for s in SCENARIOS:
        result = s["prompt"]("TestBrand", "test category")
        assert isinstance(result, str), f"Scenario '{s['label']}' prompt did not return string"
        assert len(result) > 10, f"Scenario '{s['label']}' prompt returned too short a string"
        # At least brand or category should appear in the prompt
        assert "TestBrand" in result or "test category" in result, (
            f"Scenario '{s['label']}' prompt doesn't use brand or category"
        )


def test_scenario_labels_unique():
    labels = [s["label"] for s in SCENARIOS]
    assert len(labels) == len(set(labels)), "Scenario labels are not unique"


# ── Preset brands ─────────────────────────────────────────────────────────────

def test_preset_brands_not_empty():
    assert len(PRESET_BRANDS) > 0


def test_preset_brands_have_brand_and_category():
    for name, cfg in PRESET_BRANDS.items():
        assert "brand" in cfg, f"Preset '{name}' missing 'brand'"
        assert "category" in cfg, f"Preset '{name}' missing 'category'"


def test_custom_preset_has_empty_values():
    """The 'Custom' entry should have empty brand/category to serve as a blank slate."""
    custom = next((v for k, v in PRESET_BRANDS.items() if "custom" in k.lower()), None)
    assert custom is not None, "No custom preset found"
    assert custom["brand"] == ""
    assert custom["category"] == ""
