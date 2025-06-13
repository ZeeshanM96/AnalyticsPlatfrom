// /loadFilter.js
import { getToken } from "/static/js/auth.js";
import { renderCheckboxList, createCheckboxListItem } from "/static/js/dashboard.js";
import { showAlert } from "/static/js/utils.js";
import { getSeverities, getAlertTypes, getBatches, getSources, getMetricTypes, loadEventTypes } from "/static/js/filterCache.js";

export async function loadAlertFilterOptions() {
  const batchList = document.getElementById("batchDropdownList");
  const severityList = document.getElementById("severityDropdownList");

  if (!batchList || !severityList) {
    console.error("Missing dropdown list elements in DOM.");
    return;
  }

  const token = getToken();
  const headers = { Authorization: `Bearer ${token}` };

  const severities = await getSeverities(headers);
  const alertTypes = await getAlertTypes(headers);
  const batches = await getBatches(headers);


  batchList.innerHTML = "";
  batches.forEach((batchId, index) => {
    const id = `batch_${index}`;
    batchList.innerHTML += `
      <li>
        <div class="form-check">
          <input class="form-check-input" type="checkbox" value="${batchId}" id="${id}">
          <label class="form-check-label" for="${id}">${batchId}</label>
        </div>
      </li>
    `;
  });

  severityList.innerHTML = "";
  severities.forEach((severity, index) => {
    const id = `severity_${index}`;
    severityList.innerHTML += `
      <li>
        <div class="form-check">
          <input class="form-check-input" type="checkbox" value="${severity}" id="${id}">
          <label class="form-check-label" for="${id}">${severity}</label>
        </div>
      </li>
    `;
  });
}

export async function loadResolutionFilters() {
  const token = getToken();
  const headers = { Authorization: `Bearer ${token}` };

  const sources = await getSources(headers);

  const severities = await getSeverities(headers);

  renderCheckboxList("issueSourceDropdownList", sources, "issueSource");
  renderCheckboxList("resSeverityDropdownList", severities, "resSeverity");
}

export async function loadServiceAndMetricOptions() {
  const token = getToken();
  const headers = { Authorization: `Bearer ${token}` };

  try {
     const servicesRes = await fetch("/getservices", { headers });
     const servicesData = await servicesRes.json();
     const services = servicesData.services;

     const metrics = await getMetricTypes(headers);

     const serviceList = document.getElementById("serviceDropdownList");
     const metricList = document.getElementById("metricDropdownList");

     serviceList.innerHTML = "";
     services.forEach((service, i) => {
       const item = createCheckboxListItem(`service_${i}`, service, service);
       serviceList.appendChild(item);
     });

    metricList.innerHTML = "";
    metrics.forEach((metric, i) => {
      const item = createCheckboxListItem(`metric_${i}`, metric, metric);
      metricList.appendChild(item);
    });

  } catch (err) {
    console.error("Failed to load services or metrics:", err);
    showAlert("Failed to load dropdown options.");
  }
}

export async function loadMetricTypes() {
  const token = getToken();
  const headers = { Authorization: `Bearer ${token}` };

  try {
    const metrics = await getMetricTypes(headers); 

    const list = document.getElementById("sourceEventTypesList");
    list.innerHTML = "";

    metrics.forEach((metric, index) => {
      const id = `sourceMetric_${index}`;
      list.innerHTML += `
        <li>
          <div class="form-check">
            <input class="form-check-input" type="checkbox" value="${metric}" id="${id}">
            <label class="form-check-label" for="${id}">${metric}</label>
          </div>
        </li>
      `;
    });
  } catch (err) {
    console.error("Error loading source metric types:", err);
    showAlert("An error occurred while loading metric types.");
  }
}


export async function loadSourceTypes() {
  const token = getToken();
  const headers = { Authorization: `Bearer ${token}` };

  try {
    const sources = await getSources(headers); 
    renderCheckboxList("sourceDropdownList", sources, "sourceMetric");
  } catch (err) {
    console.error("Failed to load source metric dropdown:", err);
    showAlert("An error occurred while loading source metric filters.");
  }
}