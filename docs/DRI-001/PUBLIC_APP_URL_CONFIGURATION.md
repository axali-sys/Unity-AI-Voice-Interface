# Public Application URL Configuration

## Variable

`NEXT_PUBLIC_APP_URL` is the public origin of the frontend application.
Because it has the `NEXT_PUBLIC_` prefix, Next.js can expose its value to
browser code. It must contain only a public URL; never put credentials,
session tokens, API keys, or backend secrets in it.

## Isolated DRI-001 Preview

A branch-scoped Vercel environment variable has been configured:

- Project: `unity-ai-voice-interface-ua47`
- Key: `NEXT_PUBLIC_APP_URL`
- Value: `https://unity-ai-voice-interface-ua47-git-dri-00-b9ad9a-azalibol74-8215.vercel.app`
- Target: Preview only
- Git branch: `dri-001/xparallel-master-blueprint`
- Type: plain/public configuration
- Production: not configured or changed

The value uses the branch deployment alias returned by Vercel for this
project. It is preferable to a one-off deployment URL because the alias is
intended to follow deployments for this branch. The exact current commit must
still receive its own successful Preview deployment before runtime behavior
can be considered verified.

## Local development

The committed `.env.example` uses `http://localhost:3000` as the local
development default. Copy it to an ignored local env file and replace values
only when running against a different host.

## Related settings

- `NEXT_PUBLIC_API_BASE_URL` and `NEXT_PUBLIC_XP_API_URL` are endpoint
  addresses, not the frontend origin.
- `XP_API_URL` is server-side and should remain private to server code.
- `XP_TOKEN` is a secret and must never use a `NEXT_PUBLIC_` prefix.

No Production environment variable, custom domain, DNS record, deployment
target, or production release was changed by this configuration.
