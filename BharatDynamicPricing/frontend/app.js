// ============================================================
// 🇮🇳 INDIA DYNAMIC PRICING ENGINE
// Frontend Application
// ============================================================

const API_BASE = "http://localhost:8000";

let LOCATIONS = {};
let META = {};
let chart = null;


// ============================================================
// DOM HELPER
// ============================================================

const $ = (id) => document.getElementById(id);


// ============================================================
// DOM ELEMENTS
// ============================================================

const state = $("state");
const city = $("city");
const locality = $("locality");
const zoneType = $("zoneType");

const weather = $("weather");
const traffic = $("traffic");
const festival = $("festival");



// ============================================================
// UNIFIED FIVE-DOMAIN INPUTS
// ============================================================

const DOMAIN_CONFIG = {
    ride: {
        title: "Trip base fare",
        fields: [
            ["vehicle_type", "Vehicle type", "text", "Sedan"],
            ["trip_distance_km", "Trip distance (km)", "number", "12"],
            ["pickup_location", "Pickup point / area", "text", ""],
            ["drop_location", "Drop point / area", "text", ""]
        ]
    },
    food: {
        title: "Restaurant / order reference price",
        fields: [
            ["restaurant", "Restaurant name", "text", ""],
            ["restaurant_id", "Restaurant ID", "text", ""],
            ["food_category", "Food category", "text", "Meals"],
            ["delivery_partner_capacity", "Available delivery partners", "number", "35"],
            ["restaurant_capacity", "Restaurant order capacity", "number", "50"]
        ]
    },
    ecommerce: {
        title: "Product reference price",
        fields: [
            ["product_id", "Product ID", "text", ""],
            ["category", "Product category", "text", ""],
            ["inventory_units", "Inventory units", "number", "100"],
            ["discount_rate", "Discount rate (0–1)", "number", "0"]
        ]
    },
    entertainment: {
        title: "Ticket base price",
        fields: [
            ["event_id", "Event ID / name", "text", ""],
            ["event_date", "Event date", "date", ""],
            ["days_to_event", "Days to event", "number", "14"],
            ["remaining_capacity", "Remaining seats", "number", "500"],
            ["venue_capacity", "Total venue capacity", "number", "1000"]
        ]
    },
    travel: {
        title: "Travel product reference price",
        fields: [
            ["destination", "Destination", "text", ""],
            ["travel_date", "Travel date", "date", ""],
            ["product_type", "Travel product type (flight / hotel / tour)", "text", "tour"],
            ["days_to_departure", "Days to departure", "number", "30"],
            ["remaining_capacity", "Remaining capacity", "number", "100"]
        ]
    }
};

function renderDomainFields() {
    const select = $("domain");
    const host = $("domainSpecificFields");
    if (!select || !host) return;
    const config = DOMAIN_CONFIG[select.value] || DOMAIN_CONFIG.ride;
    $("domainBaselineLabel").value = config.title;
    host.innerHTML = "";
    config.fields.forEach(([name, label, type, defaultValue]) => {
        const wrap = document.createElement("div");
        wrap.className = "field";
        const caption = document.createElement("label");
        caption.htmlFor = `domainField_${name}`;
        caption.textContent = label;
        const input = document.createElement("input");
        input.id = `domainField_${name}`;
        input.dataset.featureName = name;
        input.type = type;
        if (defaultValue !== "") input.value = defaultValue;
        if (type === "number") {
            input.min = "0";
            input.step = "any";
        }
        wrap.append(caption, input);
        host.append(wrap);
    });
}

function collectDomainFeatures() {
    const location = buildPayload();
    const values = {
        state: location.state,
        city: location.city,
        locality: location.locality,
        zone_type: location.zone_type,
        demand_requests: location.demand_requests,
        available_supply: location.available_supply,
        order_density: location.order_density,
        population_density: location.population_density,
        commercial_density: location.commercial_density,
        restaurant_density: location.restaurant_density,
        traffic_level: location.traffic_level,
        traffic_congestion_index: location.traffic_congestion_index,
        average_speed_kmph: location.average_speed_kmph,
        weather_condition: location.weather_condition,
        temperature_c: location.temperature_c,
        humidity: location.humidity,
        rainfall_mm: location.rainfall_mm,
        visibility_km: location.visibility_km,
        festival_name: location.festival_name,
        festival_intensity: location.festival_intensity,
        is_national_holiday: location.is_national_holiday,
        event_nearby: location.event_nearby,
        event_type: location.event_type,
        event_attendance: location.event_attendance
    };
    document.querySelectorAll("#domainSpecificFields [data-feature-name]").forEach(input => {
        if (input.value === "") return;
        values[input.dataset.featureName] = input.type === "number"
            ? Number(input.value)
            : input.value;
    });
    const raw = $("domainFeatureJson")?.value.trim();
    if (raw) {
        const overrides = JSON.parse(raw);
        if (!overrides || Array.isArray(overrides) || typeof overrides !== "object") {
            throw new Error("Advanced domain features must be a JSON object.");
        }
        Object.assign(values, overrides);
    }
    return values;
}

