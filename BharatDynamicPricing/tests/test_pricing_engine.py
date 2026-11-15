import unittest
from core.pricing_engine import recommend_price,counterfactual_optimize
class PricingPolicyTests(unittest.TestCase):
 def test_neutral_context_preserves_baseline(self):
  for domain in ("ride","food","ecommerce","entertainment","travel"):
   r=recommend_price(domain,350)
   self.assertEqual(r["recommended_price_inr"],350)
   self.assertEqual(r["multiplier"],1)
 def test_cap_is_respected(self):
  r=recommend_price("ride",350,demand_index=4,supply_index=.25,availability_index=.25,max_price_change_pct=25)
  self.assertLessEqual(r["multiplier"],1.25)
 def test_documented_ride_example(self):
  r=recommend_price("ride",350,demand_index=1.5,supply_index=.8,availability_index=.9)
  self.assertAlmostEqual(r["raw_multiplier"],1.218333,places=4)
  self.assertAlmostEqual(r["recommended_price_inr"],426.42,places=2)
 def test_optimizer_returns_candidate(self):
  r=counterfactual_optimize(350,12)
  self.assertIn("best_candidate",r)
if __name__=="__main__":unittest.main()
