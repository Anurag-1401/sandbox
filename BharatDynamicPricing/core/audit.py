"""Minimal privacy-conscious pricing decision audit log."""
from __future__ import annotations
import json,os
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
LOG_PATH=ROOT/"logs"/"pricing_decisions.jsonl"
def record_decision(result:dict)->None:
 LOG_PATH.parent.mkdir(parents=True,exist_ok=True)
 # Store decision metadata, not raw feature payloads or location/customer identifiers.
 item={k:result.get(k) for k in ("domain","baseline_price_inr","recommended_price_inr",
  "multiplier","price_change_pct","model_status","demand_prediction_source",
  "predicted_current_demand","predicted_next_window_demand","timestamp")}
 item["logged_at"]=datetime.now(timezone.utc).isoformat()
 with LOG_PATH.open("a",encoding="utf-8") as f:f.write(json.dumps(item,default=str)+"\\n")
def summary()->dict:
 if not LOG_PATH.exists():return {"decisions":0,"domains":{},"model_statuses":{}}
 domains={};statuses={};count=0
 with LOG_PATH.open(encoding="utf-8") as f:
  for line in f:
   try:item=json.loads(line)
   except json.JSONDecodeError:continue
   count+=1;d=item.get("domain","unknown");s=item.get("model_status","unknown")
   domains[d]=domains.get(d,0)+1;statuses[s]=statuses.get(s,0)+1
 return {"decisions":count,"domains":domains,"model_statuses":statuses,
         "note":"Decision-volume summary only; model drift requires actual outcome labels and is not inferred from pricing logs."}
