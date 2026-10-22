export async function GET() {
  const backendUrl = process.env.XP_API_URL || process.env.NEXT_PUBLIC_XP_API_URL || "http://localhost:8787";

  try {
    const response = await fetch(`${backendUrl}/health`, { cache: "no-store" });
    const data = await response.json().catch(() => ({}));

    return Response.json({
      ok: response.ok,
      backend: backendUrl,
      status: data.status || "unknown",
      message: response.ok ? "Connected" : data.error || "Backend not reachable",
    });
  } catch (error) {
    return Response.json(
      {
        ok: false,
        backend: backendUrl,
        status: "offline",
        message: "The backend is not running yet. Start the XParallel API on port 8787.",
      },
      { status: 200 }
    );
  }
}
