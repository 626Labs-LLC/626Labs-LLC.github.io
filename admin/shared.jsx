// Shared content model + helpers for both admin directions.
// Models the JSON that a CI job would bake back into index.html.

const INITIAL_CONTENT = {
  hero: {
    eyebrow: "626 Labs LLC · Fort Worth, TX",
    headline: "Vibe coded.",
    headlineAccent: "Shipped at enterprise grade.",
    subhead:
      "Claude Code plugins for builders who vibe-code fast and still ship for real. Planning, docs, tests, security — with a native Windows/macOS widget for pacing your usage.",
    primaryCta: { label: "See the work", href: "#work" },
    secondaryCta: { label: "Read the thesis", href: "#thinking" },
    meta: [
      { label: "Shipped", value: "3 plugins · 1 widget" },
      { label: "Stack", value: "TypeScript · Swift · Python" },
      { label: "Distribution", value: "Claude Code · macOS · Windows" },
    ],
    chips: [
      { label: "vibe-cartographer", tone: "cyan" },
      { label: "vibe-doc", tone: "magenta" },
      { label: "vibe-test · live", tone: "success" },
      { label: "claude-code", tone: "cyan" },
    ],
  },
  sections: {
    thinking: { enabled: true },
    labRuns: { enabled: true },
    lab: { enabled: true },
    play: { enabled: true },
    about: { enabled: true },
    support: { enabled: true },
    contact: { enabled: true },
  },
  play: {
    eyebrow: "05 · Play",
    headline: "Also, we make games.",
    lead: "A moment with Kevin Bacon. The widget pulls today's birthday actors, you walk a film chain until you find him (or don't).",
    widgets: [
      {
        id: "bacon-widget",
        script: "/widget-bacon-trail/widget.js",
        stylesheet: "/widget-bacon-trail/widget.css",
        initFn: "BaconTrailWidget.init",
        config: { ctaUrl: "#work", ctaLabel: "See the full suite →" },
      },
    ],
  },
  about: {
    eyebrow: "06 · About 626 Labs",
    headline: "New ideas to",
    headlineAccent: "old logic.",
    stack: ["TypeScript", "Swift", "Python", "Claude Code", "React 19", "Fort Worth, TX"],
    paragraphs: [],
    principles: [],
  },
  thinking: {
    eyebrow: "02 · The thesis",
    headline: "The thinking behind it.",
    lead: "",
    quote: "",
    paragraphs: [],
    cta: { label: "", href: "" },
  },
  labRuns: {
    eyebrow: "03 · Behind the scenes",
    headline: "How the lab runs.",
    lead: "",
    frames: [],
    caption: [],
  },
  support: {
    headline: "Keep the lab running.",
    body: "",
    cta: { label: "Sponsor on GitHub", href: "https://github.com/sponsors/estevanhernandez-stack-ed" },
  },
  contact: {
    eyebrow: "07 · Contact",
    headline: "Build something with us.",
    lead: "",
    primaryCta: { label: "", href: "" },
    rows: [],
  },
  products: [
    {
      id: "vibe-cartographer",
      flagship: true,
      title: "Vibe Cartographer",
      tagline: "Vibe coding with a map.",
      description:
        "Eleven slash commands walk you from first idea to shipped app — onboard, scope, PRD, spec, checklist, build, iterate, reflect — and the plugin remembers where you left off.",
      tags: [
        { label: "Flagship", tone: "magenta" },
        { label: "Live", tone: "live" },
        { label: "Claude Code plugin", tone: "cyan" },
      ],
      status: "live",
      repo: "estevanhernandez-stack-ed/vibe-cartographer",
      npm: "@esthernandez/vibe-cartographer",
      install: "/plugin marketplace add estevanhernandez-stack-ed/vibe-cartographer",
      screenshots: [],
    },
    {
      id: "vibe-doc",
      title: "Vibe Doc",
      description:
        "Point it at your codebase and it tells you which docs you're missing — ADRs, runbooks, threat models, specs — then writes them.",
      tags: [
        { label: "Plugin", tone: "cyan" },
        { label: "documentation", tone: "magenta" },
        { label: "Live", tone: "live" },
      ],
      status: "live",
      repo: "estevanhernandez-stack-ed/Vibe-Doc",
      npm: "@esthernandez/vibe-doc",
      install: "/plugin marketplace add estevanhernandez-stack-ed/Vibe-Doc",
      screenshots: [],
    },
    {
      id: "vibe-test",
      title: "Vibe Test",
      description:
        "Reads your vibe-coded app, classifies maturity, generates the tests that actually matter. Catches broken harnesses other tools assume away.",
      tags: [
        { label: "Plugin", tone: "cyan" },
        { label: "tests", tone: "magenta" },
        { label: "Live", tone: "live" },
      ],
      status: "live",
      repo: "estevanhernandez-stack-ed/vibe-plugins",
      npm: "@esthernandez/vibe-test",
      install: "/plugin marketplace add estevanhernandez-stack-ed/vibe-plugins",
      screenshots: [],
    },
    {
      id: "sanduhr",
      title: "Sanduhr für Claude",
      description:
        "Native desktop widget that shows how fast you're burning Claude.ai usage. Burn-rate, pace markers, sparkline trends, five glass themes.",
      tags: [
        { label: "macOS", tone: "cyan" },
        { label: "Windows", tone: "cyan" },
        { label: "native", tone: "magenta" },
        { label: "Live", tone: "live" },
      ],
      status: "live",
      repo: "estevanhernandez-stack-ed/Sanduhr_f-r_Claude",
      npm: null,
      install: null,
      screenshots: [],
    },
    {
      id: "vibe-sec",
      title: "Vibe Sec",
      description:
        "The security gaps AI prototyping leaves behind — leaked secrets, sketchy auth, missing input validation, stale deps. Finds them, files them.",
      tags: [
        { label: "Plugin", tone: "cyan" },
        { label: "security", tone: "magenta" },
        { label: "Coming soon", tone: "wip" },
      ],
      status: "wip",
      repo: "estevanhernandez-stack-ed/vibe-plugins",
      npm: "@esthernandez/vibe-sec",
      install: null,
      screenshots: [],
    },
  ],
  lab: [
    { id: "celestia", title: "Celestia 3", meta: "AI · tarot · astrology", blurb: "NASA-grade Swiss Ephemeris, repaired by hand.", link: "github.com/estevanhernandez-stack-ed/Celestia3", thumb: null },
    { id: "ladder", title: "LADDER", meta: "Local-first · multimodal", blurb: "Educational framework bridging the access gap.", link: "github.com/estevanhernandez-stack-ed/LADDER", thumb: null },
    { id: "anote", title: "Anote That", meta: "Handwriting · OCR", blurb: "AI agent bridging analog notes to digital intelligence.", link: "github.com/estevanhernandez-stack-ed/Anote-That", thumb: null },
  ],
};

