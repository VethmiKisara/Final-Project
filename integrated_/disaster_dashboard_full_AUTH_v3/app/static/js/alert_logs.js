function escapeHtml(str) {
  return (str || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function fetchDisasterClasses() {
  const res = await fetch("/api/disaster-classes");
  if (!res.ok) throw new Error("Failed to load disaster classes");
  return await res.json();
}

function renderTypeChecks(classes) {
  const container = document.getElementById("typeChecks");
  container.innerHTML = "";
  for (const c of classes) {
    const row = document.createElement("label");
    row.innerHTML = `<input type="checkbox" class="typeCheck" value="${c.id}" checked> ${escapeHtml(c.name)}`;
    container.appendChild(row);
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

function renderTable(rows) {
  const tbody = document.querySelector("#alertsTable tbody");
  tbody.innerHTML = "";

  for (const r of rows) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${r.post_id}</td>
      <td>${escapeHtml(r.disaster_type || "unknown")}</td>
      <td>${escapeHtml(r.location_name || "—")}</td>
      <td>${(r.a_confidence_level == null) ? "—" : (r.a_confidence_level + "/10")}</td>
      <td>${(r.b_confidence_level == null) ? "—" : (r.b_confidence_level + "/10")}</td>
      <td>${escapeHtml(r.created_at || "")}</td>
    `;
    tbody.appendChild(tr);
  }
}

async function loadAlerts() {
  const status = document.getElementById("alertsStatus");
  status.textContent = "Loading…";
  try {
    const qs = getFilters();
    const res = await fetch(`/api/alerts?${qs}`);
    const rows = await res.json();
    if (!res.ok) throw new Error(rows.error || "Failed");
    renderTable(rows);
    status.textContent = `Showing ${rows.length} active alerts.`;
  } catch (e) {
    status.textContent = `Error: ${e.message}`;
  }
}

function wireApply() {
  document.getElementById("applyBtn").addEventListener("click", () => {
    loadAlerts();
  });
}

async function init() {
  wireRangeLabels();
  wireApply();

  try {
    const classes = await fetchDisasterClasses();
    renderTypeChecks(classes);
  } catch (e) {
    console.error(e);
    document.getElementById("typeChecks").innerHTML = "<div class='status'>Could not load disaster classes.</div>";
  }

  await loadAlerts();
}

document.addEventListener("DOMContentLoaded", () => {
  init().catch(err => console.error(err));
});
