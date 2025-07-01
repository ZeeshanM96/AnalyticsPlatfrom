import { getToken } from "./auth.js";
import { showToast } from "./dashboard.js";

document.addEventListener("DOMContentLoaded", function () {
  function generateKey(length = 100) {
    const charset =
      "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()_-+=<>?";
    let key = "";
    for (let i = 0; i < length; i++) {
      key += charset.charAt(Math.floor(Math.random() * charset.length));
    }
    return key;
  }

  function copyToClipboard(fieldId) {
    const field = document.getElementById(fieldId);
    navigator.clipboard.writeText(field.value);
  }

  // Visibility toggle + copy
  document.addEventListener("click", function (e) {
    if (e.target.classList.contains("toggle-btn")) {
      const fieldId = e.target.getAttribute("data-target");
      const input = document.getElementById(fieldId);
      if (input.type === "password") {
        input.type = "text";
        e.target.textContent = "🙈";
      } else {
        input.type = "password";
        e.target.textContent = "👁️";
      }
    }

    if (e.target.classList.contains("copy-btn")) {
      const fieldId = e.target.getAttribute("data-target");
      copyToClipboard(fieldId);
    }
  });

  // Generate keys and show modal
  document
    .getElementById("setApiKeyBtn")
    .addEventListener("click", function () {
      document.getElementById("apiKeyField").value = generateKey(100);
      document.getElementById("secretKeyField").value = generateKey(100);

      document.getElementById("apiKeyField").type = "password";
      document.getElementById("secretKeyField").type = "password";
      document
        .querySelectorAll(".toggle-btn")
        .forEach((btn) => (btn.textContent = "👁️"));

      const modal = new bootstrap.Modal(document.getElementById("apiKeyModal"));
      modal.show();
    });

  // Submit keys
  document
    .getElementById("setKeyBtn")
    .addEventListener("click", async function () {
      const apiKey = document.getElementById("apiKeyField").value;
      const secretKey = document.getElementById("secretKeyField").value;
      const token = getToken();

      if (!apiKey || !secretKey) {
        showToast("API key or Secret key is missing.", true);
        return;
      }

      if (!token) {
        alert("User is not authenticated.");
        return;
      }

      try {
        const res = await fetch("/setApi", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ ApiKey: apiKey, SecretKey: secretKey }),
        });

        const data = await res.json();

        if (res.ok) {
          showToast("✅ Keys set successfully!");
          bootstrap.Modal.getInstance(
            document.getElementById("apiKeyModal"),
          ).hide();
        } else if (
          res.status === 400 &&
          data.detail?.includes("Credentials already exist")
        ) {
          showToast(
            "Key not set. Credentials already exist. Please contact admin.",
            true,
          );
          return;
        } else {
          showToast(
            data.detail ||
              data.message ||
              "Unable to set key. Please try again.",
            true,
          );
        }
      } catch (err) {
        console.error(err);
        alert("Network error. Please try again.");
      }
    });
});
