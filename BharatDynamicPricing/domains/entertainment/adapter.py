"""Entertainment/ticketing domain contract."""
FEATURES=("hour","day_of_week","event_id","days_to_event","lag_1","lag_2","rolling_mean_3","remaining_capacity","venue_capacity")
DEMAND_TARGET="tickets_booked"
SUPPLY_SIGNAL="remaining_capacity"
BASELINE="ticket_base_price_inr"
