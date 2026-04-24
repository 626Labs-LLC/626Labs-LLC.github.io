# Contributing

This is a single-maintainer project right now — Estevan at 626Labs LLC. Pull requests are welcome but expect a few days of lag before review.

## Running locally

```sh
cd apps/widget-bacon-trail
npm ci
cp .env.example .env.local   # then paste your TMDB v3 key
npm run dev                  # http://localhost:3003/dev.html
```

## Before you push

Run all three:

```sh
npm run typecheck
npm run test
npm run build
```

CI runs the same trio + a bundle-size gate on every push to `apps/widget-bacon-trail/**`. A build that exceeds 150 KB gz (js) or 20 KB gz (css) fails the gate.

## Code style

- TypeScript strict mode, `noUncheckedIndexedAccess` on. Use optional chaining / explicit guards.
- No Tailwind utility classes inside JSX — all styling lives in [`src/styles/widget.css`](./src/styles/widget.css), scoped under `.bacon-trail-widget`. Keeps the bundle predictable and avoids Tailwind's preflight stomping on any host page.
- No emoji in rendered text. Lucide icons if a glyph is needed.
- 626 Labs palette only — cyan + magenta + semantic success/warning/danger. See [`src/styles/tokens.css`](./src/styles/tokens.css).
- Commit messages follow the hub's convention: `feat(widget): ...`, `fix(widget): ...`, `chore(build): ...`, `docs(widget): ...`.

## Scope guardrails

Things the widget explicitly will not grow into, per [`docs/scope.md`](./docs/scope.md):

- User accounts, anonymous IDs, or any client-side persistence
- Leaderboard reads or writes
- Share-score / social-post generation
- Rewards or signup flows (that's CinePerks territory)
- Multiple themes or per-instance branding

If you want to add something that lands in that list, please open an issue first and let's talk about scope.

## Filing a bug

Include:

1. Browser + version
2. Viewport size
3. Console errors (pasted, not screenshot)
4. Steps to reproduce
5. What you saw vs. what you expected

For security-sensitive reports, see [`SECURITY.md`](./SECURITY.md) instead.
