"""Token pricing for cost intelligence calculations.

Prices are USD per 1M tokens. Update as provider pricing changes.
"""

from typing import Optional

# USD per 1M tokens (input, output)
MODEL_PRICING: dict[str, tuple[float, float]] = {
    "gpt-4o": (2.50, 10.00),
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4-turbo": (10.00, 30.00),
    "gpt-3.5-turbo": (0.50, 1.50),
    "nvidia/llama-3.1-nemotron-70b-instruct": (0.35, 0.40),
    "meta/llama-3.1-70b-instruct": (0.35, 0.40),
    "meta/llama-3.1-8b-instruct": (0.05, 0.05),
}

_DEFAULT_PRICING = (1.00, 3.00)


def _resolve_pricing(model: str) -> tuple[float, float]:
    if model in MODEL_PRICING:
        return MODEL_PRICING[model]
    for key, pricing in MODEL_PRICING.items():
        if key in model or model in key:
            return pricing
    return _DEFAULT_PRICING


def estimate_cost(
    model: str,
    input_tokens: int,
    output_tokens: int,
) -> float:
    """Estimate USD cost from token counts and model pricing."""
    input_rate, output_rate = _resolve_pricing(model)
    input_cost = (input_tokens / 1_000_000) * input_rate
    output_cost = (output_tokens / 1_000_000) * output_rate
    return round(input_cost + output_cost, 6)


def get_model_pricing(model: str) -> dict[str, float]:
    input_rate, output_rate = _resolve_pricing(model)
    return {
        "input_per_million": input_rate,
        "output_per_million": output_rate,
    }