function buildIntegratedPayload() {
    const locationContext = buildPayload();
    const payload = {
        domain: $("domain").value,
        location_context: locationContext,
        demand_index: Number($("domainDemandIndex").value),
        supply_index: Number($("domainSupplyIndex").value),
        availability_index: Number($("domainAvailabilityIndex").value),
        traffic_index: Number($("domainTrafficIndex").value),
        weather_index: Number($("domainWeatherIndex").value),
        event_index: Number($("domainEventIndex").value),
        festival_index: Number($("domainFestivalIndex").value),
        inventory_index: Number($("domainInventoryIndex").value),
        max_domain_price_change_pct: Number($("domainPriceCap").value),
        feature_values: collectDomainFeatures(),
        optimize: $("domainOptimize").checked,
        elasticity: Number($("domainElasticity").value)
    };
    if ($("domainCurrentDemand").value !== "") {
        payload.current_demand = Number($("domainCurrentDemand").value);
    }
    if ($("domainNextDemand").value !== "") {
        payload.predicted_next_window_demand = Number($("domainNextDemand").value);
    }
    return payload;
}

// ============================================================
// APPLICATION START
// ============================================================

document.addEventListener("DOMContentLoaded", () => {
    renderDomainFields();
    $("domain")?.addEventListener("change", renderDomainFields);
    boot();
});


// ============================================================
// BOOT
// ============================================================

async function boot() {

    try {

        console.log("🇮🇳 Starting India Dynamic Pricing Engine...");


        // ----------------------------------------------------
        // Check required HTML elements
        // ----------------------------------------------------

        const requiredElements = [
            "state",
            "city",
            "locality",
            "zoneType",
            "weather",
            "traffic",
            "festival",
            "predictBtn"
        ];

        for (const id of requiredElements) {

            if (!$(id)) {
                throw new Error(
                    `HTML element #${id} was not found.`
                );
            }

        }


        // ----------------------------------------------------
        // Load Indian locations
        // ----------------------------------------------------

        console.log(
            `Loading locations from ${API_BASE}/locations`
        );

        const locationsResponse =
            await fetch(`${API_BASE}/locations`);

        if (!locationsResponse.ok) {

            const errorText =
                await locationsResponse.text();

            throw new Error(
                `/locations returned HTTP ${locationsResponse.status}: ${errorText}`
            );
        }

        LOCATIONS =
            await locationsResponse.json();


        console.log(
            "🇮🇳 Indian locations loaded:",
            LOCATIONS
        );


        // ----------------------------------------------------
        // Load metadata
        // ----------------------------------------------------

        console.log(
            `Loading metadata from ${API_BASE}/metadata`
        );

        const metadataResponse =
            await fetch(`${API_BASE}/metadata`);

        if (!metadataResponse.ok) {

            const errorText =
                await metadataResponse.text();

            throw new Error(
                `/metadata returned HTTP ${metadataResponse.status}: ${errorText}`
            );
        }

        META =
            await metadataResponse.json();


        console.log(
            "Indian metadata loaded:",
            META
        );


        // ----------------------------------------------------
        // Populate State
        // ----------------------------------------------------

        const states =
            Object.keys(LOCATIONS);

        console.log(
            `Found ${states.length} Indian states/UTs`
        );

        populate(
            state,
            states
        );


        // ----------------------------------------------------
        // Populate metadata dropdowns
        // ----------------------------------------------------

        populate(
            weather,
            META.weather || []
        );

        populate(
            traffic,
            META.traffic || []
        );

        populate(
            festival,
            META.festivals || []
        );

        populate(
            zoneType,
            META.zone_types || []
        );


        // ----------------------------------------------------
        // Default Indian location
        // ----------------------------------------------------

        if (states.includes("Maharashtra")) {

            state.value =
                "Maharashtra";

        } else if (states.length > 0) {

            state.value =
                states[0];

        }


        updateCities();


        // ----------------------------------------------------
        // Default Mumbai
        // ----------------------------------------------------

        const availableCities =
            Object.keys(
                LOCATIONS[state.value] || {}
            );


        if (
            availableCities.includes("Mumbai")
        ) {

            city.value =
                "Mumbai";

        }


        updateLocalities();


        // ----------------------------------------------------
        // Default BKC
        // ----------------------------------------------------

        const availableLocalities =
            getLocalities();


        if (
            availableLocalities.includes("BKC")
        ) {

            locality.value =
                "BKC";

        }


        // ----------------------------------------------------
        // Default metadata
        // ----------------------------------------------------

        setDefaultValue(
            zoneType,
            "Business"
        );

        setDefaultValue(
            weather,
            "Clear"
        );

        setDefaultValue(
            traffic,
            "High"
        );

        setDefaultValue(
            festival,
            "None"
        );


        console.log(
            "🇮🇳 Indian location dropdowns initialized."
        );

        console.log(
            "State:",
            state.value
        );

        console.log(
            "City:",
            city.value
        );

        console.log(
            "Locality:",
            locality.value
        );


        // ----------------------------------------------------
        // Do NOT automatically predict until fields exist
        // ----------------------------------------------------

        await predict();


    } catch (error) {

        console.error(
            "❌ Frontend initialization failed:",
            error
        );

        showError(
            `India pricing engine initialization failed: ${error.message}`
        );

    }
}


