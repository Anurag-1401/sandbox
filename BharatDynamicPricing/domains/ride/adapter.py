"""Ride-hailing domain contract."""
FEATURES=("hour","day_of_week","pickup_zone","drop_zone","vehicle_type","lag_1","rolling_mean","available_drivers","traffic_index")
DEMAND_TARGET="ride_requests"
SUPPLY_SIGNAL="available_drivers"
BASELINE="trip_fare_inr"
