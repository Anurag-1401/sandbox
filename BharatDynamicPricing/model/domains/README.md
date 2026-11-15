# Domain-specific model artifacts

Each domain has an independent artifact folder. Do not copy metrics from a
research report into these folders and do not mark a model ready without a
matching serialized model and feature schema.

Train with a real, domain-appropriate CSV:

```powershell
python training/train_domain_model.py --domain ride --csv data/raw/ride.csv --target current_demand --features hour,day_of_week,lag_1 --timestamp timestamp --next-target next_hour_demand
```

Required outputs: `demand_model.joblib`, `feature_schema.json`, `metrics.json`,
`test_predictions.csv`; optional `next_window_demand_model.joblib` is created
when `--next-target` is supplied. The training command uses a chronological
split and records MAE, RMSE and R². Preserve data provenance and feature units.
