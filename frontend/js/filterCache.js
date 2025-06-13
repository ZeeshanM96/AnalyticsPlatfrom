// /js/filterCache.js
import { getToken } from "/static/js/auth.js";

let cachedSeverities = null;
let cachedAlertTypes = null;
let cachedBatches = null;
let cachedSources = null;
let cachedMetricTypes = null;
let cachedEventTypes = null;

export async function getSeverities(headers) {
  if (cachedSeverities) return cachedSeverities;

  const res = await fetch("/getseveritiesbytypes", { headers });
  if (!res.ok) throw new Error("Failed to fetch severities");

  const data = await res.json();
  cachedSeverities = data.severities;
  return cachedSeverities;
}

export async function getAlertTypes(headers) {
  if (cachedAlertTypes) return cachedAlertTypes;

  const res = await fetch("/getalertbytypes", { headers });

  if (!res.ok) {
    console.error("Failed to fetch alert types");
    throw new Error("Failed to fetch alert types");
  }

  const data = await res.json();

  if (!data?.alertTypes || !Array.isArray(data.alertTypes)) {
    console.error("Unexpected alert type response:", data);
    throw new Error("Invalid alert types data");
  }

  cachedAlertTypes = data.alertTypes;
  return cachedAlertTypes;
}

export async function getBatches(headers) {
  if (cachedBatches) return cachedBatches;

  const res = await fetch("/getbatches", { headers });

  if (!res.ok) {
    console.error("Failed to fetch batches");
    throw new Error("Failed to fetch batches");
  }

  const data = await res.json();

  if (!data?.batchIds || !Array.isArray(data.batchIds)) {
    console.error("Invalid batch data format:", data);
    throw new Error("Batches list is missing or invalid");
  }

  cachedBatches = data.batchIds;
  return cachedBatches;
}

export async function getSources(headers) {
  if (cachedSources) return cachedSources;

  const res = await fetch("/getsourcesbyid", { headers });

  if (!res.ok) {
    console.error("Failed to fetch sources");
    throw new Error("Failed to fetch sources");
  }

  const data = await res.json();

  if (!data?.sources || !Array.isArray(data.sources)) {
    console.error("Invalid sources data format:", data);
    throw new Error("Sources list is missing or invalid");
  }

  cachedSources = data.sources;
  return cachedSources;
}

export async function getMetricTypes(headers) {
  if (cachedMetricTypes) return cachedMetricTypes;

  const res = await fetch("/getmetricbytypes", { headers });

  if (!res.ok) {
    console.error("Failed to fetch metric types");
    throw new Error("Failed to fetch metric types");
  }

  const data = await res.json();

  if (!data?.metrics || !Array.isArray(data.metrics)) {
    console.error("Invalid metric data format:", data);
    throw new Error("Metrics list is missing or invalid");
  }

  cachedMetricTypes = data.metrics;
  return cachedMetricTypes;
}

export async function loadEventTypes(targetId = "eventTypesList") {
  try {

    if (!cachedEventTypes) {
      const res = await fetch("/geteventtypes", {
        headers: { Authorization: `Bearer ${getToken()}` }
      });

      if (!res.ok) {
        console.error("Error fetching event types", await res.text());
        return;
      }

      const data = await res.json();
      cachedEventTypes = data.eventTypes;
    }

    const list = document.getElementById(targetId);
    if (!list) {
      console.warn(`Dropdown target '${targetId}' not found.`);
      return;
    }

    list.innerHTML = "";

    cachedEventTypes.forEach((type, index) => {
      const id = `${targetId}_eventType_${index}`;
      const item = document.createElement("li");
      item.innerHTML = `
        <div class="form-check">
          <input class="form-check-input" type="checkbox" value="${type}" id="${id}">
          <label class="form-check-label" for="${id}">${type}</label>
        </div>
      `;
      list.appendChild(item);
    });
  } catch (err) {
    console.error("Fetch error:", err);
  }
}