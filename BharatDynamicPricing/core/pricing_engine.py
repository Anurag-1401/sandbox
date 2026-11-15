"""Shared, bounded BDP pricing policy and counterfactual simulator.

Demand prediction and pricing policy are deliberately separate. This module
never pretends that a policy index is a trained demand prediction.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any

DOMAINS = ("ride", "food", "ecommerce", "entertainment", "travel")
WEIGHTS = {
    "ride": {"demand": .32, "supply": .18, "availability": .12, "traffic": .08, "weather": .06, "event": .07, "festival": .07, "inventory": .08},
    "food": {"demand": .25, "supply": .15, "availability": .15, "traffic": .08, "weather": .06, "event": .06, "festival": .08, "inventory": .07},
    "ecommerce": {"demand": .30, "supply": .08, "availability": .08, "traffic": .02, "weather": .02, "event": .08, "festival": .10, "inventory": .20},
    "entertainment": {"demand": .35, "supply": .05, "availability": .18, "traffic": .02, "weather": .02, "event": .18, "festival": .10, "inventory": .08},
    "travel": {"demand": .35, "supply": .08, "availability": .20, "traffic": .02, "weather": .04, "event": .08, "festival": .10, "inventory": .11},
}
COEFFICIENTS = {"demand": .32, "supply": .18, "availability": .12, "traffic": .08, "weather": .06, "event": .07, "festival": .07, "inventory": .08}

@dataclass
class PricingResult:
    domain: str
    baseline_price_inr: float
    recommended_price_inr: float
    multiplier: float
    raw_multiplier: float
    price_change_pct: float
    demand_pressure: float
    supply_pressure: float
    availability_pressure: float
    explanation: dict[str, float]
    model_status: str
    predicted_current_demand: float | None = None
    predicted_next_window_demand: float | None = None
    optimizer: dict[str, Any] | None = None

def _positive(name: str, value: float) -> float:
    value=float(value)
    if value <= 0: raise ValueError(f"{name} must be greater than zero")
    return value

def calculate_effects(domain: str, demand_index: float, supply_index: float,
                      availability_index: float, traffic_index: float=1.0,
                      weather_index: float=1.0, event_index: float=1.0,
                      festival_index: float=1.0, inventory_index: float=1.0) -> dict[str,float]:
    if domain not in WEIGHTS: raise ValueError(f"Unsupported domain: {domain}")
    vals = {k:_positive(k,v) for k,v in {
        "demand_index":demand_index,"supply_index":supply_index,
        "availability_index":availability_index,"traffic_index":traffic_index,
        "weather_index":weather_index,"event_index":event_index,
        "festival_index":festival_index,"inventory_index":inventory_index}.items()}
    # Demand/supply/availability/inventory indices are relative to normal.
    ratios = {
        "demand": max(.25,min(4.0,vals["demand_index"])),
        "supply": max(.25,min(4.0,1/vals["supply_index"])),
        "availability": max(.25,min(4.0,1/vals["availability_index"])),
        "traffic": max(.5,min(2.0,vals["traffic_index"])),
        "weather": max(.5,min(2.0,vals["weather_index"])),
        "event": max(.5,min(2.0,vals["event_index"])),
        "festival": max(.5,min(2.0,vals["festival_index"])),
        "inventory": max(.25,min(4.0,1/vals["inventory_index"])),
    }
    weights=WEIGHTS[domain]
    return {k:weights[k]*(ratios[k]-1.0) for k in weights}

def recommend_price(domain: str, baseline_price_inr: float,
                    demand_index: float=1.0, supply_index: float=1.0,
                    availability_index: float=1.0, traffic_index: float=1.0,
                    weather_index: float=1.0, event_index: float=1.0,
                    festival_index: float=1.0, inventory_index: float=1.0,
                    max_price_change_pct: float=25.0,
                    predicted_current_demand: float|None=None,
                    predicted_next_window_demand: float|None=None,
                    optimize: bool=False, elasticity: float=-.6,
                    stability_lambda: float=.15, candidates: int=101) -> dict:
    base=_positive("baseline_price_inr",baseline_price_inr)
    if not 0 <= max_price_change_pct <= 80: raise ValueError("max_price_change_pct must be between 0 and 80")
    effects=calculate_effects(domain,demand_index,supply_index,availability_index,
        traffic_index,weather_index,event_index,festival_index,inventory_index)
    raw=1+sum(effects.values())
    # Internal policy safety bound, followed by configurable business cap.
    bounded=max(.70,min(1.80,raw))
    cap=max_price_change_pct/100
    mult=max(1-cap,min(1+cap,bounded))
    result=PricingResult(domain,round(base,2),round(base*mult,2),round(mult,4),
        round(raw,4),round((mult-1)*100,2),round(max(.25,min(4,demand_index)),4),
        round(max(.25,min(4,1/supply_index)),4),round(max(.25,min(4,1/availability_index)),4),
        {k:round(v,5) for k,v in effects.items()},
        "trained_domain_model" if predicted_current_demand is not None else "policy_only_no_validated_domain_model",
        predicted_current_demand,predicted_next_window_demand)
    out=asdict(result)
    if optimize:
        out["optimizer"]=counterfactual_optimize(base, demand_index, elasticity,
            stability_lambda, max(.70,1-cap), min(1.80,1+cap), candidates)
    return out

def counterfactual_optimize(base_price: float, reference_demand: float,
                            elasticity: float=-.6, stability_lambda: float=.15,
                            lower: float=.75, upper: float=1.25,
                            candidates: int=101) -> dict:
    if base_price<=0 or reference_demand<0: raise ValueError("base_price must be positive and demand non-negative")
    if elasticity>=0: raise ValueError("elasticity must be negative for the documented demand-response assumption")
    if stability_lambda<0: raise ValueError("stability_lambda cannot be negative")
    candidates=max(3,min(1001,int(candidates)))
    best=None
    for i in range(candidates):
        m=lower+(upper-lower)*i/(candidates-1)
        d=reference_demand*(m**elasticity)
        revenue=base_price*m*d
        penalty=stability_lambda*(m-1)**2*base_price*reference_demand
        utility=revenue-penalty
        item={"multiplier":m,"price_inr":base_price*m,"counterfactual_demand":d,"revenue":revenue,"stability_penalty":penalty,"utility":utility}
        if best is None or utility>best["utility"]: best=item
    return {"assumption":"scenario simulation using user-supplied elasticity; not a causal estimate",
            "elasticity":elasticity,"stability_lambda":stability_lambda,
            "candidate_count":candidates,"best_candidate":{k:round(v,4) for k,v in best.items()}}
