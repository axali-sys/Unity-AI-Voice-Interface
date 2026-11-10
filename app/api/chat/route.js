/**
 * Public-site guard for the assistant API.
 *
 * Live chat must remain disabled until a real user session is verified and
 * mapped to an authorized workspace. A server-side service token alone is
 * not an end-user identity and must not be used to expose shared memory.
 */
export async function POST() {
  return Response.json(
    {
      ok: false,
      error: "assistant_authentication_not_configured",
      message:
        "ƎllE chat is not available on this public preview. Sign-in and workspace authorization must be configured before live chat is enabled.",
    },
    { status: 503 }
  );
}
