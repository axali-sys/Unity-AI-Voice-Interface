/**
 * ƎllE chat gateway.
 *
 * Only the authenticated XParallel /chat endpoint is an AI chat path.
 * Public knowledge/intent endpoints are deliberately not used as chat fallbacks.
 * A demo answer must never be returned as a successful live-AI response.
 */
export async function POST(request) {
  let payload;
  try {
    payload = await request.json();
  } catch {
    return Response.json({ ok: false, error: "invalid_json" }, { status: 400 });
  }

  const query = typeof payload?.query === "string" ? payload.query.trim() : "";
  const suppliedMessages = Array.isArray(payload?.messages) ? payload.messages : [];
  const messages = suppliedMessages.length
    ? suppliedMessages
    : query
      ? [{ role: "user", content: query }]
      : [];

  if (!messages.length) {
    return Response.json({ ok: false, error: "messages_required" }, { status: 400 });
  }

  const backendUrl = (process.env.XP_API_URL || process.env.NEXT_PUBLIC_XP_API_URL || "").trim().replace(/\/$/, "");
  const token = (process.env.XP_TOKEN || "").trim();

  if (!backendUrl) {
    return Response.json(
      { ok: false, error: "xparallel_backend_not_configured", fallback: false },
      { status: 503 }
    );
  }
  if (!token) {
    return Response.json(
      { ok: false, error: "xparallel_authentication_not_configured", fallback: false },
      { status: 503 }
    );
  }

  let upstream;
  try {
    upstream = await fetch(`${backendUrl}/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        query,
        // Until a trusted browser login + membership adapter exists, do not accept
        // workspace/actor claims from the browser or read a shared memory partition.
        workspace_id: "preview",
        actor: "elle-preview",
        messages,
        use_memory: false,
      }),
      cache: "no-store",
      signal: AbortSignal.timeout(50000),
    });
  } catch (error) {
    const timedOut = error?.name === "TimeoutError";
    return Response.json(
      {
        ok: false,
        error: timedOut ? "xparallel_backend_timeout" : "xparallel_backend_unreachable",
        fallback: false,
      },
      { status: 502 }
    );
  }

  const data = await upstream.json().catch(() => null);

  if (!upstream.ok) {
    const upstreamError = typeof data?.error === "string" ? data.error : "upstream_request_failed";
    const authFailure = upstream.status === 401 || upstream.status === 403;
    const status = upstream.status === 429 ? 429 : upstream.status >= 500 ? 503 : 502;
    return Response.json(
      {
        ok: false,
        error: authFailure
          ? "xparallel_authentication_failed"
          : upstreamError,
        upstream_status: upstream.status,
        fallback: false,
      },
      { status }
    );
  }

  if (!data || typeof data !== "object" || Array.isArray(data)) {
    return Response.json(
      { ok: false, error: "xparallel_invalid_response", fallback: false },
      { status: 502 }
    );
  }

  const answer = data.answer || data.message || data.response;
  if (typeof answer !== "string" || !answer.trim()) {
    return Response.json(
      { ok: false, error: "ai_provider_empty_response", fallback: false },
      { status: 502 }
    );
  }

  return Response.json({
    ...data,
    ok: true,
    message: answer.trim(),
    fallback: false,
    source: "xparallel_authenticated_chat",
  });
}
