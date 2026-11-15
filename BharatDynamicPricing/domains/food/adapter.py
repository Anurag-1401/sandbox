"""Food-delivery domain contract."""
FEATURES=("hour","day_of_week","restaurant_id","food_category","location","lag_1","rolling_mean","delivery_partner_capacity","restaurant_capacity","traffic_index")
DEMAND_TARGET="food_orders"
SUPPLY_SIGNAL="delivery_partner_capacity"
BASELINE="restaurant_order_price_inr"
