// static/js/realtime.js
import {
  getToken
} from "/static/js/auth.js";

import { showAlert } from "/static/js/utils.js";

export async function startRealTimeChart() {
  const token = getToken();
  if (!token) {
    console.error("JWT token not found. Cannot start real-time chart.");
    showAlert("Unauthorized. Please log in.");
    return;
  }

  const ws = new WebSocket(`ws://localhost:8000/ws/data?token=${token}`);
  const ctx = document.getElementById("chart").getContext("2d");

  // Maps `metric_name|source_id` to dataset
  const datasetsMap = {};

  const sourceColors = {
    1: 'rgba(54, 162, 235, 1)',   // Blue (Marketing)
    2: 'rgba(255, 206, 86, 1)',   // Yellow (User Activity)
    3: 'rgba(75, 192, 192, 1)',   // Teal (Platform Monitoring)
    4: 'rgba(255, 99, 132, 1)',   // Red (Backend/Infra)
  };

  const chart = new Chart(ctx, {
    type: "line",
    data: {
      datasets: [],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: 'nearest',
        intersect: false,
      },
      plugins: {
        title: {
          display: true,
          text: 'Live Metrics by Source',
        },
        legend: {
          display: true,
          position: 'top',
          labels: {
            usePointStyle: true,
          },
        },
      },
      scales: {
        x: {
          type: 'time',
          time: {
            unit: 'second',
            tooltipFormat: 'HH:mm:ss',
            displayFormats: {
              second: 'HH:mm:ss',
            },
          },
          title: {
            display: true,
            text: 'Timestamp',
          },
        },
        y: {
          beginAtZero: true,
          title: {
            display: true,
            text: 'Value',
          },
        },
      },
    },
  });

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    const timestamp = new Date(data.timestamp);
    const key = `${data.metric_name}|${data.source_id}`;
    const color = sourceColors[data.source_id] || 'rgba(100,100,100,1)';

    if (!datasetsMap[key]) {
      const newDataset = {
        label: `${data.metric_name}`,
        data: [],
        borderColor: color,
        backgroundColor: color,
        borderWidth: 2,
        fill: false,
        tension: 0.1,
      };
      datasetsMap[key] = newDataset;
      chart.data.datasets.push(newDataset);
    }

    datasetsMap[key].data.push({ x: timestamp, y: data.value });
    chart.update();
  };

  ws.onerror = (err) => {
    console.error("WebSocket error:", err);
    showAlert("WebSocket connection error.");
  };

  ws.onclose = () => {
    console.warn("WebSocket closed.");
    showAlert("Real-time connection closed.");
  };
}

