# Managing this site as an agent

`scripts/site.py` is the agent-facing management surface — the equivalent of the
human admin dashboard. Prefer it over hand-editing content JSON: mutation verbs
validate (render + health doctor) and auto-revert if an edit would ship drift.

## Read

- `python scripts/site.py facts` — derived facts (plugin counts, names, etc.)
- `python scripts/site.py get <section>` — a section of content/site.json
- `python scripts/site.py doctor [--check]` — health checkup
- `python scripts/site.py render` — re-render index.html + plugin pages
- `python scripts/site.py ops` — recent CI run status (needs `gh`)

## Write (guarded)

Each validates (render + doctor) before it stands and auto-reverts on failure;
`--commit` commits on the current branch (refuses on main).

- `python scripts/site.py set-status <product-id> <live|wip>` — flip a product's status.
- `python scripts/site.py set-product <id> <field> <value>` — set a product string field.
- `python scripts/site.py add-plugin <id> --title T [--tagline TG] [--claude-code]` — append a skeleton product (status wip).
- `python scripts/site.py upload-shot <product-id> <image>` — copy + name + register a screenshot (max 6).
- `python scripts/site.py story new <slug> --title T` / `story list` — Field Note scaffolding (ships `draft: true`).

## Conventions

- Counts/lists in prose use `{{fact:KEY}}` tokens (see `scripts/site_facts.py`) —
  don't hardcode a number a fact can supply.
- Brand assets in `assets/brand/` are generated; don't hand-edit.
- The doctor (`scripts/site-doctor.py`) is the one validator; every write path —
  human admin, this CLI, and the MCP tool group — funnels through it via CI.

## Roadmap

The MCP wrapper (M3) exposes these same verbs as a `manage_site_content` tool
group on the Firebase server, so MCP-aware agents get native tool-calling.
