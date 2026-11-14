const API = window.BDP_API_BASE || "http://127.0.0.1:8000";
const $ = id => document.getElementById(id);
$("run").addEventListener("click", async () => {
  $("error").classList.add("hidden");
  const payload = {
    domain: $("domain").value,
    baseline_price_inr: Number($("baseline").value),
    demand_index: Number($("demand").value),
    supply_index: Number($("supply").value),
    availability_index: Number($("availability").value),
    context_index: Number($("context").value),
    max_price_change_pct: Number($("cap").value)
  };
  try {
    const response = await fetch(`${API}/v1/predict-price`, {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(payload)});
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || `HTTP ${response.status}`);
    $("baseOut").textContent = `₹${data.baseline_price_inr.toFixed(2)}`;
    $("multOut").textContent = `${data.multiplier.toFixed(4)}x`;
    $("priceOut").textContent = `₹${data.recommended_price_inr.toFixed(2)}`;
    $("details").textContent = JSON.stringify({price_change_pct:data.price_change_pct,demand_pressure:data.demand_pressure,supply_pressure:data.supply_pressure,component_effects:data.explanation},null,2);
    $("status").textContent = data.model_status;
  } catch (e) { $("error").textContent = e.message; $("error").classList.remove("hidden"); }
});