// ============================================================
// POPULATE SELECT
// ============================================================

function populate(element, items) {

    if (!element) {

        console.error(
            "Cannot populate missing element."
        );

        return;
    }


    if (!Array.isArray(items)) {

        console.error(
            `Expected array for ${element.id}, received:`,
            items
        );

        return;
    }


    element.innerHTML = "";


    // Placeholder
    const placeholder =
        document.createElement("option");

    placeholder.value = "";
    placeholder.textContent =
        `Select ${element.id}`;

    placeholder.disabled = true;

    element.appendChild(
        placeholder
    );


    // Actual options
    items.forEach((item) => {

        const option =
            document.createElement("option");

        option.value =
            String(item);

        option.textContent =
            String(item)
                .replaceAll("_", " ");

        element.appendChild(
            option
        );

    });


    // Automatically select first actual option
    if (items.length > 0) {

        element.value =
            String(items[0]);

    }


    console.log(
        `✓ ${element.id}: ${items.length} options`
    );
}


// ============================================================
// STATE → CITY
// ============================================================

function updateCities() {

    if (!state || !city) {
        return;
    }


    const stateData =
        LOCATIONS[state.value] || {};


    const cities =
        Object.keys(stateData);


    console.log(
        `Cities for ${state.value}:`,
        cities
    );


    populate(
        city,
        cities
    );


    updateLocalities();
}


// ============================================================
// GET LOCALITIES
// ============================================================
//
// IMPORTANT:
//
// Your JSON uses:
//
// "Mumbai": [
//     "BKC",
//     "Andheri",
//     "Bandra"
// ]
//
// Therefore we return the array directly.
// ============================================================

function getLocalities() {

    if (!state || !city) {
        return [];
    }


    const stateData =
        LOCATIONS[state.value] || {};


    const localities =
        stateData[city.value] || [];


    if (!Array.isArray(localities)) {

        console.error(
            "Expected locality array:",
            localities
        );

        return [];
    }


    return localities;
}


// ============================================================
// CITY → LOCALITY
// ============================================================

function updateLocalities() {

    if (!locality) {
        return;
    }


    const localities =
        getLocalities();


    console.log(
        `Localities for ${state.value} → ${city.value}:`,
        localities
    );


    populate(
        locality,
        localities
    );
}


// ============================================================
// SET DEFAULT SELECT VALUE
// ============================================================

function setDefaultValue(
    element,
    value
) {

    if (!element) {
        return;
    }


    const exists =
        Array.from(
            element.options
        ).some(
            option =>
                option.value === value
        );


    if (exists) {

        element.value =
            value;

    }
}


// ============================================================
// EVENT LISTENERS
// ============================================================

if (state) {

    state.addEventListener(
        "change",
        () => {

            updateCities();

        }
    );

}


if (city) {

    city.addEventListener(
        "change",
        () => {

            updateLocalities();

        }
    );

}


// ============================================================
// BUILD PREDICTION PAYLOAD
// ============================================================

