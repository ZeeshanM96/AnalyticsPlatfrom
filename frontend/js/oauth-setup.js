document.addEventListener("DOMContentLoaded", async () => {
  const socialButtons = document.querySelector(".social-btn-wrapper");
  const authTabs = document.getElementById("authTabs");

  // Setup tab-switch handler
  if (authTabs) {
    authTabs.addEventListener("shown.bs.tab", (event) => {
      const activeTabId = event.target.getAttribute("data-bs-target");

      if (activeTabId === "#oauth-setup") {
        socialButtons?.classList.add("d-none");
      } else {
        socialButtons?.classList.remove("d-none");
      }
    });
  }

  // OAuth redirect handling
  const urlParams = new URLSearchParams(window.location.search);
  const email = urlParams.get("email");

  if (window.location.pathname.includes("login.html") && email) {
    const oauthTabBtn = document.querySelector("#oauth-tab");
    oauthTabBtn.classList.remove("d-none");

    const tab = new bootstrap.Tab(oauthTabBtn);
    tab.show();

    document.getElementById("authTabs")?.classList.add("d-none");
    document.getElementById("login")?.classList.remove("show", "active");
    document.getElementById("signup")?.classList.remove("show", "active");

    const oauthTab = document.getElementById("oauth-setup");
    oauthTab.classList.add("show", "active");

    socialButtons?.classList.add("d-none");

    document.getElementById("email").value = email;

    try {
      const res = await fetch("/getsources");
      if (!res.ok) throw new Error("Failed to fetch sources");
      const data = await res.json();

      const sourceSelect = document.getElementById("source");
      sourceSelect.innerHTML = '<option value="">Select Source</option>';
      data.sources.forEach((source) => {
        const option = document.createElement("option");
        option.value = source;
        option.textContent = source;
        sourceSelect.appendChild(option);
      });
    } catch (err) {
      console.error(err);
      alert("Could not load sources.");
    }

    // Form submission for OAuth completion
    document
      .getElementById("oauthCompleteForm")
      .addEventListener("submit", async (e) => {
        e.preventDefault();
        const role = document.getElementById("role").value;
        const source = document.getElementById("source").value;

        const formData = new FormData();
        formData.append("email", email);
        formData.append("role", role);
        formData.append("source", source);

        try {
          const res = await fetch("/auth/oauth/complete-signup", {
            method: "POST",
            body: formData,
          });

          if (res.redirected) {
            window.location.href = res.url;
          } else {
            const data = await res.json();
            alert(data.detail || "Signup failed.");
          }
        } catch {
          alert("Network error during OAuth signup.");
        }
      });
  }
});
