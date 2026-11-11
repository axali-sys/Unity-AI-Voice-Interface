import { createHmac, timingSafeEqual } from "node:crypto";

export const runtime = "nodejs";

const SESSION_COOKIE = "ai_enterprise_session";

function verifySigned(value, secret) {
  if (typeof value !== "string" || value.length > 8192 || secret.length < 32) return null;
  const [body, signature, extra] = value.split(".");
  if (!body || !signature || extra !== undefined) return null;
  const expected = createHmac("sha256", secret).update(body).digest("base64url");
  const a = Buffer.from(signature);
  const b = Buffer.from(expected);
  if (a.length !== b.length || !timingSafeEqual(a, b)) return null;
  try {
    const session = JSON.parse(Buffer.from(body, "base64url").toString("utf8"));
    const now = Math.floor(Date.now() / 1000);
    if (!session?.sub || !session?.workspace_id ||
        !["owner", "admin", "operator", "viewer"].includes(session?.role) ||
        !Number.isInteger(session.exp) || session.exp <= now ||
        !Number.isInteger(session.iat) || session.iat > now + 30) return null;
    return session;
  } catch {
    return null;
  }
}

export async function GET(request) {
  const secret = process.env.AI_SESSION_SECRET || "";
  const value = request.cookies.get(SESSION_COOKIE)?.value || "";
  const session = verifySigned(value, secret);
  const headers = { "Cache-Control": "no-store", "Vary": "Cookie" };
  if (!session) return Response.json({ authenticated: false }, { status: 401, headers });
  return Response.json({
    authenticated: true,
    user: { id: session.sub, workspace_id: session.workspace_id, role: session.role },
    expires_at: session.exp,
  }, { headers });
}

export async function DELETE() {
  const secure = process.env.NODE_ENV === "production";
  const response = Response.json({ authenticated: false }, {
    headers: { "Cache-Control": "no-store" },
  });
  response.headers.append("Set-Cookie", `${SESSION_COOKIE}=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0${secure ? "; Secure" : ""}`);
  return response;
}
