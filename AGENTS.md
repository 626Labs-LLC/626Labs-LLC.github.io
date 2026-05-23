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

- `python scripts/site.py set-status <product-id> <live|wip>` — flip a product's
  status. Validates before it stands; `--commit` commits on the current branch
  (refuses on main).

## Conventions

- Counts/lists in prose use `{{fact:KEY}}` tokens (see `scripts/site_facts.py`) —
  don't hardcode a number a fact can supply.
- Brand assets in `assets/brand/` are generated; don't hand-edit.
- The doctor (`scripts/site-doctor.py`) is the one validator; every write path —
  human admin, this CLI, and the MCP tool group — funnels through it via CI.

## Roadmap

`add-plugin`, `upload-shot`, `story`, and a general `set` arrive in M2.2 — they
need a format-preserving JSON array/object editor (a naive parse→dump explodes
the hand-formatted content files). The MCP wrapper is M3.
