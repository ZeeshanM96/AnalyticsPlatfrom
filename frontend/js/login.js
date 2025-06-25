import { setToken } from "/static/js/auth.js";

// Populate sources
document.addEventListener("DOMContentLoaded", () => {
  fetch(`/getsources`)
    .then((res) => {
      if (!res.ok) throw new Error("Failed to fetch sources");
      return res.json();
    })
    .then((data) => {
      const sourceSelect = document.getElementById("signupSource");
      sourceSelect.innerHTML = '<option value="">Select Source</option>';
      data.sources.forEach((source) => {
        const option = document.createElement("option");
        option.value = source;
        option.textContent = source;
        sourceSelect.appendChild(option);
      });
    })
    .catch((err) => {
      console.error(err);
      showAlert("Failed to load sources.", "danger");
    });
});

function showAlert(message, type = "danger") {
  const alertContainer = document.getElementById("alert-container");
  alertContainer.innerHTML = `
    <div class="alert alert-${type} alert-dismissible fade show" role="alert">
      ${message}
      <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    </div>`;
}

// LOGIN
document.getElementById("loginForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const email = document.getElementById("loginEmail").value.trim();
  const password = document.getElementById("loginPassword").value.trim();
  if (!email || !password) {
    showAlert("Email and password are required.");
    return;
  }

  try {
    const res = await fetch(`/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });

    const data = await res.json();

    if (!res.ok) {
      showAlert(data.detail || "Login failed.");
      return;
    }

    setToken(data.access_token);
    showAlert("Login successful!", "success");
    document.getElementById("loginForm").reset();
    window.location.href = "/dashboard";
  } catch {
    showAlert("Network error during login.");
  }
});

// SIGNUP
document.getElementById("signupForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const email = document.getElementById("signupEmail").value;
  const role = document.getElementById("signupRole").value;
  const source = document.getElementById("signupSource").value;
  const password = document.getElementById("signupPassword").value;
  const confirm_password = document.getElementById("signupConfirm").value;

  if (password !== confirm_password) {
    showAlert("Passwords do not match.");
    return;
  }

  if (!role || !source) {
    showAlert("Please select both a role and a source.");
    return;
  }

  if (role === "Client" && source === "AWS") {
    showAlert("Clients cannot choose 'AWS' as a source.");
    return;
  }

  try {
    const res = await fetch(`/signup`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, role, source, password, confirm_password }),
    });

    const data = await res.json();

    if (!res.ok) {
      showAlert(data.detail || "Signup failed.");
      return;
    }

    showAlert("Signup successful! You can now log in.", "success");
    document.getElementById("signupForm").reset();
    document.getElementById("loginTab").click();
  } catch {
    showAlert("Network error during signup.");
  }
});
