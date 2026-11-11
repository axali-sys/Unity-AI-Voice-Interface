import { createHash, createHmac, randomBytes } from "node:crypto";
import { NextResponse } from "next/server";

export const runtime = "nodejs";

const STATE_COOKIE = "ai_nexai_oauth_state";

function b64url(value) {
  return Buffer.from(value).toString("base64url");
}

function sign(value, secret) {
  return createHmac("sha256", secret).update(value).digest("base64url");
}

function encodeSigned(payload, secret) {
  const body = b64url(JSON.stringify(payload));
  return body + "." + sign(body, secret);
}

export async function POST(request) {
  let payload;
  try {
    payload = await request.json();
  } catch {
    return Response.json({ ok: false, error: "invalid_json" }, { status: 400 });
  }

  const workspaceId = typeof payload?.workspace_id === "string" ? payload.workspace_id.trim() : "";
  if (!workspaceId || workspaceId.length > 128) {
    return Response.json({ ok: false, error: "workspace_id_required" }, { status: 400 });
  }

  const secret = process.env.AI_SESSION_SECRET || "";
  const clientId = process.env.NEXAI_AXALIAI_OAUTH_CLIENT_ID || "axaliai-enterprise";
  const redirectUri = (process.env.NEXAI_AXALIAI_REDIRECT_URI ||
    "http://localhost:3000/api/auth/nexai/callback").trim();
  if (secret.length < 32) {
    return Response.json({ ok: false, error: "ai_sso_not_configured" }, { status: 503 });
  }

  const verifier = b64url(randomBytes(32));
  const challenge = b64url(createHash("sha256").update(verifier).digest());
  const state = b64url(randomBytes(32));
  const now = Math.floor(Date.now() / 1000);
  const pending = b64url(JSON.stringify({
    state,
    verifier,
    workspace_id: workspaceId,
    created_at: now,
  }));
  const signedState = pending + "." + sign(pending, secret);

  const response = NextResponse.json({
    ok: true,
    authorization_request: {
      client_id: clientId,
      redirect_uri: redirectUri,
      response_type: "code",
      state,
      code_challenge: challenge,
      code_challenge_method: "S256",
      workspace_id: workspaceId,
    },
    consent_required: true,
    note: "Send this request through NexAI's authenticated consent UI. Set consent=true only after the user explicitly approves.",
  }, { headers: { "Cache-Control": "no-store", "Referrer-Policy": "no-referrer" } });

  response.cookies.set(STATE_COOKIE, signedState, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    maxAge: 600,
  });
  return response;
}
