let map;
let markerLayer;
let disasterNameById = {}; // { [id]: name }

const DEFAULT_VIEW = { lat: 7.8731, lon: 80.7718, zoom: 7 }; // Sri Lanka

// Marker colors (requested)
// earthquake - yellow, floods - blue, hurricane - purple, wildfires - red
function colorForDisasterName(name) {
  const k = String(name || "").trim().toLowerCase();
  if (k === "earthquake") return "#f5c542"; // yellow
  if (k === "floods" || k === "flood") return "#2b6cff"; // blue
  if (k === "hurricane") return "#7c3aed"; // purple
  if (k === "wildfires" || k === "wildfire") return "#ef4444"; // red
  return "#355872"; // fallback
}

function colorForClassId(id) {
  if (id == null) return colorForDisasterName(null);
  const name = disasterNameById[String(id)] || disasterNameById[Number(id)] || null;
  return colorForDisasterName(name);
}

function escapeHtml(str) {
  return (str || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function initMap() {
  map = L.map("map", { zoomControl: true });
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "&copy; OpenStreetMap contributors",
  }).addTo(map);

  markerLayer = L.layerGroup().addTo(map);
  map.setView([DEFAULT_VIEW.lat, DEFAULT_VIEW.lon], DEFAULT_VIEW.zoom);
}

async function fetchDisasterClasses() {
  const res = await fetch("/api/disaster-classes");
  if (!res.ok) throw new Error("Failed to load disaster classes");
  return await res.json();
}

function renderTypeChecks(classes) {
  const container = document.getElementById("typeChecks");
  const legend = document.getElementById("legendItems");
  container.innerHTML = "";
  legend.innerHTML = "";

  // Build id -> name map for consistent coloring.
  disasterNameById = {};
  for (const c of classes) {
    disasterNameById[String(c.id)] = c.name;
  }

  for (const c of classes) {
    const id = `type_${c.id}`;
    const row = document.createElement("label");
    row.innerHTML = `<input type="checkbox" class="typeCheck" value="${c.id}" checked> ${escapeHtml(c.name)}`;
    container.appendChild(row);

    const li = document.createElement("div");
    li.className = "legend-item";
    li.innerHTML = `<span class="dot" style="background:${colorForDisasterName(c.name)}"></span> ${escapeHtml(c.name)}`;
    legend.appendChild(li);
  }
}

function getSelectedTypeIds() {
  const checks = document.querySelectorAll(".typeCheck:checked");
  return Array.from(checks).map(c => c.value);
}

function getFilters() {
  const minA = document.getElementById("minAConf").value;
  const maxA = document.getElementById("maxAConf").value;
  const types = getSelectedTypeIds().join(",");

  const params = new URLSearchParams();
  params.set("min_a_conf", String(minA));
  params.set("max_a_conf", String(maxA));
  if (types) params.set("types", types);
  return params.toString();
}

function clearMarkers() {
  markerLayer.clearLayers();
}

function _coordKey(lat, lon) {
  // Grouping key for "same" lat/lon. Round to reduce float noise.
  const la = Number(lat);
  const lo = Number(lon);
  if (!Number.isFinite(la) || !Number.isFinite(lo)) return null;
  return `${la.toFixed(6)},${lo.toFixed(6)}`;
}

function groupByLatLon(points) {
  const map = new Map();
  for (const p of points || []) {
    const key = _coordKey(p.lat, p.lon);
    if (!key) continue;
    const arr = map.get(key) || [];
    arr.push(p);
    map.set(key, arr);
  }

  // Sort each group (newest first) so the marker color/name feels consistent.
  for (const [k, arr] of map.entries()) {
    arr.sort((a, b) => String(b.created_at || "").localeCompare(String(a.created_at || "")));
    map.set(k, arr);
  }
  return map;
}

