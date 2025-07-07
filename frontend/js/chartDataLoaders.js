// /js/chartDataLoaders.js
import { getToken } from "/static/js/auth.js";

import {
  renderAlertBarChart,
  renderSourceMetricChart,
  renderServiceMetricsChart,
  renderChart,
  renderResolutionChart,
} from "/static/js/rendercharts.js";

import { showAlert, getSelectedSourceEventTypes } from "/static/js/utils.js";

export async function fetchEventSummary() {
  const token = getToken();
  const eventTypes = getSelectedEventTypes();
  const fromDate = document.getElementById("fromDate").value;
  const toDate = document.getElementById("toDate").value;

  if (!fromDate || !toDate) {
    showAlert("Please select a date range.");
    return;
  }

  if (!eventTypes.length) {
    showAlert("Please select at least one event type.");
    return;
  }

  const url = new URL("/geteventtrends/", window.location.origin);
  url.searchParams.append("from_date", fromDate);
  url.searchParams.append("to_date", toDate);
  if (eventTypes.length) {
    url.searchParams.append("events", eventTypes.join(","));
  }

  try {
    const res = await fetch(url, {
      headers: { Authorization: `Bearer ${token}` },
    });

    let data;
    try {
      data = await res.json();
    } catch {
      showAlert("Invalid server response.");
      return;
    }

    if (!res.ok) {
      const msg = data?.detail || "Failed to load event data.";
      showAlert(msg);
      return;
    }

    renderChart(data.labels, data.datasets);
  } catch {
    showAlert("An error occurred while fetching data.");
  }
}

export async function fetchAlertChartData() {
  const token = getToken();

  const fromDate = document.getElementById("alertFrom").value;
  const toDate = document.getElementById("alertTo").value;
  const batches = getCheckedValues("batchDropdownList");
  const severities = getCheckedValues("severityDropdownList");

  if (!fromDate || !toDate || batches.length === 0 || severities.length === 0) {
    showAlert("Please select all filters.");
    return;
  }

  const url = new URL("/getalertsbybatch", window.location.origin);
  url.searchParams.append("from_date", fromDate);
  url.searchParams.append("to_date", toDate);
  url.searchParams.append("batches", batches.join(","));
  url.searchParams.append("severities", severities.join(","));

  try {
    const res = await fetch(url, {
      headers: { Authorization: `Bearer ${token}` },
    });

    let data;
    try {
      data = await res.json();
    } catch {
      showAlert("Invalid server response.");
      return;
    }

    if (!res.ok) {
      const msg = data?.detail || "Failed to load alert chart data.";
      showAlert(msg);
      return;
    }

    renderAlertBarChart(data.labels, data.datasets);
  } catch (err) {
    console.error("Failed to load alert chart:", err);
    showAlert("Error loading alert chart data.");
  }
}

export async function fetchResolutionChartData() {
  const token = getToken();

  const fromDate = document.getElementById("resFromDate").value;
  const toDate = document.getElementById("resToDate").value;
  const sources = getCheckedValues("issueSourceDropdownList");
  const severities = getCheckedValues("resSeverityDropdownList");

  if (!fromDate || !toDate || sources.length === 0 || severities.length === 0) {
    showAlert("Please select all filters.");
    return;
  }

  const url = new URL("/getalertsbysource", window.location.origin);
  url.searchParams.append("from_date", fromDate);
  url.searchParams.append("to_date", toDate);
  url.searchParams.append("sources", sources.join(","));
  url.searchParams.append("severities", severities.join(","));

  try {
    const res = await fetch(url, {
      headers: { Authorization: `Bearer ${token}` },
    });

    let data;
    try {
      data = await res.json();
    } catch {
      showAlert("Invalid server response.");
      return;
    }

    if (!res.ok) {
      const msg = data?.detail || "Failed to load issue resolution data.";
      showAlert(msg);
      return;
    }

    renderResolutionChart(data.labels, data.datasets);
  } catch (err) {
    console.error("Error fetching resolution chart:", err);
    showAlert("Error loading issue resolution data.");
  }
}

