/**
 * XParallel public API client for a Webli browser UI.
 *
 * SECURITY: This client intentionally calls only public endpoints.
 * Never put XP_TOKEN or XP_EXECUTION_APPROVAL_TOKEN in browser code.
 * Configure the API base URL in the Webli project environment/settings.
 */
export function createXParallelClient({ baseUrl, fetchImpl = fetch, timeoutMs = 10000 } = {}) {
  if (!baseUrl || typeof baseUrl !== "string") {
    throw new Error("XParallel API base URL is required");
  }

  const base = baseUrl.replace(/\/+$/, "");

  async function request(path, { method = "GET", body } = {}) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), timeoutMs);
    try {
      const response = await fetchImpl(`${base}${path}`, {
        method,
        headers: body ? { "Content-Type": "application/json" } : {},
        body: body ? JSON.stringify(body) : undefined,
        signal: controller.signal,
        credentials: "omit",
        redirect: "error",
      });

      const raw = await response.text();
      let data;
      try {
        data = raw ? JSON.parse(raw) : {};
      } catch {
        throw new Error(`XParallel returned non-JSON content (HTTP ${response.status})`);
      }

      if (!response.ok) {
        const reason = typeof data.error === "string" ? data.error : "request_failed";
        throw new Error(`XParallel request failed: ${reason} (HTTP ${response.status})`);
      }
      return data;
    } finally {
      clearTimeout(timeout);
    }
  }

  return Object.freeze({
    health: () => request("/public/health"),
    manifest: () => request("/public/xparallel/access"),
    ask: (query) => {
      if (typeof query !== "string" || !query.trim()) throw new Error("query_required");
      return request("/public/ask", { method: "POST", body: { query: query.trim() } });
    },
    buildPlan: (query) => {
      if (typeof query !== "string" || !query.trim()) throw new Error("query_required");
      return request("/public/build", { method: "POST", body: { query: query.trim() } });
    },
    route: (query) => {
      if (typeof query !== "string" || !query.trim()) throw new Error("query_required");
      return request("/public/route", { method: "POST", body: { query: query.trim() } });
    },
    mix: (query, plugins = ["web_search"]) => {
      if (typeof query !== "string" || !query.trim()) throw new Error("query_required");
      const allowed = Array.isArray(plugins) ? plugins.filter((id) => id === "web_search") : [];
      return request("/public/mix", { method: "POST", body: { query: query.trim(), plugins: allowed } });
    },
  });
}
