"""Train Linear Regression and XGBoost on the India-specific dataset."""
from __future__ import annotations
import json, os
from pathlib import Path
import numpy as np, pandas as pd, joblib
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
import xgboost as xgb
from .features import engineer_features

ROOT=Path(__file__).resolve().parents[1]; DATA=ROOT/"data"/"pricing_data.csv"; OUT=ROOT/"model"

def rmse(y,p): return float(np.sqrt(mean_squared_error(y,p)))

def main():
    df=pd.read_csv(DATA,parse_dates=["timestamp"],keep_default_na=False)
    df=df.sort_values("timestamp").reset_index(drop=True)
    cut=int(len(df)*0.80); train_df=df.iloc[:cut]; test_df=df.iloc[cut:]
    Xtr=engineer_features(train_df); Xte=engineer_features(test_df)
    Xte=Xte.reindex(columns=Xtr.columns,fill_value=0); ytr=train_df.actual_price_multiplier; yte=test_df.actual_price_multiplier
    feature_columns=list(Xtr.columns)
    linear=Pipeline([("scaler",StandardScaler()),("model",LinearRegression())])
    linear.fit(Xtr,ytr); lp=linear.predict(Xte)
    model=xgb.XGBRegressor(n_estimators=420,max_depth=8,learning_rate=0.055,subsample=0.85,colsample_bytree=0.85,reg_alpha=0.05,reg_lambda=1.0,objective="reg:squarederror",tree_method="hist",random_state=42,n_jobs=max(1,(os.cpu_count() or 4)-1))
    model.fit(Xtr,ytr,eval_set=[(Xte,yte)],verbose=False); xp=model.predict(Xte)
    metrics={"dataset_rows":int(len(df)),"train_rows":int(len(train_df)),"test_rows":int(len(test_df)),"train_end":str(train_df.timestamp.max()),"test_start":str(test_df.timestamp.min()),"models":{"linear_regression":{"rmse":rmse(yte,lp),"mae":float(mean_absolute_error(yte,lp))},"xgboost":{"rmse":rmse(yte,xp),"mae":float(mean_absolute_error(yte,xp))}},"coverage":{"states_or_uts":int(df.state.nunique()),"cities":int(df.city.nunique()),"localities":int(df.locality.nunique()),"zone_types":int(df.zone_type.nunique())}}
    OUT.mkdir(exist_ok=True)
    joblib.dump(linear,OUT/"linear_model.joblib"); model.save_model(OUT/"xgboost_model.json")
    with open(OUT/"feature_columns.json","w") as f: json.dump(feature_columns,f,indent=2)
    profile={}
    for (state,city,locality,zone),g in df.groupby(["state","city","locality","zone_type"]):
        key=f"{state}|{city}|{locality}|{zone}"; h=g.assign(hour=g.timestamp.dt.hour).groupby("hour").agg(avg_demand=("demand_requests","mean"),avg_supply=("available_supply","mean"),avg_order_density=("order_density","mean"),avg_traffic=("traffic_congestion_index","mean")).to_dict("index")
        profile[key]={str(k):v for k,v in h.items()}
    with open(OUT/"location_hour_profile.json","w") as f: json.dump(profile,f,indent=2)
    # Keep backwards-compatible artifact name used by earlier README/users.
    with open(OUT/"zone_hour_profile.json","w") as f: json.dump(profile,f,indent=2)
    with open(OUT/"metrics.json","w") as f: json.dump(metrics,f,indent=2)
    try:
        import shap, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
        sample=Xte.sample(min(1500,len(Xte)),random_state=42); explainer=shap.TreeExplainer(model); values=explainer.shap_values(sample)
        shap.summary_plot(values,sample,show=False,max_display=20); plt.tight_layout(); plt.savefig(OUT/"shap_summary.png",dpi=150,bbox_inches="tight"); plt.close()
    except Exception as e:
        (OUT/"shap_unavailable.txt").write_text(f"SHAP visualization was skipped: {e}\nInstall shap and matplotlib then rerun model/train.py.\n",encoding="utf-8")
    print(json.dumps(metrics,indent=2)); print("Training complete.")

if __name__=="__main__": main()
