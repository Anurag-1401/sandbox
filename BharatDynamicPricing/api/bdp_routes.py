"""Five-domain API: model-backed demand inference when validated artifacts exist,
with an explicitly labelled policy-only fallback otherwise."""
from __future__ import annotations
from datetime import datetime
from typing import Literal,Any
from fastapi import APIRouter,HTTPException
from pydantic import BaseModel,Field
from core.pricing_engine import recommend_price,DOMAINS
from core.model_registry import DomainModelRegistry
from domains.registry import list_domains,adapt_features
from core.audit import record_decision,summary as audit_summary
from .predictor import get_predictor
from .schemas import PredictPriceRequest

router=APIRouter(prefix="/v1",tags=["Bharat Dynamic Pricing"])
Domain=Literal["ride","food","ecommerce","entertainment","travel"]
registry=DomainModelRegistry()

class DomainPricingRequest(BaseModel):
 domain:Domain
 baseline_price_inr:float=Field(gt=0)
 demand_index:float=Field(default=1.0,gt=0,description="Relative current-window demand pressure; 1.0 is neutral")
 supply_index:float=Field(default=1.0,gt=0,description="Relative supply; below 1.0 means constrained")
 availability_index:float=Field(default=1.0,gt=0)
 traffic_index:float=Field(default=1.0,gt=0)
 weather_index:float=Field(default=1.0,gt=0)
 event_index:float=Field(default=1.0,gt=0)
 festival_index:float=Field(default=1.0,gt=0)
 inventory_index:float=Field(default=1.0,gt=0)
 max_price_change_pct:float=Field(default=25,ge=0,le=80)
 current_demand:float|None=Field(default=None,ge=0)
 predicted_next_window_demand:float|None=Field(default=None,ge=0)
 feature_values:dict[str,Any]=Field(default_factory=dict,description="Must match the trained domain feature schema")
 optimize:bool=False
 elasticity:float=Field(default=-.6,lt=0)
 stability_lambda:float=Field(default=.15,ge=0)
 metadata:dict[str,Any]=Field(default_factory=dict)
 timestamp:datetime|None=None

@router.get("/health")
def bdp_health():
 statuses=registry.all_status(DOMAINS)
 return {"service":"Bharat Dynamic Pricing Engine","status":"ok",
         "domains":len(DOMAINS),"trained_domain_models":sum(x["ready"] for x in statuses),
         "model_status":statuses}

@router.get("/domains")
def domains():
 statuses={x["domain"]:x for x in registry.all_status(DOMAINS)}
 result=list_domains()
 for item in result:
  status=statuses[item["id"]]
  item["model_ready"]=status["ready"];item["model_type"]=status["model_type"]
  item["metrics"]=status["metrics"]
 return {"domains":result,"note":"Historical experiment metrics are not restored model artifacts. A domain is marked model_ready only when its own trained artifact and feature schema are installed."}

