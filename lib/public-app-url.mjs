const LOCAL_APP_URL = "http://localhost:3000";

/**
 * Return a safe canonical origin for the frontend.
 * NEXT_PUBLIC_APP_URL is public configuration, never a credential.
 */
export function getPublicAppUrl(value = process.env.NEXT_PUBLIC_APP_URL) {
  const candidate = (value || LOCAL_APP_URL).trim();
  let parsed;

  try {
    parsed = new URL(candidate);
  } catch {
    throw new Error("NEXT_PUBLIC_APP_URL must be an absolute HTTP(S) URL");
  }

  if (!["http:", "https:"].includes(parsed.protocol)) {
    throw new Error("NEXT_PUBLIC_APP_URL must use HTTP or HTTPS");
  }
  if (parsed.username || parsed.password || parsed.search || parsed.hash) {
    throw new Error("NEXT_PUBLIC_APP_URL must be a public origin without credentials, query, or fragment");
  }
  if (parsed.pathname !== "/") {
    throw new Error("NEXT_PUBLIC_APP_URL must be an origin, not a path");
  }

  return parsed.origin;
}
