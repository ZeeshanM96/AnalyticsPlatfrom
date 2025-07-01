import { getToken } from "./auth.js";
import { showToast } from "./dashboard.js";

document.addEventListener("DOMContentLoaded", function () {
  function generateKey(length = 100) {
    const charset =
      "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
    const array = new Uint8Array(length);
    crypto.getRandomValues(array);
    return Array.from(array, (byte) => charset[byte % charset.length]).join("");
  }

  function copyToClipboard(fieldId) {
    const field = document.getElementById(fieldId);
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard
        .writeText(field.value)
        .then(() => showToast("✅ Copied to clipboard!"))
        .catch(() => {
          field.select();
          field.setSelectionRange(0, 99999);
          document.execCommand("copy");
          showToast("✅ Copied to clipboard!");
        });
    } else {
      field.select();
      field.setSelectionRange(0, 99999);
      document.execCommand("copy");
      showToast("✅ Copied to clipboard!");
    }
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
        showToast("User is not authenticated.", true);
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
        showToast("Network error. Please try again.", true);
      }
    });
});
