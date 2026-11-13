# Public Application URL — frontend integration

## Behavior

`lib/public-app-url.mjs` reads `NEXT_PUBLIC_APP_URL` and returns a validated
HTTP(S) origin. It defaults to `http://localhost:3000` for local development.
Credentials, non-HTTP protocols, paths, query strings and fragments are rejected.

`app/layout.js` uses that origin as Next.js `metadataBase` and declares
canonical and Open Graph URLs as relative paths. Next.js therefore resolves
those URLs against the configured Preview origin without hardcoding a
deployment-specific address in application source.

## Verification

Run:

- `npm run test:public-url` — validates defaults, normalization and rejection cases.
- `npm run build` — confirms the Next.js application compiles with the selected environment.

The tests do not contact Vercel or prove that a deployment received the environment
variable. Runtime verification still requires a successful Preview deployment
for the exact branch commit and inspection of its rendered canonical/Open Graph
metadata.

## Security

`NEXT_PUBLIC_APP_URL` is public configuration only. It must never contain
`XP_TOKEN`, API keys, passwords, session tokens or any other secret.
Backend credentials remain server-side.
