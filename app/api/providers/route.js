export async function GET() {
  const backendUrl =
    process.env.XP_API_URL ||
    process.env.NEXT_PUBLIC_XP_API_URL ||
    "http://localhost:8787";
  const token = process.env.XP_TOKEN;

  if (!token) {
    return Response.json(
      {
        error: "xparallel_backend_token_not_configured",
        providers: [],
        status_note: "Configure the backend connection to inspect provider configuration.",
      },
      { status: 503 }
    );
  }

  try {
    const response = await fetch(`${backendUrl}/providers`, {
      method: "GET",
      headers: { Authorization: `Bearer ${token}` },
      cache: "no-store",
    });
    const data = await response.json().catch(() => ({}));
    return Response.json(data, { status: response.status });
  } catch {
    return Response.json(
      {
        error: "xparallel_provider_directory_unreachable",
        providers: [],
        status_note: "The provider directory could not be reached.",
      },
      { status: 502 }
    );
  }
}