// Live data — fetched from npm + GitHub at runtime. See fetchLiveStats.
// Stats map shape (per npm package key):
//   { weekly: number | null, stars: number | null, release: string | null, ok: bool }
// Keys are product.npm values (e.g. "@esthernandez/vibe-cartographer").

// Monorepo release-tag prefixes — release fetch filters to the package's tags.
const RELEASE_TAG_PREFIX = {
  "vibe-test": "vibe-test-v",
  "vibe-sec": "vibe-sec-v",
};

async function fetchNpmWeekly(pkg) {
  try {
    const res = await fetch(`https://api.npmjs.org/downloads/point/last-week/${encodeURIComponent(pkg)}`);
    if (!res.ok) return null;
    const body = await res.json();
    return typeof body.downloads === "number" ? body.downloads : null;
  } catch { return null; }
}

async function fetchRepoMeta(repo, token) {
  try {
    const headers = token
      ? { Authorization: `Bearer ${token}`, Accept: "application/vnd.github+json" }
      : { Accept: "application/vnd.github+json" };
    const res = await fetch(`https://api.github.com/repos/${repo}`, { headers });
    if (!res.ok) return null;
    return await res.json();
  } catch { return null; }
}

async function fetchLatestRelease(repo, token, tagPrefix) {
  try {
    const headers = token
      ? { Authorization: `Bearer ${token}`, Accept: "application/vnd.github+json" }
      : { Accept: "application/vnd.github+json" };
    if (tagPrefix) {
      const res = await fetch(`https://api.github.com/repos/${repo}/releases?per_page=30`, { headers });
      if (!res.ok) return null;
      const arr = await res.json();
      const match = Array.isArray(arr) ? arr.find(r => r.tag_name?.startsWith(tagPrefix)) : null;
      return match?.tag_name || null;
    }
    const res = await fetch(`https://api.github.com/repos/${repo}/releases/latest`, { headers });
    if (!res.ok) return null;
    const body = await res.json();
    return body.tag_name || null;
  } catch { return null; }
}

async function fetchLiveStats(products, token) {
  const stats = {};
  const tasks = [];
  for (const p of products) {
    if (!p.npm) continue;
    stats[p.npm] = { weekly: null, stars: null, release: null, ok: false };
    const task = (async () => {
      const weeklyP = fetchNpmWeekly(p.npm);
      const repoP = p.repo ? fetchRepoMeta(p.repo, token) : Promise.resolve(null);
      const relP = p.repo
        ? fetchLatestRelease(p.repo, token, RELEASE_TAG_PREFIX[p.id])
        : Promise.resolve(null);
      const [weekly, repo, release] = await Promise.all([weeklyP, repoP, relP]);
      stats[p.npm] = {
        weekly,
        stars: repo?.stargazers_count ?? null,
        release,
        ok: true,
      };
    })();
    tasks.push(task);
  }
  await Promise.all(tasks);
  return stats;
}