function buildPayload() {

    const selectedZone =
        zoneType.value;


    return {

        // ----------------------------------------------------
        // Indian location
        // ----------------------------------------------------

        state:
            state.value,

        city:
            city.value,

        locality:
            locality.value,

        zone_type:
            selectedZone,


        // ----------------------------------------------------
        // Pricing
        // ----------------------------------------------------

        base_price_inr:
            Number(
                $("basePrice").value
            ),


        // ----------------------------------------------------
        // Demand & Supply
        // ----------------------------------------------------

        demand_requests:
            Number(
                $("demand").value
            ),

        available_supply:
            Number(
                $("supply").value
            ),

        order_density:
            Number(
                $("orderDensity").value
            ),


        // ----------------------------------------------------
        // Locality characteristics
        // ----------------------------------------------------

        population_density:
            Number(
                $("populationDensity").value
            ),

        commercial_density:
            Number(
                $("commercialDensity").value
            ),

        restaurant_density:
            Number(
                $("restaurantDensity").value
            ),


        // ----------------------------------------------------
        // Traffic
        // ----------------------------------------------------

        traffic_level:
            traffic.value,

        traffic_congestion_index:
            Number(
                $("congestion").value
            ),

        average_speed_kmph:
            Number(
                $("speed").value
            ),


        // ----------------------------------------------------
        // Weather
        // ----------------------------------------------------

        weather_condition:
            weather.value,

        temperature_c:
            Number(
                $("temperature").value
            ),

        humidity:
            Number(
                $("humidity").value
            ),

        rainfall_mm:
            Number(
                $("rainfall").value
            ),

        visibility_km:
            Number(
                $("visibility").value
            ),


        // ----------------------------------------------------
        // Indian festivals
        // ----------------------------------------------------

        festival_name:
            festival.value,

        festival_intensity:
            Number(
                $("festivalIntensity").value
            ),

        is_national_holiday:
            $("holiday").checked,


        // ----------------------------------------------------
        // Events
        // ----------------------------------------------------

        event_nearby:
            $("event").checked,

        event_type:
            $("eventType").value,

        event_attendance:
            Number(
                $("attendance").value
            ),


        // ----------------------------------------------------
        // Transportation
        // ----------------------------------------------------

        airport_activity:
            selectedZone === "Airport_Transit"
                ? 0.8
                : 0.05,

        railway_activity:
            selectedZone === "Railway_Transit"
                ? 0.8
                : 0.08,

        metro_activity:
            selectedZone === "Metro_Transit"
                ? 0.8
                : 0.25
    };
}


// ============================================================
// CURRENT PRICE PREDICTION
// ============================================================

async function predict() {

    clearError();


    const button =
        $("predictBtn");


    if (button) {

        button.disabled = true;

        button.textContent =
            "⏳ Predicting...";

    }


    try {

        const requestPayload =
            buildIntegratedPayload();


        console.log(
            "📤 Prediction request:",
            requestPayload
        );


        const response =
            await fetch(
                `${API_BASE}/v1/predict-integrated`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify(
                            requestPayload
                        )
                }
            );


        if (!response.ok) {

            const errorBody =
                await response
                    .json()
                    .catch(
                        () => ({})
                    );


            throw new Error(
                errorBody.detail
                    ? JSON.stringify(
                        errorBody.detail
                    )
                    : `HTTP ${response.status}`
            );

        }


        const data =
            await response.json();


        console.log(
            "📥 Prediction response:",
            data
        );


        // ----------------------------------------------------
        // Output
        // ----------------------------------------------------

        $("baseOut").textContent =
            `₹${Number(data.baseline_price_inr).toFixed(2)}`;

        $("multOut").textContent =
            `${Number(data.combined_multiplier).toFixed(4)}x`;

        $("priceOut").textContent =
            `₹${Number(data.recommended_price_inr).toFixed(2)}`;

        $("locationBadge").textContent =
            `${data.location.city} • ${data.location.locality} • ${data.domain}`;

        $("locationMultiplierOut").textContent =
            `${Number(data.location_model_multiplier).toFixed(4)}×`;

        $("domainMultiplierOut").textContent =
            `${Number(data.domain_adjustment_multiplier).toFixed(4)}×`;

        $("domainModelStatusOut").textContent =
            data.domain_policy.model_status;

        $("domainDemandSourceOut").textContent =
            `Demand source: ${data.domain_policy.demand_prediction_source}`;

        $("integrationExplanation").textContent =
            `Final price = ₹${Number(data.baseline_price_inr).toFixed(2)} × location multiplier ${Number(data.location_model_multiplier).toFixed(4)} × ${data.domain} adjustment ${Number(data.domain_adjustment_multiplier).toFixed(4)}, with the combined multiplier bounded to 1.0–4.0.`;

        const effectsHost = $("domainEffectsOut");
        effectsHost.innerHTML = "";
        Object.entries(data.domain_policy.context_effects || {}).forEach(([name, value]) => {
            const line = document.createElement("div");
            line.className = "domain-effect-line";
            const label = document.createElement("span");
            label.textContent = name;
            const amount = document.createElement("strong");
            amount.textContent = `${value >= 0 ? "+" : ""}${(value * 100).toFixed(2)}%`;
            line.append(label, amount);
            effectsHost.append(line);
        });


        // ----------------------------------------------------
        // Forecast
        // ----------------------------------------------------

        await forecast();


    } catch (error) {

        console.error(
            "❌ Prediction failed:",
            error
        );


        showError(
            `Prediction failed: ${error.message}`
        );


    } finally {

        if (button) {

            button.disabled =
                false;

            button.textContent =
                "⚡ Predict Unified Price";

        }

    }
}


