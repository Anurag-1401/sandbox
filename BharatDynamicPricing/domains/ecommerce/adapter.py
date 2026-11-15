"""E-commerce domain contract."""
FEATURES=("hour","day_of_week","product_id","category","lag_1","lag_2","rolling_mean_3","inventory_units","discount_rate")
DEMAND_TARGET="product_units"
SUPPLY_SIGNAL="inventory_units"
BASELINE="product_reference_price_inr"