const TONE_COLORS = {
  cyan: { fg: "#17d4fa", bg: "rgba(23,212,250,.08)", br: "rgba(23,212,250,.32)" },
  magenta: { fg: "#ff5aa3", bg: "rgba(242,47,137,.08)", br: "rgba(242,47,137,.32)" },
  live: { fg: "#2bd99a", bg: "rgba(43,217,154,.08)", br: "rgba(43,217,154,.32)" },
  wip: { fg: "#ffb454", bg: "rgba(255,180,84,.08)", br: "rgba(255,180,84,.32)" },
  success: { fg: "#2bd99a", bg: "rgba(43,217,154,.08)", br: "rgba(43,217,154,.32)" },
};

function Chip({ tone = "cyan", children, size = "sm" }) {
  const c = TONE_COLORS[tone] || TONE_COLORS.cyan;
  const pad = size === "sm" ? "3px 8px" : "5px 11px";
  const fs = size === "sm" ? 10 : 11;
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: 6,
      padding: pad, fontSize: fs, fontFamily: "JetBrains Mono, ui-monospace, monospace",
      letterSpacing: ".08em", textTransform: "uppercase",
      color: c.fg, background: c.bg, border: `1px solid ${c.br}`,
      borderRadius: 999, fontWeight: 500,
    }}>{children}</span>
  );
}

function StatusDot({ status }) {
  const c = status === "live" ? "#2bd99a" : status === "wip" ? "#ffb454" : "#6a849e";
  return <span style={{
    display: "inline-block", width: 7, height: 7, borderRadius: 999,
    background: c, boxShadow: `0 0 8px ${c}`,
  }}/>;
}

// Tiny inline icons (lucide-style)
const Ic = {
  plus: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round"><path d="M12 5v14M5 12h14"/></svg>,
  save: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><path d="M17 21v-8H7v8M7 3v5h8"/></svg>,
  eye: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8S1 12 1 12z"/><circle cx="12" cy="12" r="3"/></svg>,
  image: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="M21 15l-5-5L5 21"/></svg>,
  upload: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M17 8l-5-5-5 5M12 3v12"/></svg>,
  home: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2h-4v-7h-6v7H5a2 2 0 0 1-2-2z"/></svg>,
  grid: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>,
  flask: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"><path d="M10 2v7.31M14 9.3V2M8.5 2h7M14 9.3a6.5 6.5 0 1 1-4 0"/></svg>,
  brain: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"><path d="M12 5a3 3 0 0 0-6 0 3 3 0 0 0-3 3 3 3 0 0 0 1 5.8V17a3 3 0 0 0 6 0M12 5a3 3 0 0 1 6 0 3 3 0 0 1 3 3 3 3 0 0 1-1 5.8V17a3 3 0 0 1-6 0"/></svg>,
  rocket: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"><path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09zM12 15l-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z"/></svg>,
  mail: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="M22 6l-10 7L2 6"/></svg>,
  heart: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"><path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1-1.1a5.5 5.5 0 0 0-7.8 7.8l1 1L12 21l7.8-7.6 1-1a5.5 5.5 0 0 0 0-7.8z"/></svg>,
  trash: <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"><path d="M3 6h18M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/></svg>,
  drag: <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round"><circle cx="9" cy="6" r="1"/><circle cx="9" cy="12" r="1"/><circle cx="9" cy="18" r="1"/><circle cx="15" cy="6" r="1"/><circle cx="15" cy="12" r="1"/><circle cx="15" cy="18" r="1"/></svg>,
  edit: <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"><path d="M12 20h9M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4z"/></svg>,
  chev: <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"><path d="M6 9l6 6 6-6"/></svg>,
  arrowR: <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14M13 5l7 7-7 7"/></svg>,
  sparkle: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"><path d="M12 3l2 6 6 2-6 2-2 6-2-6-6-2 6-2z"/></svg>,
  download: <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"/></svg>,
  star: <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2l3.1 6.3 6.9 1-5 4.9 1.2 6.8L12 17.8l-6.2 3.2L7 14.2 2 9.3l6.9-1z"/></svg>,
  link: <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"><path d="M10 13a5 5 0 0 0 7.5.5l3-3a5 5 0 1 0-7-7l-1.7 1.7M14 11a5 5 0 0 0-7.5-.5l-3 3a5 5 0 1 0 7 7l1.7-1.7"/></svg>,
  activity: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>,
  refresh: <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>,
};

Object.assign(window, { INITIAL_CONTENT, TONE_COLORS, Chip, StatusDot, Ic, fetchLiveStats });