// ============================================================
// 6-HOUR FORECAST
// ============================================================

async function forecast() {

    const p =
        buildPayload();


    const params =
        new URLSearchParams({

            state:
                p.state,

            city:
                p.city,

            locality:
                p.locality,

            zone_type:
                p.zone_type,

            base_price_inr:
                p.base_price_inr,

            weather_condition:
                p.weather_condition,

            festival_name:
                p.festival_name,

            festival_intensity:
                p.festival_intensity,

            is_national_holiday:
                p.is_national_holiday,

            event_nearby:
                p.event_nearby,

            hours_ahead:
                6

        });


    console.log(
        "📈 Forecast request:",
        params.toString()
    );


    const response =
        await fetch(
            `${API_BASE}/price-forecast?${params}`
        );


    if (!response.ok) {

        const errorBody =
            await response
                .json()
                .catch(
                    () => ({})
                );


        throw new Error(
            errorBody.detail
                ? JSON.stringify(
                    errorBody.detail
                )
                : `Forecast HTTP ${response.status}`
        );

    }


    const data =
        await response.json();


    renderChart(data);
}


// ============================================================
// FORECAST CHART
// ============================================================

function renderChart(data) {

    if (!data || !data.forecast) {
        return;
    }


    const labels =
        data.forecast.map(
            point =>
                new Date(
                    point.timestamp
                ).toLocaleTimeString(
                    [],
                    {
                        hour: "2-digit",
                        minute: "2-digit"
                    }
                )
        );


    const prices =
        data.forecast.map(
            point =>
                point.predicted_price_inr
        );


    if (chart) {

        chart.destroy();

    }


    const canvas =
        $("forecastChart");


    if (!canvas) {
        return;
    }


    const context =
        canvas.getContext("2d");


    chart =
        new Chart(
            context,
            {
                type: "line",

                data: {

                    labels,

                    datasets: [
                        {
                            label:
                                "Predicted Fare (₹)",

                            data:
                                prices,

                            tension:
                                0.35,

                            fill:
                                true,

                            borderWidth:
                                2,

                            pointRadius:
                                3
                        }
                    ]
                },

                options: {

                    responsive:
                        true,

                    plugins: {

                        legend: {
                            labels: {
                                color:
                                    "#b8c1d1"
                            }
                        },

                        tooltip: {

                            callbacks: {

                                afterLabel:
                                    (item) => {

                                        const multiplier =
                                            data
                                                .forecast[
                                                    item.dataIndex
                                                ]
                                                .predicted_multiplier;


                                        return (
                                            `Surge: ${Number(
                                                multiplier
                                            ).toFixed(2)}x`
                                        );

                                    }
                            }
                        }
                    },

                    scales: {

                        x: {

                            ticks: {
                                color:
                                    "#8792a6"
                            },

                            grid: {
                                color:
                                    "#222b3a"
                            }

                        },

                        y: {

                            ticks: {

                                color:
                                    "#8792a6",

                                callback:
                                    value =>
                                        `₹${value}`

                            },

                            grid: {
                                color:
                                    "#222b3a"
                            }

                        }

                    }

                }

            }
        );
}


// ============================================================
// ERROR DISPLAY
// ============================================================

function showError(message) {

    const errorElement =
        $("apiError");


    if (!errorElement) {

        console.error(
            message
        );

        return;
    }


    errorElement.textContent =
        message;


    errorElement.classList.remove(
        "hidden"
    );
}


function clearError() {

    const errorElement =
        $("apiError");


    if (!errorElement) {
        return;
    }


    errorElement.textContent =
        "";


    errorElement.classList.add(
        "hidden"
    );
}


// ============================================================
// PREDICT BUTTON
// ============================================================

const predictButton =
    $("predictBtn");


if (predictButton) {

    predictButton.addEventListener(
        "click",
        predict
    );

}