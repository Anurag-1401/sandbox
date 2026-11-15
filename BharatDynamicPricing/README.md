# 🇮🇳 India Dynamic Pricing Engine

<p align="center"><img src="https://readme-typing-svg.demolab.com?font=Fira+Code\&size=23\&duration=2600\&pause=800\&center=true\&vCenter=true\&width=850\&lines=India-Specific+Dynamic+Pricing;Demand+%2B+Supply+%2B+Traffic+%2B+Weather;Festivals+%2B+Locality+%2B+Transport+Activity;XGBoost+%2B+SHAP+%2B+FastAPI" alt="India Dynamic Pricing Engine" /></p>

An end-to-end machine-learning portfolio project for predicting a dynamic
price multiplier and final fare in **Indian Rupees (INR)**. The project is
built around synthetic Indian demand patterns across states, cities and
localities, including commuting, markets, IT hubs, tourism, religious areas,
festivals, monsoon conditions, traffic, airport/railway/metro activity and
order density.

> \*\*Important:\*\* all training data is synthetic. The project does not claim to
> use proprietary ride-hailing, delivery, driver GPS or company data.

## ✨ What changed from the original version

The original five generic US-style zones (`Downtown`, `Airport`, `Suburban`,
`University`, `Entertainment\_District`) have been removed from the application
flow. The system now uses Indian geography and context end-to-end:

* 36 Indian states/UT-level locations represented in the generator
* 78 Indian cities and 3,298 locality entries in the location catalog (151 representative localities in the committed training dataset)
* INR base fares
* locality-specific demand and supply behavior
* order density, population/commercial/restaurant density
* Indian traffic and congestion patterns
* monsoon, rain, heatwave and fog effects
* Indian festivals and regional cultural patterns
* weddings, concerts, cricket, conferences and cultural/religious events
* airport, railway and metro activity
* XGBoost prediction + Linear Regression baseline
* SHAP explainability when SHAP/Matplotlib are available
* FastAPI endpoints for metadata and location discovery
* Indian frontend with State → City → Locality → Zone Type selection

## 🧱 Project structure

```text
dynamic-pricing-engine/
├── data/
│   ├── generate\_dataset.py       # India-specific synthetic data generator
│   ├── india\_locations.json      # generated location metadata
│   └── pricing\_data.csv          # generated training dataset
├── model/
│   ├── features.py               # shared train/serve feature engineering
│   ├── train.py                  # Linear Regression + XGBoost + SHAP
│   ├── xgboost\_model.json
│   ├── linear\_model.joblib
│   ├── feature\_columns.json
│   ├── location\_hour\_profile.json
│   ├── zone\_hour\_profile.json    # backwards-compatible profile artifact
│   ├── metrics.json
│   └── shap\_summary.png
├── api/
│   ├── main.py                   # FastAPI routes
│   ├── schemas.py                # Pydantic contracts
│   ├── predictor.py              # model loading + inference
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── style.css
│   ├── app.js
│   └── vendor/chart.umd.js
└── README.md
```

## 🚀 Quickstart

From the repository root:

```powershell
# 1. Install dependencies
pip install -r model/requirements.txt

# 2. Generate the Indian dataset
python data/generate\_dataset.py

# 3. Train Linear Regression + XGBoost
python -m model.train

# 4. Start the API
python -m uvicorn api.main:app --reload --port 8000
```

Open Swagger at `http://localhost:8000/docs`.

In a second terminal:

```powershell
cd frontend
python -m http.server 8080
```

Open `http://localhost:8080`.

## 🇮🇳 Indian data design

The generator deliberately covers Indian diversity rather than four or five
zones. The current configuration includes states/UTs such as Maharashtra,
Karnataka, Tamil Nadu, Telangana, Kerala, Gujarat, Rajasthan, Uttar Pradesh,
West Bengal, Delhi, Jammu \& Kashmir, Ladakh, Goa, Assam, Odisha, Punjab,
Bihar, Jharkhand and the remaining configured Indian states/UTs.

Locality types include:

