"""Domain metadata and input adapters for the five BDP service domains."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any

@dataclass(frozen=True)
class DomainSpec:
    id: str
    label: str
    demand_unit: str
    supply_unit: str
    baseline_label: str
    required_business_inputs: tuple[str,...]
    target_hint: str

SPECS = {
 "ride": DomainSpec("ride","Ride-hailing","ride requests","available drivers","Trip base fare",("pickup_location","drop_location","vehicle_type"),"ride requests per time window"),
 "food": DomainSpec("food","Food delivery","food orders","delivery/restaurant capacity","Restaurant/order reference price",("restaurant","food_category","location"),"orders per time window"),
 "ecommerce": DomainSpec("ecommerce","E-commerce","product units","inventory units","Product reference price",("product_id","category"),"product units sold per time window"),
 "entertainment": DomainSpec("entertainment","Entertainment / ticketing","tickets booked","remaining seats","Ticket base price",("event_id","event_date","remaining_capacity"),"tickets booked per time window"),
 "travel": DomainSpec("travel","Travel and tourism","bookings","remaining capacity","Travel product reference price",("destination","travel_date","product_type"),"bookings per time window"),
}
def list_domains():
 return [{**asdict(s),"required_business_inputs":list(s.required_business_inputs)} for s in SPECS.values()]
def adapt_features(domain: str, values: dict[str,Any]) -> dict[str,Any]:
 if domain not in SPECS: raise ValueError(f"Unsupported domain: {domain}")
 # Preserve source feature names; add canonical aliases for common model contracts.
 out=dict(values)
 out["domain"]=domain
 out.setdefault("timestamp",values.get("timestamp"))
 aliases={"current_demand":"demand","next_window_demand":"next_demand","capacity":"available_supply"}
 for target,source in aliases.items():
  if target not in out and source in out: out[target]=out[source]
 return out
