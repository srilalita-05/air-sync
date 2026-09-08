/**
 * AirSync Web Dashboard Logic.
 * Team: Semantic Souls (SIH 2026 - Problem ID: SIH26082)
 */

document.addEventListener("DOMContentLoaded", () => {
  let chartInstance = null;
  let mapInstance = null;
  let plumeLayerGroup = null;

  // Initialize Map
  initMap();

  // Load Initial 72h Forecast Data
  loadForecastData();

  // Event Listeners
  document.getElementById("btn-refresh").addEventListener("click", loadForecastData);
  document.getElementById("select-scenario").addEventListener("change", loadForecastData);
  document.getElementById("select-station").addEventListener("change", loadForecastData);
  document.getElementById("toggle-ml-residual").addEventListener("change", loadForecastData);
  document.getElementById("form-plume").addEventListener("submit", handlePlumeSimulation);

  function initMap() {
    // Center on Delhi-NCR (28.6139 N, 77.2090 E)
    mapInstance = L.map("map").setView([28.6139, 77.2090], 10);

    // Dark Tile Layer
    L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
      attribution: "&copy; OpenStreetMap contributors &copy; CARTO",
      maxZoom: 18,
    }).addTo(mapInstance);

    plumeLayerGroup = L.layerGroup().addTo(mapInstance);

    // Add CPCB Monitoring Stations
    const stations = [
      { id: "DEL001", name: "Anand Vihar, Delhi", lat: 28.6469, lon: 77.3160, aqi: 362 },
      { id: "DEL002", name: "R.K. Puram, Delhi", lat: 28.5633, lon: 77.1864, aqi: 310 },
      { id: "DEL003", name: "Punjabi Bagh, Delhi", lat: 28.6740, lon: 77.1310, aqi: 325 },
      { id: "DEL004", name: "ITO, Delhi", lat: 28.6317, lon: 77.2494, aqi: 345 },
      { id: "NCR001", name: "Sector 62, Noida", lat: 28.6245, lon: 77.3577, aqi: 295 },
      { id: "NCR002", name: "Vikas Sadan, Gurugram", lat: 28.4501, lon: 77.0263, aqi: 270 },
    ];

    stations.forEach(st => {
      const circle = L.circleMarker([st.lat, st.lon], {
        radius: 9,
        fillColor: st.aqi > 300 ? "#ff1744" : "#ff9100",
        color: "#ffffff",
        weight: 1.5,
        opacity: 1,
        fillOpacity: 0.85,
      }).addTo(mapInstance);

      circle.bindPopup(`
        <div style="font-family: sans-serif; color: #0b0f19;">
          <strong>${st.name}</strong><br/>
          Forecast AQI: <strong>${st.aqi}</strong> (Very Poor)<br/>
          <small>CPCB Station ID: ${st.id}</small>
        </div>
      `);
    });
  }

  async function loadForecastData() {
    const scenario = document.getElementById("select-scenario").value;
    const station = document.getElementById("select-station").value;
    const useML = document.getElementById("toggle-ml-residual").checked;

    try {
      const resp = await fetch("/forecast/72h", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          scenario_type: scenario,
          station_id: station,
          use_ml_residual: useML,
        }),
      });

      const data = await resp.json();
      renderDashboard(data);
    } catch (err) {
      console.error("Error loading forecast data:", err);
    }
  }

  function renderDashboard(data) {
    if (!data || !data.hourly_forecast || data.hourly_forecast.length === 0) return;

    const currentStep = data.hourly_forecast[0];
    const episode = data.episode_summary;

    // 1. Update Metrics Cards
    const aqiScore = currentStep.aqi.overall_aqi || 0;
    const aqiValElem = document.getElementById("aqi-value");
    aqiValElem.innerText = aqiScore;
    
    const categoryElem = document.getElementById("aqi-category");
    categoryElem.innerText = currentStep.aqi.aqi_category || "N/A";
    categoryElem.style.color = currentStep.aqi.color_hex || "#ff1744";

    document.getElementById("aqi-dominant").innerText = `Dominant: ${currentStep.aqi.dominant_pollutant || "PM2.5"}`;
    document.getElementById("aqi-bar-fill").style.width = `${Math.min(100, (aqiScore / 500) * 100)}%`;

    // 2. Ventilation & Stability
    const diag = currentStep.physics_diagnostics;
    const vc = diag.ventilation_coefficient_m2s || 0;
    document.getElementById("vc-value").innerHTML = `${vc} <span class="unit">m²/s</span>`;

    const accum = diag.accumulation || {};
    const accumPill = document.getElementById("accum-status-pill");
    if (accum.severe_stagnation) {
      accumPill.className = "badge badge-danger";
      accumPill.innerText = "Severe Stagnation";
    } else if (accum.poor_ventilation) {
      accumPill.className = "badge badge-warning";
      accumPill.innerText = "Poor Ventilation";
    } else {
      accumPill.className = "badge badge-neutral";
      accumPill.innerText = "Good Ventilation";
    }

    const inv = diag.inversion || {};
    const invPill = document.getElementById("inv-status-pill");
    if (inv.inversion_detected === true) {
      invPill.className = "badge badge-danger";
      invPill.innerText = `Inversion Confirmed (+${inv.lapse_rate_c_100m}°C/100m)`;
    } else {
      invPill.className = "badge badge-neutral";
      invPill.innerText = "Data Unavailable (No Vertical Temp)";
    }

    // 3. Episode Summary
    if (episode && episode.episode_detected) {
      document.getElementById("episode-status-badge").className = "badge badge-danger";
      document.getElementById("episode-status-badge").innerText = "EPISODE DETECTED";
      document.getElementById("ep-peak-aqi").innerText = episode.max_forecast_aqi;
      
      const peakTimeStr = episode.peak_timestamp ? episode.peak_timestamp.substring(11, 16) : "N/A";
      document.getElementById("ep-peak-time").innerText = `Step Peak (${peakTimeStr})`;
    } else {
      document.getElementById("episode-status-badge").className = "badge badge-neutral";
      document.getElementById("episode-status-badge").innerText = "NORMAL LEVELS";
      document.getElementById("ep-peak-aqi").innerText = episode.max_forecast_aqi || aqiScore;
      document.getElementById("ep-peak-time").innerText = "No Episode Peak";
    }

    // 4. Update "WHY?" Explainability Panel
    const exp = currentStep.explanation;
    document.getElementById("dominant-driver-badge").innerText = (exp.dominant_driver || "NORMAL").toUpperCase().replace("_", " ");
    document.getElementById("narrative-summary").innerText = exp.narrative_explanation || "No explanation narrative available.";

    const driversListElem = document.getElementById("drivers-list");
    driversListElem.innerHTML = "";

    (exp.drivers || []).forEach(d => {
      const div = document.createElement("div");
      div.className = "driver-card";
      div.innerHTML = `
        <div class="driver-header">
          <span class="driver-name">${d.name.toUpperCase().replace("_", " ")}</span>
          <span class="badge ${d.severity === 'critical' || d.severity === 'high' ? 'badge-danger' : d.severity === 'beneficial' ? 'badge-neutral' : 'badge-warning'}">${d.severity}</span>
        </div>
        <div class="driver-desc">${d.description} (${d.value} ${d.unit})</div>
      `;
      driversListElem.appendChild(div);
    });

    // 5. Render Chart
    renderChart(data.hourly_forecast);
  }

  function renderChart(timeline) {
    const ctx = document.getElementById("forecastChart").getContext("2d");

    const labels = timeline.map(t => `H+${t.hour}`);
    const pm25Data = timeline.map(t => t.pollutants.pm25_ugm3);
    const pm10Data = timeline.map(t => t.pollutants.pm10_ugm3);
    const o3Data = timeline.map(t => t.pollutants.o3_ugm3);
    const aqiData = timeline.map(t => t.aqi.overall_aqi);

    if (chartInstance) {
      chartInstance.destroy();
    }

    chartInstance = new Chart(ctx, {
      type: "line",
      data: {
        labels: labels,
        datasets: [
          { label: "PM2.5 (µg/m³)", data: pm25Data, borderColor: "#00f2fe", backgroundColor: "rgba(0, 242, 254, 0.1)", tension: 0.3, fill: true },
          { label: "PM10 (µg/m³)", data: pm10Data, borderColor: "#ffea00", backgroundColor: "transparent", tension: 0.3 },
          { label: "O3 (µg/m³)", data: o3Data, borderColor: "#76ff03", backgroundColor: "transparent", tension: 0.3 },
          { label: "CPCB AQI", data: aqiData, borderColor: "#ff1744", borderDash: [4, 4], backgroundColor: "transparent", tension: 0.2 },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { color: "rgba(255, 255, 255, 0.05)" }, ticks: { color: "#94a3b8" } },
          y: { grid: { color: "rgba(255, 255, 255, 0.05)" }, ticks: { color: "#94a3b8" } },
        },
      },
    });
  }

  async function handlePlumeSimulation(e) {
    e.preventDefault();
    const lat = parseFloat(document.getElementById("plume-lat").value);
    const lon = parseFloat(document.getElementById("plume-lon").value);
    const speed = parseFloat(document.getElementById("plume-speed").value);
    const dir = parseFloat(document.getElementById("plume-dir").value);
    const frp = parseFloat(document.getElementById("plume-frp").value);

    try {
      const resp = await fetch("/plume", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          fire_latitude: lat,
          fire_longitude: lon,
          wind_speed_ms: speed,
          wind_direction_deg: dir,
          frp_mw: frp,
          target_latitude: 28.6139,
          target_longitude: 77.2090,
          horizon_hours: 24,
        }),
      });

      const plumeRes = await resp.json();

      document.getElementById("plume-score").innerText = `${plumeRes.potential_downwind_influence_score} / 1.0`;

      // Draw Trajectory on Map
      plumeLayerGroup.clearLayers();

      const latlngs = plumeRes.trajectory_points.map(pt => [pt.latitude, pt.longitude]);
      const polyline = L.polyline(latlngs, { color: "#ff9100", weight: 3, dashArray: "6, 6" }).addTo(plumeLayerGroup);

      // Fire Origin Marker
      L.circleMarker([lat, lon], { radius: 8, fillColor: "#ff1744", color: "#fff", weight: 2, fillOpacity: 0.9 })
        .bindPopup(`<b>Fire Hotspot</b><br/>FRP: ${frp} MW`)
        .addTo(plumeLayerGroup);

      mapInstance.fitBounds(polyline.getBounds(), { padding: [40, 40] });
    } catch (err) {
      console.error("Plume simulation failed:", err);
    }
  }
});