* Business districts
* IT hubs
* Residential areas
* Markets
* Entertainment districts
* Tourist areas
* Religious areas
* Universities
* Airport transit zones
* Railway transit zones
* Metro transit zones
* Industrial areas
* Mixed-use areas

The generator is configuration-driven. Adding another Indian city or locality
requires extending `INDIA\_LOCATIONS` rather than changing the ML pipeline.

## 🪔 Indian cultural and seasonal modeling

The target is intentionally generated from multiple signals, not only the
raw demand/supply ratio.

### Festivals

Synthetic recurring festival windows model additional demand pressure for
examples such as:

* Diwali
* Holi
* Ganesh Chaturthi
* Navratri
* Durga Puja
* Eid windows
* Christmas
* Onam
* Pongal
* Baisakhi
* Janmashtami
* Dussehra
* Makar Sankranti
* Chhath Puja
* Raksha Bandhan
* Gurpurab
* Republic Day
* Independence Day

Regional effects are also encoded; for example, Ganesh Chaturthi has a
stronger synthetic prior in Maharashtra, Navratri in Gujarat, Durga Puja in
West Bengal, Onam in Kerala, Pongal in Tamil Nadu and Chhath Puja in Bihar,
Jharkhand and parts of Uttar Pradesh.

These are **modeling assumptions**, not official statistics or a claim about
actual ride demand.

### Weather and monsoon

Weather categories include Clear, Cloudy, Light Rain, Heavy Rain,
Thunderstorm, Heatwave and Fog. Monsoon-heavy regions receive higher
synthetic rainfall probability during June–September, while northern regions
receive more winter-fog scenarios.

Weather changes both demand and supply. Severe weather reduces synthetic
available supply while potentially increasing demand.

### Traffic and transport

Traffic congestion, average speed and peak commuting periods are explicit
features. Airport, railway and metro activity are also represented so that a
transit locality behaves differently from a residential locality.

## 📦 Order density

`order\_density` represents the normalized concentration of requests/orders in
a locality. It is influenced synthetically by locality type, commercial
density, restaurant density and city scale. This allows a market, IT hub or
entertainment district to have a different demand profile from a low-density
residential area.

## 🤖 Machine-learning pipeline

```text
Indian synthetic generator
        ↓
pricing\_data.csv
        ↓
Time-based 80/20 split
        ↓
Shared feature engineering
        ↓
 ┌───────────────┬─────────────────┐
 │ Linear        │ XGBoost         │
 │ Regression    │ Regressor       │
 └───────────────┴─────────────────┘
        ↓
RMSE / MAE evaluation
        ↓
XGBoost artifact + feature columns
        ↓
FastAPI predictor
        ↓
₹ INR prediction
```

### Why XGBoost?

The synthetic pricing function is non-linear and saturating. Traffic,
weather, festival intensity, locality type and supply pressure can also
interact. Gradient-boosted trees model these relationships without requiring
large numbers of manually constructed polynomial interactions.

Linear Regression remains as a baseline so the project can answer whether the
extra model complexity is actually useful.

### Time-based evaluation

The last 20% of chronological observations are used as the test set. Random
shuffling is deliberately avoided because a future observation should not
leak into training when the goal is future-facing prediction.

## 🔮 How prediction works

`api/predictor.py` loads the trained XGBoost model and the exact feature-column
list produced during training.

For a current request:

1. The frontend collects Indian location and context signals.
2. `POST /predict-price` validates the request through `schemas.py`.
3. `predictor.py` converts the raw request into a one-row DataFrame.
4. `model/features.py` applies the same feature engineering used during training.
5. Columns are reindexed to the saved training order.
6. XGBoost predicts the multiplier.
7. The API calculates `base\_price\_inr × predicted\_multiplier`.
8. The frontend displays the INR fare.

This shared feature-engineering path prevents train/serve skew.

## 📈 6-hour forecast

`GET /price-forecast` estimates future demand and supply from the historical
hour-of-day profile for the selected **state + city + locality + zone type**.

This is intentionally **not** presented as a real demand forecasting model.
A production system would use live bookings, driver availability, traffic
feeds, weather forecasts, event feeds and a dedicated time-series model.

## 🌐 API

### `GET /locations`

