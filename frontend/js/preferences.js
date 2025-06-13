// /js/preferences.js
import { getToken,
   } from "/static/js/auth.js";

export async function fetchUserPreferences() {
  const token = getToken(); 
  const res = await fetch('/getuserpreferences', {
    headers: { Authorization: `Bearer ${token}` }
  });

  if (!res.ok) {
    console.error("Failed to fetch preferences");
    return {};
  }

  return await res.json(); 
}

export async function fetchUserPreferencesAndRender() {
  const data = await fetchUserPreferences();
  const container = document.getElementById("preferencesContent");

  if (!data.preferences || data.preferences.length === 0) {
    container.innerHTML = "<p class='text-muted'>No preferences found.</p>";
    return;
  }

  const rows = data.preferences.map((pref, idx) => `
    <tr>
      <td>${pref.viewName}</td>
      <td class="text-center">
        <input type="checkbox" id="prefEnabled-${idx}" ${pref.enabled ? "checked" : ""}>
      </td>
    </tr>
  `).join("");

  container.innerHTML = `
    <table class="table table-bordered table-sm">
      <thead class="table-light">
        <tr>
          <th>View Name</th>
          <th>Enabled</th>
        </tr>
      </thead>
      <tbody id="preferencesTableBody">
        ${rows}
      </tbody>
    </table>
  `;

  window._preferencesData = data.preferences;
}

export async function applyPreferences() {
  const prefData = await fetchUserPreferences();
  const preferences = prefData.preferences.reduce((map, pref) => {
    map[pref.viewName] = pref.enabled;
    return map;
  }, {});

  // ----- Overall Status and its child cards -----
  const batchCard = document.getElementById("totalBatchesCard");
  const serviceCard = document.getElementById("servicesStatusCard");
  const alertCard = document.getElementById("criticalAlertsCard");
  const overallCard = document.getElementById("overallStatusCard");

  if (!preferences["Overall Status"]) {
    overallCard.style.display = "none";
  } else {
    const batchVisible = preferences["Total Batches"];
    const serviceVisible = preferences["Services Status"];
    const alertVisible = preferences["Critical Alert"];

    batchCard.style.display = batchVisible ? "block" : "none";
    serviceCard.style.display = serviceVisible ? "block" : "none";
    alertCard.style.display = alertVisible ? "block" : "none";

    const allHidden = !batchVisible && !serviceVisible && !alertVisible;
    overallCard.style.display = allHidden ? "none" : "block";
  }

  // ----- Individual charts -----
  const eventChartSection = document.getElementById("EventTrends");
  const serviceMetricChartSection = document.getElementById("serviceMetricsCard");
  const sourceMetricChartSection = document.getElementById("sourceMetricsCard");
  const alertsByBatchSection = document.getElementById("AlertsByBatch");
  const issueResolutionSection = document.getElementById("IssueResolution");
  const RealTimeCard = document.getElementById("RealTimeCard");

  if (eventChartSection) {
    eventChartSection.style.display = preferences["Event Trends"] ? "block" : "none";
  }
  if (alertsByBatchSection) {
    alertsByBatchSection.style.display = preferences["Alerts by Batch"] ? "block" : "none";
  }
  if (issueResolutionSection) {
    issueResolutionSection.style.display = preferences["Issue Resolution"] ? "block" : "none";
  }
  if (serviceMetricChartSection) {
    serviceMetricChartSection.style.display = preferences["Service Metrics"] ? "block" : "none";
  }
    if (sourceMetricChartSection) {
    sourceMetricChartSection.style.display = preferences["Source Metrics"] ? "block" : "none";
  }
  console.log("Real Time View enabled?", preferences["Real Time View"]);
  console.log("RealTimeCard element found?", !!RealTimeCard);
  if (RealTimeCard) {
    RealTimeCard.style.display = preferences["Real Time View"] ? "flex" : "none";
    
  }
    applyPreferencesLayout(); 
}

export function applyPreferencesLayout() {
  const eventChart = document.getElementById("EventTrends");
  const serviceChart = document.getElementById("serviceMetricsCard");
  const sourceChart = document.getElementById("sourceMetricsCard");

  // Reset layout and spacing
  [eventChart, serviceChart, sourceChart].forEach(card => {
    if (card) {
      card.classList.remove("col-md-6", "col-md-12", "mt-5");
      card.classList.add("col-md-12");
    }
  });

  // Get visible cards only
  const visibleCards = [eventChart, serviceChart, sourceChart].filter(
    card => card && card.style.display !== "none"
  );

  if (visibleCards.length === 3) {
    // First two side-by-side
    visibleCards[0].classList.replace("col-md-12", "col-md-6");
    visibleCards[1].classList.replace("col-md-12", "col-md-6");

    // Third one takes full row with margin top
    visibleCards[2].classList.replace("col-md-12", "col-md-12");
    visibleCards[2].classList.add("mt-5");
  } else if (visibleCards.length === 2) {
    visibleCards.forEach(card => {
      card.classList.replace("col-md-12", "col-md-6");
      card.classList.remove("mt-5");
    });
  } else if (visibleCards.length === 1) {
    visibleCards[0].classList.replace("col-md-6", "col-md-12");
    visibleCards[0].classList.remove("mt-5");
  }
}