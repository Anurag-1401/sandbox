# Bharat Dynamic Pricing Engine (BDP)

A five-domain dynamic-pricing platform that keeps demand prediction, contextual
signals, price policy, counterfactual simulation and domain adapters separate.
The original India-focused pricing application remains in place; the BDP API
and dashboard are additive.

## Domains
- **Ride:** ride requests, available drivers, trip fare, pickup/drop and vehicle.
- **Food:** orders, restaurant/delivery capacity and restaurant/order reference price.
- **E-commerce:** product units, inventory and product reference price.
- **Entertainment:** ticket bookings, remaining seats, event horizon and ticket price.
- **Travel:** travel bookings, remaining capacity, departure horizon and travel product price.

The same policy framework is shared, but each domain has its own feature contract,
training artifact and data provenance. Do not merge unrelated row-level datasets.

## Architecture
1. Frontend: original India pricing UI plus `frontend/bdp.html`.
2. FastAPI: original endpoints plus `/v1/*`.
3. Domain adapters: `domains/<domain>/adapter.py`.
4. Model registry: `core/model_registry.py` loads only domain-specific artifacts.
5. Demand models: one current-window model per domain and optional next-window model.
6. Context-aware policy: `core/pricing_engine.py`.
7. Counterfactual simulator: optional elasticity-based scenario analysis.
8. Monitoring artifacts: metrics, feature schema and held-out predictions.

## Run on Windows PowerShell
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m uvicorn api.main:app --reload --port 8000
```
Open `http://127.0.0.1:8000/docs`. Original interface: serve `frontend/` on
port 8080 and open `/index.html`. BDP dashboard: `/bdp.html`.

## BDP API
- `GET /v1/health` — service and per-domain model readiness.
- `GET /v1/domains` — domain descriptions and artifact readiness.
- `GET /v1/model-status` — model and evaluation metadata.
- `POST /v1/predict-price` — current price recommendation, context effects,
  current/next-window demand fields, optional counterfactual optimizer.

Example:
```json
{
  "domain": "ride",
  "baseline_price_inr": 350,
  "demand_index": 1.5,
  "supply_index": 0.8,
  "availability_index": 0.9,
  "traffic_index": 1,
  "weather_index": 1,
  "event_index": 1,
  "festival_index": 1,
  "inventory_index": 1,
  "max_price_change_pct": 25,
  "optimize": true,
  "feature_values": {}
}
```
The indices are relative: `1.0` is neutral; for supply/availability/inventory,
values below `1.0` mean constrained capacity. The API returns an explicit
`model_status`. It never silently substitutes synthetic or unrelated data.

## Current demand vs next-window demand
Current-window demand describes observations already received during the
current interval. Next-window demand is a separate forecast target. The current
price decision must not use a future target as an input. The endpoint returns
these separately and only uses a trained model when the matching artifact and
feature schema are installed. Otherwise the pricing policy uses the supplied
relative demand index and reports policy-only status.

## Train a domain model from a real CSV
```powershell
python training/train_domain_model.py --domain ride --csv data/raw/ride.csv --target current_demand --features hour,day_of_week,lag_1,rolling_mean,available_drivers --timestamp timestamp --next-target next_hour_demand
```
Use the equivalent real feature names for each domain. The script:
- validates the selected columns;
- sorts by timestamp and uses a chronological train/test split;
- trains HistGradientBoostingRegressor by default (or RandomForest), with numeric imputation and categorical one-hot encoding;
- writes the model, feature schema, MAE/RMSE/R², and held-out predictions;
- optionally trains a separate next-window model.

For trained current-window inference, the training script stores the median training-target value as a reference demand. The API normalizes the predicted current demand against this training reference before applying the demand effect. Caller-supplied observed demand is only normalized when `metadata.normal_demand` is explicitly provided.

The model registry expects:
`model/domains/<domain>/demand_model.joblib`,
`feature_schema.json`, and optionally `next_window_demand_model.joblib`.
Only install artifacts built with matching feature schemas and documented
provenance. The old generic XGBoost model is the original India fare multiplier
model; it is not a substitute for the five domain demand models.

## Pricing policy
The policy is documented in `core/pricing_engine.py`. It combines demand,
supply, availability, traffic, weather, event, festival and inventory effects.
The raw multiplier is internally bounded to `[0.70, 1.80]`; the default
customer-facing movement cap is ±25% (configurable up to ±80%, still subject
to the internal bound). The five domains have different weights.

`optimize=true` runs a grid-based counterfactual scenario using the documented
assumed elasticity `-0.6` by default:
`D_cf(m) = D * m^epsilon`,
`R_cf(m) = P_base * m * D_cf(m)`,
`Penalty(m) = lambda * (m-1)^2 * P_base * D`,
`U(m) = R_cf(m) - Penalty(m)`.
This is a simulation, not a causal estimate. Production elasticity requires
observed price variation or controlled experiments.

## Data integrity and current limitations
The uploaded base archive contains a synthetic India-focused pricing dataset
and its XGBoost multiplier model. It does **not** contain the historical
empirical NCR Ride, Zomato/Swiggy Food, E-commerce, Entertainment or Travel
domain model artifacts discussed in the project explanation. Those deleted
datasets and model binaries cannot be reconstructed from reported metrics.
Accordingly, the five-domain API returns `policy_only_no_validated_domain_model`
until each real domain model is trained and installed. No fake datasets or
historical metrics are generated to make the system appear trained.

The original empirical results in the project explanation are historical
research records, not results reproduced by this ZIP. Travel's old tourism
arrivals proxy is not a flight/hotel booking model; E-commerce's reported
negative R² requires further model work. Live traffic/weather/event feeds,
route distance calculation, auth, production monitoring and causal price
experiments remain external integration/deployment work.

## Model provenance, audit and monitoring
Training writes a `model_card.json` with dataset SHA-256, target, feature list,
model type, training timestamp, chronological split and measured metrics.
The API writes a privacy-conscious JSONL decision log without raw feature
payloads or customer/location identifiers. `GET /v1/monitoring/summary`
reports decision counts by domain and model status. This is operational
decision-volume monitoring, not statistical drift detection: true drift
monitoring requires timestamped feature distributions and subsequently
observed ground-truth outcomes. Protect and rotate the local log before
production deployment.

## Tests
```powershell
python -m unittest discover -s tests -v
```


## Unified location + domain pricing (primary dashboard)

The primary page is `frontend/index.html`. It now contains both sets of inputs:
- Indian state, city, locality and zone type;
- the original location XGBoost inputs for demand/supply, locality density,
  traffic, weather, festivals, events and transit activity;
- one of Ride, Food, E-commerce, Entertainment or Travel;
- domain-specific business fields and demand/supply/availability/context indices.

The page submits one request to `POST /v1/predict-integrated`. The API runs the
original India XGBoost location model and the selected domain's demand/policy
layer, then combines the multipliers:

`combined_multiplier = location_model_multiplier * domain_adjustment_multiplier`

The combined result is bounded by the selected domain adjustment's lower
bound and the original India model's upper bound of 4.0. The response exposes
both component multipliers and the effect breakdown. The legacy `/predict-price`
and `/price-forecast` endpoints remain available; the six-hour chart is still
the original location-model forecast and is not a domain-specific future-price
forecast.

When a domain model artifact is absent, its layer is explicitly marked
`policy_only_no_validated_domain_model`; the original India XGBoost location
model still runs. A trained domain model is used only when its artifact and
feature schema are present. The optional advanced JSON field lets you pass
additional feature values matching that domain's trained feature schema.
