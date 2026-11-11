import { createHmac, timingSafeEqual } from "node:crypto";
import { NextResponse } from "next/server";

export const runtime = "nodejs";

const STATE_COOKIE = "ai_nexai_oauth_state";
const SESSION_COOKIE = "ai_enterprise_session";
const ISSUER = "nexai-platform";
const AUDIENCE = "axaliai-enterprise";

function b64url(value) {
  return Buffer.from(value).toString("base64url");
}

function safeEqual(left, right) {
  const a = Buffer.from(String(left));
  const b = Buffer.from(String(right));
  return a.length === b.length && timingSafeEqual(a, b);
}

function sign(value, secret) {
  return createHmac("sha256", secret).update(value).digest("base64url");
}

function encodeSigned(payload, secret) {
  const body = b64url(JSON.stringify(payload));
  return body + "." + sign(body, secret);
}

function decodeSigned(value, secret) {
  if (typeof value !== "string" || value.length > 8192) return null;
  const [body, signature, extra] = value.split(".");
  if (!body || !signature || extra !== undefined || !safeEqual(signature, sign(body, secret))) return null;
  try {
    return JSON.parse(Buffer.from(body, "base64url").toString("utf8"));
  } catch {
    return null;
  }
}

function verifyNexAiAssertion(token, secret) {
  if (typeof token !== "string" || token.length > 16384) throw new Error("invalid_identity_assertion");
  const parts = token.split(".");
  if (parts.length !== 3) throw new Error("invalid_identity_assertion");
  const [headerPart, claimsPart, signature] = parts;
  const expected = sign(headerPart + "." + claimsPart, secret);
  if (!safeEqual(signature, expected)) throw new Error("invalid_identity_signature");

  const header = JSON.parse(Buffer.from(headerPart, "base64url").toString("utf8"));
  const claims = JSON.parse(Buffer.from(claimsPart, "base64url").toString("utf8"));
  const now = Math.floor(Date.now() / 1000);
  if (header?.alg !== "HS256" || header?.typ !== "JWT") throw new Error("invalid_identity_algorithm");
  if (claims?.iss !== ISSUER || claims?.aud !== AUDIENCE) throw new Error("invalid_identity_issuer_or_audience");
  if (!claims?.sub || !claims?.workspace_id || !["owner", "admin", "operator", "viewer"].includes(claims?.role)) {
    throw new Error("invalid_identity_claims");
  }
  if (!Number.isInteger(claims.iat) || !Number.isInteger(claims.exp) ||
      claims.iat > now + 30 || claims.exp <= now || claims.exp <= claims.iat ||
      claims.exp - claims.iat > 3600) {
    throw new Error("identity_assertion_expired");
  }
  return {
    sub: String(claims.sub).slice(0, 128),
    workspace_id: String(claims.workspace_id).slice(0, 128),
    role: claims.role,
    iat: claims.iat,
    exp: claims.exp,
  };
}

export async function GET(request) {
  const url = new URL(request.url);
  const code = url.searchParams.get("code") || "";
  const returnedState = url.searchParams.get("state") || "";
  const oauthError = url.searchParams.get("error");
  const stateCookie = request.cookies.get(STATE_COOKIE)?.value || "";
  const stateSecret = process.env.AI_SESSION_SECRET || "";
  const identitySecret = process.env.NEXAI_AXALIAI_IDENTITY_SECRET || "";
  const clientId = process.env.NEXAI_AXALIAI_OAUTH_CLIENT_ID || "axaliai-enterprise";
  const clientSecret = process.env.NEXAI_AXALIAI_OAUTH_CLIENT_SECRET || "";
  const tokenUrl = (process.env.NEXAI_AXALIAI_TOKEN_URL || "").trim();
  const redirectUri = (process.env.NEXAI_AXALIAI_REDIRECT_URI || "").trim();

  const fail = (reason, status = 400) => {
    const response = NextResponse.json({ ok: false, error: reason }, { status });
    response.cookies.set(STATE_COOKIE, "", { httpOnly: true, secure: process.env.NODE_ENV === "production", sameSite: "lax", path: "/", maxAge: 0 });
    response.headers.set("Cache-Control", "no-store");
    response.headers.set("Referrer-Policy", "no-referrer");
    return response;
  };

  if (oauthError) return fail("nexai_authorization_denied");
  if (!code || !returnedState || !stateCookie) return fail("oauth_callback_parameters_missing");
  if (stateSecret.length < 32 || identitySecret.length < 32 || clientSecret.length < 32 || !tokenUrl || !redirectUri) {
    return fail("nexai_sso_not_configured", 503);
  }

  const pending = decodeSigned(stateCookie, stateSecret);
  const now = Math.floor(Date.now() / 1000);
  if (!pending || typeof pending.state !== "string" || !safeEqual(returnedState, pending.state) ||
      !pending.verifier || !Number.isInteger(pending.created_at) || pending.created_at + 600 < now) {
    return fail("oauth_state_invalid_or_expired");
  }

  let tokenResponse;
  try {
    tokenResponse = await fetch(tokenUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({
        grant_type: "authorization_code",
        client_id: clientId,
        client_secret: clientSecret,
        code,
        redirect_uri: redirectUri,
        code_verifier: pending.verifier,
      }),
      cache: "no-store",
      signal: AbortSignal.timeout(10000),
    });
  } catch {
    return fail("nexai_token_exchange_unavailable", 502);
  }
  if (!tokenResponse.ok) return fail("nexai_token_exchange_rejected", 401);

  const tokenData = await tokenResponse.json().catch(() => null);
  let identity;
  try {
    identity = verifyNexAiAssertion(tokenData?.access_token, identitySecret);
  } catch {
    return fail("nexai_identity_assertion_invalid", 401);
  }

  // AI Enterprise creates its own short-lived session. NexAI's token is never
  // sent to the browser and NexAI's session cookie is never copied or reused.
  const sessionExpires = Math.min(identity.exp, now + 900);
  const session = encodeSigned({
    sub: identity.sub,
    workspace_id: identity.workspace_id,
    role: identity.role,
    iat: now,
    exp: sessionExpires,
  }, stateSecret);

  const response = NextResponse.redirect(new URL("/", request.url));
  const secure = process.env.NODE_ENV === "production";
  response.cookies.set(SESSION_COOKIE, session, {
    httpOnly: true, secure, sameSite: "lax", path: "/", maxAge: Math.max(0, sessionExpires - now),
  });
  response.cookies.set(STATE_COOKIE, "", {
    httpOnly: true, secure, sameSite: "lax", path: "/", maxAge: 0,
  });
  response.headers.set("Cache-Control", "no-store");
  response.headers.set("Referrer-Policy", "no-referrer");
  return response;
}
