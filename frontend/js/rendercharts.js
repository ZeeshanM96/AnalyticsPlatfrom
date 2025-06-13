// /js/charts.js

let serviceChartInstance;
let sourceMetricChartInstance;
let chartInstance;  
let resolutionChartInstance;
let alertChartInstance;

export function renderAlertBarChart(labels, datasets) {
  const container = document.getElementById("alertChartContainer");
  container.innerHTML = "";

  const noData = !labels.length || !datasets.length || datasets.every(ds => ds.data.length === 0);
  if (noData) {
    container.innerHTML = "<p class='text-muted text-center'>Not enough data to display graph.</p>";
    return;
  }

  const canvas = document.createElement("canvas");
  canvas.id = "alertBatchChart";
  container.appendChild(canvas);

  const ctx = canvas.getContext("2d");

  if (window.alertChartInstance) window.alertChartInstance.destroy();

  window.alertChartInstance = new Chart(ctx, {
    type: "bar",
    data: {
      labels,
      datasets: datasets.map(ds => ({
        ...ds,
        backgroundColor: getRandomColor()
      }))
    },
    options: {
      responsive: true,
      scales: {
        y: {
          beginAtZero: true,
          title: { display: true, text: "Alert Count" }
        },
        x: {
          title: { display: true, text: "Batch ID" }
        }
      },
      plugins: {
        legend: { position: "top" }
      }
    }
  });
}

export function renderSourceMetricChart(labels, datasets) {
  const container = document.getElementById("sourceMetricChartContainer");
  container.innerHTML = '<canvas id="sourceMetricChart"></canvas>';

  const canvas = document.getElementById("sourceMetricChart");
  if (!canvas) {
    console.error("Canvas not found.");
    return;
  }

  if (sourceMetricChartInstance) {
    sourceMetricChartInstance.destroy();
  }

  const ctx = canvas.getContext("2d");

  const styledDatasets = datasets.map(ds => ({
    ...ds,
    backgroundColor: getRandomColor()
  }));

  sourceMetricChartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels, 
      datasets: styledDatasets 
    },
    options: {
      responsive: true,
      plugins: {
        title: {
          display: true,
          text: 'Metric Counts by Source'
        },
        legend: {
          position: 'top'
        }
      },
      scales: {
        x: {
          title: { display: true, text: "Source" }
        },
        y: {
          beginAtZero: true,
          title: { display: true, text: "Metric Value" }
        }
      }
    }
  });
}

export function renderServiceMetricsChart(labels, datasets) {
  const container = document.getElementById("serviceMetricChartContainer");

  container.innerHTML = '<canvas id="serviceMetricChart"></canvas>';
  const canvas = document.getElementById("serviceMetricChart");

  if (!canvas) {
    console.error("Canvas not found in the DOM.");
    return;
  }

  const noData = !labels.length || !datasets.length || datasets.every(ds => ds.data.every(val => val === 0));
  if (noData) {
    container.innerHTML = "<p class='text-muted text-center'>No data available for selected filters.</p>";
    return;
  }

  const ctx = canvas.getContext("2d");

  if (serviceChartInstance) {
    serviceChartInstance.destroy();
  }

  const styledDatasets = datasets.map(ds => ({
    ...ds,
    borderColor: getRandomColor(),
    tension: 0.3,
    pointRadius: 4
  }));

  serviceChartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: styledDatasets
    },
    options: {
      responsive: true,
      plugins: {
        legend: { position: 'top' },
        title: {
          display: true,
          text: 'Service Metrics Over Time'
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          title: { display: true, text: 'Metric Value' }
        },
        x: {
          title: { display: true, text: 'Date' }
        }
      }
    }
  });
}

export function renderChart(labels, datasets) {
  const container = document.getElementById("eventChart").parentElement;
  container.innerHTML = ""; 

  const noData = !labels.length || !datasets.length || datasets.every(ds => !ds.data || ds.data.length === 0);
  if (noData) {
    container.innerHTML = "<p class='text-muted text-center'>Not enough data to display graph.</p>";
    return;
  }

  const canvas = document.createElement("canvas");
  canvas.id = "eventChart";
  container.appendChild(canvas);

  const ctx = canvas.getContext("2d");

  if (chartInstance) {
    chartInstance.destroy();
  }

  const coloredDatasets = datasets.map(ds => ({
    ...ds,
    borderColor: getRandomColor(),
    tension: 0.3,
    pointRadius: 4
  }));

  chartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: coloredDatasets
    },
    options: {
      responsive: true,
      plugins: {
        legend: {
          display: true,
          position: 'top'
        }
      },
      scales: {
        y: {
          beginAtZero: true
        }
      }
    }
  });
}

export function renderResolutionChart(labels, datasets) {
  const container = document.getElementById("resolutionChartContainer");
  container.innerHTML = "";

  const noData = !labels.length || !datasets.length || datasets.every(ds => ds.data.length === 0);
  if (noData) {
    container.innerHTML = "<p class='text-muted text-center'>Not enough data to display graph.</p>";
    return;
  }


  const shortLabels = labels.map(label => label.length > 8 ? label.slice(0, 6) + "..." : label);

  const canvas = document.createElement("canvas");
  canvas.id = "issueResolutionChart";
  container.appendChild(canvas);

  const ctx = canvas.getContext("2d");

  if (resolutionChartInstance) resolutionChartInstance.destroy();

  resolutionChartInstance = new Chart(ctx, {
    type: "bar",
    data: {
      labels: shortLabels,
      datasets: datasets
    },
    options: {
      responsive: true,
      plugins: {
        title: {
          display: true,
          text: 'Resolution Status by Source and Severity'
        },
        tooltip: {
          mode: 'index',
          intersect: false,
          callbacks: {
            
            title: function (tooltipItems) {
              const index = tooltipItems[0].dataIndex;
              return labels[index]; 
            }
          }
        },
        legend: {
          position: 'bottom'
        }
      },
      scales: {
        x: {
          stacked: true,
          ticks: {
            maxRotation: 45,
            minRotation: 45
          }
        },
        y: {
          stacked: true,
          beginAtZero: true
        }
      }
    }
  });
}

export function getRandomColor() {
  const r = Math.floor(Math.random() * 200);
  const g = Math.floor(Math.random() * 200);
  const b = Math.floor(Math.random() * 200);
  return `rgb(${r}, ${g}, ${b})`;
}