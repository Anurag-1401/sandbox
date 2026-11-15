from datetime import datetime
from pydantic import BaseModel, Field
from typing import List

class PredictPriceRequest(BaseModel):
    state:str=Field(...,min_length=1); city:str=Field(...,min_length=1); locality:str=Field(...,min_length=1); zone_type:str=Field(...,min_length=1)
    base_price_inr:float=Field(...,gt=0); demand_requests:int=Field(...,ge=0); available_supply:int=Field(...,ge=0)
    order_density:float=Field(0.5,ge=0,le=1); population_density:float=Field(0.5,ge=0,le=1); commercial_density:float=Field(0.5,ge=0,le=1); restaurant_density:float=Field(0.5,ge=0,le=1)
    traffic_level:str="Moderate"; traffic_congestion_index:float=Field(0.5,ge=0,le=1); average_speed_kmph:float=Field(25,ge=0)
    weather_condition:str="Clear"; temperature_c:float=25; humidity:float=60; rainfall_mm:float=0; visibility_km:float=10
    festival_name:str="None"; festival_intensity:float=Field(0,ge=0,le=1); is_national_holiday:bool=False
    event_nearby:bool=False; event_type:str="None"; event_attendance:int=Field(0,ge=0)
    airport_activity:float=Field(0,ge=0,le=1); railway_activity:float=Field(0,ge=0,le=1); metro_activity:float=Field(0,ge=0,le=1)
    timestamp:datetime|None=None
    model_config={"json_schema_extra":{"example":{"state":"Maharashtra","city":"Mumbai","locality":"BKC","zone_type":"Business","base_price_inr":220,"demand_requests":420,"available_supply":85,"order_density":0.90,"population_density":0.72,"commercial_density":0.98,"restaurant_density":0.88,"traffic_level":"Severe","traffic_congestion_index":0.91,"average_speed_kmph":11,"weather_condition":"Heavy_Rain","temperature_c":27,"humidity":84,"rainfall_mm":18,"visibility_km":3,"festival_name":"Ganesh_Chaturthi","festival_intensity":0.95,"is_national_holiday":False,"event_nearby":True,"event_type":"Cultural_Event","event_attendance":15000,"airport_activity":0.05,"railway_activity":0.10,"metro_activity":0.35}}}

class PredictPriceResponse(BaseModel):
    state:str; city:str; locality:str; zone_type:str; predicted_multiplier:float; predicted_price_inr:float; base_price_inr:float; currency:str="INR"; model_used:str="xgboost"
class ForecastPoint(BaseModel):
    timestamp:datetime; hour_offset:int; predicted_multiplier:float; predicted_price_inr:float; assumed_demand:float; assumed_supply:float; assumed_order_density:float
class PriceForecastResponse(BaseModel):
    state:str; city:str; locality:str; zone_type:str; base_price_inr:float; currency:str="INR"; generated_at:datetime; forecast:List[ForecastPoint]
