# Website verification checklist

## Automated
- GitHub Actions runs the Next.js production build on pull requests and pushes to the website branch.
- Existing Python compilation and test workflow remains independent and must continue passing.

## Manual preview checks
- [ ] Home page loads at desktop and mobile widths.
- [ ] Every section anchor resolves and keyboard navigation remains usable.
- [ ] `/assistant` loads and preserves the prior assistant experience.
- [ ] `/api/chat` rejects an empty query with HTTP 400.
- [ ] `/api/chat` uses only server-side XP_TOKEN; no secret is shipped to the browser bundle.
- [ ] Live XParallel request is tested only in a configured preview environment.
- [ ] Demo fallback is clearly understood as demo behavior, not live AI availability.
- [ ] Contact route is not published until a real monitored inbox is configured.
- [ ] Metadata, accessibility, contrast, focus states and external links are reviewed.

## Release gates
A green CI build is necessary but not sufficient for release. Require a preview review and explicit authorization before merging, connecting axaliai.com DNS, or deploying production.