Returns the same Indian state/city/locality configuration used by the
frontend, preventing frontend/backend location mismatches.

### `GET /metadata`

Returns supported weather, traffic, festival and zone-type values.

### `POST /predict-price`

Example request:

```json
{
  "state": "Maharashtra",
  "city": "Mumbai",
  "locality": "BKC",
  "zone\_type": "Business",
  "base\_price\_inr": 220,
  "demand\_requests": 420,
  "available\_supply": 85,
  "order\_density": 0.90,
  "population\_density": 0.72,
  "commercial\_density": 0.98,
  "restaurant\_density": 0.88,
  "traffic\_level": "Severe",
  "traffic\_congestion\_index": 0.91,
  "average\_speed\_kmph": 11,
  "weather\_condition": "Heavy\_Rain",
  "temperature\_c": 27,
  "humidity": 84,
  "rainfall\_mm": 18,
  "visibility\_km": 3,
  "festival\_name": "Ganesh\_Chaturthi",
  "festival\_intensity": 0.95,
  "is\_national\_holiday": false,
  "event\_nearby": true,
  "event\_type": "Cultural\_Event",
  "event\_attendance": 15000,
  "airport\_activity": 0.05,
  "railway\_activity": 0.10,
  "metro\_activity": 0.35
}
```

Response shape:

```json
{
  "state": "Maharashtra",
  "city": "Mumbai",
  "locality": "BKC",
  "zone\_type": "Business",
  "predicted\_multiplier": 2.34,
  "predicted\_price\_inr": 514.8,
  "base\_price\_inr": 220,
  "currency": "INR",
  "model\_used": "xgboost"
}
```

The numbers above are illustrative; the actual prediction is produced by
the trained model.

## 🖥️ Frontend

The frontend is plain HTML/CSS/JS and requires no Node build step. It provides:

* State → City → Locality → Zone Type selection
* INR base fare
* Demand and supply controls
* Order density
* Traffic and congestion
* Weather, rainfall, temperature, humidity and visibility
* Festival and festival intensity
* Event attendance/type
* Airport/railway/metro context inferred from zone type
* Current predicted fare
* 6-hour forecast chart

Chart.js is bundled locally so the demo does not depend on a CDN being
reachable.

## 📊 Training artifacts

After `python -m model.train`:

* `model/xgboost\_model.json` — trained main model
* `model/linear\_model.joblib` — baseline model
* `model/feature\_columns.json` — exact inference column order
* `model/location\_hour\_profile.json` — locality/hour forecast profile
* `model/metrics.json` — measured RMSE/MAE and coverage
* `model/shap\_summary.png` — SHAP summary when SHAP is available
* `model/feature\_importance.png` — compact XGBoost importance plot included with the ready-to-run artifact

## ⚠️ Limitations

* Data is fully synthetic and should not be interpreted as real Indian
ride-hailing demand statistics.
* Festival dates/intensities and locality behavior are assumptions.
* The 6-hour forecast is a historical-profile baseline, not a live
time-series forecasting model.
* The API has no authentication.
* CORS is permissive for local development.
* A real deployment should use real-time data pipelines, weather/traffic
services, monitoring, model versioning and access control.

## 🎯 Portfolio positioning

The project is intentionally transparent about simulation. In an interview,
the strongest claim is not that the synthetic model reproduces a production
ride-hailing company; it is that the project demonstrates a complete ML/data
science pipeline: domain-specific data generation, feature engineering,
chronological evaluation, model comparison, explainability, model serving,
API contracts and an interactive frontend.



## Bharat Dynamic Pricing (five-domain extension)

See [README_BDP.md](README_BDP.md) for the five-domain architecture, `/v1` API, domain model training, pricing policy, counterfactual optimizer, and known artifact limitations. The original India-specific application and its files remain preserved.


## Unified dashboard update

The primary `frontend/index.html` now combines the India location-aware XGBoost
inputs with the five BDP business domains. Start FastAPI on port 8000 and serve
`frontend/` on port 8080. Open `http://127.0.0.1:8080/index.html`. The old
`/bdp.html` path redirects to this unified dashboard; the former standalone
domain-only interface is retained as `bdp-standalone.html`.
