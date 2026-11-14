from __future__ import annotations
import json, os
from datetime import datetime,timedelta
from pathlib import Path
import joblib, pandas as pd, xgboost as xgb
from model.features import engineer_features

ROOT=Path(__file__).resolve().parents[1]; MODEL_DIR=ROOT/"model"; DATA_DIR=ROOT/"data"
class PricingPredictor:
    def __init__(self):
        self.model=xgb.XGBRegressor(); self.model.load_model(str(MODEL_DIR/"xgboost_model.json"))
        with open(MODEL_DIR/"feature_columns.json",encoding="utf-8") as f:self.feature_columns=json.load(f)
        profile=MODEL_DIR/"location_hour_profile.json"
        if not profile.exists(): profile=MODEL_DIR/"zone_hour_profile.json"
        with open(profile,encoding="utf-8") as f:self.profile=json.load(f)
    def _row(self,d):
        X=engineer_features(pd.DataFrame([d])); return X.reindex(columns=self.feature_columns,fill_value=0)
    def predict_single(self,request):
        ts=request.timestamp or datetime.now()
        d=request.model_dump(); d["timestamp"]=ts
        pred=float(self.model.predict(self._row(d))[0]); return round(max(1.0,min(4.0,pred)), 4)
    def forecast(self,request,hours_ahead=6):
        key=f"{request.state}|{request.city}|{request.locality}|{request.zone_type}"; prof=self.profile.get(key)
        if not prof:
            # The public location catalog contains more localities than the
            # compact training sample. Fall back to another trained locality
            # in the same city and zone type, preserving a usable forecast
            # instead of failing just because that locality was not sampled.
            prefix=f"{request.state}|{request.city}|"
            candidates=[(k,v) for k,v in self.profile.items() if k.startswith(prefix) and k.endswith(f"|{request.zone_type}")]
            if not candidates:
                candidates=[(k,v) for k,v in self.profile.items() if k.startswith(prefix)]
            if not candidates: raise ValueError(f"No historical profile for city '{request.city}'")
            prof=candidates[0][1]
        now=request.timestamp or datetime.now(); out=[]
        for i in range(1,hours_ahead+1):
            ts=now+timedelta(hours=i); p=prof.get(str(ts.hour)) or next(iter(prof.values()))
            d=request.model_dump(); d.update(timestamp=ts,demand_requests=p["avg_demand"],available_supply=p["avg_supply"],order_density=p.get("avg_order_density",request.order_density))
            pred=max(1.0,min(4.0,float(self.model.predict(self._row(d))[0])))
            out.append({"timestamp":ts,"hour_offset":i,"predicted_multiplier":round(pred,4),"predicted_price_inr":round(request.base_price_inr*pred,2),"assumed_demand":round(p["avg_demand"],1),"assumed_supply":round(p["avg_supply"],1),"assumed_order_density":round(p.get("avg_order_density",request.order_density),3)})
        return out
_predictor=None
def get_predictor():
    global _predictor
    if _predictor is None:_predictor=PricingPredictor()
    return _predictor
