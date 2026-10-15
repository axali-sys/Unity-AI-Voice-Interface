# AXALIAI Roaming Access

AXALIAI can be opened from the hosting provider's HTTPS URL; it does not require `axaliai.com` to be the entry point.

## Web access
Open `/axaliai.html` on the active Vercel or other HTTPS host. The existing XParallel console remains at `/index.html`.

## Install on Android
1. Open the HTTPS `/axaliai.html` URL in Chrome.
2. Select **Install app** if the browser offers it, or open the browser menu and select **Install app** / **Add to Home screen**.
3. Launch AXALIAI from the home screen.

This is an installable Progressive Web App (PWA), not a signed APK. A native Android package would require a separate Android build and signing/release process.

## Offline and API behavior
The service worker caches only the AXALIAI shell and its manifest/icon. It deliberately does not cache chat, memory, conversation, or API responses. The shell may open offline, but live AI, remote memory, and synchronized history require connectivity.

The existing interface still uses the configured XParallel API and its bearer token. Do not put a permanent server-wide token into public frontend code. Use a per-user or otherwise appropriately scoped credential. Configure the backend's allowed CORS origins for the exact HTTPS hosting origin, including the active `.vercel.app` host if applicable, via `XP_PUBLIC_ORIGINS`. Keep `XP_TOKEN` and `XP_EXECUTION_APPROVAL_TOKEN` in the backend's secret manager, never in the repository.

## Verification checklist
- [ ] HTTPS deployment serves `/axaliai.html`, `/manifest.webmanifest`, `/axaliai-icon.svg`, and `/sw.js`.
- [ ] Browser reports a valid manifest and active service worker.
- [ ] Install prompt / browser menu installs the app on Android.
- [ ] API health check succeeds with the intended backend URL and credential.
- [ ] AI chat returns a real provider response.
- [ ] Memory save/search works against the intended persistent store.
- [ ] Browser network panel shows no API response cached by the service worker.

A Git commit or successful static asset check is not proof that deployment, AI provider calls, or persistence are live.
