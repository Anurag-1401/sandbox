"""Shared feature engineering for training and inference."""
from __future__ import annotations
import pandas as pd

STATES = ["Andhra Pradesh","Arunachal Pradesh","Assam","Bihar","Chhattisgarh","Goa","Gujarat","Haryana","Himachal Pradesh","Jharkhand","Karnataka","Kerala","Madhya Pradesh","Maharashtra","Manipur","Meghalaya","Mizoram","Nagaland","Odisha","Punjab","Rajasthan","Sikkim","Tamil Nadu","Telangana","Tripura","Uttar Pradesh","Uttarakhand","West Bengal","Andaman and Nicobar Islands","Chandigarh","Dadra and Nagar Haveli and Daman and Diu","Delhi","Jammu and Kashmir","Ladakh","Lakshadweep","Puducherry"]
# Cities/localities are read from the generated metadata when available; these
# fallback lists make inference robust even if metadata is absent.
ZONE_TYPES=["Business","IT_Hub","Residential","Market","Entertainment","Tourist","Religious","University","Airport_Transit","Railway_Transit","Metro_Transit","Industrial","Mixed_Use"]
WEATHER=["Clear","Cloudy","Light_Rain","Heavy_Rain","Thunderstorm","Heatwave","Fog"]
TRAFFIC=["Low","Moderate","High","Severe"]
FESTIVALS=["None","Diwali","Holi","Ganesh_Chaturthi","Navratri","Durga_Puja","Eid_al_Fitr","Eid_al_Adha","Christmas","Onam","Pongal","Baisakhi","Janmashtami","Dussehra","Makar_Sankranti","Chhath_Puja","Raksha_Bandhan","Buddha_Purnima","Gurpurab","Republic_Day","Independence_Day","Ramadan_Eid_Window","Gudi_Padwa","Mysuru_Dasara","Bihu"]

def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    out=df.copy().reset_index(drop=True)
    out["timestamp"]=pd.to_datetime(out["timestamp"])
    out["demand_supply_ratio"]=out["demand_requests"] / out["available_supply"].clip(lower=1)
    out["hour_of_day"]=out.timestamp.dt.hour
    out["day_of_week"]=out.timestamp.dt.dayofweek
    out["day_of_year"]=out.timestamp.dt.dayofyear
    out["week_of_year"]=out.timestamp.dt.isocalendar().week.astype(int)
    out["month"]=out.timestamp.dt.month
    out["is_weekend"]=out["day_of_week"].ge(5).astype(int)
    out["is_rush_hour"]=out["hour_of_day"].isin({7,8,9,10,17,18,19,20}).astype(int)
    out["is_night"]=out["hour_of_day"].isin({22,23,0,1,2,3,4,5}).astype(int)
    out["is_festival"]=out["festival_name"].ne("None").astype(int)
    out["event_nearby"]=out["event_nearby"].astype(int)
    out["is_national_holiday"]=out["is_national_holiday"].astype(int)
    # Cyclic time features help the tree model generalize around midnight and
    # month/year boundaries without requiring huge one-hot vectors.
    import numpy as np
    out["hour_sin"]=np.sin(2*np.pi*out.hour_of_day/24); out["hour_cos"]=np.cos(2*np.pi*out.hour_of_day/24)
    out["dow_sin"]=np.sin(2*np.pi*out.day_of_week/7); out["dow_cos"]=np.cos(2*np.pi*out.day_of_week/7)
    out["month_sin"]=np.sin(2*np.pi*out.month/12); out["month_cos"]=np.cos(2*np.pi*out.month/12)
    cats={"state":STATES,"zone_type":ZONE_TYPES,"weather_condition":WEATHER,"traffic_level":TRAFFIC,"festival_name":FESTIVALS}
    # Locality/city categories are discovered from the training data and fixed
    # by feature_columns.json for serving. We intentionally one-hot them because
    # locality-specific demand is a central part of this India-focused model.
    for col,categories in cats.items():
        d=pd.get_dummies(pd.Categorical(out[col],categories=categories),prefix=col)
        out=pd.concat([out,d],axis=1)
    # Stable categorical hashes keep the feature matrix compact even though
    # the India catalog contains hundreds of cities/localities. The model also
    # receives explicit density/context features, so these codes are identifiers
    # rather than pretending that locality names have numeric meaning.
    out["city_code"]=out["city"].astype(str).map(lambda x: (sum((i+1)*ord(c) for i,c in enumerate(x)) % 1009)/1009.0)
    out["locality_code"]=out["locality"].astype(str).map(lambda x: (sum((i+1)*ord(c) for i,c in enumerate(x)) % 5003)/5003.0)
    out["event_type_code"]=out["event_type"].astype(str).map(lambda x: (sum((i+1)*ord(c) for i,c in enumerate(x)) % 97)/97.0)
    numeric=["base_price_inr","city_code","locality_code","event_type_code","demand_requests","available_supply","order_density","population_density","commercial_density","restaurant_density","traffic_congestion_index","average_speed_kmph","temperature_c","humidity","rainfall_mm","visibility_km","festival_intensity","event_attendance","airport_activity","railway_activity","metro_activity","demand_supply_ratio","hour_of_day","day_of_week","day_of_year","week_of_year","month","is_weekend","is_rush_hour","is_night","is_festival","event_nearby","is_national_holiday","hour_sin","hour_cos","dow_sin","dow_cos","month_sin","month_cos"]
    return out[[c for c in out.columns if c in numeric or c.startswith(("state_","zone_type_","weather_condition_","traffic_level_","festival_name_"))]]

def get_feature_columns(df: pd.DataFrame|None=None):
    if df is None:return []
    return list(engineer_features(df).columns)
