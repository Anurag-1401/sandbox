"""Multi-domain Bharat Dynamic Pricing API routes."""
from typing import Literal
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from core.pricing_engine import recommend_price

router = APIRouter(prefix="/v1", tags=["Bharat Dynamic Pricing"])
Domain = Literal["ride", "food", "ecommerce", "entertainment", "travel"]

class DomainPricingRequest(BaseModel):
    domain: Domain
    baseline_price_inr: float = Field(gt=0)
    demand_index: float = Field(default=1.0, gt=0, description="1.0 is normal demand; >1 is elevated")
    supply_index: float = Field(default=1.0, gt=0, description="1.0 is normal supply; <1 is constrained supply")
    availability_index: float = Field(default=1.0, gt=0, description="1.0 is normal availability; <1 is scarce")
    context_index: float = Field(default=1.0, gt=0)
    max_price_change_pct: float = Field(default=25.0, ge=0, le=80)
    timestamp: str | None = None
    location: str | None = None
    pickup_location: str | None = None
    drop_location: str | None = None
    restaurant: str | None = None
    food_category: str | None = None
    product_id: str | None = None
    event_id: str | None = None
    destination: str | None = None
    metadata: dict = Field(default_factory=dict)

@router.get("/domains")
def domains():
    return {
        "domains": [
            {"id":"ride", "label":"Ride-hailing", "empirical_model_in_base_archive": False},
            {"id":"food", "label":"Food delivery", "empirical_model_in_base_archive": False},
            {"id":"ecommerce", "label":"E-commerce", "empirical_model_in_base_archive": False},
            {"id":"entertainment", "label":"Entertainment / Tickets", "empirical_model_in_base_archive": False},
            {"id":"travel", "label":"Travel", "empirical_model_in_base_archive": False}
        ],
        "note": "The uploaded base archive contains a synthetic India-wide pricing model, not the empirical Ride/Food models discussed in prior BDP work. This endpoint is the transparent shared pricing-policy layer, not a trained demand predictor."
    }

@router.post("/predict-price")
def predict_domain_price(request: DomainPricingRequest):
    try:
        return recommend_price(
            domain=request.domain,
            baseline_price_inr=request.baseline_price_inr,
            demand_index=request.demand_index,
            supply_index=request.supply_index,
            availability_index=request.availability_index,
            context_index=request.context_index,
            max_price_change_pct=request.max_price_change_pct,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
