"""
India-specific synthetic dynamic-pricing dataset generator.

The dataset is intentionally synthetic. It does not use or claim access to
proprietary ride-hailing data. Instead, it encodes transparent assumptions
about Indian cities, localities, commuting, commerce, festivals, monsoon,
traffic and transport activity.

Run from the repository root:
    python data/generate_dataset.py
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
import json
import numpy as np
import pandas as pd

RNG = np.random.default_rng(42)
ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent / "pricing_data.csv"
LOCATION_CONFIG_OUT = Path(__file__).resolve().parent / "india_locations.json"

# Broad national coverage: all 28 states + 8 union territories, with major
# cities/localities represented. Localities are synthetic modeling zones, not
# claims about official administrative boundaries.
INDIA_LOCATIONS = {
"Andhra Pradesh": {"Visakhapatnam":["Madhurawada","Dwaraka Nagar","Gajuwaka","Beach Road"],"Vijayawada":["Benz Circle","MG Road","Governorpet","Kanuru"],"Tirupati":["Tirumala","Tiruchanoor","Renigunta","Tirupati Central"]},
"Arunachal Pradesh": {"Itanagar":["Naharlagun","Ganga Market","Bank Tinali","Itanagar Central"]},
"Assam": {"Guwahati":["Paltan Bazaar","Dispur","Beltola","Six Mile","Guwahati Railway"],"Dibrugarh":["Chowkidingee","AMCH Area","Milan Nagar"]},
"Bihar": {"Patna":["Boring Road","Kankarbagh","Patliputra Colony","Patna Junction","Bailey Road"],"Gaya":["Bodh Gaya","Gaya Junction","Civil Lines"]},
"Chhattisgarh": {"Raipur":["Telibandha","Pandri","Tatibandh","Naya Raipur","Railway Station"],"Bhilai":["Civic Centre","Supela","Nehru Nagar"]},
"Goa": {"Panaji":["Miramar","Campal","Panjim Market","Dona Paula"],"Vasco da Gama":["Airport Road","Chicalim","Vasco Market"]},
"Gujarat": {"Ahmedabad":["SG Highway","Navrangpura","Satellite","Maninagar","Bopal","Airport Road"],"Surat":["Vesu","Adajan","Varachha","Ring Road","Athwa"],"Vadodara":["Alkapuri","Gotri","Sayajigunj","Manjalpur"],"Rajkot":["Kalawad Road","University Road","Raiya Road"]},
"Haryana": {"Gurugram":["Cyber City","Golf Course Road","Sohna Road","Sector 29","Udyog Vihar","IFFCO Chowk"],"Faridabad":["Sector 15","NIT","Neelam Chowk","Mathura Road"],"Panipat":["Model Town","GT Road","Bus Stand"]},
"Himachal Pradesh": {"Shimla":["Mall Road","Sanjauli","Chotta Shimla","ISBT"],"Manali":["Mall Road","Old Manali","Vashisht","Bus Stand"]},
"Jharkhand": {"Ranchi":["Morabadi","Harmu","Lalpur","Kanke Road","Ranchi Junction"],"Jamshedpur":["Bistupur","Sakchi","Sonari","Adityapur"]},
"Karnataka": {"Bengaluru":["Whitefield","Electronic City","Koramangala","Indiranagar","HSR Layout","Marathahalli","MG Road","Hebbal","Yelahanka"],"Mysuru":["Vijayanagar","Hebbal","Kuvempunagar","Mysore Palace"],"Mangaluru":["Kadri","Hampankatta","Kottara","Surathkal"],"Hubballi":["Gokul Road","Vidya Nagar","Keshwapur"]},
"Kerala": {"Kochi":["Kakkanad","Edappally","Fort Kochi","Vyttila","Aluva"],"Thiruvananthapuram":["Technopark","Kowdiar","Pattom","East Fort"],"Kozhikode":["Mavoor Road","Nadakkavu","Kallai","Beach Road"]},
"Madhya Pradesh": {"Indore":["Vijay Nagar","Palasia","Bhawarkua","Rau","Airport Road"],"Bhopal":["MP Nagar","Arera Colony","New Market","Kolar Road"],"Gwalior":["Thatipur","Lashkar","City Centre"]},
"Maharashtra": {"Mumbai":["BKC","Andheri","Bandra","Powai","Dadar","Lower Parel","Colaba","Borivali","Kurla","Thane Road"],"Pune":["Hinjawadi","Kharadi","Baner","Wakad","Viman Nagar","Hadapsar","Kothrud","Shivajinagar"],"Nagpur":["Sitabuldi","Dharampeth","Sadar","Wardha Road","Manish Nagar"],"Nashik":["Gangapur Road","College Road","Panchavati","Nashik Road"],"Navi Mumbai":["Vashi","Nerul","Belapur","Kharghar","Airoli"]},
"Manipur": {"Imphal":["Paona Bazaar","Lamphel","Singjamei","Airport Road"]},
"Meghalaya": {"Shillong":["Police Bazaar","Laitumkhrah","Laban","Mawlai"]},
"Mizoram": {"Aizawl":["Dawrpui","Chaltlang","Zarkawt","Bawngkawn"]},
"Nagaland": {"Kohima":["Mao Gate","PR Hill","Midland","Kohima Market"]},
"Odisha": {"Bhubaneswar":["Saheed Nagar","Patia","Khandagiri","Jaydev Vihar","Airport Road"],"Cuttack":["Badambadi","College Square","CDA","Choudwar"]},
"Punjab": {"Ludhiana":["Ferozepur Road","Model Town","Dugri","Ludhiana Junction"],"Amritsar":["Golden Temple","Ranjit Avenue","Mall Road","Airport Road"],"Jalandhar":["Model Town","GT Road","Urban Estate"]},
"Rajasthan": {"Jaipur":["Malviya Nagar","C Scheme","Vaishali Nagar","Mansarovar","Tonk Road"],"Jodhpur":["Sardarpura","Ratanada","Paota","Clock Tower"],"Udaipur":["Hiran Magri","Fateh Sagar","Lake Pichola","Udaipur Station"]},
"Sikkim": {"Gangtok":["MG Marg","Tadong","Deorali","Tibet Road"]},
"Tamil Nadu": {"Chennai":["OMR","T Nagar","Anna Nagar","Adyar","Guindy","Velachery","Tambaram","Airport Road"],"Coimbatore":["RS Puram","Peelamedu","Gandhipuram","Saravanampatti"],"Madurai":["Anna Nagar","KK Nagar","Mattuthavani","Temple Area"],"Tiruchirappalli":["Srirangam","Cantonment","Woraiyur"]},
"Telangana": {"Hyderabad":["HITEC City","Gachibowli","Banjara Hills","Jubilee Hills","Madhapur","Kukatpally","Secunderabad","Airport Road"],"Warangal":["Hanamkonda","Kazipet","Warangal Fort"]},
"Tripura": {"Agartala":["GB Bazaar","Dhaleswar","Battala","Airport Road"]},
"Uttar Pradesh": {"Lucknow":["Gomti Nagar","Hazratganj","Aliganj","Indira Nagar","Charbagh"],"Noida":["Sector 62","Sector 18","Noida Expressway","Botanical Garden","Sector 137"],"Kanpur":["Swaroop Nagar","Kakadeo","Mall Road","Govind Nagar"],"Varanasi":["Assi Ghat","Lanka","Godowlia","Cantt","Sarnath"],"Agra":["Taj Ganj","Sanjay Place","Sikandra","Agra Cantt"]},
"Uttarakhand": {"Dehradun":["Rajpur Road","Clock Tower","ISBT","Sahastradhara Road"],"Haridwar":["Har Ki Pauri","Jwalapur","Railway Road","Kankhal"],"Rishikesh":["Tapovan","Laxman Jhula","Ram Jhula","Bus Stand"]},
"West Bengal": {"Kolkata":["Salt Lake","New Town","Park Street","Ballygunge","Howrah","Sealdah","Airport Road"],"Siliguri":["Sevoke Road","Hill Cart Road","Matigara","NJ P Station"]},
"Andaman and Nicobar Islands": {"Port Blair":["Aberdeen Bazaar","Airport Road","Corbyn's Cove","Dairy Farm"]},
"Chandigarh": {"Chandigarh":["Sector 17","Sector 22","IT Park","Industrial Area"]},
"Dadra and Nagar Haveli and Daman and Diu": {"Daman":["Nani Daman","Moti Daman","Devka","Airport Road"],"Silvassa":["Vapi Road","Tokarkhada","Dadra"]},
"Delhi": {"New Delhi":["Connaught Place","Saket","Dwarka","Rohini","Karol Bagh","Hauz Khas","Aerocity","Delhi Airport"]},
"Jammu and Kashmir": {"Srinagar":["Lal Chowk","Dal Lake","Hazratbal","Airport Road"],"Jammu":["Gandhi Nagar","Trikuta Nagar","Jammu Tawi","Airport Road"]},
"Ladakh": {"Leh":["Leh Market","Changspa","Skara","Airport Road"]},
"Lakshadweep": {"Kavaratti":["Kavaratti Market","Jetty Area","Beach Area"]},
"Puducherry": {"Puducherry":["White Town","Lawspet","Auroville Road","Bus Stand"]},
}

ZONE_TYPES = ["Business", "IT_Hub", "Residential", "Market", "Entertainment", "Tourist", "Religious", "University", "Airport_Transit", "Railway_Transit", "Metro_Transit", "Industrial", "Mixed_Use"]
WEATHER = ["Clear", "Cloudy", "Light_Rain", "Heavy_Rain", "Thunderstorm", "Heatwave", "Fog"]
FESTIVALS = ["None", "Diwali", "Holi", "Ganesh_Chaturthi", "Navratri", "Durga_Puja", "Eid_al_Fitr", "Eid_al_Adha", "Christmas", "Onam", "Pongal", "Baisakhi", "Janmashtami", "Dussehra", "Makar_Sankranti", "Chhath_Puja", "Raksha_Bandhan", "Buddha_Purnima", "Gurpurab", "Republic_Day", "Independence_Day"]
FESTIVAL_BOOST = {"None":0.0,"Diwali":0.34,"Holi":0.22,"Ganesh_Chaturthi":0.30,"Navratri":0.28,"Durga_Puja":0.30,"Eid_al_Fitr":0.24,"Eid_al_Adha":0.18,"Christmas":0.20,"Onam":0.22,"Pongal":0.24,"Baisakhi":0.20,"Janmashtami":0.18,"Dussehra":0.22,"Makar_Sankranti":0.16,"Chhath_Puja":0.22,"Raksha_Bandhan":0.16,"Buddha_Purnima":0.14,"Gurpurab":0.20,"Republic_Day":0.08,"Independence_Day":0.08}
REGIONAL_FESTIVALS = {
"Maharashtra":{"Ganesh_Chaturthi","Gudi_Padwa"}, "Gujarat":{"Navratri"}, "West Bengal":{"Durga_Puja"},
"Kerala":{"Onam"}, "Tamil Nadu":{"Pongal"}, "Punjab":{"Baisakhi","Gurpurab"},
"Bihar":{"Chhath_Puja"}, "Uttar Pradesh":{"Chhath_Puja","Janmashtami"}, "Delhi":{"Diwali","Holi"},
"Karnataka":{"Mysuru_Dasara"}, "Goa":{"Christmas"}, "Assam":{"Bihu"}
}

ZONE_WEIGHTS = {
"Business":1.35,"IT_Hub":1.55,"Residential":1.05,"Market":1.40,"Entertainment":1.30,"Tourist":1.20,"Religious":1.25,"University":0.90,"Airport_Transit":1.60,"Railway_Transit":1.50,"Metro_Transit":1.35,"Industrial":0.95,"Mixed_Use":1.15}
CITY_TIER = {"Mumbai":1.35,"Delhi":1.35,"Bengaluru":1.30,"Hyderabad":1.25,"Chennai":1.22,"Pune":1.18,"Kolkata":1.20,"Ahmedabad":1.15,"Gurugram":1.22,"Noida":1.18,"default":1.0}

# Deterministic locality classification using recognizable Indian locality
# names. Everything else receives a sensible mixed-use prior.
def classify_locality(name: str) -> str:
    n=name.lower()
    if any(x in n for x in ["airport","aerocity"]): return "Airport_Transit"
    if any(x in n for x in ["railway","junction","njp","jammu tawi","sealdah"]): return "Railway_Transit"
    if any(x in n for x in ["metro","mg road","station"]): return "Metro_Transit"
    if any(x in n for x in ["it park","hitech","hitec","electronic city","whitefield","cyber city","technopark","omr","hinjawadi","gachibowli","madhapur","silicon"]): return "IT_Hub"
    if any(x in n for x in ["market","bazaar","chowk","ring road","pandri","varachha"]): return "Market"
    if any(x in n for x in ["temple","ghat","golden temple","tirumala","tiruchanoor","sarnath","religious"]): return "Religious"
    if any(x in n for x in ["beach","lake","pichola","taj","tourist","fort kochi","auroville","old manali","dal lake","fateh sagar"]): return "Tourist"
    if any(x in n for x in ["mall road","mall","park street","entertainment","campal"]): return "Entertainment"
    if any(x in n for x in ["university","campus","vidya nagar","bawngkawn"]): return "University"
    if any(x in n for x in ["industrial","udyog","supela","adityapur"]): return "Industrial"
    if any(x in n for x in ["bkc","business","c scheme","navrangpura","baner","kharadi","t nagar","salt lake","sector 62","sector 18"]): return "Business"
    return "Mixed_Use"

def festival_for_date(ts: pd.Timestamp, state: str, city: str) -> str:
    # Synthetic recurring calendar windows, deliberately approximate rather
    # than pretending to reproduce official lunar-calendar dates.
    m,d=ts.month,ts.day
    if (m==1 and d in range(13,17)): return "Pongal" if state=="Tamil Nadu" else "Makar_Sankranti"
    if m==1 and d==26: return "Republic_Day"
    if m==2 and d in range(20,26): return "Holi"
    if m==3 and d in range(25,31): return "Eid_al_Fitr"
    if m==4 and d in range(10,18): return "Baisakhi" if state=="Punjab" else "Ramadan_Eid_Window"
    if m==5 and d in range(15,22): return "Buddha_Purnima"
    if m==8 and d in range(15,17): return "Independence_Day"
    if m==8 and d in range(20,31):
        if state=="Maharashtra": return "Ganesh_Chaturthi"
        if state=="Kerala": return "Onam"
        if state=="Punjab": return "Gurpurab"
    if m==9 and d in range(20,30): return "Navratri" if state=="Gujarat" else "Durga_Puja" if state=="West Bengal" else "Dussehra"
    if m==10 and d in range(10,25): return "Diwali"
    if m==11 and d in range(1,15): return "Chhath_Puja" if state in {"Bihar","Jharkhand","Uttar Pradesh"} else "Diwali"
    if m==12 and d in range(20,27): return "Christmas"
    return "None"

def weather_for(ts: pd.Timestamp, state: str) -> str:
    # Indian seasonal weather assumptions: monsoon-heavy states get more rain
    # during Jun-Sep; northern hill/continental regions get more fog in winter.
    monsoon = state in {"Maharashtra","Goa","Kerala","Karnataka","Tamil Nadu","Assam","West Bengal","Odisha","Andhra Pradesh","Telangana","Gujarat"}
    r=RNG.random()
    if ts.month in (6,7,8,9) and monsoon:
        if r<0.40:return "Heavy_Rain"
        if r<0.62:return "Light_Rain"
        if r<0.68:return "Thunderstorm"
    if ts.month in (4,5) and state not in {"Himachal Pradesh","Jammu and Kashmir","Ladakh","Sikkim","Uttarakhand","Meghalaya"} and r<0.10:return "Heatwave"
    if ts.month in (12,1,2) and state in {"Delhi","Punjab","Haryana","Uttar Pradesh","Bihar","Rajasthan","West Bengal","Jammu and Kashmir","Uttarakhand","Himachal Pradesh"} and r<0.13:return "Fog"
    if r<0.18:return "Cloudy"
    return "Clear"

WEATHER_DEMAND={"Clear":1.0,"Cloudy":1.03,"Light_Rain":1.12,"Heavy_Rain":1.28,"Thunderstorm":1.35,"Heatwave":1.10,"Fog":1.12}
WEATHER_SUPPLY={"Clear":1.0,"Cloudy":0.98,"Light_Rain":0.92,"Heavy_Rain":0.82,"Thunderstorm":0.70,"Heatwave":0.94,"Fog":0.88}

BASE_PRICE_ZONE={"Business":190,"IT_Hub":175,"Residential":120,"Market":130,"Entertainment":165,"Tourist":180,"Religious":145,"University":95,"Airport_Transit":260,"Railway_Transit":190,"Metro_Transit":150,"Industrial":125,"Mixed_Use":140}

def generate_dataset(days: int=30) -> pd.DataFrame:
    start=pd.Timestamp("2026-01-01 00:00:00")
    hours=pd.date_range(start=start, periods=days*24, freq="h")
    rows=[]
    locality_count=0
    for state,cities in INDIA_LOCATIONS.items():
        for city,localities in cities.items():
            for locality in localities: locality_count+=1
    print(f"Generating {days} days across {len(INDIA_LOCATIONS)} Indian states/UTs and {locality_count} localities...")
    for ts in hours:
        dow=ts.dayofweek; hour=ts.hour; weekend=dow>=5
        for state,cities in INDIA_LOCATIONS.items():
            for city,all_localities in cities.items():
                city_factor=CITY_TIER.get(city,CITY_TIER["default"])
                # Keep every configured city represented, while sampling at most
                # two representative localities per city for a practical training
                # dataset. The full location catalog remains available to the UI.
                localities=all_localities[:2]
                for locality in localities:
                    zone=classify_locality(locality)
                    zone_factor=ZONE_WEIGHTS[zone]
                    weather=weather_for(ts,state)
                    festival=festival_for_date(ts,state,city)
                    festival_intensity=0.0 if festival=="None" else min(1.0, 0.55+RNG.random()*0.45)
                    # Daily/weekly Indian mobility rhythm.
                    if zone in {"Business","IT_Hub"}:
                        time_factor=2.35 if (not weekend and hour in {8,9,10,17,18,19,20}) else 1.35 if 11<=hour<=16 else 0.70
                    elif zone in {"Market","Religious"}:
                        time_factor=1.55 if hour in {10,11,12,17,18,19,20,21} else 0.75
                    elif zone=="Entertainment":
                        time_factor=2.15 if hour in {20,21,22,23,0,1} else 0.55 if 5<=hour<=11 else 1.0
                        if weekend and hour>=18: time_factor*=1.25
                    elif zone=="Tourist":
                        time_factor=1.75 if 10<=hour<=18 else 0.75
                    elif zone=="University":
                        time_factor=1.75 if (not weekend and hour in {8,9,10,12,13,16,17}) else 0.45 if weekend else 0.85
                    elif zone in {"Airport_Transit","Railway_Transit","Metro_Transit"}:
                        time_factor=1.65 if hour in {6,7,8,9,17,18,19,20,21,22} else 1.15
                    elif zone=="Industrial":
                        time_factor=1.50 if not weekend and hour in {7,8,9,16,17,18} else 0.65
                    else:
                        time_factor=1.50 if hour in {8,9,10,17,18,19,20} else 0.80
                    if weekend and zone in {"Business","IT_Hub","Industrial"}: time_factor*=0.72
                    if weekend and zone in {"Tourist","Entertainment","Religious","Market"}: time_factor*=1.12
                    if festival!="None":
                        time_factor*=1.0 + 0.55*festival_intensity
                    commercial_density=float(np.clip(0.35 + zone_factor/2 + RNG.normal(0,0.08),0.05,1.0))
                    population_density=float(np.clip(0.45 + (1.3 if zone in {"Residential","Mixed_Use"} else 0.7)*RNG.random(),0.05,1.0))
                    restaurant_density=float(np.clip(0.25 + (0.55 if zone in {"Market","Entertainment","Tourist","IT_Hub"} else 0.30)*RNG.random(),0.02,1.0))
                    order_density=float(np.clip(0.35 + 0.32*zone_factor + 0.15*commercial_density + 0.08*restaurant_density + RNG.normal(0,0.06),0.05,1.0))
                    traffic_base=0.35 + 0.55*(hour in {8,9,10,17,18,19,20}) + 0.10*(not weekend) + 0.08*(zone in {"Business","IT_Hub","Market","Airport_Transit"})
                    traffic_congestion=float(np.clip(traffic_base + RNG.normal(0,0.08),0.05,1.0))
                    traffic_level="Low" if traffic_congestion<0.35 else "Moderate" if traffic_congestion<0.60 else "High" if traffic_congestion<0.80 else "Severe"
                    average_speed=float(np.clip(42 - 31*traffic_congestion + RNG.normal(0,3),7,50))
                    airport_activity=float(np.clip((1.0 if zone=="Airport_Transit" else 0.10) * (0.65+0.35*(hour in {5,6,7,8,21,22,23})) + RNG.normal(0,0.04),0,1))
                    railway_activity=float(np.clip((1.0 if zone=="Railway_Transit" else 0.08) * (0.70+0.30*(hour in {6,7,8,17,18,19,20,21})) + RNG.normal(0,0.04),0,1))
                    metro_activity=float(np.clip((1.0 if zone=="Metro_Transit" else 0.12) * (0.55+0.45*(hour in {7,8,9,17,18,19,20})) + RNG.normal(0,0.04),0,1))
                    event_nearby=bool(RNG.random()< (0.035 + 0.04*(festival!="None") + 0.02*(zone in {"Entertainment","Tourist","Religious"})))
                    event_type="None"
                    if event_nearby:
                        event_type=RNG.choice(["Concert","Cricket_Match","Wedding","Conference","Cultural_Event","Religious_Event","College_Event"], p=[.15,.15,.14,.10,.16,.18,.12])
                    event_attendance=int(max(0,RNG.lognormal(7.0,0.8))) if event_nearby else 0
                    base_orders=42*city_factor*zone_factor*time_factor*(0.70+0.55*order_density)
                    base_orders*=WEATHER_DEMAND[weather]
                    base_orders*=1+0.30*traffic_congestion
                    if event_nearby: base_orders*=1.0+min(0.75,event_attendance/30000)
                    demand=int(max(1,RNG.normal(base_orders, max(3,base_orders*0.13))))
                    supply_base=38*city_factor*(0.92+0.12*np.sin((hour/24)*2*np.pi))* (1.0-0.18*traffic_congestion) * WEATHER_SUPPLY[weather]
                    supply_base*=1.0 + 0.10*(zone in {"Airport_Transit","Railway_Transit","Metro_Transit"})
                    supply=int(max(1,RNG.normal(supply_base,supply_base*0.12)))
                    ratio=demand/max(1,supply)
                    surge=1.0 + 2.35*(1-np.exp(-0.48*ratio))
                    surge += 0.12*traffic_congestion + 0.12*order_density + FESTIVAL_BOOST.get(festival,0)*festival_intensity
                    if weather in {"Light_Rain","Heavy_Rain","Thunderstorm"}: surge += {"Light_Rain":0.05,"Heavy_Rain":0.16,"Thunderstorm":0.28}[weather]
                    if weather=="Heatwave": surge+=0.07
                    if weather=="Fog": surge+=0.08
                    if event_nearby: surge+=0.12+min(0.28,event_attendance/50000)
                    surge += RNG.normal(0,0.055)
                    multiplier=float(np.clip(surge,1.0,4.0))
                    base_price=BASE_PRICE_ZONE[zone]*(0.90+0.12*city_factor)
                    rows.append({
                        "timestamp":ts,"state":state,"city":city,"locality":locality,"zone_type":zone,
                        "base_price_inr":round(base_price,2),"demand_requests":demand,"available_supply":supply,
                        "order_density":round(order_density,4),"population_density":round(population_density,4),"commercial_density":round(commercial_density,4),"restaurant_density":round(restaurant_density,4),
                        "traffic_level":traffic_level,"traffic_congestion_index":round(traffic_congestion,4),"average_speed_kmph":round(average_speed,2),
                        "weather_condition":weather,"temperature_c":round(float(np.clip(18+12*np.sin((ts.dayofyear-80)/365*2*np.pi)+RNG.normal(0,4),8,44)),1),"humidity":round(float(np.clip(65+18*np.cos((ts.dayofyear)/365*2*np.pi)+RNG.normal(0,8),20,100)),1),
                        "rainfall_mm":round(float({"Clear":0,"Cloudy":0.5,"Light_Rain":5,"Heavy_Rain":18,"Thunderstorm":25,"Heatwave":0,"Fog":0.2}[weather]*(0.6+0.8*RNG.random())),2),"visibility_km":round(float({"Clear":10,"Cloudy":8,"Light_Rain":6,"Heavy_Rain":3,"Thunderstorm":2,"Heatwave":6,"Fog":1.5}[weather]*(0.85+0.25*RNG.random())),2),
                        "festival_name":festival,"festival_intensity":round(festival_intensity,4),"is_national_holiday":bool(festival in {"Republic_Day","Independence_Day","Diwali","Holi","Christmas"}),
                        "event_nearby":event_nearby,"event_type":event_type,"event_attendance":event_attendance,
                        "airport_activity":round(airport_activity,4),"railway_activity":round(railway_activity,4),"metro_activity":round(metro_activity,4),
                        "is_weekend":weekend,"actual_price_multiplier":round(multiplier,4)
                    })
    df=pd.DataFrame(rows).sort_values("timestamp").reset_index(drop=True)
    return df

if __name__=="__main__":
    df=generate_dataset(30)
    df.to_csv(OUT,index=False)
    with open(LOCATION_CONFIG_OUT,"w",encoding="utf-8") as f: json.dump(INDIA_LOCATIONS,f,ensure_ascii=False,indent=2)
    print(f"Generated {len(df):,} rows -> {OUT}")
    print(f"Coverage: {len(INDIA_LOCATIONS)} states/UTs, {sum(len(v) for x in INDIA_LOCATIONS.values() for v in x.values())} cities, {sum(len(l) for c in INDIA_LOCATIONS.values() for x in c.values() for l in x)} localities")
    print(df.groupby("zone_type").size().sort_values(ascending=False))
