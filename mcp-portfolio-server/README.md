# mcp-portfolio-server

A local **stdio** MCP server that exposes 626 Labs portfolio content to AI
assistants (Claude Desktop, Cursor, Claude Code, etc.).

It is **integrated with the live site**, not a standalone content store:

| Portfolio concept | Where it actually lives |
|---|---|
| Projects | `content/site.json` `products` array (rendered into the live cards) |
| Blog posts | `content/stories/*.md` (frontmatter-bearing Field Notes) |
| Resume | `content/resume.md` |

Mutations go through the **guarded site CLI** (`scripts/site.py`) — the same
edit path local agents and the human admin use — so changes validate, render,
and can't ship drift. The server never re-implements those edits.

## What it exposes

**Resource**
- `portfolio://about/resume` — reads `content/resume.md`.

**Tools**
- `list_projects` — products from `content/site.json` (id, title, tagline, status, claudeCode).
- `create_project { id, title, tagline?, claudeCode? }` — appends a guarded skeleton product (via `site.py add-plugin`); left in the working tree for review/commit.
- `list_blog_posts` — Field Notes from `content/stories/*.md` (title, published, draft, file).
- `create_blog_post { slug, title }` — scaffolds a draft Field Note (via `site.py story new`); ships `draft: true` so it stays unpublished until you fill it in.

## Setup

```bash
cd mcp-portfolio-server
npm install
npm run build      # compiles src/ -> dist/
```

For development without a build step: `npm run dev` (tsx watch), or
`npm run inspect` to open the MCP Inspector.

## IDE config

The server needs the **absolute path to the built Node script** and (optionally)
`PORTFOLIO_REPO_ROOT`. The repo root is auto-derived as two levels up from the
script, so the env var is only needed if you run the script from elsewhere.
`PYTHON_BIN` overrides the Python used for the guarded CLI (default `python`).

Paths below are for this machine — adjust if the repo moves.

### Cursor (`.cursor/mcp.json`, or copy this file's `.mcp.json`)

```json
{
  "mcpServers": {
    "portfolio": {
      "command": "node",
      "args": ["C:/Users/estev/Projects/626labs-hub/mcp-portfolio-server/dist/index.js"],
      "env": { "PORTFOLIO_REPO_ROOT": "C:/Users/estev/Projects/626labs-hub" }
    }
  }
}
```

### Claude Desktop (`%APPDATA%/Claude/claude_desktop_config.json`)

```json
{
  "mcpServers": {
    "portfolio": {
      "command": "node",
      "args": ["C:/Users/estev/Projects/626labs-hub/mcp-portfolio-server/dist/index.js"],
      "env": { "PORTFOLIO_REPO_ROOT": "C:/Users/estev/Projects/626labs-hub" }
    }
  }
}
```

Restart the client after editing its config. The server logs its repo root to
stderr on startup; stdout is reserved for the JSON-RPC channel.

## Notes

- `node_modules/` and `dist/` are gitignored — run `npm install && npm run build`
  after cloning.
- Because mutations shell out to `scripts/site.py`, Python must be on PATH (or
  set `PYTHON_BIN`). The CLI leaves changes in the working tree; review and
  commit them through your normal flow.
