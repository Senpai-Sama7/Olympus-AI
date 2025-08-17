const statusEl = document.getElementById("status");
const badgeEl = document.getElementById("badge");

function setBadge(ok) {
  badgeEl.textContent = ok ? "Healthy" : "Unavailable";
  badgeEl.className = ok ? "badge ok" : "badge bad";
}

async function call(method, args) {
  // pywebview exposes window.pywebview.api.<method>
  return await window.pywebview.api[method](...(args || []));
}

async function refresh() {
  try {
    const s = await call("status");
    statusEl.textContent = JSON.stringify(s, null, 2);
    setBadge(!!(s.health && s.health.code === 200));
  } catch (e) {
    statusEl.textContent = String(e);
    setBadge(false);
  }
}

document.getElementById("btn-start").addEventListener("click", async () => {
  await call("start");
  await refresh();
});
document.getElementById("btn-stop").addEventListener("click", async () => {
  await call("stop");
  await refresh();
});
document.getElementById("btn-status").addEventListener("click", refresh);
document.getElementById("btn-docs").addEventListener("click", () => call("open_docs"));
document.getElementById("btn-config").addEventListener("click", () => call("open_config"));

refresh();
setInterval(refresh, 3000);
