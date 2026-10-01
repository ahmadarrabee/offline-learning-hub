"use strict";

document.addEventListener("DOMContentLoaded", () => {
  const indicator = document.getElementById("status-indicator");
  if (!indicator) return;
  let checking = false;

  async function checkConnection() {
    if (checking) return;
    checking = true;
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 4000);
    try {
      const response = await fetch(new URL("index.html", window.location.href), {
        method: "HEAD", cache: "no-store", signal: controller.signal,
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      indicator.textContent = "متصل بالشبكة المحلية";
      indicator.dataset.state = "online";
    } catch {
      indicator.textContent = "غير متصل بالسيرفر المحلي";
      indicator.dataset.state = "offline";
    } finally {
      clearTimeout(timeout);
      checking = false;
    }
  }

  checkConnection();
  setInterval(checkConnection, 10000);
  window.addEventListener("online", checkConnection);
  window.addEventListener("offline", checkConnection);
});
