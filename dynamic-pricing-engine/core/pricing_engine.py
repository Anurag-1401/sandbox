"""Shared bounded pricing policy for all supported service domains.

This is a transparent policy layer, NOT a trained demand model. Domain-specific
trained predictors can be plugged into `predicted_demand` when validated data
and artifacts are available.
"""
from dataclasses import dataclass, asdict

@dataclass
class PricingResult:
    domain: str
    baseline_price_inr: float
    recommended_price_inr: float
    multiplier: float
    price_change_pct: float
    demand_pressure: float
    supply_pressure: float
    explanation: dict
    model_status: str = "policy_only_no_validated_domain_model"


def recommend_price(domain: str, baseline_price_inr: float,
                    demand_index: float = 1.0, supply_index: float = 1.0,
                    availability_index: float = 1.0, context_index: float = 1.0,
                    max_price_change_pct: float = 25.0,
                    predicted_demand: float | None = None) -> dict:
    if baseline_price_inr <= 0:
        raise ValueError("baseline_price_inr must be greater than zero")
    if not 0 <= max_price_change_pct <= 80:
        raise ValueError("max_price_change_pct must be between 0 and 80")
    for name, value in {"demand_index": demand_index, "supply_index": supply_index,
                        "availability_index": availability_index,
                        "context_index": context_index}.items():
        if value <= 0:
            raise ValueError(f"{name} must be greater than zero")

    # Normalized pressure: >1 means stronger demand / tighter capacity.
    demand_pressure = max(0.25, min(4.0, float(demand_index)))
    supply_pressure = max(0.25, min(4.0, 1.0 / float(supply_index)))
    availability_pressure = max(0.25, min(4.0, 1.0 / float(availability_index)))
    context_pressure = max(0.5, min(2.0, float(context_index)))

    # Conservative, interpretable domain-specific policy weights.
    weights = {
        "ride": (0.32, 0.18, 0.12, 0.08),
        "food": (0.25, 0.15, 0.15, 0.10),
        "ecommerce": (0.30, 0.20, 0.12, 0.08),
        "entertainment": (0.35, 0.10, 0.18, 0.12),
        "travel": (0.35, 0.12, 0.20, 0.12),
    }
    if domain not in weights:
        raise ValueError(f"Unsupported domain: {domain}")
    wd, ws, wa, wc = weights[domain]
    effects = {
        "demand": wd * (demand_pressure - 1.0),
        "supply": ws * (supply_pressure - 1.0),
        "availability": wa * (availability_pressure - 1.0),
        "context": wc * (context_pressure - 1.0),
    }
    raw_multiplier = 1.0 + sum(effects.values())
    cap = max_price_change_pct / 100.0
    multiplier = max(1.0 - cap, min(1.0 + cap, raw_multiplier))
    price = round(float(baseline_price_inr) * multiplier, 2)
    return asdict(PricingResult(
        domain=domain,
        baseline_price_inr=round(float(baseline_price_inr), 2),
        recommended_price_inr=price,
        multiplier=round(multiplier, 4),
        price_change_pct=round((multiplier - 1.0) * 100.0, 2),
        demand_pressure=round(demand_pressure, 4),
        supply_pressure=round(supply_pressure, 4),
        explanation={k: round(v, 4) for k, v in effects.items()},
        model_status="policy_only_no_validated_domain_model",
    ))
