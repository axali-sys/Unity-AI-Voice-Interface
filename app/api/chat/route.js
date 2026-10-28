export async function POST(request) {
  const payload = await request.json();
  const query = payload?.query || "";

  if (!query) {
    return Response.json({ error: "query_required" }, { status: 400 });
  }

  const backendUrl = process.env.XP_API_URL || process.env.NEXT_PUBLIC_XP_API_URL || "http://localhost:8787";
  const token = process.env.XP_TOKEN;

  const candidates = token
    ? [
        { path: "/chat", headers: { Authorization: `Bearer ${token}` } },
        { path: "/public/ask", headers: {} },
      ]
    : [{ path: "/public/ask", headers: {} }, { path: "/public/route", headers: {} }];

  for (const candidate of candidates) {
    try {
      const response = await fetch(`${backendUrl}${candidate.path}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...candidate.headers,
        },
        body: JSON.stringify({
          query,
          workspace_id: payload.workspace_id || "demo-workspace",
          actor: payload.actor || "demo-user",
          messages: payload.messages || [],
          use_memory: payload.use_memory !== false,
        }),
      });

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        // Do not disguise an authenticated live-chat failure as a successful
        // public/demo answer. Keep fallback for auth/routing compatibility,
        // but surface provider outages and missing configuration honestly.
        if (candidate.path === "/chat" && response.status >= 500) {
          return Response.json(
            { error: data?.error || "live_ai_unavailable", fallback: false },
            { status: response.status }
          );
        }
        continue;
      }

      const message =
        data.message ||
        data.response ||
        data.summary ||
        data.answer ||
        (Array.isArray(data.results) && data.results.length > 0 ? data.results[0]?.summary || data.results[0]?.title || "Found a matching result." : null) ||
        "I’m ready to help.";

      return Response.json({
        ok: true,
        message,
        ...data,
      });
    } catch (error) {
      continue;
    }
  }

  return Response.json(
    {
      ok: true,
      message:
        "I’m in demo mode because no live XParallel backend is connected yet. Set XP_API_URL and XP_TOKEN to connect the actual AI service.",
      fallback: true,
    },
    { status: 200 }
  );
}