@router.post("/predict-price")
def predict_domain_price(request:DomainPricingRequest):
 domain=request.domain
 current=request.current_demand
 next_demand=request.predicted_next_window_demand
 model_status="policy_only_no_validated_domain_model"
 current_from_model=False
 model_reference_demand=None
 feature_values=adapt_features(domain,request.feature_values)
 # Explicit current demand, when supplied, is the observed current-window value.
 # A trained model is used only when its artifact and matching schema exist.
 try:
  if current is None:
   prediction=registry.predict(domain,feature_values)
   if prediction is not None:
    current=prediction["prediction"];model_reference_demand=prediction.get("reference_demand")
    current_from_model=True;model_status="trained_domain_model"
  if next_demand is None:
   next_file=registry.root/domain/"next_window_demand_model.joblib"
   schema=registry.load(domain)
   if next_file.exists() and schema:
    import joblib,pandas as pd
    cols=schema["schema"]["features"]
    row=pd.DataFrame([{c:feature_values.get(c,0) for c in cols}],columns=cols)
    next_demand=max(0,float(joblib.load(next_file).predict(row)[0]))
 except Exception as exc:
  raise HTTPException(status_code=500,detail=f"Domain inference failed: {exc}") from exc
 # Demand index remains a transparent policy input. If a trained current
 # prediction is available, scale it against an explicit normalizer supplied
 # by the caller; never infer a baseline from the test set.
 demand_index=request.demand_index
 normalizer=request.metadata.get("normal_demand")
 if current_from_model and normalizer is None:
  normalizer=model_reference_demand
 if current is not None and normalizer is not None:
  if float(normalizer)<=0: raise HTTPException(status_code=422,detail="normal demand reference must be positive")
  demand_index=current/float(normalizer)
 try:
  result=recommend_price(domain,request.baseline_price_inr,demand_index,
   request.supply_index,request.availability_index,request.traffic_index,
   request.weather_index,request.event_index,request.festival_index,
   request.inventory_index,request.max_price_change_pct,current,next_demand,
   request.optimize,request.elasticity,request.stability_lambda)
  result["model_status"]=model_status
  result["demand_prediction_source"]="trained_model" if current_from_model else ("caller_observation" if current is not None else "not_available")
  result["demand_index_used"]=round(float(demand_index),5)
  result["demand_reference_used"]=normalizer
  result["next_window_prediction_source"]="trained_model" if next_demand is not None and (registry.root/domain/"next_window_demand_model.joblib").exists() else ("caller_supplied" if next_demand is not None else "not_available")
  result["timestamp"]=(request.timestamp or datetime.now()).isoformat()
  result["policy_limits"]={"internal_multiplier_min":.70,"internal_multiplier_max":1.80,"max_price_change_pct":request.max_price_change_pct}
  record_decision(result)
  return result
 except ValueError as exc: raise HTTPException(status_code=422,detail=str(exc)) from exc

@router.get("/model-status")
def model_status():
 return {"models":registry.all_status(DOMAINS)}


@router.get("/monitoring/summary")
def monitoring_summary():
    return audit_summary()


class IntegratedPricingRequest(BaseModel):
    """One request carrying the complete India context plus domain context."""
    domain: Domain
    location_context: dict[str, Any]
    demand_index: float = Field(default=1.0, gt=0)
    supply_index: float = Field(default=1.0, gt=0)
    availability_index: float = Field(default=1.0, gt=0)
    traffic_index: float = Field(default=1.0, gt=0)
    weather_index: float = Field(default=1.0, gt=0)
    event_index: float = Field(default=1.0, gt=0)
    festival_index: float = Field(default=1.0, gt=0)
    inventory_index: float = Field(default=1.0, gt=0)
    max_domain_price_change_pct: float = Field(default=25, ge=0, le=80)
    feature_values: dict[str, Any] = Field(default_factory=dict)
    current_demand: float | None = Field(default=None, ge=0)
    predicted_next_window_demand: float | None = Field(default=None, ge=0)
    optimize: bool = False
    elasticity: float = Field(default=-.6, lt=0)
    stability_lambda: float = Field(default=.15, ge=0)

