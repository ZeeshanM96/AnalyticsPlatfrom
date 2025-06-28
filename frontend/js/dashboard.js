// frontend/dashboard.js
// /js/dashboard.js
import { startRealTimeChart } from "/static/js/realtime.js";

import {
  fetchUserPreferencesAndRender,
  applyPreferences,
} from "/static/js/preferences.js";

import {
  getToken,
  scheduleAutoLogout,
  clearAuth,
  setUser,
} from "/static/js/auth.js";

import {
  fetchServiceMetricsData,
  fetchSourceMetricChartData,
  fetchAlertChartData,
  fetchResolutionChartData,
  loadDashboardStats,
  fetchEventSummary,
} from "/static/js/chartDataLoaders.js";

import {
  loadAlertFilterOptions,
  loadResolutionFilters,
  loadServiceAndMetricOptions,
  loadMetricTypes,
  loadSourceTypes,
} from "/static/js/loadFilters.js";

import { showAlert } from "/static/js/utils.js";

import { loadEventTypes } from "/static/js/filterCache.js";

const params = new URLSearchParams(window.location.search);
const tokenFromUrl = params.get("token");

if (tokenFromUrl) {
  localStorage.setItem("token", tokenFromUrl);
  window.history.replaceState({}, "", "/dashboard");
}

document.addEventListener("DOMContentLoaded", async () => {
  const token = getToken();

  if (!token) {
    showAlert("You are not logged in.");
    setTimeout(() => (window.location.href = "/"), 2000);
    return;
  }

  // Check if user is authenticated
  scheduleAutoLogout(token);

  try {
    await loadDashboardStats();
    await loadAlertFilterOptions();
    await loadResolutionFilters();
    await loadServiceAndMetricOptions();
    await loadMetricTypes();
    await loadSourceTypes();
    await loadEventTypes();
    await loadEventTypes("sourceEventTypesList");
    await startRealTimeChart();
    await applyPreferences();
  } catch (err) {
    showAlert("Error loading dashboard.");
    console.error(err);
  }

  try {
    const res = await fetch("/getuserdetails", {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    let data;
    try {
      data = await res.json();
    } catch {
      showAlert("Invalid response from server.");
      return;
    }

    if (!res.ok) {
      showAlert(data.detail || "Session expired.");
      clearAuth();
      setTimeout(() => (window.location.href = "/"), 2000);
      return;
    }

    setUser(data);
    // logState();
    const namePart = data.email.split("@")[0];
    const words = namePart.split(/[._]/);
    const displayName = words
      .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
      .join(" ");

    document.getElementById("welcomeMessage").textContent =
      `Welcome, ${displayName}`;
    document.getElementById("userEmail").textContent = data.email;
    document.getElementById("userRole").textContent = data.role;
    document.getElementById("userName").textContent = displayName;
    document.getElementById("userSource").textContent = data.source;
  } catch (err) {
    showAlert("Network error.");
    console.error(err);
  }

  document.getElementById("logoutBtn").addEventListener("click", () => {
    clearAuth();
    window.location.href = "/";
  });
});

export function renderCheckboxList(containerId, values, prefix) {
  const container = document.getElementById(containerId);
  container.innerHTML = "";
  values.forEach((value, index) => {
    const id = `${prefix}_${index}`;
    container.innerHTML += `
      <li>
        <div class="form-check">
          <input class="form-check-input" type="checkbox" value="${value}" id="${id}">
          <label class="form-check-label" for="${id}">${value}</label>
        </div>
      </li>
    `;
  });
}

document
  .getElementById("setPreferencesBtn")
  .addEventListener("click", async () => {
    await fetchUserPreferencesAndRender();
    const modalEl = document.getElementById("preferencesModal");
    const modal = new bootstrap.Modal(modalEl);
    modal.show();
  });

document
  .getElementById("savePreferencesBtn")
  .addEventListener("click", async () => {
    const updatedPrefs = window._preferencesData.map((pref, idx) => ({
      viewName: pref.viewName,
      preferredView: pref.preferredView,
      enabled: document.getElementById(`prefEnabled-${idx}`).checked,
    }));

    const res = await fetch("/updatepreferences", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${getToken()}`,
      },
      body: JSON.stringify(updatedPrefs),
    });

    const modalEl = document.getElementById("preferencesModal");
    const modal = bootstrap.Modal.getOrCreateInstance(modalEl);

    if (res.ok) {
      showToast("Preferences updated successfully.");
      modal.hide();
      await applyPreferences();
    } else {
      showToast("Failed to update preferences.", true);
    }
  });

export function createCheckboxListItem(id, label, value) {
  const li = document.createElement("li");
  li.innerHTML = `
    <div class="form-check">
      <input class="form-check-input" type="checkbox" value="${value}" id="${id}">
      <label class="form-check-label" for="${id}">${label}</label>
    </div>
  `;
  return li;
}

document.addEventListener("DOMContentLoaded", () => {
  const setPreferencesBtn = document.getElementById("setPreferencesBtn");

  setPreferencesBtn.addEventListener("click", () => {
    const nameEl = document.getElementById("userName");
    if (nameEl) {
      document.getElementById("modalUserName").textContent = nameEl.textContent;
    }
    fetchUserPreferencesAndRender();
  });
});

function showToast(message, isError = false) {
  const toastEl = document.getElementById("preferencesToast");
  const toastMessage = document.getElementById("toastMessage");

  toastMessage.textContent = message;
  toastEl.classList.remove("bg-success", "bg-danger");
  toastEl.classList.add(isError ? "bg-danger" : "bg-success");

  const toast = bootstrap.Toast.getOrCreateInstance(toastEl);
  toast.show();
}

// Load filter options on page load
document.addEventListener("DOMContentLoaded", loadAlertFilterOptions);

// Event listener
document
  .getElementById("filterBtn")
  .addEventListener("click", fetchEventSummary);
document
  .getElementById("metricSearchBtn")
  .addEventListener("click", fetchServiceMetricsData);
document
  .getElementById("sourceMetricSearchBtn")
  .addEventListener("click", fetchSourceMetricChartData);
document
  .getElementById("alertFilterBtn")
  .addEventListener("click", fetchAlertChartData);
document
  .getElementById("issueResolutionBtn")
  .addEventListener("click", fetchResolutionChartData);
