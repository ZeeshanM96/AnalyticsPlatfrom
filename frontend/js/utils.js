// /js/utlis.js
export function showAlert(message, type = "danger") {
  if (document.querySelector(".alert")) return;

  const alertContainer = document.getElementById("alertContainer");
  alertContainer.innerHTML = `
    <div class="alert alert-${type} alert-dismissible fade show py-2 px-3 small" role="alert">
      ${message}
      <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    </div>`;
}

export function getSelectedSourceEventTypes() {
  const checkboxes = document.querySelectorAll(
    "#sourceEventTypesList input[type='checkbox']:checked",
  );
  return Array.from(checkboxes).map((cb) => cb.value);
}
