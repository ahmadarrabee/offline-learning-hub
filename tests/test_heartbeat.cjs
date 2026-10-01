"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

async function check() {
  const indicator = {textContent: "", dataset: {}};
  let heartbeat, abortTimeout, resolveFetch;
  let mode = "ok";
  let calls = 0;
  const context = {
    URL, AbortController,
    document: {
      getElementById: () => indicator,
      addEventListener: (_, fn) => fn(),
    },
    window: {location: {href: "http://192.168.1.100/custom_interface/"}, addEventListener() {}},
    setTimeout(fn, ms) { assert.equal(ms, 4000); abortTimeout = fn; return 1; },
    clearTimeout() {},
    setInterval(fn, ms) { assert.equal(ms, 10000); heartbeat = fn; },
    fetch: async (url, options) => {
      calls++;
      assert.equal(url.href, "http://192.168.1.100/custom_interface/index.html");
      assert.equal(options.cache, "no-store");
      assert.equal(options.method, "HEAD");
      if (mode === "network") throw new Error("Disconnected");
      if (mode === "pending") return new Promise((resolve, reject) => {
        resolveFetch = resolve;
        options.signal.addEventListener("abort", () => reject(new Error("Aborted")));
      });
      return {ok: mode === "ok", status: mode === "ok" ? 200 : 503};
    },
  };
  vm.runInNewContext(fs.readFileSync(path.join(__dirname, "../custom_interface/app.js"), "utf8"), context);
  await new Promise(setImmediate);
  assert.equal(indicator.dataset.state, "online");
  for (mode of ["http", "network"]) {
    await heartbeat();
    assert.equal(indicator.dataset.state, "offline");
  }
  mode = "pending";
  const pending = heartbeat();
  const before = calls;
  await heartbeat();
  assert.equal(calls, before, "Overlapping requests must be skipped");
  abortTimeout();
  await pending;
  assert.equal(indicator.dataset.state, "offline");
  mode = "ok";
  await heartbeat();
  assert.equal(indicator.dataset.state, "online", "Must recover after timeout");
  console.log("Heartbeat checks passed: initial ping, HTTP failure, network failure, timeout, overlap, recovery.");
}
check().catch(error => { console.error(error); process.exitCode = 1; });