function buildMultiPopupHtml(locationName, postsAtPoint) {
  const list = postsAtPoint || [];
  const count = list.length;

  const itemsHtml = list.map((p) => {
    const txt = (p.text || "").trim();
    const bConf = (p.b_confidence_level == null) ? "—" : String(p.b_confidence_level);
    const aConf = (p.a_confidence_level == null) ? "—" : String(p.a_confidence_level);

    return `
      <div class="dw-popup__item">
        <div class="dw-popup__row"><span class="k">Disaster:</span> ${escapeHtml(p.disaster_type || "unknown")} <span class="v">(${bConf}/10)</span></div>
        <div class="dw-popup__row"><span class="k">Confidence:</span> ${aConf}/10</div>
        <div class="dw-popup__row muted"><span class="k">Created:</span> ${escapeHtml(p.created_at || "")}</div>
        <div class="dw-popup__msg">${escapeHtml(txt || "—")}</div>
      </div>
    `;
  }).join("");

  return `
    <div class="dw-popup">
      <div class="dw-popup__title">${escapeHtml(locationName || "Unknown location")}</div>
      <div class="dw-popup__meta">${count} post${count === 1 ? "" : "s"} at this location</div>
      <div class="dw-popup__list">${itemsHtml}</div>
    </div>
  `;
}

function addMarkers(points) {
  const groups = groupByLatLon(points);

  for (const arr of groups.values()) {
    if (!arr || arr.length === 0) continue;

    // Use the newest post in the group to decide marker color.
    const primary = arr[0];
    const color = colorForClassId(primary.disaster_class_id);
    const radius = 7 + Math.min(6, Math.max(0, arr.length - 1));

    const marker = L.circleMarker([primary.lat, primary.lon], {
      radius,
      weight: 2,
      opacity: 0.9,
      fillOpacity: 0.75,
      color,
      fillColor: color,
    });

    // Prefer the most recent location name, but fall back to any non-empty in the group.
    const locName = (primary.location_name || arr.find(x => x.location_name)?.location_name || "Unknown location");
    const popupHtml = buildMultiPopupHtml(locName, arr);

    marker.bindPopup(popupHtml, { maxWidth: 380, closeButton: true });
    marker.addTo(markerLayer);
  }
}

function fitMapToPoints(points) {
  if (!map) return;
  if (!points || points.length === 0) {
    map.setView([DEFAULT_VIEW.lat, DEFAULT_VIEW.lon], DEFAULT_VIEW.zoom);
    return;
  }
  const bounds = L.latLngBounds(points.map(p => [p.lat, p.lon]));
  // Auto-fit the map to the visible points.
  map.fitBounds(bounds, { padding: [30, 30], maxZoom: 15 });
}

async function loadPoints() {
  const qs = getFilters();
  const res = await fetch(`/api/posts?${qs}`);
  const points = await res.json();
  const groups = groupByLatLon(points);
  clearMarkers();
  addMarkers(points);
  fitMapToPoints(points);

  const countBox = document.getElementById("countBox");
  if (countBox) countBox.textContent = `Locations: ${groups.size}  •  Posts: ${points.length}`;
}

function wireRangeLabels() {
  const minA = document.getElementById("minAConf");
  const maxA = document.getElementById("maxAConf");
  const minVal = document.getElementById("minAConfVal");
  const maxVal = document.getElementById("maxAConfVal");

  function sync() {
    minVal.textContent = String(minA.value);
    maxVal.textContent = String(maxA.value);
  }
  minA.addEventListener("input", sync);
  maxA.addEventListener("input", sync);
  sync();
}

function wireApply() {
  document.getElementById("applyBtn").addEventListener("click", () => {
    loadPoints().catch(err => console.error(err));
  });
}

function wireIngestForm() {
  const form = document.getElementById("ingestForm");
  const status = document.getElementById("ingestStatus");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    status.textContent = "Saving…";

    const fd = new FormData(form);
    try {
      const res = await fetch("/api/posts", { method: "POST", body: fd });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Failed");

      status.textContent = `Saved post #${data.post_id}. Image path: ${data.saved_image_path || "—"}`;
      form.reset();

      // Map won't show it until your processing pipeline writes pipeline_runs + results + location.
      await loadPoints();
    } catch (err) {
      status.textContent = `Error: ${err.message}`;
    }
  });
}

async function init() {
  initMap();
  wireRangeLabels();
  wireApply();
  wireIngestForm();

  try {
    const classes = await fetchDisasterClasses();
    renderTypeChecks(classes);
  } catch (e) {
    console.error(e);
    document.getElementById("typeChecks").innerHTML = "<div class='status'>Could not load disaster classes.</div>";
  }

  await loadPoints();
}

document.addEventListener("DOMContentLoaded", () => {
  init().catch(err => console.error(err));
});
