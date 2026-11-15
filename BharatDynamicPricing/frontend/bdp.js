const API=window.BDP_API_BASE||"http://127.0.0.1:8000";
const $=id=>document.getElementById(id);
let domain="ride";
const labels={ride:"Ride-hailing pricing",food:"Food delivery pricing",ecommerce:"E-commerce pricing",entertainment:"Entertainment / ticket pricing",travel:"Travel pricing"};
document.querySelectorAll(".domain").forEach(btn=>btn.addEventListener("click",()=>{document.querySelectorAll(".domain").forEach(x=>x.classList.remove("active"));btn.classList.add("active");domain=btn.dataset.domain;$("domainTitle").textContent=labels[domain];}));
function fmt(v){return Number(v).toLocaleString("en-IN",{maximumFractionDigits:2});}
async function loadStatus(){try{const r=await fetch(`${API}/v1/health`);if(!r.ok)throw Error("API unavailable");const d=await r.json();$("apiStatus").textContent="API connected";$("modelStatus").textContent=`${d.trained_domain_models}/${d.domains} domain demand models ready`;}catch(e){$("apiStatus").textContent="API offline";$("modelStatus").textContent="Start FastAPI on port 8000";}}
function showEffects(effects){const host=$("effects");host.innerHTML="";for(const [name,value] of Object.entries(effects||{})){const row=document.createElement("div");row.className="effect-row";const label=document.createElement("span");label.textContent=name;const val=document.createElement("strong");val.textContent=`${value>=0?"+":""}${(value*100).toFixed(2)}%`;row.append(label,val);host.append(row);}}
$("run").addEventListener("click",async()=>{
 $("error").classList.add("hidden");$("run").disabled=true;$("run").textContent="Calculating…";
 try{
  let features={};const raw=$("features").value.trim();if(raw)features=JSON.parse(raw);
  const payload={domain,baseline_price_inr:Number($("baseline").value),demand_index:Number($("demand").value),
   supply_index:Number($("supply").value),availability_index:Number($("availability").value),
   traffic_index:Number($("traffic").value),weather_index:Number($("weather").value),
   event_index:Number($("event").value),festival_index:Number($("festival").value),
   inventory_index:Number($("inventory").value),max_price_change_pct:Number($("cap").value),
   optimize:$("optimize").checked,elasticity:Number($("elasticity").value),feature_values:features};
  if($("currentDemand").value!=="")payload.current_demand=Number($("currentDemand").value);
  if($("nextDemand").value!=="")payload.predicted_next_window_demand=Number($("nextDemand").value);
  const response=await fetch(`${API}/v1/predict-price`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)});
  const data=await response.json();if(!response.ok)throw Error(data.detail||`HTTP ${response.status}`);
  $("baseOut").textContent=`₹${fmt(data.baseline_price_inr)}`;$("priceOut").textContent=`₹${fmt(data.recommended_price_inr)}`;
  $("multOut").textContent=`${data.multiplier.toFixed(4)}×`;$("changeOut").textContent=`${data.price_change_pct>0?"+":""}${data.price_change_pct.toFixed(2)}%`;
  $("currentOut").textContent=data.predicted_current_demand==null?"Not available":fmt(data.predicted_current_demand);
  $("nextOut").textContent=data.predicted_next_window_demand==null?"Not available":fmt(data.predicted_next_window_demand);
  $("sourceOut").textContent=data.demand_prediction_source;$("status").textContent=data.model_status;
  showEffects(data.explanation);$("optimizer").textContent=data.optimizer?JSON.stringify(data.optimizer,null,2):"Optimizer not enabled.";
 }catch(e){$("error").textContent=e.message;$("error").classList.remove("hidden");}
 finally{$("run").disabled=false;$("run").textContent="Calculate recommended price";}
});
loadStatus();
