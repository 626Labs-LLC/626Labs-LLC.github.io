#!/usr/bin/env node
/**
 * mcp-portfolio-server — a local stdio MCP server exposing 626 Labs portfolio
 * content (resume, projects, Field Notes) to AI assistants.
 *
 * Integrated, not standalone. In this repo:
 *   - "projects" are the products in content/site.json (rendered into live cards)
 *   - "blog posts" are content/stories/*.md (frontmatter-bearing Field Notes)
 *   - the resume is content/resume.md
 *
 * Mutations go through the guarded site CLI (scripts/site.py): the same edit
 * implementation local agents and the human admin use, so changes validate +
 * render and can't ship drift. The server never re-implements those edits.
 */
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { promises as fs } from "node:fs";
import { spawn } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
// The server lives at <repo>/mcp-portfolio-server/{src|dist}/index.* — so the
// repo root is two levels up. Overridable for unusual checkouts.
const REPO_ROOT = process.env.PORTFOLIO_REPO_ROOT
  ? path.resolve(process.env.PORTFOLIO_REPO_ROOT)
  : path.resolve(__dirname, "..", "..");

const SITE_JSON = path.join(REPO_ROOT, "content", "site.json");
const STORIES_DIR = path.join(REPO_ROOT, "content", "stories");
const RESUME_MD = path.join(REPO_ROOT, "content", "resume.md");
const SITE_PY = path.join(REPO_ROOT, "scripts", "site.py");
const PYTHON = process.env.PYTHON_BIN ?? "python";

/** Run the guarded site CLI and capture combined output. */
function runSiteCli(args: string[]): Promise<{ code: number; out: string }> {
  return new Promise((resolve) => {
    const child = spawn(PYTHON, [SITE_PY, ...args], { cwd: REPO_ROOT });
    let out = "";
    child.stdout.on("data", (d) => (out += d.toString()));
    child.stderr.on("data", (d) => (out += d.toString()));
    child.on("close", (code) => resolve({ code: code ?? 1, out }));
    child.on("error", (e) => resolve({ code: 1, out: String(e) }));
  });
}

/** Parse a ---fenced YAML-subset frontmatter block (key: value lines). */
function parseFrontmatter(text: string): Record<string, string> {
  const fields: Record<string, string> = {};
  const m = text.match(/^---\r?\n([\s\S]*?)\r?\n---/);
  if (!m) return fields;
  for (const line of m[1].split(/\r?\n/)) {
    const kv = line.match(/^([A-Za-z0-9_]+):\s*(.*)$/);
    if (!kv) continue;
    let v = kv[2].trim();
    if (
      (v.startsWith('"') && v.endsWith('"')) ||
      (v.startsWith("'") && v.endsWith("'"))
    ) {
      v = v.slice(1, -1);
    }
    fields[kv[1]] = v;
  }
  return fields;
}

const server = new McpServer({ name: "portfolio", version: "1.0.0" });

// ── Resource: resume ────────────────────────────────────────────────────────
server.resource(
  "resume",
  "portfolio://about/resume",
  { description: "Este's resume (content/resume.md)", mimeType: "text/markdown" },
  async (uri) => {
    let text: string;
    try {
      text = await fs.readFile(RESUME_MD, "utf-8");
    } catch {
      text = "# Resume\n\n(content/resume.md not found — scaffold it.)";
    }
    return {
      contents: [{ uri: uri.href, mimeType: "text/markdown", text }],
    };
  }
);

// ── Tool: list_projects ──────────────────────────────────────────────────────
server.tool(
  "list_projects",
  "List portfolio projects — the products in content/site.json — with id, title, tagline, status, and whether each is a Claude Code plugin.",
  {},
  async () => {
    const data = JSON.parse(await fs.readFile(SITE_JSON, "utf-8"));
    const projects = (data.products ?? []).map((p: Record<string, unknown>) => ({
      id: p.id,
      title: p.title,
      tagline: p.tagline,
      status: p.status,
      claudeCode: p.claudeCode === true,
    }));
    return {
      content: [{ type: "text" as const, text: JSON.stringify(projects, null, 2) }],
    };
  }
);

// ── Tool: create_project ─────────────────────────────────────────────────────
server.tool(
  "create_project",
  "Create a new project by appending a guarded skeleton product to content/site.json via the site CLI (validates + renders; left in the working tree for review/commit).",
  {
    id: z.string().describe("kebab-case product id, e.g. vibe-foo"),
    title: z.string().describe("Display title"),
    tagline: z.string().optional().describe("One-line tagline"),
    claudeCode: z.boolean().optional().describe("Is this a Claude Code plugin?"),
  },
  async ({ id, title, tagline, claudeCode }) => {
    const args = ["add-plugin", id, "--title", title];
    if (tagline) args.push("--tagline", tagline);
    if (claudeCode) args.push("--claude-code");
    const { code, out } = await runSiteCli(args);
    return {
      content: [{ type: "text" as const, text: out || "(no output)" }],
      isError: code !== 0,
    };
  }
);

// ── Tool: list_blog_posts ────────────────────────────────────────────────────
server.tool(
  "list_blog_posts",
  "List blog posts / Field Notes (content/stories/*.md) with title, published date, draft flag, and filename.",
  {},
  async () => {
    let files: string[] = [];
    try {
      files = (await fs.readdir(STORIES_DIR)).filter((f) => f.endsWith(".md"));
    } catch {
      /* no stories dir yet */
    }
    const posts = [];
    for (const f of files.sort()) {
      const fm = parseFrontmatter(
        await fs.readFile(path.join(STORIES_DIR, f), "utf-8")
      );
      posts.push({
        file: f,
        title: fm.title ?? "",
        published: fm.published ?? "",
        draft: fm.draft === "true",
      });
    }
    return {
      content: [{ type: "text" as const, text: JSON.stringify(posts, null, 2) }],
    };
  }
);

// ── Tool: create_blog_post ───────────────────────────────────────────────────
server.tool(
  "create_blog_post",
  "Create a new blog post / Field Note draft (content/stories/<slug>.md) via the site CLI. Ships draft: true — stays unpublished until you fill it in and flip the flag.",
  {
    slug: z.string().describe("kebab-case slug (becomes the filename)"),
    title: z.string().describe("Post title"),
  },
  async ({ slug, title }) => {
    const { code, out } = await runSiteCli(["story", "new", slug, "--title", title]);
    return {
      content: [{ type: "text" as const, text: out || "(no output)" }],
      isError: code !== 0,
    };
  }
);

const transport = new StdioServerTransport();
await server.connect(transport);
// Logs MUST go to stderr — stdout is the JSON-RPC channel.
console.error(`mcp-portfolio-server running on stdio (repo root: ${REPO_ROOT})`);
