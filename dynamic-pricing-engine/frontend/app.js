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
// APPLICATION START
// ============================================================

document.addEventListener("DOMContentLoaded", () => {
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
            buildPayload();


        console.log(
            "📤 Prediction request:",
            requestPayload
        );


        const response =
            await fetch(
                `${API_BASE}/predict-price`,
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
            `₹${Number(
                data.base_price_inr
            ).toFixed(2)}`;


        $("multOut").textContent =
            `${Number(
                data.predicted_multiplier
            ).toFixed(2)}x`;


        $("priceOut").textContent =
            `₹${Number(
                data.predicted_price_inr
            ).toFixed(2)}`;


        $("locationBadge").textContent =
            `${data.city} • ${data.locality}`;


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
                "⚡ Predict Indian Price";

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