export async function fetchServiceMetricsData() {
  const token = getToken();
  const fromDate = document.getElementById("metricFromDate").value;
  const toDate = document.getElementById("metricToDate").value;
  const services = getCheckedValues("serviceDropdownList");
  const metrics = getCheckedValues("metricDropdownList");

  if (!fromDate || !toDate || services.length === 0 || metrics.length === 0) {
    showAlert("Please select date range, services, and metrics.");
    return;
  }

  const url = new URL("/getservicemetrics", window.location.origin);
  url.searchParams.append("from_date", fromDate);
  url.searchParams.append("to_date", toDate);
  url.searchParams.append("services", services.join(","));
  url.searchParams.append("metrics", metrics.join(","));

  try {
    const res = await fetch(url, {
      headers: { Authorization: `Bearer ${token}` },
    });

    let data;
    try {
      data = await res.json();
    } catch {
      showAlert("Invalid server response.");
      return;
    }

    if (!res.ok) {
      const msg = data?.detail || "Failed to fetch service metrics.";
      showAlert(msg);
      return;
    }

    renderServiceMetricsChart(data.labels, data.datasets);
  } catch (err) {
    console.error("Error fetching service metrics:", err);
    showAlert("Error loading service metrics data.");
  }
}

export async function fetchSourceMetricChartData() {
  const token = getToken();
  const fromDate = document.getElementById("sourceFromDate").value;
  const toDate = document.getElementById("sourceToDate").value;
  const sources = getCheckedValues("sourceDropdownList");
  const eventTypes = getSelectedSourceEventTypes();

  if (!fromDate || !toDate || sources.length === 0 || eventTypes.length === 0) {
    showAlert("Please select date range, sources, and event types.");
    return;
  }

  const url = new URL("/getsourcemetrics/", window.location.origin);
  url.searchParams.append("from_date", fromDate);
  url.searchParams.append("to_date", toDate);
  sources.forEach((source) => url.searchParams.append("sources", source));
  eventTypes.forEach((type) => url.searchParams.append("event_type", type));

  try {
    const res = await fetch(url, {
      headers: { Authorization: `Bearer ${token}` },
    });

    const data = await res.json();

    if (!res.ok) {
      const msg = data?.detail || "Failed to fetch source metric data.";
      showAlert(msg);
      return;
    }

    renderSourceMetricChart(data.labels, data.datasets);
  } catch (err) {
    console.error("Source metric chart error:", err);
    showAlert("Error loading chart.");
  }
}

export async function loadDashboardStats() {
  const token = getToken();
  const headers = { Authorization: `Bearer ${token}` };

  try {
    // 1. Batches
    const batchesRes = await fetch("/getbatchstatus", { headers });
    const batches = await batchesRes.json();
    document.getElementById("batchTodayCount").textContent = batches.today;
    document.getElementById("batchYesterdayCount").textContent =
      batches.yesterday;

    // 2. Services
    const servicesRes = await fetch("/getservicestatus", { headers });
    const services = await servicesRes.json();
    document.getElementById("runningServices").textContent = services.running;
    document.getElementById("totalServices").textContent = services.total;

    // 3. Critical Alerts
    const alertsRes = await fetch("/getalertstatus", { headers });
    const alerts = await alertsRes.json();
    document.getElementById("alertsToday").textContent = alerts.today;
    document.getElementById("alertsYesterday").textContent = alerts.yesterday;

    animateValue(
      document.getElementById("batchTodayCount"),
      0,
      batches.yesterday,
    );
    animateValue(
      document.getElementById("batchYesterdayCount"),
      0,
      batches.yesterday,
    );
    animateValue(
      document.getElementById("runningServices"),
      0,
      services.running,
    );
    animateValue(document.getElementById("totalServices"), 0, services.total);
    animateValue(document.getElementById("alertsToday"), 0, alerts.today);
    animateValue(
      document.getElementById("alertsYesterday"),
      0,
      alerts.yesterday,
    );
  } catch (err) {
    console.error("Failed to load dashboard stats:", err);
    showAlert("Error loading dashboard summary.");
  }
}

export function getCheckedValues(listId) {
  const checked = document.querySelectorAll(
    `#${listId} input[type="checkbox"]:checked`,
  );
  return Array.from(checked).map((cb) => cb.value);
}

export function getSelectedEventTypes() {
  const checkboxes = document.querySelectorAll(
    "#eventTypesList input[type='checkbox']:checked",
  );
  return Array.from(checkboxes).map((cb) => cb.value);
}

function animateValue(element, start, end, duration = 1000) {
  if (isNaN(end) || isNaN(start)) return;

  const range = end - start;

  // No need to animate if start and end are the same
  if (range === 0) {
    element.textContent = end;
    return;
  }

  const increment = range > 0 ? 1 : -1;
  const stepTime = Math.max(Math.floor(duration / Math.abs(range)), 20);
  let current = start;

  const timer = setInterval(() => {
    current += increment;
    element.textContent = current;
    if (current === end) {
      clearInterval(timer);
    }
  }, stepTime);
}
