"""Train one domain-specific demand regressor from a user-supplied real CSV.

Example:
python training/train_domain_model.py --domain ride --csv data/raw/ride.csv \
  --target current_demand --features hour,day_of_week,lag_1 --timestamp timestamp \
  --next-target next_hour_demand
No datasets or metrics are fabricated by this script.
"""
from __future__ import annotations
import argparse,json,hashlib,datetime
from pathlib import Path
import numpy as np,pandas as pd,joblib
from sklearn.ensemble import HistGradientBoostingRegressor,RandomForestRegressor
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder,StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error,mean_squared_error,r2_score
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--domain",required=True,choices=["ride","food","ecommerce","entertainment","travel"])
 p.add_argument("--csv",required=True);p.add_argument("--target",required=True)
 p.add_argument("--features",required=True,help="Comma-separated numeric feature columns")
 p.add_argument("--timestamp",default="timestamp");p.add_argument("--next-target",default=None)
 p.add_argument("--model",choices=["hist_gradient_boosting","random_forest"],default="hist_gradient_boosting")
 p.add_argument("--test-size",type=float,default=.2)
 a=p.parse_args()
 if not 0.05<=a.test_size<=.5: p.error("--test-size must be between .05 and .5")
 path=Path(a.csv); path=path if path.is_absolute() else ROOT/path
 df=pd.read_csv(path)
 features=[x.strip() for x in a.features.split(",") if x.strip()]
 required=[a.target,*features]
 if a.timestamp in df: df[a.timestamp]=pd.to_datetime(df[a.timestamp],errors="coerce");df=df.dropna(subset=[a.timestamp]).sort_values(a.timestamp)
 missing=[c for c in required if c not in df]
 if missing: p.error(f"Missing CSV columns: {missing}")
 df=df.dropna(subset=required).copy()
 if len(df)<30: p.error("At least 30 valid observations are required for chronological evaluation")
 cut=int(len(df)*(1-a.test_size))
 if cut<10 or len(df)-cut<5:p.error("Insufficient train/test rows after split")
 X=df[features].copy()
 y=pd.to_numeric(df[a.target],errors="coerce")
 valid=y.notna();X=X.loc[valid];y=y.loc[valid]
 numeric=[c for c in features if pd.api.types.is_numeric_dtype(X[c])]
 categorical=[c for c in features if c not in numeric]
 pre=ColumnTransformer([
  ("numeric",Pipeline([("imputer",SimpleImputer(strategy="median"))]),numeric),
  ("categorical",Pipeline([("imputer",SimpleImputer(strategy="most_frequent")),("onehot",OneHotEncoder(handle_unknown="ignore"))]),categorical)
 ],remainder="drop")
 estimator=HistGradientBoostingRegressor(max_iter=250,learning_rate=.06,max_leaf_nodes=31,min_samples_leaf=20,l2_regularization=1.0) if a.model=="hist_gradient_boosting" else RandomForestRegressor(n_estimators=300,min_samples_leaf=2,n_jobs=-1,random_state=42)
 model=Pipeline([("preprocessor",pre),("regressor",estimator)])
 cut=int(len(X)*(1-a.test_size));Xtr,Xte=X.iloc[:cut],X.iloc[cut:];ytr,yte=y.iloc[:cut],y.iloc[cut:]
 model.fit(Xtr,ytr);pred=model.predict(Xte)
 metrics={"observations":int(len(X)),"train_observations":len(Xtr),"test_observations":len(Xte),
  "mae":float(mean_absolute_error(yte,pred)),"rmse":float(np.sqrt(mean_squared_error(yte,pred))),
  "r2":float(r2_score(yte,pred)),"target":a.target,"model_type":a.model,
  "timestamp_column":a.timestamp if a.timestamp in df else None}
 out=ROOT/"model"/"domains"/a.domain;out.mkdir(parents=True,exist_ok=True)
 joblib.dump(model,out/"demand_model.joblib")
 schema={"domain":a.domain,"features":features,"numeric_features":numeric,"categorical_features":categorical,
         "target":a.target,"next_target":a.next_target,"model_type":a.model,
         "timestamp_column":metrics["timestamp_column"],"training_rows":len(Xtr),"reference_demand":float(ytr.median())}
 (out/"feature_schema.json").write_text(json.dumps(schema,indent=2),encoding="utf-8")
 (out/"metrics.json").write_text(json.dumps(metrics,indent=2),encoding="utf-8")
 pd.DataFrame({"actual":yte.to_numpy(),"predicted":pred}).to_csv(out/"test_predictions.csv",index=False)
 digest=hashlib.sha256(path.read_bytes()).hexdigest()
 model_card={"model_version":"1.0.0","domain":a.domain,"target":a.target,"model_type":a.model,
  "source_dataset_name":path.name,"source_dataset_sha256":digest,
  "trained_at_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
  "chronological_split":True,"test_size_fraction":a.test_size,"feature_columns":features,
  "numeric_features":numeric,"categorical_features":categorical,"metrics":metrics}
 (out/"model_card.json").write_text(json.dumps(model_card,indent=2),encoding="utf-8")
 if a.next_target:
  if a.next_target not in df: p.error(f"Next target column '{a.next_target}' not found")
  yn=pd.to_numeric(df[a.next_target],errors="coerce")
  validn=yn.notna();Xn=X.loc[validn];yn=yn.loc[validn]
  cn=int(len(Xn)*(1-a.test_size))
  if cn>=10 and len(Xn)-cn>=5:
   next_estimator=HistGradientBoostingRegressor(max_iter=250,learning_rate=.06,max_leaf_nodes=31,min_samples_leaf=20,l2_regularization=1.0) if a.model=="hist_gradient_boosting" else RandomForestRegressor(n_estimators=300,min_samples_leaf=2,n_jobs=-1,random_state=43)
   next_model=Pipeline([("preprocessor",pre),("regressor",next_estimator)])
   next_model.fit(Xn.iloc[:cn],yn.iloc[:cn]);pn=next_model.predict(Xn.iloc[cn:])
   joblib.dump(next_model,out/"next_window_demand_model.joblib")
   schema["next_target"]=a.next_target
   (out/"feature_schema.json").write_text(json.dumps(schema,indent=2),encoding="utf-8")
   metrics["next_window"]={"mae":float(mean_absolute_error(yn.iloc[cn:],pn)),"rmse":float(np.sqrt(mean_squared_error(yn.iloc[cn:],pn))),"r2":float(r2_score(yn.iloc[cn:],pn))}
   (out/"metrics.json").write_text(json.dumps(metrics,indent=2),encoding="utf-8")
 print(json.dumps(metrics,indent=2))
if __name__=="__main__":main()
