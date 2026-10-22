# Axaliai Assistant starter

This repo now includes a polished AI assistant UI that is designed to sit on top of the XParallel backend.

## Run locally

1. Install dependencies:
   ```bash
   npm install
   ```

2. Start the dev server:
   ```bash
   npm run dev
   ```

3. Open the app:
   ```bash
   http://localhost:3000
   ```

## Connect to the live backend

Set these environment variables before running the app:

```bash
export XP_API_URL=http://localhost:8787
export XP_TOKEN=your-xparallel-token
```

The UI calls `/api/chat`, which proxies to the backend. If no backend is configured, the app falls back to a local demo response.

## Frontend stack

- Next.js
- React
- Tailwind-style custom CSS
- XParallel-compatible API proxy

## Notes

This is a starter Lovable-style assistant interface. It is intentionally clean and launch-ready visually, while keeping the underlying XParallel logic in the existing repo.
