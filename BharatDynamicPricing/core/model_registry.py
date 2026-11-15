"""Safe loader for independently trained domain demand models."""
from __future__ import annotations
import json
from pathlib import Path
import joblib
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
MODEL_ROOT=ROOT/"model"/"domains"
class DomainModelRegistry:
 def __init__(self, root:Path|None=None):
  self.root=root or MODEL_ROOT
  self.cache={}
 def load(self, domain:str):
  if domain in self.cache:return self.cache[domain]
  folder=self.root/domain
  model_file=folder/"demand_model.joblib"
  schema_file=folder/"feature_schema.json"
  if not model_file.exists() or not schema_file.exists():return None
  with schema_file.open(encoding="utf-8") as f:schema=json.load(f)
  model=joblib.load(model_file)
  entry={"model":model,"schema":schema,"metrics":self._json(folder/"metrics.json"),
          "model_card":self._json(folder/"model_card.json")}
  self.cache[domain]=entry
  return entry
 @staticmethod
 def _json(path):
  if not path.exists():return {}
  try:return json.loads(path.read_text(encoding="utf-8"))
  except Exception:return {}
 def predict(self,domain:str,features:dict):
  entry=self.load(domain)
  if not entry:return None
  columns=entry["schema"]["features"]
  row=pd.DataFrame([{c:features.get(c,0) for c in columns}],columns=columns)
  prediction=float(entry["model"].predict(row)[0])
  return {"prediction":max(0.0,prediction),"reference_demand":entry["schema"].get("reference_demand"),
          "model_file":f"model/domains/{domain}/demand_model.joblib","metrics":entry["metrics"]}
 def status(self,domain:str):
  e=self.load(domain)
  return {"domain":domain,"ready":bool(e),"model_type":e["schema"].get("model_type") if e else None,
          "target":e["schema"].get("target") if e else None,"metrics":e["metrics"] if e else None,
          "model_card":e["model_card"] if e else None}
 def all_status(self,domains):
  return [self.status(d) for d in domains]
