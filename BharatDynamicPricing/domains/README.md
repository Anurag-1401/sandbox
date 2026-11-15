# Domain integration status

The API exposes five domain identifiers: ride, food, ecommerce, entertainment, and travel.

The uploaded base ZIP only contains one India-focused synthetic pricing dataset and one XGBoost multiplier model. It does **not** contain the previously discussed empirical NCR Ride model, Zomato/Swiggy Food models, or validated E-commerce, Entertainment, and Travel training artifacts.

Until those artifacts and their matching feature schemas are supplied, `/v1/predict-price` uses the transparent shared pricing-policy layer in `core/pricing_engine.py`. Its output is not a machine-learning demand prediction and is labeled `policy_only_no_validated_domain_model`.

Add each domain's genuine data pipeline, held-out prediction export, trained artifact, feature schema, and inference adapter before marking that domain as ML-trained.
