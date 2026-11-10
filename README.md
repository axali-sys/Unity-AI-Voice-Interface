# Axaliai — General AI Infrastructure

This repository contains the Axaliai web experience and the existing AI assistant / XParallel integration work.

## Website
- `/` — Axaliai public infrastructure website.
- `/assistant` — preserved assistant workspace UI.
- `/api/chat` — existing server-side chat proxy; backend configuration is environment-specific.

## Run locally
1. Install dependencies: `npm install`
2. Start the app: `npm run dev`
3. Visit `http://localhost:3000`

## Existing assistant backend
The assistant continues to use the existing `/api/chat` route. Configure `XP_API_URL` and `XP_TOKEN` only in the server environment. Never expose bearer credentials in browser code.

## Website scope
The public site explains Axaliai's infrastructure direction, architecture layers, independent product identities, developer platform, API publication policy, documentation, research and security principles. It intentionally distinguishes architecture concepts from verified operational services.

## Development branch
Website work is on `feat/axaliai-infrastructure-website`. The default `main` branch and production services are not changed by this work.

## Hosting
Squarespace remains the domain/DNS management surface. Vercel + Next.js is the proposed website host, pending preview review and explicit authorization. No DNS change, production deployment, paid service commitment or domain transfer is included.

## Verification
A successful repository edit is not a build or deployment verification. Run:
- `npm install`
- `npm run build`
- manual checks for mobile/desktop navigation, `/assistant`, and `/api/chat` with configured preview credentials
- accessibility, link and security review

Do not describe API endpoints as public services until their method, schema, authentication, limits and runtime availability have been verified.
