from datetime import datetime
import json
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .predictor import get_predictor
from .schemas import (
    PredictPriceRequest,
    PredictPriceResponse,
    PriceForecastResponse,
)


# ============================================================
# 🇮🇳 India Dynamic Pricing Engine
# FastAPI Application
# ============================================================

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"


app = FastAPI(
    title="🇮🇳 India Dynamic Pricing Engine",
    description=(
        "India-focused synthetic dynamic-pricing ML API using "
        "locality, demand, supply, order density, traffic, weather, "
        "Indian festivals, cultural events and transportation signals."
    ),
    version="2.0.0",
)


# ============================================================
# CORS
# ============================================================

# Wide-open CORS is intentional for local portfolio development.
# Tighten this before deploying to production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# Startup
# ============================================================

@app.on_event("startup")
def startup() -> None:
    """
    Load and validate the ML predictor when FastAPI starts.
    """

    try:
        get_predictor()
    except Exception as exc:
        raise RuntimeError(
            f"Failed to load pricing model: {exc}"
        ) from exc


# ============================================================
# Root
# ============================================================

@app.get("/")
def root():
    return {
        "service": "India Dynamic Pricing Engine",
        "version": "2.0.0",
        "country": "India",
        "currency": "INR",
        "status": "running",
        "docs": "/docs",
        "endpoints": [
            "POST /predict-price",
            "GET /price-forecast",
            "GET /locations",
            "GET /metadata",
        ],
    }


# ============================================================
# Indian Locations
# ============================================================

@app.get("/locations")
def locations():
    """
    Return the complete Indian state → city → locality structure.

    The frontend uses this endpoint to populate:

        State
          ↓
        City
          ↓
        Locality
    """

    location_file = DATA_DIR / "india_locations.json"

    if not location_file.exists():
        raise HTTPException(
            status_code=500,
            detail=(
                "Indian location dataset not found: "
                f"{location_file}"
            ),
        )

    try:
        with location_file.open(
            "r",
            encoding="utf-8",
        ) as file:
            return json.load(file)

    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Invalid india_locations.json: {exc}",
        ) from exc


# ============================================================
# Metadata
# ============================================================

@app.get("/metadata")
def metadata():
    """
    Metadata used by the Indian frontend.

    These values must remain consistent with the values accepted
    by the dataset generator, feature engineering and schemas.
    """

    return {
        "country": "India",

        "currency": "INR",

        "currency_symbol": "₹",

        "weather": [
            "Clear",
            "Cloudy",
            "Light_Rain",
            "Heavy_Rain",
            "Thunderstorm",
            "Heatwave",
            "Fog",
        ],

        "traffic": [
            "Low",
            "Moderate",
            "High",
            "Severe",
        ],

        "zone_types": [
            "Business",
            "IT_Hub",
            "Residential",
            "Market",
            "Entertainment",
            "Tourist",
            "Religious",
            "University",
            "Airport_Transit",
            "Railway_Transit",
            "Metro_Transit",
            "Industrial",
            "Mixed_Use",
        ],

        "festivals": [
            "None",
            "Diwali",
            "Holi",
            "Ganesh_Chaturthi",
            "Navratri",
            "Durga_Puja",
            "Eid_al_Fitr",
            "Eid_al_Adha",
            "Christmas",
            "Onam",
            "Pongal",
            "Baisakhi",
            "Janmashtami",
            "Dussehra",
            "Makar_Sankranti",
            "Chhath_Puja",
            "Raksha_Bandhan",
            "Buddha_Purnima",
            "Gurpurab",
            "Republic_Day",
            "Independence_Day",
        ],

        "event_types": [
            "None",
            "Concert",
            "Cricket_Match",
            "Football_Match",
            "Wedding",
            "Conference",
            "Exhibition",
            "Cultural_Event",
            "Religious_Event",
            "Political_Event",
            "College_Event",
            "Local_Event",
        ],
    }


# ============================================================
# Prediction
# ============================================================

@app.post(
    "/predict-price",
    response_model=PredictPriceResponse,
)
def predict_price(
    request: PredictPriceRequest,
):
    """
    Predict the dynamic pricing multiplier for an Indian locality.

    The ML model uses the demand/supply and contextual features
    supplied in PredictPriceRequest.
    """

    try:
        predictor = get_predictor()

        multiplier = predictor.predict_single(request)

        predicted_price = round(
            request.base_price_inr * multiplier,
            2,
        )

        return PredictPriceResponse(
            state=request.state,
            city=request.city,
            locality=request.locality,
            zone_type=request.zone_type,
            predicted_multiplier=round(
                float(multiplier),
                4,
            ),
            predicted_price_inr=predicted_price,
            base_price_inr=request.base_price_inr,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed: {exc}",
        ) from exc


# ============================================================
# 6-Hour Price Forecast
# ============================================================

@app.get(
    "/price-forecast",
    response_model=PriceForecastResponse,
)
def forecast(
    state: str = Query(
        ...,
        description="Indian state or union territory",
    ),

    city: str = Query(
        ...,
        description="Indian city",
    ),

    locality: str = Query(
        ...,
        description="Indian locality",
    ),

    zone_type: str = Query(
        ...,
        description="Locality/zone type",
    ),

    base_price_inr: float = Query(
        ...,
        gt=0,
        description="Base price in INR",
    ),

    weather_condition: str = Query(
        "Clear",
        description="Current/assumed weather condition",
    ),

    festival_name: str = Query(
        "None",
        description="Indian festival",
    ),

    festival_intensity: float = Query(
        0,
        ge=0,
        le=1,
        description="Festival intensity from 0 to 1",
    ),

    is_national_holiday: bool = Query(
        False,
        description="Whether the selected period is a national holiday",
    ),

    event_nearby: bool = Query(
        False,
        description="Whether a nearby event is active",
    ),

    hours_ahead: int = Query(
        6,
        ge=1,
        le=24,
        description="Number of hours to forecast",
    ),
):
    """
    Generate an hourly price forecast.

    IMPORTANT:
    This project does not contain a dedicated live demand forecasting
    model. Future demand/supply are estimated using historical
    locality/hour profiles generated during training.

    This is a deliberate portfolio-project simplification.
    """

    request = PredictPriceRequest(
        state=state,
        city=city,
        locality=locality,
        zone_type=zone_type,

        base_price_inr=base_price_inr,

        # The forecast predictor internally estimates future
        # demand/supply using historical locality/hour profiles.
        demand_requests=1,
        available_supply=1,

        weather_condition=weather_condition,

        festival_name=festival_name,
        festival_intensity=festival_intensity,

        is_national_holiday=is_national_holiday,

        event_nearby=event_nearby,
    )

    try:
        predictor = get_predictor()

        forecast_points = predictor.forecast(
            request,
            hours_ahead,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Forecast failed: {exc}",
        ) from exc

    return PriceForecastResponse(
        state=state,
        city=city,
        locality=locality,
        zone_type=zone_type,
        base_price_inr=base_price_inr,
        generated_at=datetime.now(),
        forecast=forecast_points,
    )