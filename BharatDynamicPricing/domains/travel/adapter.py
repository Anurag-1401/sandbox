"""Travel domain contract."""
FEATURES=("month","day_of_week","destination","product_type","days_to_departure","lag_1","rolling_mean","remaining_capacity","season_index")
DEMAND_TARGET="travel_bookings"
SUPPLY_SIGNAL="remaining_capacity"
BASELINE="travel_product_price_inr"
