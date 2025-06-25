// /js/auth.js
export function getToken() {
  return localStorage.getItem("token");
}

export function isLoggedIn() {
  return !!getToken();
}

export function logout() {
  localStorage.removeItem("token");
  window.location.href = "/";
}

export function setToken(token) {
  localStorage.setItem("token", token);
}

export function setUser(userData) {
  localStorage.setItem("user", JSON.stringify(userData));
}

export function getUser() {
  const user = localStorage.getItem("user");
  return user ? JSON.parse(user) : null;
}

export function isAuthenticated() {
  return getToken();
}

export function scheduleAutoLogout(token) {
  try {
    const payload = JSON.parse(atob(token.split(".")[1]));
    const expiryTime = payload.exp * 1000;
    const timeout = expiryTime - Date.now();

    if (timeout > 0) {
      setTimeout(() => {
        try {
          alert("Session expired. Redirecting to login...");
          localStorage.removeItem("token");
        } finally {
          window.location.href = "/";
        }
      }, timeout);
    } else {
      // Token already expired
      localStorage.removeItem("token");
      window.location.href = "/";
    }
  } catch {
    // Invalid token
    localStorage.removeItem("token");
    window.location.href = "/";
  }
}

export function clearAuth() {
  localStorage.removeItem("token");
}

// Initialize state, invoke it in dashboard.js
export function logState() {
  alert(
    JSON.stringify(
      {
        token: getToken(),
        user: getUser(),
        isAuthenticated: isAuthenticated(),
      },
      null,
      2,
    ),
  );
}