@router.post("/predict-integrated")
def predict_integrated_price(request: IntegratedPricingRequest):
    """
    Unified recommendation:
      location XGBoost multiplier (locality, traffic, weather, events, etc.)
      multiplied by selected-domain adjustment (domain demand/supply/capacity).
    The final multiplier is bounded to the original model's [1, 4] range.
    """
    try:
        location_request = PredictPriceRequest(**request.location_context)
        location_predictor = get_predictor()
        location_multiplier = float(location_predictor.predict_single(location_request))
        base = float(location_request.base_price_inr)

        # Compose model features from the full location payload plus any
        # domain-specific fields supplied by the unified form.
        features = dict(request.location_context)
        features.update(request.feature_values)
        feature_timestamp = location_request.timestamp or datetime.now()
        features.setdefault("hour", feature_timestamp.hour)
        features.setdefault("day_of_week", feature_timestamp.weekday())
        features.setdefault("state", location_request.state)
        features.setdefault("city", location_request.city)
        features.setdefault("locality", location_request.locality)
        features.setdefault("zone_type", location_request.zone_type)

        current = request.current_demand
        next_demand = request.predicted_next_window_demand
        model_status = "policy_only_no_validated_domain_model"
        current_from_model = False
        normalizer = None

        if current is None:
            prediction = registry.predict(request.domain, adapt_features(request.domain, features))
            if prediction is not None:
                current = prediction["prediction"]
                normalizer = prediction.get("reference_demand")
                current_from_model = True
                model_status = "trained_domain_model"

        next_file = registry.root / request.domain / "next_window_demand_model.joblib"
        model_entry = registry.load(request.domain)
        if next_demand is None and next_file.exists() and model_entry:
            import joblib, pandas as pd
            columns = model_entry["schema"]["features"]
            row = pd.DataFrame([{c: features.get(c, 0) for c in columns}], columns=columns)
            next_demand = max(0.0, float(joblib.load(next_file).predict(row)[0]))

        demand_index_used = request.demand_index
        if current_from_model and normalizer is not None:
            if float(normalizer) <= 0:
                raise ValueError("Trained model reference demand must be positive")
            demand_index_used = current / float(normalizer)

        domain_result = recommend_price(
            request.domain, base,
            demand_index_used, request.supply_index,
            request.availability_index, request.traffic_index,
            request.weather_index, request.event_index,
            request.festival_index, request.inventory_index,
            request.max_domain_price_change_pct,
            current, next_demand, request.optimize,
            request.elasticity, request.stability_lambda
        )
        domain_multiplier = float(domain_result["multiplier"])
        combined_lower_bound = max(0.01, 1.0 - request.max_domain_price_change_pct / 100.0)
        combined_multiplier = max(combined_lower_bound, min(4.0, location_multiplier * domain_multiplier))
        recommended = round(base * combined_multiplier, 2)

        result = {
            "domain": request.domain,
            "location": {
                "state": location_request.state, "city": location_request.city,
                "locality": location_request.locality, "zone_type": location_request.zone_type
            },
            "baseline_price_inr": round(base, 2),
            "location_model_multiplier": round(location_multiplier, 4),
            "domain_adjustment_multiplier": round(domain_multiplier, 4),
            "combined_multiplier": round(combined_multiplier, 4),
            "recommended_price_inr": recommended,
            "price_change_pct": round((combined_multiplier - 1) * 100, 2),
            "location_model": "original_india_xgboost",
            "location_context_used": [
                "state", "city", "locality", "zone_type", "demand_requests",
                "available_supply", "order_density", "population_density",
                "commercial_density", "restaurant_density", "traffic_level",
                "traffic_congestion_index", "average_speed_kmph",
                "weather_condition", "temperature_c", "humidity",
                "rainfall_mm", "visibility_km", "festival_name",
                "festival_intensity", "is_national_holiday", "event_nearby",
                "event_type", "event_attendance", "airport_activity",
                "railway_activity", "metro_activity"
            ],
            "domain_policy": {
                "model_status": model_status,
                "demand_prediction_source": "trained_model" if current_from_model else ("caller_observation" if current is not None else "not_available"),
                "current_demand": current,
                "next_window_demand": next_demand,
                "demand_index_used": round(float(demand_index_used), 5),
                "supply_index": request.supply_index,
                "availability_index": request.availability_index,
                "context_effects": domain_result["explanation"],
                "optimizer": domain_result.get("optimizer"),
                "policy_multiplier": domain_multiplier,
                "price_change_cap_pct": request.max_domain_price_change_pct
            },
            "combination_rule": "clamp(location_model_multiplier * domain_adjustment_multiplier, domain lower bound, 4.0)",
            "timestamp": (request.location_context.get("timestamp") or datetime.now()).isoformat()
                         if isinstance(request.location_context.get("timestamp"), datetime)
                         else datetime.now().isoformat()
        }
        record_decision({
            "domain": request.domain, "baseline_price_inr": base,
            "recommended_price_inr": recommended,
            "multiplier": combined_multiplier,
            "price_change_pct": result["price_change_pct"],
            "model_status": model_status,
            "demand_prediction_source": result["domain_policy"]["demand_prediction_source"],
            "predicted_current_demand": current,
            "predicted_next_window_demand": next_demand,
            "timestamp": result["timestamp"]
        })
        return result
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Integrated pricing failed: {exc}") from exc
