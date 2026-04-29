// 626 Labs admin — Direction A (Control Room), full build.
// Dark agent-OS palette, operable forms, live state, Cmd-K palette, unsaved guard,
// drag-drop + paste screenshots with crop affordance, full-screen preview, shortcut help.

const A = {
  bg: "#07090d", panel: "#0c1016", panel2: "#10151d", panel3: "#151b25",
  line: "rgba(255,255,255,.06)", line2: "rgba(255,255,255,.10)", line3: "rgba(255,255,255,.16)",
  text: "#e7edf5", dim: "#8a99ae", dim2: "#5b6b82",
  cyan: "#17d4fa", magenta: "#ff5aa3", green: "#2bd99a", amber: "#ffb454", danger: "#ff6b6b",
};

// ─────────────────────────────────────────────────────────────
// Top-level app
// ─────────────────────────────────────────────────────────────
function AdminApp({ token, login, onSignOut }) {
  const [content, setContent] = React.useState(null);
  const [original, setOriginal] = React.useState(null);
  const [contentSha, setContentSha] = React.useState(null);
  const [loading, setLoading] = React.useState(true);
  const [loadError, setLoadError] = React.useState(null);
  const [saving, setSaving] = React.useState(false);
  const [reloadTick, setReloadTick] = React.useState(0);
  const [liveStats, setLiveStats] = React.useState({});
  const [nav, setNav] = React.useState("home");
  const [selProduct, setSelProduct] = React.useState("vibe-cartographer");
  const [palette, setPalette] = React.useState(false);
  const [preview, setPreview] = React.useState(false);
  const [cheatsheet, setCheatsheet] = React.useState(false);
  const [guard, setGuard] = React.useState(null); // pending nav target
  const [toast, setToast] = React.useState(null);

  // Load content/site.json from GitHub on mount (and on reload).
  React.useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setLoadError(null);
    (async () => {
      try {
        const { content: c, sha } = await fetchSiteJson(token);
        if (cancelled) return;
        setContent(c);
        setOriginal(c);
        setContentSha(sha);
        setLoading(false);
        if (c.products?.length && !c.products.find(p => p.id === selProduct)) {
          setSelProduct(c.products[0].id);
        }
      } catch (ex) {
        if (cancelled) return;
        setLoadError(ex.message || "Failed to load content/site.json");
        setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [token, reloadTick]);

  // Fetch real npm + GitHub stats whenever products change.
  React.useEffect(() => {
    if (!content?.products?.length) return;
    let cancelled = false;
    (async () => {
      const stats = await fetchLiveStats(content.products, token);
      if (!cancelled) setLiveStats(stats);
    })();
    return () => { cancelled = true; };
  }, [content?.products, token]);

  const dirty = React.useMemo(() => {
    if (!content || !original) return false;
    return JSON.stringify(content) !== JSON.stringify(original);
  }, [content, original]);

  // Edit helpers
  const updateProduct = (id, patch) => setContent(c => ({ ...c, products: c.products.map(p => p.id === id ? { ...p, ...patch } : p) }));
  const addProduct = () => {
    const id = `new-${Date.now().toString(36)}`;
    setContent(c => ({ ...c, products: [...c.products, { id, title: "New project", tagline: "", description: "", tags: [], status: "wip", repo: "", npm: "", install: "", screenshots: [] }] }));
    setSelProduct(id);
    setNav("products");
  };
  const deleteProduct = (id) => setContent(c => ({ ...c, products: c.products.filter(p => p.id !== id) }));

  // Guarded nav
  const safeNav = (target) => {
    if (dirty && target !== nav) setGuard(target);
    else setNav(target);
  };

  const showToast = React.useCallback((msg, tone = "cyan", duration = 3500) => {
    setToast({ msg, tone });
    if (duration > 0) setTimeout(() => setToast(null), duration);
  }, []);

  const save = async () => {
    if (!dirty || saving || !content) return;
    setSaving(true);
    try {
      const msg = "admin: update content/site.json\n\nfrom: 626labs.dev/admin-dashboard.html";
      const { sha } = await writeSiteJson(token, content, contentSha, msg);
      setContentSha(sha);
      setOriginal(content);
      showToast("Saved. Pages will redeploy shortly.", "green", 3500);
    } catch (ex) {
      showToast(`Save failed: ${ex.message}`, "red", 6000);
    } finally {
      setSaving(false);
    }
  };
  const discard = () => setContent(original);

  // Keyboard
  React.useEffect(() => {
    const onKey = (e) => {
      const mod = e.metaKey || e.ctrlKey;
      if (mod && e.key.toLowerCase() === "k") { e.preventDefault(); setPalette(p => !p); }
      else if (mod && e.key.toLowerCase() === "s") { e.preventDefault(); if (dirty) save(); }
      else if (mod && e.key.toLowerCase() === "p") { e.preventDefault(); setPreview(true); }
      else if (e.key === "?" && !e.target.matches?.("input, textarea")) { e.preventDefault(); setCheatsheet(true); }
      else if (e.key === "Escape") { setPalette(false); setPreview(false); setCheatsheet(false); setGuard(null); }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [dirty, content, saving]);

  if (loading) return <LoadingScreen label="Fetching content/site.json…"/>;
  if (loadError) return <LoadError error={loadError} onRetry={() => setReloadTick(t => t + 1)} onSignOut={onSignOut}/>;
  if (!content) return null;

  return (
    <div style={{
      width: "100vw", height: "100vh", background: A.bg, color: A.text,
      fontFamily: "Inter, system-ui, sans-serif", fontSize: 13,
      display: "grid", gridTemplateColumns: "240px 1fr 380px",
      gridTemplateRows: "52px 1fr",
      overflow: "hidden",
    }}>
      <TopBar dirty={dirty} saving={saving} login={login} onSave={save} onDiscard={discard} onPreview={()=>setPreview(true)} onPalette={()=>setPalette(true)} onHelp={()=>setCheatsheet(true)} onSignOut={onSignOut}/>
      <Sidebar nav={nav} onNav={safeNav} content={content} token={token}/>

      <div style={{ overflow: "auto", background: A.bg, position: "relative" }}>
        {nav === "home" && <HomeView content={content} liveStats={liveStats} onNav={safeNav} onAddProduct={addProduct} onSelect={(id)=>{setSelProduct(id); safeNav("products");}}/>}
        {nav === "hero" && <HeroView hero={content.hero} onChange={h => setContent(c => ({...c, hero: h}))}/>}
        {nav === "products" && <ProductsView products={content.products} liveStats={liveStats} selectedId={selProduct} onSelect={setSelProduct} onUpdate={updateProduct} onAdd={addProduct} onDelete={deleteProduct} token={token} onToast={showToast}/>}
        {nav === "lab" && <LabView lab={content.lab} onChange={l => setContent(c => ({...c, lab: l}))}/>}
        {nav === "play" && <PlayView play={content.play || {}} onChange={p => setContent(c => ({...c, play: p}))}/>}
        {nav === "about" && <AboutView about={content.about || {}} onChange={a => setContent(c => ({...c, about: a}))}/>}
        {nav === "thinking" && <ThinkingView thinking={content.thinking || {}} onChange={t => setContent(c => ({...c, thinking: t}))}/>}
        {nav === "labRuns" && <LabRunsView labRuns={content.labRuns || {}} onChange={lr => setContent(c => ({...c, labRuns: lr}))} token={token} onToast={showToast}/>}
        {nav === "support" && <SupportView support={content.support || {}} onChange={s => setContent(c => ({...c, support: s}))}/>}
        {nav === "contact" && <ContactView contact={content.contact || {}} onChange={ct => setContent(c => ({...c, contact: ct}))}/>}
        {nav === "sections" && <SectionsView sections={content.sections} onChange={s => setContent(c => ({...c, sections: s}))}/>}
        {nav === "stories" && <StoriesView token={token} onToast={showToast}/>}
        {nav === "ops" && <OpsView token={token}/>}
        {nav === "analytics" && <AnalyticsView token={token}/>}
      </div>

      <RightRail content={content} liveStats={liveStats} nav={nav} selectedId={selProduct} dirty={dirty} original={original} onPreview={()=>setPreview(true)} onSave={save}/>

      {palette && <CommandPalette close={()=>setPalette(false)} onNav={(n)=>{setPalette(false); safeNav(n);}} onPreview={()=>{setPalette(false); setPreview(true);}} onAddProduct={()=>{setPalette(false); addProduct();}} products={content.products} onSelectProduct={(id)=>{setPalette(false); setSelProduct(id); safeNav("products");}}/>}
      {preview && <PreviewOverlay content={content} close={()=>setPreview(false)}/>}
      {cheatsheet && <CheatsheetOverlay close={()=>setCheatsheet(false)}/>}
      {guard && <GuardDialog target={guard} onDiscard={()=>{discard(); setNav(guard); setGuard(null);}} onSave={()=>{save(); setNav(guard); setGuard(null);}} onCancel={()=>setGuard(null)}/>}
      {toast && <Toast msg={toast.msg} tone={toast.tone}/>}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// Top bar / sidebar / buttons
// ─────────────────────────────────────────────────────────────
function TopBar({ dirty, saving, login, onSave, onDiscard, onPreview, onPalette, onHelp, onSignOut }) {
  return (
    <div style={{
      gridColumn: "1 / -1",
      display: "flex", alignItems: "center", gap: 14, padding: "0 18px",
      borderBottom: `1px solid ${A.line}`, background: A.panel,
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <div style={{ width: 26, height: 26, borderRadius: 6, background: "linear-gradient(135deg,#17d4fa,#ff5aa3)", display: "grid", placeItems: "center", color: A.bg, fontSize: 11, fontWeight: 700, fontFamily: "JetBrains Mono, monospace" }}>626</div>
        <div style={{ fontSize: 12, letterSpacing: ".04em", fontWeight: 600 }}>626labs.dev<span style={{ color: A.dim2, fontWeight: 400 }}> / admin</span></div>
      </div>
      <div style={{ width: 1, height: 22, background: A.line2 }}/>
      <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 11, color: A.dim, display: "flex", alignItems: "center", gap: 8 }}>
        <span style={{ color: A.cyan }}>●</span>
        <span>content/site.json</span>
        <span style={{ color: A.dim2 }}>main</span>
      </div>
      <div style={{ flex: 1 }}/>

      <button onClick={onPalette} style={{
        display: "flex", alignItems: "center", gap: 8, padding: "6px 10px 6px 12px",
        background: A.panel2, border: `1px solid ${A.line2}`, borderRadius: 6,
        color: A.dim, fontSize: 11.5, cursor: "pointer",
      }}>
        Jump to…
        <span style={{ padding: "2px 5px", background: A.panel3, borderRadius: 3, fontFamily: "JetBrains Mono, monospace", fontSize: 10, color: A.dim2 }}>⌘K</span>
      </button>

      <div style={{ display: "flex", alignItems: "center", gap: 10, fontSize: 11 }}>
        <span style={{ display: "inline-block", width: 6, height: 6, borderRadius: 99, background: dirty ? A.amber : A.green, boxShadow: `0 0 8px ${dirty ? A.amber : A.green}` }}/>
        <span style={{ color: A.dim }}>{dirty ? "Unsaved changes" : "All saved"}</span>
      </div>

      {dirty && <Btn ghost onClick={onDiscard} size="sm">Discard</Btn>}
      <Btn ghost onClick={onPreview}><span style={{display:"inline-flex",alignItems:"center",gap:6}}>{Ic.eye} Preview</span></Btn>
      <Btn primary onClick={onSave} disabled={!dirty || saving}><span style={{display:"inline-flex",alignItems:"center",gap:6}}>{Ic.save} {saving ? "Saving…" : "Save & deploy"}</span></Btn>
      <button onClick={onHelp} title="Keyboard shortcuts" style={{ background: "transparent", border: "none", color: A.dim2, cursor: "pointer", padding: 4, fontSize: 14, fontFamily: "JetBrains Mono, monospace" }}>?</button>
      {login && (
        <div style={{ display: "flex", alignItems: "center", gap: 8, paddingLeft: 10, borderLeft: `1px solid ${A.line2}` }}>
          <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 11, color: A.dim }}>@{login}</span>
          <button onClick={onSignOut} title="Sign out" style={{ background: "transparent", border: "none", color: A.dim2, cursor: "pointer", padding: "2px 4px", fontSize: 10.5, fontFamily: "JetBrains Mono, monospace", textDecoration: "underline", letterSpacing: ".04em" }}>sign out</button>
        </div>
      )}
    </div>
  );
}

function Btn({ children, primary, ghost, danger, size = "md", onClick, disabled, style = {} }) {
  const bg = disabled ? A.panel2 : primary ? A.cyan : danger ? "rgba(255,107,107,.1)" : ghost ? "transparent" : A.panel2;
  const color = disabled ? A.dim2 : primary ? A.bg : danger ? A.danger : A.text;
  const border = primary ? "none" : `1px solid ${A.line2}`;
  const pad = size === "sm" ? "6px 10px" : "8px 14px";
  return (
    <button onClick={onClick} disabled={disabled} style={{
      padding: pad, background: bg, color, border, borderRadius: 6,
      fontSize: 11.5, fontWeight: primary ? 600 : 500, cursor: disabled ? "default" : "pointer",
      fontFamily: "inherit", letterSpacing: ".02em", ...style,
    }}>{children}</button>
  );
}

function Sidebar({ nav, onNav, content, token }) {
  const [head, setHead] = React.useState(null);
  React.useEffect(() => {
    let cancelled = false;
    const headers = { Accept: "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28" };
    if (token) headers.Authorization = `Bearer ${token}`;
    fetch(`https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/commits/${REPO_BRANCH}`, { headers })
      .then(r => r.ok ? r.json() : null)
      .then(body => {
        if (cancelled || !body?.sha) return;
        setHead({
          sha: body.sha.slice(0, 7),
          msg: (body.commit?.message || "").split("\n")[0],
          at: body.commit?.author?.date || null,
        });
      })
      .catch(() => {});
    return () => { cancelled = true; };
  }, [token]);

  const items = [
    { id: "home", label: "Overview", ic: Ic.home, kbd: "1" },
    { id: "hero", label: "Hero", ic: Ic.sparkle, kbd: "2" },
    { id: "products", label: "Products", ic: Ic.grid, kbd: "3", badge: content.products.length },
    { id: "thinking", label: "Thinking", ic: Ic.brain, kbd: "4" },
    { id: "labRuns", label: "Lab runs", ic: Ic.image, kbd: "5", badge: content.labRuns?.frames?.length ?? 0 },
    { id: "lab", label: "Lab shelf", ic: Ic.flask, kbd: "6", badge: content.lab.length },
    { id: "play", label: "Play", ic: Ic.rocket, kbd: "7", badge: content.play?.widgets?.length ?? 0 },
    { id: "about", label: "About", ic: Ic.heart, kbd: "8", badge: content.about?.paragraphs?.length ?? 0 },
    { id: "support", label: "Support", ic: Ic.star, kbd: "9" },
    { id: "contact", label: "Contact", ic: Ic.mail, badge: content.contact?.rows?.length ?? 0 },
    { id: "sections", label: "Sections", ic: Ic.eye },
    { id: "stories", label: "Stories", ic: Ic.edit },
    { id: "ops", label: "Ops", ic: Ic.activity },
    { id: "analytics", label: "Analytics", ic: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"><line x1="6" y1="20" x2="6" y2="14"/><line x1="12" y1="20" x2="12" y2="8"/><line x1="18" y1="20" x2="18" y2="11"/><line x1="3" y1="20" x2="21" y2="20"/></svg> },
  ];
  return (
    <div style={{
      borderRight: `1px solid ${A.line}`, background: A.panel,
      padding: "14px 10px", display: "flex", flexDirection: "column", gap: 2, overflow: "auto",
    }}>
      <div style={{ padding: "6px 10px 10px", fontSize: 10, color: A.dim2, textTransform: "uppercase", letterSpacing: ".12em", fontFamily: "JetBrains Mono, monospace" }}>Edit</div>
      {items.map(it => {
        const active = nav === it.id;
        return (
          <button key={it.id} onClick={() => onNav(it.id)} style={{
            display: "flex", alignItems: "center", gap: 10,
            padding: "8px 10px", background: active ? "rgba(23,212,250,.08)" : "transparent",
            border: "none", borderLeft: `2px solid ${active ? A.cyan : "transparent"}`,
            color: active ? A.text : A.dim, fontFamily: "inherit", fontSize: 12.5,
            fontWeight: active ? 500 : 400, cursor: "pointer", textAlign: "left", borderRadius: 0,
          }}>
            <span style={{ color: active ? A.cyan : A.dim2 }}>{it.ic}</span>
            <span style={{ flex: 1 }}>{it.label}</span>
            {it.badge != null && <span style={{ fontSize: 10, color: A.dim2, fontFamily: "JetBrains Mono, monospace" }}>{it.badge}</span>}
          </button>
        );
      })}

      <div style={{ marginTop: 18, padding: "6px 10px 10px", fontSize: 10, color: A.dim2, textTransform: "uppercase", letterSpacing: ".12em", fontFamily: "JetBrains Mono, monospace" }}>Live</div>
      <div style={{ padding: "8px 12px", fontSize: 11, color: A.dim, display: "flex", alignItems: "center", gap: 8 }}>
        <span style={{ display: "inline-block", width: 6, height: 6, borderRadius: 99, background: A.green, boxShadow: `0 0 8px ${A.green}` }}/>
        626labs.dev
      </div>
      <a
        href={head ? `https://github.com/${REPO_OWNER}/${REPO_NAME}/commit/${head.sha}` : `https://github.com/${REPO_OWNER}/${REPO_NAME}/commits/${REPO_BRANCH}`}
        target="_blank"
        rel="noopener"
        title={head?.msg || ""}
        style={{ padding: "2px 12px 4px", fontSize: 10, color: A.dim2, fontFamily: "JetBrains Mono, monospace", textDecoration: "none", display: "block" }}
      >main@{head?.sha || "…"}</a>
      <a href="https://626labs.dev" target="_blank" rel="noopener" style={{ padding: "2px 12px", fontSize: 10, color: A.cyan, fontFamily: "JetBrains Mono, monospace", textDecoration: "none" }}>open site ↗</a>

      <div style={{ flex: 1 }}/>
      <div style={{ margin: "8px 4px 0", padding: "10px 12px", border: `1px dashed ${A.line2}`, borderRadius: 6, fontSize: 11, color: A.dim, lineHeight: 1.5 }}>
        <div style={{ color: A.cyan, fontFamily: "JetBrains Mono, monospace", fontSize: 10, letterSpacing: ".08em", marginBottom: 4 }}>press ?</div>
        Keyboard shortcuts
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// Home / overview
// ─────────────────────────────────────────────────────────────
function PanelHeader({ title, subtitle, actions }) {
  return (
    <div style={{ padding: "20px 26px 16px", borderBottom: `1px solid ${A.line}`, display: "flex", alignItems: "flex-end", gap: 16 }}>
      <div style={{ flex: 1 }}>
        <div style={{ fontSize: 18, fontWeight: 600, letterSpacing: "-.01em" }}>{title}</div>
        {subtitle && <div style={{ fontSize: 12, color: A.dim, marginTop: 3 }}>{subtitle}</div>}
      </div>
      {actions}
    </div>
  );
}

function HomeView({ content, liveStats, onNav, onAddProduct, onSelect }) {
  const totals = {
    weekly: Object.values(liveStats || {}).reduce((a, b) => a + (b.weekly || 0), 0),
    stars: Object.values(liveStats || {}).reduce((a, b) => a + (b.stars || 0), 0),
    live: content.products.filter(p => p.status === "live").length,
  };
  const liveLoaded = Object.keys(liveStats || {}).length > 0;
  return (
    <div>
      <PanelHeader title="Overview" subtitle="Snapshot of 626labs.dev"/>
      <div style={{ padding: "18px 26px", display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 14 }}>
        <StatTile label="Products live" value={totals.live} sub={`${content.products.length - totals.live} in progress`} c={A.green}/>
        <StatTile label="Lab cards" value={content.lab.length} sub="on the shelf" c={A.cyan}/>
        <StatTile label="Weekly npm" value={liveLoaded ? totals.weekly.toLocaleString() : "…"} sub={liveLoaded ? "across all plugins" : "fetching"} c={A.magenta}/>
        <StatTile label="GitHub stars" value={liveLoaded ? totals.stars : "…"} sub={liveLoaded ? "across plugin repos" : "fetching"} c={A.amber}/>
      </div>

      <div style={{ padding: "0 26px 18px" }}>
        <SectionLabel>Quick actions</SectionLabel>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(2,1fr)", gap: 10 }}>
          <Quick ic={Ic.plus} title="Add a project" sub="Open a new row in products — edits live" tone="cyan" onClick={onAddProduct}/>
          <Quick ic={Ic.image} title="Add screenshots" sub="Drop onto Vibe Cartographer" tone="magenta" onClick={()=>onSelect("vibe-cartographer")}/>
        </div>
      </div>

      <div style={{ padding: "0 26px 32px" }}>
        <SectionLabel>Projects</SectionLabel>
        <div style={{ background: A.panel, border: `1px solid ${A.line}`, borderRadius: 8 }}>
          {content.products.map((p, i) => (
            <button key={p.id} onClick={()=>onSelect(p.id)} style={{
              display: "flex", alignItems: "center", gap: 14, padding: "12px 14px", width: "100%",
              background: "transparent", border: "none", borderBottom: i < content.products.length - 1 ? `1px solid ${A.line}` : "none",
              color: A.text, cursor: "pointer", fontFamily: "inherit", textAlign: "left",
            }}>
              <StatusDot status={p.status}/>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13, fontWeight: 500 }}>
                  {p.title}
                  {p.flagship && <span style={{ fontSize: 9.5, color: A.magenta, fontFamily: "JetBrains Mono, monospace", letterSpacing: ".08em" }}>FLAGSHIP</span>}
                </div>
                <div style={{ fontSize: 11.5, color: A.dim, marginTop: 2, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {p.description || <span style={{ color: A.dim2, fontStyle: "italic" }}>no description</span>}
                </div>
              </div>
              <div style={{ fontSize: 10.5, color: A.dim2, fontFamily: "JetBrains Mono, monospace", display: "flex", alignItems: "center", gap: 14 }}>
                <span>{(p.screenshots||[]).length} shots</span>
                {p.npm && liveStats[p.npm]?.weekly != null && <span style={{ color: A.cyan }}>{liveStats[p.npm].weekly.toLocaleString()}/wk</span>}
              </div>
              <span style={{ color: A.dim2 }}>{Ic.arrowR}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

function SectionLabel({ children }) {
  return <div style={{ fontSize: 11, color: A.dim2, textTransform: "uppercase", letterSpacing: ".12em", fontFamily: "JetBrains Mono, monospace", margin: "18px 0 10px" }}>{children}</div>;
}

function StatTile({ label, value, sub, c }) {
  return (
    <div style={{ padding: 14, background: A.panel, border: `1px solid ${A.line}`, borderRadius: 6 }}>
      <div style={{ fontSize: 10.5, color: A.dim2, textTransform: "uppercase", letterSpacing: ".12em", fontFamily: "JetBrains Mono, monospace" }}>{label}</div>
      <div style={{ fontSize: 24, fontWeight: 600, color: c, marginTop: 6, fontFamily: "JetBrains Mono, monospace" }}>{value}</div>
      <div style={{ fontSize: 11, color: A.dim, marginTop: 2 }}>{sub}</div>
    </div>
  );
}

function Quick({ ic, title, sub, tone, onClick }) {
  const c = TONE_COLORS[tone] || TONE_COLORS.cyan;
  return (
    <button onClick={onClick} style={{
      display: "flex", alignItems: "center", gap: 14, padding: "14px 16px",
      background: A.panel, border: `1px solid ${A.line}`, borderLeft: `2px solid ${c.fg}`,
      borderRadius: 6, cursor: "pointer", color: A.text, textAlign: "left", fontFamily: "inherit",
    }}>
      <span style={{ color: c.fg, display: "inline-flex", width: 32, height: 32, borderRadius: 6, background: c.bg, alignItems: "center", justifyContent: "center" }}>{ic}</span>
      <div style={{ flex: 1 }}>
        <div style={{ fontSize: 13, fontWeight: 500 }}>{title}</div>
        <div style={{ fontSize: 11.5, color: A.dim, marginTop: 2 }}>{sub}</div>
      </div>
      <span style={{ color: A.dim2 }}>{Ic.arrowR}</span>
    </button>
  );
}

// ─────────────────────────────────────────────────────────────
// Products / editor with drag-drop screenshots
// ─────────────────────────────────────────────────────────────
function ProductsView({ products, liveStats, selectedId, onSelect, onUpdate, onAdd, onDelete, token, onToast }) {
  const selected = products.find(p => p.id === selectedId) || products[0];
  return (
    <div>
      <PanelHeader
        title="Products"
        subtitle={`${products.length} products · drag to reorder on the live site`}
        actions={<Btn primary onClick={onAdd}><span style={{display:"inline-flex",alignItems:"center",gap:6}}>{Ic.plus} New product</span></Btn>}
      />
      <div style={{ display: "grid", gridTemplateColumns: "280px 1fr" }}>
        <div style={{ borderRight: `1px solid ${A.line}`, padding: "10px 8px", minHeight: 700 }}>
          {products.map((p) => {
            const active = p.id === selected?.id;
            const live = p.npm && liveStats?.[p.npm];
            return (
              <button key={p.id} onClick={()=>onSelect(p.id)} style={{
                display: "flex", alignItems: "center", gap: 10, width: "100%",
                padding: "10px 10px", background: active ? "rgba(23,212,250,.06)" : "transparent",
                border: "none", borderRadius: 5, textAlign: "left", cursor: "pointer",
                color: A.text, fontFamily: "inherit", marginBottom: 2,
              }}>
                <span style={{ color: A.dim2 }}>{Ic.drag}</span>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12.5, fontWeight: 500 }}>
                    {p.title}
                    {p.flagship && <span style={{ fontSize: 9, color: A.magenta }}>★</span>}
                  </div>
                  <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 10.5, color: A.dim2, fontFamily: "JetBrains Mono, monospace", marginTop: 2 }}>
                    <StatusDot status={p.status}/>{p.status}<span>·</span>
                    <span>{(p.screenshots||[]).length} shots</span>
                    {live && <><span>·</span><span style={{ color: A.cyan }}>{live.weekly}/w</span></>}
                  </div>
                </div>
              </button>
            );
          })}
        </div>
        {selected && <ProductEditor key={selected.id} p={selected} onUpdate={(patch)=>onUpdate(selected.id, patch)} onDelete={()=>onDelete(selected.id)} token={token} onToast={onToast}/>}
      </div>
    </div>
  );
}

function ProductEditor({ p, onUpdate, onDelete, token, onToast }) {
  const derivedInstall = React.useMemo(() => {
    if (!p.repo) return "";
    return `/plugin marketplace add ${p.repo}`;
  }, [p.repo]);

  return (
    <div style={{ padding: "18px 26px", overflow: "auto" }}>
      {/* Header row */}
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 20 }}>
        <StatusDot status={p.status}/>
        <div style={{ fontSize: 11, fontFamily: "JetBrains Mono, monospace", color: A.dim2 }}>products[{p.id}]</div>
        <div style={{ flex: 1 }}/>
        <select value={p.status} onChange={e=>onUpdate({status: e.target.value})} style={selectStyle}>
          <option value="live">Live</option>
          <option value="wip">Coming soon</option>
          <option value="archived">Archived</option>
        </select>
        <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 11.5, color: A.dim }}>
          <input type="checkbox" checked={!!p.flagship} onChange={e=>onUpdate({flagship: e.target.checked})}/>
          Flagship
        </label>
        <Btn danger size="sm" onClick={onDelete}>{Ic.trash}</Btn>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 18 }}>
        <Field label="Title"><Input value={p.title} onChange={v=>onUpdate({title:v})}/></Field>
        <Field label="Tagline" hint="one-liner"><Input value={p.tagline} onChange={v=>onUpdate({tagline:v})}/></Field>
      </div>
      <Field label="Description"><Input multiline value={p.description} onChange={v=>onUpdate({description:v})}/></Field>

      <Field label="Tags" hint="click × to remove">
        <TagEditor tags={p.tags||[]} onChange={tags=>onUpdate({tags})}/>
      </Field>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 18 }}>
        <Field label="Repo" mono><Input mono value={p.repo} onChange={v=>onUpdate({repo:v})} placeholder="owner/name"/></Field>
        <Field label="npm package" mono><Input mono value={p.npm||""} onChange={v=>onUpdate({npm:v})}/></Field>
      </div>

      <Field label="Install command" mono hint={derivedInstall && p.install !== derivedInstall ? "auto-suggest available" : null}>
        <div style={{ display: "flex", gap: 8 }}>
          <Input mono value={p.install||""} onChange={v=>onUpdate({install:v})}/>
          {derivedInstall && p.install !== derivedInstall && (
            <Btn ghost size="sm" onClick={()=>onUpdate({install: derivedInstall})}>
              <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>{Ic.sparkle} Auto from repo</span>
            </Btn>
          )}
        </div>
      </Field>

      <ScreenshotsEditor
        shots={p.screenshots || []}
        token={token}
        productId={p.id}
        onToast={onToast}
        onChange={(s) => {
          const firstPath = s[0]?.path;
          const desiredBanner = firstPath ? `/${firstPath}` : "";
          const patch = { screenshots: s };
          if ((p.banner || "") !== desiredBanner) patch.banner = desiredBanner;
          onUpdate(patch);
        }}
      />
    </div>
  );
}

const selectStyle = {
  padding: "6px 10px", background: A.panel, border: `1px solid ${A.line2}`,
  borderRadius: 5, color: A.text, fontSize: 11.5, fontFamily: "inherit",
};

function Field({ label, hint, children, mono }) {
  return (
    <label style={{ display: "block", marginBottom: 14 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
        <span style={{ fontSize: 10.5, fontWeight: 500, color: A.dim, textTransform: "uppercase", letterSpacing: ".1em", fontFamily: mono ? "JetBrains Mono, monospace" : "inherit" }}>{label}</span>
        {hint && <span style={{ fontSize: 10.5, color: A.cyan, fontStyle: "italic" }}>{hint}</span>}
      </div>
      {children}
    </label>
  );
}

function Input({ value, onChange, mono, placeholder, multiline }) {
  const s = {
    width: "100%", padding: multiline ? "10px 12px" : "8px 12px",
    background: A.panel, border: `1px solid ${A.line2}`,
    borderRadius: 5, color: A.text, fontSize: 12.5,
    fontFamily: mono ? "JetBrains Mono, monospace" : "inherit",
    outline: "none", resize: "vertical", boxSizing: "border-box",
  };
  const on = (e) => {
    onChange?.(e.target.value);
    e.currentTarget.style.borderColor = A.cyan;
  };
  const blur = (e) => { e.currentTarget.style.borderColor = A.line2; };
  if (multiline) return <textarea rows={3} value={value||""} onChange={on} onBlur={blur} placeholder={placeholder} style={s}/>;
  return <input type="text" value={value||""} onChange={on} onBlur={blur} placeholder={placeholder} style={s}/>;
}

function TagEditor({ tags, onChange }) {
  const [adding, setAdding] = React.useState(false);
  const [val, setVal] = React.useState("");
  const tones = ["cyan", "magenta", "live", "wip"];
  const add = () => {
    if (!val.trim()) { setAdding(false); return; }
    onChange([...tags, { label: val.trim(), tone: "cyan" }]);
    setVal(""); setAdding(false);
  };
  return (
    <div style={{ display: "flex", flexWrap: "wrap", gap: 6, padding: 8, border: `1px dashed ${A.line2}`, borderRadius: 5, minHeight: 42, alignItems: "center" }}>
      {tags.map((t,i) => (
        <span key={i} style={{ display: "inline-flex", alignItems: "center", gap: 4 }}>
          <Chip tone={t.tone}>{t.label}</Chip>
          <button onClick={()=>onChange(tags.filter((_,j)=>j!==i))} style={{ background: "transparent", border: "none", color: A.dim2, cursor: "pointer", padding: 2, fontSize: 11, marginLeft: -4 }}>×</button>
          <select value={t.tone} onChange={e=>onChange(tags.map((x,j)=>j===i?{...x,tone:e.target.value}:x))} style={{ background: "transparent", border: "none", color: A.dim2, fontSize: 9, fontFamily: "JetBrains Mono, monospace", outline: "none", cursor: "pointer" }}>
            {tones.map(tn => <option key={tn} value={tn} style={{ background: A.panel, color: A.text }}>{tn}</option>)}
          </select>
        </span>
      ))}
      {adding ? (
        <input autoFocus value={val} onChange={e=>setVal(e.target.value)} onBlur={add} onKeyDown={e=>{if(e.key==="Enter")add();if(e.key==="Escape"){setVal("");setAdding(false);}}} placeholder="label" style={{
          padding: "3px 8px", background: A.panel2, border: `1px solid ${A.cyan}`, color: A.text,
          borderRadius: 999, fontSize: 10, fontFamily: "JetBrains Mono, monospace", outline: "none", width: 100,
          letterSpacing: ".08em", textTransform: "uppercase",
        }}/>
      ) : (
        <button onClick={()=>setAdding(true)} style={{ padding: "3px 8px", background: "transparent", border: `1px dashed ${A.line2}`, color: A.dim, borderRadius: 999, fontSize: 10, cursor: "pointer", fontFamily: "JetBrains Mono, monospace", letterSpacing: ".08em" }}>+ ADD TAG</button>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// MetaEditor: label/value rows for hero stat strip
// ─────────────────────────────────────────────────────────────
function MetaEditor({ meta, onChange }) {
  const update = (i, patch) => onChange(meta.map((m, j) => j === i ? { ...m, ...patch } : m));
  const remove = (i) => onChange(meta.filter((_, j) => j !== i));
  const add = () => onChange([...meta, { label: "", value: "" }]);
  return (
    <div style={{ padding: 8, border: `1px dashed ${A.line2}`, borderRadius: 5, display: "flex", flexDirection: "column", gap: 8 }}>
      {meta.map((m, i) => (
        <div key={i} style={{ display: "grid", gridTemplateColumns: "180px 1fr auto", gap: 8, alignItems: "center" }}>
          <Input mono value={m.label} onChange={v => update(i, { label: v })} placeholder="label"/>
          <Input value={m.value} onChange={v => update(i, { value: v })} placeholder="value"/>
          <button onClick={() => remove(i)} style={{ background: "transparent", border: "none", color: A.dim2, cursor: "pointer", padding: 4 }}>{Ic.trash}</button>
        </div>
      ))}
      <button onClick={add} style={{ padding: "6px 10px", background: "transparent", border: `1px dashed ${A.line2}`, color: A.dim, borderRadius: 5, fontSize: 10.5, cursor: "pointer", fontFamily: "JetBrains Mono, monospace", letterSpacing: ".08em", textTransform: "uppercase", alignSelf: "flex-start" }}>+ ADD ROW</button>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// Screenshots: drag-drop + paste + reorder + crop + set cover
// ─────────────────────────────────────────────────────────────
function ScreenshotsEditor({ shots, onChange, token, productId, onToast }) {
  const [over, setOver] = React.useState(false);
  const [dragIdx, setDragIdx] = React.useState(null);
  const [cropping, setCropping] = React.useState(null);
  const [uploading, setUploading] = React.useState(null); // { done, total } | null
  const fileRef = React.useRef(null);

  const ingestFiles = async (files) => {
    const imgs = [...files].filter(f => f.type.startsWith("image/"));
    if (imgs.length === 0) return;
    const remaining = Math.max(0, 6 - shots.length);
    const batch = imgs.slice(0, remaining);
    if (batch.length === 0) {
      onToast?.("Already have 6 screenshots — remove one first.", "amber", 3500);
      return;
    }
    if (!token || !productId) {
      onToast?.("Missing token or product id — can't upload.", "red", 4500);
      return;
    }
    setUploading({ done: 0, total: batch.length });
    const next = [...shots];
    try {
      for (let i = 0; i < batch.length; i++) {
        const f = batch[i];
        const extMatch = (f.name || "").match(/\.[a-z0-9]+$/i);
        const ext = (extMatch?.[0] || ".png").toLowerCase();
        const base = (f.name || "shot")
          .replace(/\.[a-z0-9]+$/i, "")
          .toLowerCase()
          .replace(/[^a-z0-9]+/g, "-")
          .replace(/^-|-$/g, "") || "shot";
        const fname = `${Date.now()}-${base}${ext}`;
        const repoPath = `assets/screenshots/${productId}/${fname}`;
        const b64 = await fileToBase64(f);
        const { path } = await uploadAsset(token, repoPath, b64, `admin: upload screenshot for ${productId}`);
        next.push({
          id: `shot-${Date.now()}-${Math.random().toString(36).slice(2,6)}`,
          path,
          name: f.name || `shot${ext}`,
          size: f.size,
        });
        setUploading({ done: i + 1, total: batch.length });
      }
      onChange(next);
      onToast?.(`Uploaded ${batch.length} screenshot${batch.length>1?"s":""}. Hit save to deploy.`, "green", 3500);
    } catch (ex) {
      onToast?.(`Upload failed: ${ex.message}`, "red", 6000);
    } finally {
      setUploading(null);
    }
  };

  const onDrop = (e) => {
    e.preventDefault(); setOver(false);
    if (uploading) return;
    ingestFiles([...e.dataTransfer.files]);
  };

  // Paste handler bound to document while editor is mounted
  React.useEffect(() => {
    const onPaste = (e) => {
      if (uploading) return;
      const items = [...(e.clipboardData?.items || [])];
      const imgs = items.filter(it => it.type.startsWith("image/")).map(it => it.getAsFile()).filter(Boolean);
      if (imgs.length) {
        e.preventDefault();
        ingestFiles(imgs);
      }
    };
    window.addEventListener("paste", onPaste);
    return () => window.removeEventListener("paste", onPaste);
  }, [shots, uploading, token, productId]);

  const setCover = (i) => {
    if (i === 0) return;
    const next = [...shots];
    const [picked] = next.splice(i, 1);
    next.unshift(picked);
    onChange(next);
  };

  const remove = (i) => onChange(shots.filter((_,j)=>j!==i));

  const onDragStart = (i) => (e) => { setDragIdx(i); e.dataTransfer.effectAllowed = "move"; };
  const onDragOver = (i) => (e) => { e.preventDefault(); };
  const onDropOn = (i) => (e) => {
    e.preventDefault();
    if (dragIdx == null || dragIdx === i) return;
    const next = [...shots];
    const [picked] = next.splice(dragIdx, 1);
    next.splice(i, 0, picked);
    onChange(next);
    setDragIdx(null);
  };

  return (
    <div style={{ marginTop: 22 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 10 }}>
        <span style={{ fontSize: 10.5, fontWeight: 500, color: A.dim, textTransform: "uppercase", letterSpacing: ".1em" }}>Screenshots</span>
        <span style={{ fontSize: 11, color: A.dim2 }}>{shots.length} / 6</span>
        <span style={{ fontSize: 10, color: A.dim2, fontFamily: "JetBrains Mono, monospace", padding: "2px 6px", background: A.panel2, borderRadius: 3 }}>⌘V to paste</span>
        <div style={{ flex: 1 }}/>
        <input ref={fileRef} type="file" accept="image/*" multiple style={{ display: "none" }} onChange={e=>{ if (!uploading) ingestFiles([...e.target.files]); e.target.value = ""; }}/>
        <Btn size="sm" onClick={()=>{ if (!uploading) fileRef.current?.click(); }} disabled={!!uploading}><span style={{display:"inline-flex",alignItems:"center",gap:6}}>{Ic.upload} Upload</span></Btn>
      </div>

      {/* Dropzone — always visible, taller when empty */}
      <div
        onDragOver={(e)=>{e.preventDefault(); if (!uploading) setOver(true);}}
        onDragLeave={()=>setOver(false)}
        onDrop={onDrop}
        onClick={()=>{ if (!uploading) fileRef.current?.click(); }}
        style={{
          border: `2px dashed ${uploading ? A.cyan : (over ? A.cyan : A.line2)}`,
          background: uploading ? "rgba(23,212,250,.08)" : (over ? "rgba(23,212,250,.06)" : A.panel),
          borderRadius: 8, padding: shots.length ? "12px 14px" : "28px 20px",
          marginBottom: 12, cursor: uploading ? "wait" : "pointer",
          display: "flex", alignItems: "center", gap: 14, justifyContent: "center",
          transition: "border-color .12s, background .12s",
        }}>
        <span style={{ color: uploading || over ? A.cyan : A.dim2 }}>{Ic.upload}</span>
        <div>
          {uploading ? (
            <>
              <div style={{ fontSize: 12.5, color: A.cyan, fontWeight: 500, fontFamily: "JetBrains Mono, monospace" }}>Uploading {uploading.done} / {uploading.total}…</div>
              <div style={{ fontSize: 11, color: A.dim, marginTop: 2 }}>Committing to assets/screenshots/{productId}/</div>
            </>
          ) : (
            <>
              <div style={{ fontSize: 12.5, color: A.text, fontWeight: 500 }}>Drop images here, paste from clipboard, or click to browse</div>
              <div style={{ fontSize: 11, color: A.dim, marginTop: 2 }}>PNG / JPG · max 6 · first image is the card cover + banner</div>
            </>
          )}
        </div>
      </div>

      {shots.length > 0 && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 10 }}>
          {shots.map((s, i) => (
            <div
              key={s.id}
              draggable
              onDragStart={onDragStart(i)}
              onDragOver={onDragOver(i)}
              onDrop={onDropOn(i)}
              style={{
                aspectRatio: "16/10", background: A.panel, border: `1px solid ${i === 0 ? A.magenta : A.line2}`,
                borderRadius: 6, position: "relative", overflow: "hidden", cursor: "grab",
                boxShadow: i === 0 ? "0 0 0 1px rgba(255,90,163,.25)" : "none",
              }}>
              {s.path ? (
                <img src={rawUrl(s.path)} alt={s.name} style={{ width: "100%", height: "100%", objectFit: "cover", display: "block", pointerEvents: "none" }}/>
              ) : s.url ? (
                <img src={s.url} alt={s.name} style={{ width: "100%", height: "100%", objectFit: "cover", display: "block", pointerEvents: "none" }}/>
              ) : (
                <div style={{ height: "100%", display: "grid", placeItems: "center", color: A.dim2, fontSize: 11 }}>{Ic.image}</div>
              )}

              {/* Top badges */}
              <div style={{ position: "absolute", top: 6, left: 6, right: 6, display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 6 }}>
                {i === 0 ? (
                  <span style={{ padding: "2px 6px", fontSize: 9.5, fontFamily: "JetBrains Mono, monospace", letterSpacing: ".08em", background: A.magenta, color: A.bg, borderRadius: 3, fontWeight: 600 }}>COVER</span>
                ) : (
                  <button onClick={(e)=>{e.stopPropagation(); setCover(i);}} style={{ padding: "2px 6px", fontSize: 9.5, fontFamily: "JetBrains Mono, monospace", letterSpacing: ".08em", background: "rgba(0,0,0,.6)", color: A.text, border: `1px solid ${A.line3}`, borderRadius: 3, cursor: "pointer" }}>SET COVER</button>
                )}
                <span style={{ color: A.text, background: "rgba(0,0,0,.6)", padding: 4, borderRadius: 3, display: "inline-flex" }}>{Ic.drag}</span>
              </div>

              {/* Bottom bar */}
              <div style={{ position: "absolute", bottom: 0, left: 0, right: 0, background: "linear-gradient(180deg,transparent,rgba(0,0,0,.7))", padding: "14px 8px 6px", display: "flex", alignItems: "flex-end", gap: 6 }}>
                <div style={{ flex: 1, minWidth: 0, fontSize: 10.5, fontFamily: "JetBrains Mono, monospace", color: A.text, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{s.name}</div>
                <button onClick={(e)=>{e.stopPropagation(); setCropping(s);}} title="Crop" style={tileBtn}>✂</button>
                <button onClick={(e)=>{e.stopPropagation(); remove(i);}} title="Remove" style={tileBtn}>{Ic.trash}</button>
              </div>
            </div>
          ))}
        </div>
      )}

      {cropping && <CropModal shot={cropping} close={()=>setCropping(null)} onApply={(r)=>{
        onChange(shots.map(x => x.id === cropping.id ? { ...x, crop: r } : x));
        setCropping(null);
      }}/>}
    </div>
  );
}

const tileBtn = {
  padding: 4, fontSize: 11, background: "rgba(0,0,0,.6)", color: A.text,
  border: `1px solid ${A.line3}`, borderRadius: 3, cursor: "pointer",
  display: "inline-flex", alignItems: "center", justifyContent: "center", minWidth: 22, minHeight: 22,
};

function CropModal({ shot, close, onApply }) {
  // Draggable rect crop affordance. Rect is in 0..1 coordinates.
  const [rect, setRect] = React.useState(shot.crop || { x: 0.05, y: 0.05, w: 0.9, h: 0.9 });
  const ref = React.useRef(null);
  const drag = React.useRef(null);

  const onDown = (mode) => (e) => {
    e.preventDefault();
    const r = ref.current.getBoundingClientRect();
    drag.current = { mode, startX: e.clientX, startY: e.clientY, r: { ...rect }, w: r.width, h: r.height };
    window.addEventListener("pointermove", onMove);
    window.addEventListener("pointerup", onUp);
  };
  const onMove = (e) => {
    const d = drag.current; if (!d) return;
    const dx = (e.clientX - d.startX) / d.w;
    const dy = (e.clientY - d.startY) / d.h;
    let n = { ...d.r };
    if (d.mode === "move") {
      n.x = Math.max(0, Math.min(1 - n.w, d.r.x + dx));
      n.y = Math.max(0, Math.min(1 - n.h, d.r.y + dy));
    } else if (d.mode === "se") {
      n.w = Math.max(0.1, Math.min(1 - n.x, d.r.w + dx));
      n.h = Math.max(0.1, Math.min(1 - n.y, d.r.h + dy));
    } else if (d.mode === "nw") {
      const nx = Math.max(0, Math.min(d.r.x + d.r.w - 0.1, d.r.x + dx));
      const ny = Math.max(0, Math.min(d.r.y + d.r.h - 0.1, d.r.y + dy));
      n.w = d.r.w - (nx - d.r.x); n.h = d.r.h - (ny - d.r.y);
      n.x = nx; n.y = ny;
    }
    setRect(n);
  };
  const onUp = () => { drag.current = null; window.removeEventListener("pointermove", onMove); window.removeEventListener("pointerup", onUp); };

  return (
    <div style={overlayStyle} onClick={close}>
      <div onClick={(e)=>e.stopPropagation()} style={{ background: A.panel, border: `1px solid ${A.line2}`, borderRadius: 10, padding: 18, width: 560, maxWidth: "90vw" }}>
        <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 4 }}>Crop</div>
        <div style={{ fontSize: 11.5, color: A.dim, marginBottom: 14 }}>Drag the frame. Product cards use 16:10 — the cropped region will be what renders.</div>
        <div ref={ref} style={{ position: "relative", aspectRatio: "16/10", background: A.bg, borderRadius: 6, overflow: "hidden", userSelect: "none" }}>
          {shot.url && <img src={shot.url} alt="" style={{ width: "100%", height: "100%", objectFit: "cover", display: "block", pointerEvents: "none" }}/>}
          {/* dim mask */}
          <div style={{ position: "absolute", inset: 0, boxShadow: `0 0 0 9999px rgba(0,0,0,.55) inset`, clipPath: `polygon(0 0, 100% 0, 100% 100%, 0 100%, 0 ${rect.y*100}%, ${rect.x*100}% ${rect.y*100}%, ${rect.x*100}% ${(rect.y+rect.h)*100}%, ${(rect.x+rect.w)*100}% ${(rect.y+rect.h)*100}%, ${(rect.x+rect.w)*100}% ${rect.y*100}%, 0 ${rect.y*100}%)`, pointerEvents: "none" }}/>
          <div onPointerDown={onDown("move")} style={{
            position: "absolute", left: `${rect.x*100}%`, top: `${rect.y*100}%`,
            width: `${rect.w*100}%`, height: `${rect.h*100}%`,
            border: `1.5px solid ${A.cyan}`, boxShadow: `0 0 0 1px rgba(0,0,0,.5)`, cursor: "move",
            backgroundImage: `linear-gradient(to right, transparent 33%, rgba(255,255,255,.15) 33%, rgba(255,255,255,.15) 34%, transparent 34%), linear-gradient(to right, transparent 66%, rgba(255,255,255,.15) 66%, rgba(255,255,255,.15) 67%, transparent 67%), linear-gradient(to bottom, transparent 33%, rgba(255,255,255,.15) 33%, rgba(255,255,255,.15) 34%, transparent 34%), linear-gradient(to bottom, transparent 66%, rgba(255,255,255,.15) 66%, rgba(255,255,255,.15) 67%, transparent 67%)`,
          }}>
            <span onPointerDown={(e)=>{e.stopPropagation(); onDown("nw")(e);}} style={{ position: "absolute", left: -6, top: -6, width: 12, height: 12, background: A.cyan, borderRadius: 2, cursor: "nwse-resize" }}/>
            <span onPointerDown={(e)=>{e.stopPropagation(); onDown("se")(e);}} style={{ position: "absolute", right: -6, bottom: -6, width: 12, height: 12, background: A.cyan, borderRadius: 2, cursor: "nwse-resize" }}/>
          </div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginTop: 14 }}>
          <div style={{ fontSize: 10.5, fontFamily: "JetBrains Mono, monospace", color: A.dim2 }}>
            x {(rect.x*100).toFixed(0)}% · y {(rect.y*100).toFixed(0)}% · w {(rect.w*100).toFixed(0)}% · h {(rect.h*100).toFixed(0)}%
          </div>
          <div style={{ flex: 1 }}/>
          <Btn ghost onClick={close}>Cancel</Btn>
          <Btn primary onClick={()=>onApply(rect)}>Apply crop</Btn>
        </div>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// Hero / Lab / Sections views
// ─────────────────────────────────────────────────────────────
function HeroView({ hero, onChange }) {
  const u = (patch) => onChange({ ...hero, ...patch });
  return (
    <div>
      <PanelHeader title="Hero" subtitle="First impression on 626labs.dev"/>
      <div style={{ padding: "18px 26px", maxWidth: 820 }}>
        <Field label="Eyebrow"><Input value={hero.eyebrow} onChange={v=>u({eyebrow:v})}/></Field>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 18 }}>
          <Field label="Headline"><Input value={hero.headline} onChange={v=>u({headline:v})}/></Field>
          <Field label="Headline accent" hint="gradient line"><Input value={hero.headlineAccent} onChange={v=>u({headlineAccent:v})}/></Field>
        </div>
        <Field label="Subhead"><Input multiline value={hero.subhead} onChange={v=>u({subhead:v})}/></Field>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 18 }}>
          <Field label="Primary CTA label"><Input value={hero.primaryCta.label} onChange={v=>u({primaryCta:{...hero.primaryCta,label:v}})}/></Field>
          <Field label="Primary CTA link" mono><Input mono value={hero.primaryCta.href} onChange={v=>u({primaryCta:{...hero.primaryCta,href:v}})}/></Field>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 18 }}>
          <Field label="Secondary CTA label"><Input value={hero.secondaryCta.label} onChange={v=>u({secondaryCta:{...hero.secondaryCta,label:v}})}/></Field>
          <Field label="Secondary CTA link" mono><Input mono value={hero.secondaryCta.href} onChange={v=>u({secondaryCta:{...hero.secondaryCta,href:v}})}/></Field>
        </div>
        <Field label="Stat rows" hint="the three label/value pairs under the hero">
          <MetaEditor meta={hero.meta||[]} onChange={meta => u({meta})}/>
        </Field>
        <Field label="Chips" hint="shown in the hero surround">
          <TagEditor tags={hero.chips} onChange={chips => u({chips})}/>
        </Field>
      </div>
    </div>
  );
}

function LabView({ lab, onChange }) {
  const add = () => onChange([...lab, { id: `lab-${Date.now().toString(36)}`, title: "New lab card", meta: "", blurb: "", link: "" }]);
  const update = (id, patch) => onChange(lab.map(l => l.id === id ? { ...l, ...patch } : l));
  const remove = (id) => onChange(lab.filter(l => l.id !== id));
  return (
    <div>
      <PanelHeader title="Lab shelf" subtitle="Exploratory / older projects" actions={<Btn primary onClick={add}><span style={{display:"inline-flex",alignItems:"center",gap:6}}>{Ic.plus} Add card</span></Btn>}/>
      <div style={{ padding: "18px 26px", display: "grid", gridTemplateColumns: "repeat(2,1fr)", gap: 12 }}>
        {lab.map(l => (
          <div key={l.id} style={{ padding: 14, background: A.panel, border: `1px solid ${A.line}`, borderRadius: 6 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10 }}>
              <span style={{ color: A.dim2 }}>{Ic.drag}</span>
              <div style={{ flex: 1 }}/>
              <button onClick={()=>remove(l.id)} style={{ background: "transparent", border: "none", color: A.dim2, cursor: "pointer", padding: 4 }}>{Ic.trash}</button>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
              <Input value={l.title} onChange={v=>update(l.id,{title:v})} placeholder="title"/>
              <Input mono value={l.meta} onChange={v=>update(l.id,{meta:v})} placeholder="meta tags"/>
            </div>
            <div style={{ marginTop: 8 }}><Input multiline value={l.blurb} onChange={v=>update(l.id,{blurb:v})} placeholder="blurb"/></div>
            <div style={{ marginTop: 8 }}><Input mono value={l.link} onChange={v=>update(l.id,{link:v})} placeholder="link"/></div>
          </div>
        ))}
      </div>
    </div>
  );
}

function AboutView({ about, onChange }) {
  const u = (patch) => onChange({ ...about, ...patch });
  const stack = about.stack || [];
  const paragraphs = about.paragraphs || [];
  const principles = about.principles || [];

  const updateStack = (i, v) => u({ stack: stack.map((s, j) => j === i ? v : s) });
  const addStack = () => u({ stack: [...stack, ""] });
  const removeStack = (i) => u({ stack: stack.filter((_, j) => j !== i) });

  const updatePara = (i, v) => u({ paragraphs: paragraphs.map((p, j) => j === i ? v : p) });
  const addPara = () => u({ paragraphs: [...paragraphs, ""] });
  const removePara = (i) => u({ paragraphs: paragraphs.filter((_, j) => j !== i) });
  const movePara = (i, dir) => {
    const next = [...paragraphs];
    const j = i + dir;
    if (j < 0 || j >= next.length) return;
    [next[i], next[j]] = [next[j], next[i]];
    u({ paragraphs: next });
  };

  const updatePrin = (i, patch) => u({ principles: principles.map((p, j) => j === i ? { ...p, ...patch } : p) });
  const addPrin = () => u({ principles: [...principles, { num: `P/${String(principles.length + 1).padStart(2, "0")}`, heading: "", body: "" }] });
  const removePrin = (i) => u({ principles: principles.filter((_, j) => j !== i) });

  return (
    <div>
      <PanelHeader title="About" subtitle="Manifesto — who 626 Labs is and the principles behind the work"/>
      <div style={{ padding: "18px 26px", maxWidth: 820 }}>
        <Field label="Eyebrow" hint="e.g. '06 · About 626 Labs'"><Input value={about.eyebrow||""} onChange={v=>u({eyebrow:v})}/></Field>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 18 }}>
          <Field label="Headline"><Input value={about.headline||""} onChange={v=>u({headline:v})}/></Field>
          <Field label="Headline accent" hint="rendered in <em>"><Input value={about.headlineAccent||""} onChange={v=>u({headlineAccent:v})}/></Field>
        </div>

        <Field label="Stack chips" hint="short labels above the manifesto body">
          <div>
            {stack.map((s, i) => (
              <div key={i} style={{ display: "grid", gridTemplateColumns: "1fr 34px", gap: 8, marginBottom: 6 }}>
                <Input value={s} onChange={v=>updateStack(i, v)} placeholder="TypeScript"/>
                <button onClick={()=>removeStack(i)} style={{ background: "transparent", border: `1px solid ${A.line}`, color: A.dim2, cursor: "pointer", borderRadius: 4 }}>{Ic.trash}</button>
              </div>
            ))}
            <button onClick={addStack} style={{ marginTop: 4, padding: "6px 10px", background: "transparent", border: `1px dashed ${A.line2}`, color: A.dim, fontSize: 11, cursor: "pointer", borderRadius: 4, fontFamily: "inherit" }}>+ add chip</button>
          </div>
        </Field>

        <div style={{ fontSize: 10, color: A.dim2, textTransform: "uppercase", letterSpacing: ".12em", fontFamily: "JetBrains Mono, monospace", margin: "22px 0 10px" }}>
          Paragraphs <span style={{ color: A.cyan, textTransform: "none", letterSpacing: 0, fontStyle: "italic" }}>— inline &lt;strong&gt; / &lt;em&gt; allowed</span>
        </div>
        {paragraphs.length === 0 && (
          <div style={{ padding: "14px 18px", border: `1px dashed ${A.line2}`, borderRadius: 6, color: A.dim, fontSize: 12, marginBottom: 12 }}>
            No paragraphs. Add one to populate the manifesto body.
          </div>
        )}
        {paragraphs.map((p, i) => (
          <div key={i} style={{ padding: 12, background: A.panel, border: `1px solid ${A.line}`, borderRadius: 6, marginBottom: 10 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 8 }}>
              <span style={{ fontSize: 10.5, color: A.dim2, fontFamily: "JetBrains Mono, monospace", letterSpacing: ".08em" }}>#{i + 1}</span>
              <div style={{ flex: 1 }}/>
              <button onClick={()=>movePara(i, -1)} disabled={i === 0} style={{ background: "transparent", border: "none", color: i === 0 ? A.line2 : A.dim2, cursor: i === 0 ? "default" : "pointer", padding: 4, transform: "rotate(180deg)" }}>{Ic.chev}</button>
              <button onClick={()=>movePara(i, 1)} disabled={i === paragraphs.length - 1} style={{ background: "transparent", border: "none", color: i === paragraphs.length - 1 ? A.line2 : A.dim2, cursor: i === paragraphs.length - 1 ? "default" : "pointer", padding: 4 }}>{Ic.chev}</button>
              <button onClick={()=>removePara(i)} style={{ background: "transparent", border: "none", color: A.dim2, cursor: "pointer", padding: 4 }}>{Ic.trash}</button>
            </div>
            <Input multiline value={p} onChange={v=>updatePara(i, v)} placeholder="Paragraph text (HTML <strong>/<em> allowed)"/>
          </div>
        ))}
        <button onClick={addPara} style={{ padding: "8px 12px", background: "transparent", border: `1px dashed ${A.line2}`, color: A.dim, fontSize: 12, cursor: "pointer", borderRadius: 4, fontFamily: "inherit" }}>+ add paragraph</button>

        <div style={{ fontSize: 10, color: A.dim2, textTransform: "uppercase", letterSpacing: ".12em", fontFamily: "JetBrains Mono, monospace", margin: "26px 0 10px" }}>Principles</div>
        {principles.map((pr, i) => (
          <div key={i} style={{ padding: 14, background: A.panel, border: `1px solid ${A.line}`, borderRadius: 6, marginBottom: 10 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10 }}>
              <span style={{ fontSize: 11, color: A.cyan, fontFamily: "JetBrains Mono, monospace" }}>{pr.num || `P/${String(i+1).padStart(2, "0")}`}</span>
              <div style={{ flex: 1 }}/>
              <button onClick={()=>removePrin(i)} style={{ background: "transparent", border: "none", color: A.dim2, cursor: "pointer", padding: 4 }}>{Ic.trash}</button>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "100px 1fr", gap: 10, marginBottom: 8 }}>
              <Input mono value={pr.num||""} onChange={v=>updatePrin(i,{num:v})} placeholder="P/01"/>
              <Input value={pr.heading||""} onChange={v=>updatePrin(i,{heading:v})} placeholder="Heading"/>
            </div>
            <Input multiline value={pr.body||""} onChange={v=>updatePrin(i,{body:v})} placeholder="Body"/>
          </div>
        ))}
        <button onClick={addPrin} style={{ padding: "8px 12px", background: "transparent", border: `1px dashed ${A.line2}`, color: A.dim, fontSize: 12, cursor: "pointer", borderRadius: 4, fontFamily: "inherit" }}>+ add principle</button>
      </div>
    </div>
  );
}

function PlayView({ play, onChange }) {
  const u = (patch) => onChange({ ...play, ...patch });
  const widgets = play.widgets || [];
  const addWidget = () => u({ widgets: [...widgets, { id: `widget-${Date.now().toString(36)}`, script: "", stylesheet: "", initFn: "", config: {} }] });
  const updateWidget = (i, patch) => u({ widgets: widgets.map((w, j) => j === i ? { ...w, ...patch } : w) });
  const removeWidget = (i) => u({ widgets: widgets.filter((_, j) => j !== i) });
  return (
    <div>
      <PanelHeader title="Play" subtitle="Embedded game widgets on the homepage" actions={<Btn primary onClick={addWidget}><span style={{display:"inline-flex",alignItems:"center",gap:6}}>{Ic.plus} Add widget</span></Btn>}/>
      <div style={{ padding: "18px 26px", maxWidth: 820 }}>
        <Field label="Eyebrow"><Input value={play.eyebrow||""} onChange={v=>u({eyebrow:v})}/></Field>
        <Field label="Headline"><Input value={play.headline||""} onChange={v=>u({headline:v})}/></Field>
        <Field label="Lead"><Input multiline value={play.lead||""} onChange={v=>u({lead:v})}/></Field>

        <div style={{ fontSize: 10, color: A.dim2, textTransform: "uppercase", letterSpacing: ".12em", fontFamily: "JetBrains Mono, monospace", margin: "22px 0 10px" }}>Widgets</div>
        {widgets.length === 0 && (
          <div style={{ padding: "18px 22px", border: `1px dashed ${A.line2}`, borderRadius: 6, color: A.dim, fontSize: 12 }}>
            No widgets. Add one to embed a playable game on the homepage.
          </div>
        )}
        {widgets.map((w, i) => (
          <div key={i} style={{ padding: 16, background: A.panel, border: `1px solid ${A.line}`, borderRadius: 6, marginBottom: 12 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
              <span style={{ color: A.dim2 }}>{Ic.rocket}</span>
              <div style={{ flex: 1, fontSize: 12, fontFamily: "JetBrains Mono, monospace", color: A.cyan }}>{w.id || `widget ${i+1}`}</div>
              <button onClick={()=>removeWidget(i)} style={{ background: "transparent", border: "none", color: A.dim2, cursor: "pointer", padding: 4 }}>{Ic.trash}</button>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
              <Field label="ID" mono><Input mono value={w.id||""} onChange={v=>updateWidget(i,{id:v})}/></Field>
              <Field label="Init fn" mono hint="global function the page calls"><Input mono value={w.initFn||""} onChange={v=>updateWidget(i,{initFn:v})}/></Field>
            </div>
            <Field label="Script URL" mono><Input mono value={w.script||""} onChange={v=>updateWidget(i,{script:v})}/></Field>
            <Field label="Stylesheet URL" mono><Input mono value={w.stylesheet||""} onChange={v=>updateWidget(i,{stylesheet:v})}/></Field>
            <Field label="Config" hint="key/value pairs passed to init fn">
              <KVEditor kv={w.config||{}} onChange={kv=>updateWidget(i,{config:kv})}/>
            </Field>
          </div>
        ))}
      </div>
    </div>
  );
}

function KVEditor({ kv, onChange }) {
  const entries = Object.entries(kv);
  const setKey = (oldK, newK) => {
    if (oldK === newK || !newK) return;
    const next = {};
    for (const [k, v] of entries) next[k === oldK ? newK : k] = v;
    onChange(next);
  };
  const setVal = (k, v) => onChange({ ...kv, [k]: v });
  const addRow = () => {
    let base = "key", n = entries.length + 1, key = `${base}${n}`;
    while (key in kv) { n += 1; key = `${base}${n}`; }
    onChange({ ...kv, [key]: "" });
  };
  const removeRow = (k) => { const next = { ...kv }; delete next[k]; onChange(next); };
  return (
    <div>
      {entries.map(([k, v], i) => (
        <div key={i} style={{ display: "grid", gridTemplateColumns: "180px 1fr 34px", gap: 8, marginBottom: 6 }}>
          <Input mono value={k} onChange={nk=>setKey(k, nk)} placeholder="key"/>
          <Input value={String(v ?? "")} onChange={nv=>setVal(k, nv)} placeholder="value"/>
          <button onClick={()=>removeRow(k)} style={{ background: "transparent", border: `1px solid ${A.line}`, color: A.dim2, cursor: "pointer", borderRadius: 4 }}>{Ic.trash}</button>
        </div>
      ))}
      <button onClick={addRow} style={{ marginTop: 6, padding: "6px 10px", background: "transparent", border: `1px dashed ${A.line2}`, color: A.dim, fontSize: 11, cursor: "pointer", borderRadius: 4, fontFamily: "inherit" }}>+ add pair</button>
    </div>
  );
}

function LabRunsView({ labRuns, onChange, token, onToast }) {
  const u = (patch) => onChange({ ...labRuns, ...patch });
  const frames = labRuns.frames || [];
  const caption = labRuns.caption || [];

  const updateFrame = (i, patch) => u({ frames: frames.map((f, j) => j === i ? { ...f, ...patch } : f) });
  const addFrame = () => u({ frames: [...frames, { tag: "", src: "", alt: "" }] });
  const removeFrame = (i) => u({ frames: frames.filter((_, j) => j !== i) });
  const moveFrame = (i, dir) => {
    const next = [...frames];
    const j = i + dir;
    if (j < 0 || j >= next.length) return;
    [next[i], next[j]] = [next[j], next[i]];
    u({ frames: next });
  };

  const updateCap = (i, v) => u({ caption: caption.map((p, j) => j === i ? v : p) });
  const addCap = () => u({ caption: [...caption, ""] });
  const removeCap = (i) => u({ caption: caption.filter((_, j) => j !== i) });
  const moveCap = (i, dir) => {
    const next = [...caption];
    const j = i + dir;
    if (j < 0 || j >= next.length) return;
    [next[i], next[j]] = [next[j], next[i]];
    u({ caption: next });
  };

  return (
    <div>
      <PanelHeader title="Lab runs" subtitle="Behind-the-scenes montage — Dashboard screenshots + caption" actions={<Btn primary onClick={addFrame}><span style={{display:"inline-flex",alignItems:"center",gap:6}}>{Ic.plus} Add frame</span></Btn>}/>
      <div style={{ padding: "18px 26px", maxWidth: 820 }}>
        <Field label="Eyebrow"><Input value={labRuns.eyebrow||""} onChange={v=>u({eyebrow:v})}/></Field>
        <Field label="Headline"><Input value={labRuns.headline||""} onChange={v=>u({headline:v})}/></Field>
        <Field label="Lead"><Input multiline value={labRuns.lead||""} onChange={v=>u({lead:v})}/></Field>

        <div style={{ fontSize: 10, color: A.dim2, textTransform: "uppercase", letterSpacing: ".12em", fontFamily: "JetBrains Mono, monospace", margin: "22px 0 10px" }}>Frames</div>
        {frames.length === 0 && (
          <div style={{ padding: "14px 18px", border: `1px dashed ${A.line2}`, borderRadius: 6, color: A.dim, fontSize: 12, marginBottom: 10 }}>
            No frames. Add one to show a screenshot montage.
          </div>
        )}
        {frames.map((f, i) => (
          <FrameRow
            key={i}
            frame={f}
            index={i}
            count={frames.length}
            token={token}
            onToast={onToast}
            onChange={(patch) => updateFrame(i, patch)}
            onMove={(dir) => moveFrame(i, dir)}
            onRemove={() => removeFrame(i)}
          />
        ))}

        <div style={{ fontSize: 10, color: A.dim2, textTransform: "uppercase", letterSpacing: ".12em", fontFamily: "JetBrains Mono, monospace", margin: "26px 0 10px" }}>Caption paragraphs</div>
        {caption.map((p, i) => (
          <div key={i} style={{ padding: 12, background: A.panel, border: `1px solid ${A.line}`, borderRadius: 6, marginBottom: 10 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 8 }}>
              <span style={{ fontSize: 10.5, color: A.dim2, fontFamily: "JetBrains Mono, monospace", letterSpacing: ".08em" }}>#{i + 1}</span>
              <div style={{ flex: 1 }}/>
              <button onClick={()=>moveCap(i, -1)} disabled={i === 0} style={{ background: "transparent", border: "none", color: i === 0 ? A.line2 : A.dim2, cursor: i === 0 ? "default" : "pointer", padding: 4, transform: "rotate(180deg)" }}>{Ic.chev}</button>
              <button onClick={()=>moveCap(i, 1)} disabled={i === caption.length - 1} style={{ background: "transparent", border: "none", color: i === caption.length - 1 ? A.line2 : A.dim2, cursor: i === caption.length - 1 ? "default" : "pointer", padding: 4 }}>{Ic.chev}</button>
              <button onClick={()=>removeCap(i)} style={{ background: "transparent", border: "none", color: A.dim2, cursor: "pointer", padding: 4 }}>{Ic.trash}</button>
            </div>
            <Input multiline value={p} onChange={v=>updateCap(i, v)} placeholder="Caption paragraph"/>
          </div>
        ))}
        <button onClick={addCap} style={{ padding: "8px 12px", background: "transparent", border: `1px dashed ${A.line2}`, color: A.dim, fontSize: 12, cursor: "pointer", borderRadius: 4, fontFamily: "inherit" }}>+ add paragraph</button>
      </div>
    </div>
  );
}

function FrameRow({ frame, index, count, token, onToast, onChange, onMove, onRemove }) {
  const [uploading, setUploading] = React.useState(false);
  const fileRef = React.useRef(null);
  const src = frame.src || "";
  const previewSrc = src.startsWith("http") ? src : (src ? rawUrl(src) : null);

  const upload = async (file) => {
    if (!file || !token) { onToast?.("Missing file or token.", "red", 4500); return; }
    if (!file.type.startsWith("image/")) { onToast?.("Not an image.", "amber", 3500); return; }
    setUploading(true);
    onToast?.("Uploading frame image…", "cyan", 2000);
    try {
      const extMatch = (file.name || "").match(/\.[a-z0-9]+$/i);
      const ext = (extMatch?.[0] || ".png").toLowerCase();
      const base = (file.name || "frame")
        .replace(/\.[a-z0-9]+$/i, "")
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, "-")
        .replace(/^-|-$/g, "") || "frame";
      const fname = `${Date.now()}-${base}${ext}`;
      const repoPath = `assets/lab-runs/${fname}`;
      const b64 = await fileToBase64(file);
      const { path } = await uploadAsset(token, repoPath, b64, "admin: upload lab-runs frame image");
      onChange({ src: path });
      onToast?.("Frame image uploaded. Save to deploy.", "green", 3500);
    } catch (ex) {
      onToast?.(`Upload failed: ${ex.message}`, "red", 6000);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div style={{ padding: 14, background: A.panel, border: `1px solid ${A.line}`, borderRadius: 6, marginBottom: 12 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10 }}>
        <span style={{ fontSize: 10.5, color: A.dim2, fontFamily: "JetBrains Mono, monospace", letterSpacing: ".08em" }}>#{index + 1}</span>
        <div style={{ flex: 1 }}/>
        <button onClick={()=>onMove(-1)} disabled={index === 0} style={{ background: "transparent", border: "none", color: index === 0 ? A.line2 : A.dim2, cursor: index === 0 ? "default" : "pointer", padding: 4, transform: "rotate(180deg)" }}>{Ic.chev}</button>
        <button onClick={()=>onMove(1)} disabled={index === count - 1} style={{ background: "transparent", border: "none", color: index === count - 1 ? A.line2 : A.dim2, cursor: index === count - 1 ? "default" : "pointer", padding: 4 }}>{Ic.chev}</button>
        <button onClick={onRemove} style={{ background: "transparent", border: "none", color: A.dim2, cursor: "pointer", padding: 4 }}>{Ic.trash}</button>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "180px 1fr", gap: 14 }}>
        <div style={{ aspectRatio: "16/10", background: A.panel2, border: `1px solid ${A.line2}`, borderRadius: 5, overflow: "hidden", display: "grid", placeItems: "center" }}>
          {uploading ? (
            <div style={{ fontSize: 10.5, color: A.cyan, fontFamily: "JetBrains Mono, monospace" }}>uploading…</div>
          ) : previewSrc ? (
            <img src={previewSrc} alt={frame.alt || ""} style={{ width: "100%", height: "100%", objectFit: "cover" }}/>
          ) : (
            <div style={{ color: A.dim2, fontSize: 11, display: "flex", flexDirection: "column", alignItems: "center", gap: 4 }}>{Ic.image}<span>no image</span></div>
          )}
        </div>
        <div>
          <Field label="Tag" hint="short label on the image"><Input value={frame.tag||""} onChange={v=>onChange({tag:v})} placeholder="Universe"/></Field>
          <Field label="Image path" mono hint="assets/… or https://…">
            <div style={{ display: "flex", gap: 8 }}>
              <Input mono value={frame.src||""} onChange={v=>onChange({src:v})} placeholder="assets/lab-runs/…"/>
              <input ref={fileRef} type="file" accept="image/*" style={{ display: "none" }} onChange={e=>{ if (!uploading) upload(e.target.files?.[0]); e.target.value = ""; }}/>
              <Btn ghost size="sm" onClick={()=>{ if (!uploading) fileRef.current?.click(); }} disabled={uploading}><span style={{display:"inline-flex",alignItems:"center",gap:6}}>{Ic.upload} Upload</span></Btn>
            </div>
          </Field>
          <Field label="Alt text" hint="accessibility + SEO"><Input multiline value={frame.alt||""} onChange={v=>onChange({alt:v})}/></Field>
        </div>
      </div>
    </div>
  );
}

function ThinkingView({ thinking, onChange }) {
  const u = (patch) => onChange({ ...thinking, ...patch });
  const paragraphs = thinking.paragraphs || [];
  const cta = thinking.cta || {};
  const updatePara = (i, v) => u({ paragraphs: paragraphs.map((p, j) => j === i ? v : p) });
  const addPara = () => u({ paragraphs: [...paragraphs, ""] });
  const removePara = (i) => u({ paragraphs: paragraphs.filter((_, j) => j !== i) });
  const movePara = (i, dir) => {
    const next = [...paragraphs];
    const j = i + dir;
    if (j < 0 || j >= next.length) return;
    [next[i], next[j]] = [next[j], next[i]];
    u({ paragraphs: next });
  };
  return (
    <div>
      <PanelHeader title="Thinking" subtitle="The thesis section — Self-Evolving Plugin Framework pitch"/>
      <div style={{ padding: "18px 26px", maxWidth: 820 }}>
        <Field label="Eyebrow"><Input value={thinking.eyebrow||""} onChange={v=>u({eyebrow:v})}/></Field>
        <Field label="Headline"><Input value={thinking.headline||""} onChange={v=>u({headline:v})}/></Field>
        <Field label="Lead" hint="short paragraph next to the headline"><Input multiline value={thinking.lead||""} onChange={v=>u({lead:v})}/></Field>
        <Field label="Pull quote" hint="rendered in <blockquote> — leave empty to hide"><Input multiline value={thinking.quote||""} onChange={v=>u({quote:v})}/></Field>

        <div style={{ fontSize: 10, color: A.dim2, textTransform: "uppercase", letterSpacing: ".12em", fontFamily: "JetBrains Mono, monospace", margin: "22px 0 10px" }}>
          Paragraphs <span style={{ color: A.cyan, textTransform: "none", letterSpacing: 0, fontStyle: "italic" }}>— inline &lt;strong&gt; / &lt;em&gt; allowed</span>
        </div>
        {paragraphs.map((p, i) => (
          <div key={i} style={{ padding: 12, background: A.panel, border: `1px solid ${A.line}`, borderRadius: 6, marginBottom: 10 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 8 }}>
              <span style={{ fontSize: 10.5, color: A.dim2, fontFamily: "JetBrains Mono, monospace", letterSpacing: ".08em" }}>#{i + 1}</span>
              <div style={{ flex: 1 }}/>
              <button onClick={()=>movePara(i, -1)} disabled={i === 0} style={{ background: "transparent", border: "none", color: i === 0 ? A.line2 : A.dim2, cursor: i === 0 ? "default" : "pointer", padding: 4, transform: "rotate(180deg)" }}>{Ic.chev}</button>
              <button onClick={()=>movePara(i, 1)} disabled={i === paragraphs.length - 1} style={{ background: "transparent", border: "none", color: i === paragraphs.length - 1 ? A.line2 : A.dim2, cursor: i === paragraphs.length - 1 ? "default" : "pointer", padding: 4 }}>{Ic.chev}</button>
              <button onClick={()=>removePara(i)} style={{ background: "transparent", border: "none", color: A.dim2, cursor: "pointer", padding: 4 }}>{Ic.trash}</button>
            </div>
            <Input multiline value={p} onChange={v=>updatePara(i, v)} placeholder="Paragraph text (HTML <strong>/<em> allowed)"/>
          </div>
        ))}
        <button onClick={addPara} style={{ padding: "8px 12px", background: "transparent", border: `1px dashed ${A.line2}`, color: A.dim, fontSize: 12, cursor: "pointer", borderRadius: 4, fontFamily: "inherit" }}>+ add paragraph</button>

        <div style={{ fontSize: 10, color: A.dim2, textTransform: "uppercase", letterSpacing: ".12em", fontFamily: "JetBrains Mono, monospace", margin: "26px 0 10px" }}>Call-to-action</div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 18 }}>
          <Field label="CTA label"><Input value={cta.label||""} onChange={v=>u({cta: {...cta, label: v}})}/></Field>
          <Field label="CTA link" mono><Input mono value={cta.href||""} onChange={v=>u({cta: {...cta, href: v}})}/></Field>
        </div>
      </div>
    </div>
  );
}

function SupportView({ support, onChange }) {
  const u = (patch) => onChange({ ...support, ...patch });
  const cta = support.cta || {};
  return (
    <div>
      <PanelHeader title="Support" subtitle="Sponsor CTA band above the contact footer"/>
      <div style={{ padding: "18px 26px", maxWidth: 820 }}>
        <Field label="Headline"><Input value={support.headline||""} onChange={v=>u({headline:v})}/></Field>
        <Field label="Body"><Input multiline value={support.body||""} onChange={v=>u({body:v})}/></Field>

        <div style={{ fontSize: 10, color: A.dim2, textTransform: "uppercase", letterSpacing: ".12em", fontFamily: "JetBrains Mono, monospace", margin: "22px 0 10px" }}>Call-to-action</div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 18 }}>
          <Field label="CTA label"><Input value={cta.label||""} onChange={v=>u({cta: {...cta, label: v}})}/></Field>
          <Field label="CTA link" mono hint="e.g. github.com/sponsors/…"><Input mono value={cta.href||""} onChange={v=>u({cta: {...cta, href: v}})}/></Field>
        </div>
      </div>
    </div>
  );
}

function ContactView({ contact, onChange }) {
  const u = (patch) => onChange({ ...contact, ...patch });
  const pcta = contact.primaryCta || {};
  const rows = contact.rows || [];
  const updateRow = (i, patch) => u({ rows: rows.map((r, j) => j === i ? { ...r, ...patch } : r) });
  const addRow = () => u({ rows: [...rows, { label: "", value: "", href: "" }] });
  const removeRow = (i) => u({ rows: rows.filter((_, j) => j !== i) });
  const moveRow = (i, dir) => {
    const next = [...rows];
    const j = i + dir;
    if (j < 0 || j >= next.length) return;
    [next[i], next[j]] = [next[j], next[i]];
    u({ rows: next });
  };
  return (
    <div>
      <PanelHeader title="Contact" subtitle="Email CTA + contact rows (github, email, sponsors, etc.)" actions={<Btn primary onClick={addRow}><span style={{display:"inline-flex",alignItems:"center",gap:6}}>{Ic.plus} Add row</span></Btn>}/>
      <div style={{ padding: "18px 26px", maxWidth: 820 }}>
        <Field label="Eyebrow"><Input value={contact.eyebrow||""} onChange={v=>u({eyebrow:v})}/></Field>
        <Field label="Headline"><Input value={contact.headline||""} onChange={v=>u({headline:v})}/></Field>
        <Field label="Lead"><Input multiline value={contact.lead||""} onChange={v=>u({lead:v})}/></Field>

        <div style={{ fontSize: 10, color: A.dim2, textTransform: "uppercase", letterSpacing: ".12em", fontFamily: "JetBrains Mono, monospace", margin: "22px 0 10px" }}>Primary CTA</div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 18 }}>
          <Field label="CTA label"><Input value={pcta.label||""} onChange={v=>u({primaryCta: {...pcta, label: v}})}/></Field>
          <Field label="CTA link" mono><Input mono value={pcta.href||""} onChange={v=>u({primaryCta: {...pcta, href: v}})}/></Field>
        </div>

        <div style={{ fontSize: 10, color: A.dim2, textTransform: "uppercase", letterSpacing: ".12em", fontFamily: "JetBrains Mono, monospace", margin: "22px 0 10px" }}>
          Contact rows <span style={{ color: A.cyan, textTransform: "none", letterSpacing: 0, fontStyle: "italic" }}>— https:// links open in new tab, mailto:/tel: stay in-window</span>
        </div>
        {rows.length === 0 && (
          <div style={{ padding: "14px 18px", border: `1px dashed ${A.line2}`, borderRadius: 6, color: A.dim, fontSize: 12, marginBottom: 10 }}>
            No rows. Add one to populate the contact sidebar.
          </div>
        )}
        {rows.map((r, i) => (
          <div key={i} style={{ padding: 12, background: A.panel, border: `1px solid ${A.line}`, borderRadius: 6, marginBottom: 10 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 8 }}>
              <span style={{ fontSize: 10.5, color: A.dim2, fontFamily: "JetBrains Mono, monospace", letterSpacing: ".08em" }}>#{i + 1}</span>
              <div style={{ flex: 1 }}/>
              <button onClick={()=>moveRow(i, -1)} disabled={i === 0} style={{ background: "transparent", border: "none", color: i === 0 ? A.line2 : A.dim2, cursor: i === 0 ? "default" : "pointer", padding: 4, transform: "rotate(180deg)" }}>{Ic.chev}</button>
              <button onClick={()=>moveRow(i, 1)} disabled={i === rows.length - 1} style={{ background: "transparent", border: "none", color: i === rows.length - 1 ? A.line2 : A.dim2, cursor: i === rows.length - 1 ? "default" : "pointer", padding: 4 }}>{Ic.chev}</button>
              <button onClick={()=>removeRow(i)} style={{ background: "transparent", border: "none", color: A.dim2, cursor: "pointer", padding: 4 }}>{Ic.trash}</button>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "140px 1fr", gap: 10, marginBottom: 8 }}>
              <Input value={r.label||""} onChange={v=>updateRow(i,{label:v})} placeholder="label (e.g. email)"/>
              <Input value={r.value||""} onChange={v=>updateRow(i,{value:v})} placeholder="display value"/>
            </div>
            <Input mono value={r.href||""} onChange={v=>updateRow(i,{href:v})} placeholder="https://… or mailto:…"/>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// Stories — markdown files under content/stories/
// ─────────────────────────────────────────────────────────────
const STORIES_DIR = "content/stories";
const NEW_KEY = "__new__";

function StoriesView({ token, onToast }) {
  const [files, setFiles] = React.useState([]);
  const [loading, setLoading] = React.useState(true);
  const [selected, setSelected] = React.useState(null); // filename or NEW_KEY
  const [text, setText] = React.useState("");
  const [origText, setOrigText] = React.useState("");
  const [sha, setSha] = React.useState(null);
  const [loadingFile, setLoadingFile] = React.useState(false);
  const [saving, setSaving] = React.useState(false);
  const [newName, setNewName] = React.useState("");

  const dirty = selected !== null && text !== origText;

  const loadList = React.useCallback(async () => {
    setLoading(true);
    try {
      const items = (await listDir(token, STORIES_DIR)).filter(f => f.type === "file" && f.name.endsWith(".md"));
      items.sort((a, b) => a.name.localeCompare(b.name));
      setFiles(items);
    } catch (ex) {
      onToast?.(`Failed to list stories: ${ex.message}`, "red", 6000);
    } finally {
      setLoading(false);
    }
  }, [token, onToast]);

  React.useEffect(() => { loadList(); }, [loadList]);

  const openFile = async (f) => {
    if (dirty && !window.confirm("Discard unsaved changes?")) return;
    setSelected(f.name);
    setLoadingFile(true);
    setText(""); setOrigText(""); setSha(null);
    try {
      const { content, sha: s } = await fetchFileText(token, f.path);
      setText(content);
      setOrigText(content);
      setSha(s);
    } catch (ex) {
      onToast?.(`Failed to load ${f.name}: ${ex.message}`, "red", 6000);
    } finally {
      setLoadingFile(false);
    }
  };

  const startNew = () => {
    if (dirty && !window.confirm("Discard unsaved changes?")) return;
    setSelected(NEW_KEY);
    setNewName("");
    setText("# New story\n\n");
    setOrigText("");
    setSha(null);
  };

  const save = async () => {
    if (saving) return;
    let path, filename;
    if (selected === NEW_KEY) {
      filename = newName.trim().toLowerCase().replace(/[^a-z0-9.-]+/g, "-").replace(/^-|-$/g, "");
      if (!filename) { onToast?.("Enter a filename.", "amber", 3000); return; }
      if (!filename.endsWith(".md")) filename += ".md";
      if (files.some(f => f.name === filename)) { onToast?.(`${filename} already exists.`, "amber", 3500); return; }
      path = `${STORIES_DIR}/${filename}`;
    } else {
      filename = selected;
      path = `${STORIES_DIR}/${filename}`;
    }
    setSaving(true);
    try {
      const { sha: newSha } = await writeFileText(token, path, text, sha, sha ? `admin: update ${path}` : `admin: create ${path}`);
      setSha(newSha);
      setOrigText(text);
      if (selected === NEW_KEY) {
        setSelected(filename);
      }
      onToast?.(sha ? `Saved ${filename}.` : `Created ${filename}.`, "green", 3000);
      await loadList();
    } catch (ex) {
      onToast?.(`Save failed: ${ex.message}`, "red", 6000);
    } finally {
      setSaving(false);
    }
  };

  const removeFile = async () => {
    if (!selected || selected === NEW_KEY || !sha) return;
    if (!window.confirm(`Delete ${selected}? This creates a delete commit on main.`)) return;
    setSaving(true);
    try {
      await deleteFile(token, `${STORIES_DIR}/${selected}`, sha, `admin: delete ${STORIES_DIR}/${selected}`);
      onToast?.(`Deleted ${selected}.`, "green", 3000);
      setSelected(null); setText(""); setOrigText(""); setSha(null);
      await loadList();
    } catch (ex) {
      onToast?.(`Delete failed: ${ex.message}`, "red", 6000);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div>
      <PanelHeader
        title="Stories"
        subtitle={`Markdown files in ${STORIES_DIR}/ — long-form case studies, handoff write-ups, sub-pages`}
        actions={<Btn primary onClick={startNew}><span style={{display:"inline-flex",alignItems:"center",gap:6}}>{Ic.plus} New story</span></Btn>}
      />
      <div style={{ display: "grid", gridTemplateColumns: "280px 1fr", minHeight: 600 }}>
        <div style={{ borderRight: `1px solid ${A.line}`, padding: "10px 8px", overflow: "auto" }}>
          {loading && <div style={{ padding: "10px 12px", fontSize: 11, color: A.dim2, fontFamily: "JetBrains Mono, monospace" }}>loading…</div>}
          {!loading && files.length === 0 && (
            <div style={{ padding: "14px 18px", color: A.dim2, fontSize: 11.5, lineHeight: 1.55 }}>
              No stories yet. Click "New story" to create one.
            </div>
          )}
          {files.map(f => {
            const active = selected === f.name;
            return (
              <button key={f.name} onClick={()=>openFile(f)} style={{
                display: "flex", flexDirection: "column", gap: 2, width: "100%",
                padding: "8px 10px", background: active ? "rgba(23,212,250,.06)" : "transparent",
                border: "none", borderLeft: `2px solid ${active ? A.cyan : "transparent"}`,
                cursor: "pointer", textAlign: "left", borderRadius: 0,
                color: active ? A.text : A.dim, fontFamily: "inherit", marginBottom: 2,
              }}>
                <span style={{ fontSize: 12.5, fontFamily: "JetBrains Mono, monospace" }}>{f.name}</span>
                <span style={{ fontSize: 10, color: A.dim2, fontFamily: "JetBrains Mono, monospace" }}>{Math.round(f.size / 1024 * 10) / 10} KB</span>
              </button>
            );
          })}
        </div>

        <div style={{ padding: "16px 20px", display: "flex", flexDirection: "column", minHeight: 0 }}>
          {selected === null && (
            <div style={{ color: A.dim, fontSize: 12.5, lineHeight: 1.6, padding: "8px 0" }}>
              Pick a story on the left to edit, or start a new one.
            </div>
          )}

          {selected !== null && (
            <>
              <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 12 }}>
                {selected === NEW_KEY ? (
                  <>
                    <span style={{ fontSize: 10.5, color: A.dim2, fontFamily: "JetBrains Mono, monospace", letterSpacing: ".08em", textTransform: "uppercase" }}>New · {STORIES_DIR}/</span>
                    <Input mono value={newName} onChange={setNewName} placeholder="filename.md"/>
                  </>
                ) : (
                  <span style={{ fontSize: 12, fontFamily: "JetBrains Mono, monospace", color: A.text }}>{STORIES_DIR}/{selected}</span>
                )}
                <div style={{ flex: 1 }}/>
                {selected !== NEW_KEY && (
                  <Btn danger size="sm" onClick={removeFile} disabled={saving}><span style={{display:"inline-flex",alignItems:"center",gap:6}}>{Ic.trash} Delete</span></Btn>
                )}
                <Btn primary size="sm" onClick={save} disabled={saving || (!dirty && selected !== NEW_KEY) || loadingFile}>
                  <span style={{display:"inline-flex",alignItems:"center",gap:6}}>{Ic.save} {saving ? "saving…" : dirty || selected === NEW_KEY ? "Save" : "Saved"}</span>
                </Btn>
              </div>

              {loadingFile ? (
                <div style={{ padding: 20, color: A.dim2, fontSize: 12, fontFamily: "JetBrains Mono, monospace" }}>loading file…</div>
              ) : (
                <textarea
                  value={text}
                  onChange={e => setText(e.target.value)}
                  spellCheck
                  style={{
                    flex: 1, minHeight: 420,
                    padding: "14px 16px",
                    background: "#05070b", color: A.text,
                    border: `1px solid ${A.line2}`, borderRadius: 6,
                    fontFamily: "JetBrains Mono, ui-monospace, monospace",
                    fontSize: 12.5, lineHeight: 1.65,
                    outline: "none", resize: "vertical",
                  }}
                />
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}


// ─────────────────────────────────────────────────────────────
// Ops — GitHub Actions bot-runs dashboard
// ─────────────────────────────────────────────────────────────
const BOT_WORKFLOWS = [
  { file: "build-widget.yml",         label: "Build widget",        trigger: "on widget src push" },
  { file: "refresh-bacon-shards.yml", label: "Refresh bacon shards", trigger: "daily · 06:00 UTC" },
  { file: "rebuild-hub.yml",          label: "Rebuild hub",          trigger: "on content/site.json push" },
  { file: "track-traffic.yml",        label: "Track traffic (plugin repos)", trigger: "daily · 06:00 UTC" },
  { file: "fetch-site-stats.yml",     label: "Fetch site stats (GoatCounter)", trigger: "daily · 06:30 UTC" },
];

async function fetchWorkflowRuns(file, token) {
  const headers = token
    ? { Authorization: `Bearer ${token}`, Accept: "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28" }
    : { Accept: "application/vnd.github+json" };
  const url = `https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/actions/workflows/${encodeURIComponent(file)}/runs?per_page=10`;
  const res = await fetch(url, { headers });
  if (!res.ok) throw new Error(`${file} → ${res.status}`);
  const body = await res.json();
  return body.workflow_runs || [];
}

function OpsView({ token }) {
  const [runs, setRuns] = React.useState({});   // { [file]: run[] }
  const [errors, setErrors] = React.useState({}); // { [file]: message }
  const [loading, setLoading] = React.useState(true);
  const [reloadKey, setReloadKey] = React.useState(0);

  React.useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setErrors({});
    Promise.allSettled(BOT_WORKFLOWS.map(w => fetchWorkflowRuns(w.file, token))).then(results => {
      if (cancelled) return;
      const nextRuns = {};
      const nextErrors = {};
      results.forEach((r, i) => {
        const file = BOT_WORKFLOWS[i].file;
        if (r.status === "fulfilled") nextRuns[file] = r.value;
        else nextErrors[file] = r.reason?.message || String(r.reason);
      });
      setRuns(nextRuns);
      setErrors(nextErrors);
      setLoading(false);
    });
    return () => { cancelled = true; };
  }, [token, reloadKey]);

  return (
    <div>
      <PanelHeader
        title="Ops"
        subtitle="Bot workflows pushing to main — build-widget, refresh-bacon-shards, rebuild-hub, track-traffic"
        actions={<Btn ghost size="sm" onClick={()=>setReloadKey(k=>k+1)} disabled={loading}><span style={{display:"inline-flex",alignItems:"center",gap:6}}>{Ic.refresh} {loading ? "loading…" : "Refresh"}</span></Btn>}
      />
      <div style={{ padding: "18px 26px", maxWidth: 960 }}>
        {BOT_WORKFLOWS.map(w => (
          <WorkflowCard key={w.file} meta={w} runs={runs[w.file]} error={errors[w.file]} loading={loading}/>
        ))}
      </div>
    </div>
  );
}

function WorkflowCard({ meta, runs, error, loading }) {
  const latest = runs?.[0];
  const latestTone =
    latest?.conclusion === "success" ? A.green :
    latest?.conclusion === "failure" || latest?.conclusion === "cancelled" || latest?.conclusion === "timed_out" ? A.danger :
    latest?.status === "in_progress" || latest?.status === "queued" ? A.amber :
    A.dim2;

  return (
    <div style={{ padding: 16, background: A.panel, border: `1px solid ${A.line}`, borderRadius: 8, marginBottom: 14 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 12 }}>
        <span style={{ display: "inline-block", width: 9, height: 9, borderRadius: 99, background: latestTone, boxShadow: `0 0 10px ${latestTone}` }}/>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 13, fontWeight: 600, color: A.text }}>{meta.label}</div>
          <div style={{ fontSize: 10.5, color: A.dim2, fontFamily: "JetBrains Mono, monospace", letterSpacing: ".04em", marginTop: 2 }}>{meta.file} · {meta.trigger}</div>
        </div>
        <a href={`https://github.com/${REPO_OWNER}/${REPO_NAME}/actions/workflows/${meta.file}`} target="_blank" rel="noopener" style={{ fontSize: 10.5, color: A.cyan, fontFamily: "JetBrains Mono, monospace", textDecoration: "none" }}>open in GitHub ↗</a>
      </div>

      {error && (
        <div style={{ padding: "10px 12px", background: "rgba(255,107,107,.08)", border: `1px solid rgba(255,107,107,.32)`, borderRadius: 5, color: A.danger, fontSize: 11.5, fontFamily: "JetBrains Mono, monospace" }}>{error}</div>
      )}

      {!error && (runs === undefined || loading) && (
        <div style={{ fontSize: 11, color: A.dim2, fontFamily: "JetBrains Mono, monospace" }}>loading runs…</div>
      )}

      {!error && runs && runs.length === 0 && (
        <div style={{ fontSize: 11, color: A.dim2 }}>No runs yet.</div>
      )}

      {!error && runs && runs.length > 0 && (
        <>
          <div style={{ display: "flex", gap: 4, marginBottom: 10 }}>
            {runs.map(r => {
              const tone =
                r.conclusion === "success" ? A.green :
                r.conclusion === "failure" || r.conclusion === "cancelled" || r.conclusion === "timed_out" ? A.danger :
                r.status === "in_progress" || r.status === "queued" ? A.amber :
                A.dim2;
              return (
                <a key={r.id} href={r.html_url} target="_blank" rel="noopener"
                   title={`${r.conclusion || r.status} · ${new Date(r.created_at).toLocaleString()} · ${r.head_commit?.message?.split("\n")[0] || r.head_sha?.slice(0,7)}`}
                   style={{ width: 22, height: 22, background: tone, borderRadius: 3, cursor: "pointer", opacity: 0.85, transition: "opacity .1s" }}
                   onMouseEnter={(e)=>e.currentTarget.style.opacity = "1"}
                   onMouseLeave={(e)=>e.currentTarget.style.opacity = "0.85"}
                />
              );
            })}
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "80px 1fr auto", gap: 10, fontSize: 11, alignItems: "center" }}>
            <span style={{ color: A.dim2, fontFamily: "JetBrains Mono, monospace", letterSpacing: ".06em", textTransform: "uppercase" }}>Latest</span>
            <span style={{ color: A.text, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
              {latest.head_commit?.message?.split("\n")[0] || "(no message)"}
            </span>
            <span style={{ color: A.dim, fontFamily: "JetBrains Mono, monospace", fontSize: 10.5 }}>
              {new Date(latest.created_at).toLocaleString([], { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })}
            </span>
          </div>
        </>
      )}
    </div>
  );
}

function SectionsView({ sections, onChange }) {
  const rows = [
    { key: "thinking", label: "Thinking behind it", desc: "Framework thesis + Self-Evolving Plugin Framework link" },
    { key: "labRuns", label: "How the lab runs", desc: "Private Agent OS dashboard screenshots + caption" },
    { key: "lab", label: "Also from the lab", desc: "JS-shuffled shelf of 8 other projects" },
    { key: "play", label: "Play", desc: "Embedded games — Birthday Bacon Trail widget" },
    { key: "about", label: "About 626 Labs", desc: "Manifesto — paragraphs + 3 guiding principles" },
    { key: "support", label: "Keep the lab running", desc: "GitHub Sponsors CTA block" },
    { key: "contact", label: "Contact", desc: "Email + GitHub + support rows" },
  ];
  return (
    <div>
      <PanelHeader title="Sections" subtitle="Toggle whole sections on or off"/>
      <div style={{ padding: "6px 26px 18px" }}>
        {rows.map(r => (
          <div key={r.key} style={{ padding: "14px 0", borderBottom: `1px solid ${A.line}`, display: "flex", alignItems: "center", gap: 14 }}>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 13, fontWeight: 500 }}>{r.label}</div>
              <div style={{ fontSize: 11.5, color: A.dim, marginTop: 2 }}>{r.desc}</div>
            </div>
            <div style={{ fontSize: 10.5, color: A.dim2, fontFamily: "JetBrains Mono, monospace" }}>{sections[r.key]?.enabled ? "VISIBLE" : "HIDDEN"}</div>
            <Toggle on={sections[r.key]?.enabled} onChange={v=>onChange({ ...sections, [r.key]: { enabled: v } })}/>
          </div>
        ))}
      </div>
    </div>
  );
}

function Toggle({ on, onChange }) {
  return (
    <button onClick={()=>onChange?.(!on)} style={{
      width: 40, height: 22, borderRadius: 999, background: on ? A.cyan : A.line2,
      border: "none", position: "relative", cursor: "pointer", transition: "background .15s",
    }}>
      <span style={{ position: "absolute", top: 2, left: on ? 20 : 2, width: 18, height: 18, borderRadius: 999, background: A.bg, transition: "left .15s" }}/>
    </button>
  );
}

// ─────────────────────────────────────────────────────────────
// Analytics — site visits (committed JSON) + plugin-repo traffic (CSV)
// ─────────────────────────────────────────────────────────────
// Site stats are fetched by .github/workflows/fetch-site-stats.yml
// (daily 06:30 UTC) and committed to data/site-stats.json. The admin
// reads the committed JSON via the Contents API — we don't hit
// GoatCounter directly because (a) /stats/hits fails CORS preflight,
// and (b) the free-tier API rate-limits at ~5 req/min.

function parseTrafficCSV(text) {
  const lines = text.trim().split("\n");
  if (lines.length < 2) return [];
  const cols = lines[0].split(",");
  return lines.slice(1).map(line => {
    const vals = line.split(",");
    const row = {};
    cols.forEach((c, i) => { row[c] = vals[i]; });
    return row;
  });
}

function MiniSparkline({ values, w, h, color }) {
  if (!values || values.length === 0) return null;
  const ww = w || 120, hh = h || 28;
  const max = Math.max(...values, 1);
  const stepX = values.length > 1 ? ww / (values.length - 1) : ww;
  const pts = values.map((v, i) => {
    const x = i * stepX;
    const y = hh - (v / max) * (hh - 2) - 1;
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(" ");
  const area = `0,${hh} ${pts} ${ww},${hh}`;
  const c = color || A.cyan;
  return (
    <svg width={ww} height={hh} viewBox={`0 0 ${ww} ${hh}`} style={{ display: "block" }}>
      <polygon points={area} fill={c} fillOpacity="0.12"/>
      <polyline points={pts} fill="none" stroke={c} strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );
}

function DailyChart({ days, color }) {
  if (!days || days.length === 0) {
    return <div style={{ padding: 24, color: A.dim2, fontSize: 12, textAlign: "center" }}>No data in this window yet.</div>;
  }
  const w = 760, h = 200;
  const padL = 38, padR = 12, padT = 12, padB = 28;
  const innerW = w - padL - padR, innerH = h - padT - padB;
  const counts = days.map(d => d.count || 0);
  const max = Math.max(...counts, 1);
  const stepX = days.length > 1 ? innerW / (days.length - 1) : innerW;
  const pts = days.map((d, i) => ({
    x: padL + i * stepX,
    y: padT + innerH - ((d.count || 0) / max) * innerH,
    day: d.day, count: d.count || 0,
  }));
  const linePath = pts.map((p, i) => `${i === 0 ? "M" : "L"} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(" ");
  const lastPt = pts[pts.length - 1];
  const firstPt = pts[0];
  const areaPath = `${linePath} L ${lastPt.x.toFixed(1)} ${(padT + innerH).toFixed(1)} L ${firstPt.x.toFixed(1)} ${(padT + innerH).toFixed(1)} Z`;
  const c = color || A.cyan;
  const gridYs = [0, 0.25, 0.5, 0.75, 1].map(t => padT + innerH - t * innerH);
  const labelIdx = [0, Math.floor(pts.length / 2), pts.length - 1];
  return (
    <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} style={{ display: "block", maxWidth: "100%", height: "auto" }} preserveAspectRatio="xMidYMid meet">
      <defs>
        <linearGradient id="dailyChartGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={c} stopOpacity="0.35"/>
          <stop offset="100%" stopColor={c} stopOpacity="0"/>
        </linearGradient>
      </defs>
      {gridYs.map((y, i) => (
        <line key={i} x1={padL} y1={y} x2={padL + innerW} y2={y} stroke={A.line} strokeWidth="1" strokeDasharray={i === gridYs.length - 1 ? "0" : "2 4"}/>
      ))}
      <text x={padL - 6} y={padT + 4} textAnchor="end" fontSize="10" fill={A.dim2} fontFamily="JetBrains Mono, monospace">{max}</text>
      <text x={padL - 6} y={padT + innerH + 4} textAnchor="end" fontSize="10" fill={A.dim2} fontFamily="JetBrains Mono, monospace">0</text>
      <path d={areaPath} fill="url(#dailyChartGrad)"/>
      <path d={linePath} fill="none" stroke={c} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
      {pts.map((p, i) => (
        <circle key={i} cx={p.x} cy={p.y} r={i === pts.length - 1 ? 3 : 1.6} fill={c}/>
      ))}
      {labelIdx.map(i => pts[i] && (
        <text key={`lbl${i}`} x={pts[i].x} y={h - 8} textAnchor="middle" fontSize="10" fill={A.dim2} fontFamily="JetBrains Mono, monospace">{(pts[i].day || "").slice(5)}</text>
      ))}
    </svg>
  );
}

function LeaderboardList({ items, accent, emptyLabel }) {
  if (!items || items.length === 0) {
    return <div style={{ padding: "10px 0", fontSize: 12, color: A.dim2 }}>{emptyLabel || "No data yet."}</div>;
  }
  const max = Math.max(...items.map(it => it.count || 0), 1);
  const c = accent || A.cyan;
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>
      {items.map((it, i) => (
        <div key={i} style={{
          display: "grid", gridTemplateColumns: "1fr auto", gap: 14, alignItems: "center",
          padding: "9px 0", borderBottom: i < items.length - 1 ? `1px solid ${A.line}` : "none",
        }}>
          <div style={{ minWidth: 0 }}>
            <div title={it.label} style={{ fontSize: 12, color: A.text, fontFamily: "JetBrains Mono, monospace", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{it.label || "(empty)"}</div>
            <div style={{ height: 3, background: "rgba(255,255,255,.04)", borderRadius: 2, marginTop: 5, overflow: "hidden" }}>
              <div style={{ width: `${(it.count / max) * 100}%`, height: "100%", background: c, borderRadius: 2 }}/>
            </div>
          </div>
          <div style={{ fontSize: 12, fontFamily: "JetBrains Mono, monospace", color: c, textAlign: "right", minWidth: 56 }}>
            <div>{(it.count || 0).toLocaleString()}</div>
            {it.unique != null && <div style={{ fontSize: 10, color: A.dim2, marginTop: 1 }}>{(it.unique || 0).toLocaleString()} uniq</div>}
          </div>
        </div>
      ))}
    </div>
  );
}

function TabBar({ value, onChange, options }) {
  return (
    <div style={{ display: "inline-flex", padding: 3, background: A.panel2, border: `1px solid ${A.line}`, borderRadius: 8, gap: 2 }}>
      {options.map(opt => {
        const active = value === opt.value;
        return (
          <button key={opt.value} onClick={() => onChange(opt.value)} style={{
            padding: "6px 14px", border: "none", borderRadius: 5,
            background: active ? A.cyan : "transparent",
            color: active ? A.bg : A.dim,
            fontFamily: "inherit", fontSize: 11.5, fontWeight: active ? 600 : 500,
            letterSpacing: ".02em", cursor: "pointer",
          }}>{opt.label}</button>
        );
      })}
    </div>
  );
}

function SiteStatsBootstrap({ onTriggerFresh, onRefresh, triggering, dispatchStatus }) {
  return (
    <div style={{ maxWidth: 720 }}>
      <div style={{ background: A.panel, border: `1px solid ${A.line}`, borderRadius: 8, padding: 22 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
          <span style={{ width: 8, height: 8, borderRadius: 99, background: A.amber, boxShadow: `0 0 8px ${A.amber}` }}/>
          <div style={{ fontSize: 14, fontWeight: 600 }}>Site stats workflow hasn't run yet</div>
        </div>
        <div style={{ fontSize: 12, color: A.dim, lineHeight: 1.6, marginBottom: 14 }}>
          The tracking script is collecting visits at{" "}
          <a href="https://626labs.goatcounter.com" target="_blank" rel="noopener" style={{ color: A.cyan, textDecoration: "none", borderBottom: `1px solid ${A.cyan}` }}>626labs.goatcounter.com</a>{" "}
          but <code style={{ background: A.panel2, padding: "1px 5px", borderRadius: 3, fontFamily: "JetBrains Mono, monospace", fontSize: 11 }}>data/site-stats.json</code> doesn't exist in the repo yet. Two ways to populate it:
        </div>
        <div style={{ background: A.panel2, border: `1px solid ${A.line}`, borderRadius: 6, padding: 14, fontSize: 11.5, color: A.dim, lineHeight: 1.7, marginBottom: 14, fontFamily: "JetBrains Mono, monospace" }}>
          <div style={{ color: A.cyan, marginBottom: 4 }}># Option A — kick off the workflow now</div>
          <div>1. Add a GitHub Actions secret named <span style={{ color: A.text }}>GOATCOUNTER_TOKEN</span></div>
          <div>2. Click <span style={{ color: A.cyan }}>Trigger fresh fetch</span> below</div>
          <div>3. Reload after ~30 seconds</div>
          <div style={{ color: A.cyan, margin: "10px 0 4px" }}># Option B — bootstrap from your machine</div>
          <div>$ GOATCOUNTER_TOKEN=&lt;your_token&gt; node scripts/fetch-site-stats.mjs</div>
          <div>$ git add data/site-stats.json && git commit -m "site-stats: first snapshot" && git push</div>
        </div>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <Btn primary onClick={onTriggerFresh} disabled={triggering}>{triggering ? "Triggering…" : "Trigger fresh fetch"}</Btn>
          <Btn ghost size="sm" onClick={onRefresh}><span style={{display:"inline-flex",alignItems:"center",gap:6}}>{Ic.refresh} Reload</span></Btn>
          {dispatchStatus && <span style={{ fontSize: 11, color: dispatchStatus.ok ? A.green : A.danger, fontFamily: "JetBrains Mono, monospace" }}>{dispatchStatus.message}</span>}
        </div>
      </div>
      <div style={{ marginTop: 14, fontSize: 11.5, color: A.dim, lineHeight: 1.6 }}>
        Meanwhile the <b style={{ color: A.text }}>Plugin repos</b> tab still works — it reads <code style={{ background: A.panel2, padding: "1px 5px", borderRadius: 3, fontFamily: "JetBrains Mono, monospace", fontSize: 11 }}>data/traffic.csv</code> from this repo, separate path entirely.
      </div>
    </div>
  );
}

function SiteStats({ token }) {
  const [data, setData] = React.useState(null);
  const [error, setError] = React.useState(null);
  const [missing, setMissing] = React.useState(false);
  const [loading, setLoading] = React.useState(true);
  const [reloadKey, setReloadKey] = React.useState(0);
  const [triggering, setTriggering] = React.useState(false);
  const [dispatchStatus, setDispatchStatus] = React.useState(null);

  React.useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    setMissing(false);
    const headers = { Accept: "application/vnd.github.raw", "X-GitHub-Api-Version": "2022-11-28" };
    if (token) headers.Authorization = `Bearer ${token}`;
    fetch(`https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/contents/data/site-stats.json?ref=${REPO_BRANCH}&t=${Date.now()}`, { headers, cache: "no-store" })
      .then(r => {
        if (r.status === 404) { setMissing(true); return null; }
        if (!r.ok) return r.text().then(t => Promise.reject(`${r.status} ${t.slice(0, 100)}`));
        return r.json();
      })
      .then(json => {
        if (cancelled) return;
        if (json) setData(json);
        setLoading(false);
      })
      .catch(e => {
        if (cancelled) return;
        setError(typeof e === "string" ? e : (e && e.message) || "Failed to load");
        setLoading(false);
      });
    return () => { cancelled = true; };
  }, [token, reloadKey]);

  async function triggerFresh() {
    if (!token) {
      setDispatchStatus({ ok: false, message: "no PAT loaded" });
      return;
    }
    setTriggering(true);
    setDispatchStatus(null);
    try {
      const res = await fetch(`https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/actions/workflows/fetch-site-stats.yml/dispatches`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          Accept: "application/vnd.github+json",
          "X-GitHub-Api-Version": "2022-11-28",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ ref: REPO_BRANCH }),
      });
      if (res.status === 204) {
        setDispatchStatus({ ok: true, message: "queued — reload in ~30s" });
      } else {
        const txt = await res.text();
        setDispatchStatus({ ok: false, message: `${res.status}: ${txt.slice(0, 80)}` });
      }
    } catch (e) {
      setDispatchStatus({ ok: false, message: (e && e.message) || "dispatch failed" });
    } finally {
      setTriggering(false);
    }
  }

  if (loading) {
    return <div style={{ padding: 56, color: A.dim, textAlign: "center", fontSize: 13 }}>Loading site analytics…</div>;
  }
  if (missing) {
    return <SiteStatsBootstrap onTriggerFresh={triggerFresh} onRefresh={() => setReloadKey(k => k + 1)} triggering={triggering} dispatchStatus={dispatchStatus}/>;
  }
  if (error) {
    return (
      <div style={{ background: "rgba(255,107,107,.06)", border: `1px solid rgba(255,107,107,.2)`, borderRadius: 8, padding: 18, maxWidth: 620 }}>
        <div style={{ color: A.danger, fontSize: 13, fontWeight: 500, marginBottom: 6 }}>Couldn't load site stats</div>
        <div style={{ color: A.dim, fontSize: 12, fontFamily: "JetBrains Mono, monospace", marginBottom: 14, wordBreak: "break-all" }}>{error}</div>
        <Btn ghost size="sm" onClick={() => setReloadKey(k => k + 1)}><span style={{display:"inline-flex",alignItems:"center",gap:6}}>{Ic.refresh} Retry</span></Btn>
      </div>
    );
  }
  if (!data) {
    return <SiteStatsBootstrap onTriggerFresh={triggerFresh} onRefresh={() => setReloadKey(k => k + 1)} triggering={triggering} dispatchStatus={dispatchStatus}/>;
  }
  return <SiteStatsDashboard data={data} onRefresh={() => setReloadKey(k => k + 1)} onTriggerFresh={triggerFresh} triggering={triggering} dispatchStatus={dispatchStatus}/>;
}

function fmtRelative(iso) {
  if (!iso) return "—";
  const ms = Date.now() - new Date(iso).getTime();
  if (ms < 0) return "just now";
  const min = Math.floor(ms / 60000);
  if (min < 1) return "just now";
  if (min < 60) return `${min}m ago`;
  const hr = Math.floor(min / 60);
  if (hr < 24) return `${hr}h ago`;
  const day = Math.floor(hr / 24);
  return `${day}d ago`;
}

function SiteStatsDashboard({ data, onRefresh, onTriggerFresh, triggering, dispatchStatus }) {
  const totalCount = data.total?.total || 0;
  const totalUnique = data.total?.total_unique || 0;
  const stats = data.total?.stats || [];
  const days = stats.map(s => ({ day: s.day, count: s.daily || 0 }));
  const dailyAvg = days.length ? Math.round(days.reduce((a, d) => a + d.count, 0) / days.length) : 0;
  const peakDay = days.reduce((a, b) => (b.count > a.count ? b : a), { day: "", count: 0 });

  const topPages = (data.hits?.hits || []).slice(0, 8).map(h => ({
    label: h.path || "/",
    count: h.count || 0,
    unique: h.count_unique,
  }));
  const topRefs = (data.refs?.stats || []).slice(0, 8).map(r => ({
    label: r.name || "(direct)",
    count: r.count || 0,
    unique: r.count_unique,
  }));
  const topLocs = (data.locations?.stats || []).slice(0, 6).map(l => ({
    label: l.name || l.id || "—",
    count: l.count || 0,
    unique: l.count_unique,
  }));
  const topBrowsers = (data.browsers?.stats || []).slice(0, 6).map(b => ({
    label: b.name || "—",
    count: b.count || 0,
    unique: b.count_unique,
  }));

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14, flexWrap: "wrap", gap: 12 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10, fontFamily: "JetBrains Mono, monospace", fontSize: 11, color: A.dim, letterSpacing: ".06em", flexWrap: "wrap" }}>
          <span style={{ width: 8, height: 8, borderRadius: 99, background: A.cyan, boxShadow: `0 0 8px ${A.cyan}` }}/>
          <span>{data.range?.start || "—"}</span>
          <span style={{ color: A.dim2 }}>→</span>
          <span>{data.range?.end || "—"}</span>
          <span style={{ color: A.dim2 }}>·</span>
          <span style={{ color: A.cyan }}>626labs.dev</span>
          <span style={{ color: A.dim2 }}>·</span>
          <span title={data.generatedAt}>fetched {fmtRelative(data.generatedAt)}</span>
        </div>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          {dispatchStatus && <span style={{ fontSize: 11, color: dispatchStatus.ok ? A.green : A.danger, fontFamily: "JetBrains Mono, monospace" }}>{dispatchStatus.message}</span>}
          <a href="https://626labs.goatcounter.com" target="_blank" rel="noopener" style={{ fontSize: 11, color: A.cyan, fontFamily: "JetBrains Mono, monospace", textDecoration: "none", padding: "6px 10px", border: `1px solid ${A.line2}`, borderRadius: 6 }}>open in GoatCounter ↗</a>
          <Btn ghost size="sm" onClick={onTriggerFresh} disabled={triggering}>{triggering ? "queueing…" : "Fetch fresh"}</Btn>
          <Btn ghost size="sm" onClick={onRefresh}><span style={{display:"inline-flex",alignItems:"center",gap:6}}>{Ic.refresh} Reload</span></Btn>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 12, marginBottom: 18 }}>
        <StatTile label="Total views" value={totalCount.toLocaleString()} sub={`last ${data.range?.days || 30} days`} c={A.cyan}/>
        <StatTile label="Unique visitors" value={totalUnique.toLocaleString()} sub="distinct browsers" c={A.magenta}/>
        <StatTile label="Daily average" value={dailyAvg.toLocaleString()} sub="views per day" c={A.green}/>
        <StatTile label="Peak day" value={peakDay.count ? peakDay.count.toLocaleString() : "—"} sub={peakDay.day || "no traffic yet"} c={A.amber}/>
      </div>

      <div style={{ background: A.panel, border: `1px solid ${A.line}`, borderRadius: 8, padding: 18, marginBottom: 14 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 12 }}>
          <SectionLabel>Daily views — 30-day trend</SectionLabel>
          <div style={{ fontSize: 10.5, color: A.dim2, fontFamily: "JetBrains Mono, monospace", letterSpacing: ".08em" }}>views per day</div>
        </div>
        <DailyChart days={days} color={A.cyan}/>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14, marginBottom: 14 }}>
        <div style={{ background: A.panel, border: `1px solid ${A.line}`, borderRadius: 8, padding: 18 }}>
          <SectionLabel>Top pages</SectionLabel>
          <LeaderboardList items={topPages} accent={A.cyan} emptyLabel="No page views yet — give it a few hours."/>
        </div>
        <div style={{ background: A.panel, border: `1px solid ${A.line}`, borderRadius: 8, padding: 18 }}>
          <SectionLabel>Top referrers</SectionLabel>
          <LeaderboardList items={topRefs} accent={A.magenta} emptyLabel="No referrers logged yet."/>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
        <div style={{ background: A.panel, border: `1px solid ${A.line}`, borderRadius: 8, padding: 18 }}>
          <SectionLabel>Top locations</SectionLabel>
          <LeaderboardList items={topLocs} accent={A.green} emptyLabel="No country data yet."/>
        </div>
        <div style={{ background: A.panel, border: `1px solid ${A.line}`, borderRadius: 8, padding: 18 }}>
          <SectionLabel>Browsers</SectionLabel>
          <LeaderboardList items={topBrowsers} accent={A.amber} emptyLabel="No browser data yet."/>
        </div>
      </div>
    </div>
  );
}

function RepoStats({ token }) {
  const [rows, setRows] = React.useState(null);
  const [repoIndex, setRepoIndex] = React.useState(null); // discovered-repos sidecar
  const [error, setError] = React.useState(null);
  const [loading, setLoading] = React.useState(true);
  const [reloadKey, setReloadKey] = React.useState(0);
  const [sortBy, setSortBy] = React.useState("unique_cloners");
  const [sortDir, setSortDir] = React.useState("desc");
  const [hideZero, setHideZero] = React.useState(true);
  const [search, setSearch] = React.useState("");
  const [triggering, setTriggering] = React.useState(false);
  const [dispatchStatus, setDispatchStatus] = React.useState(null);

  React.useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    const headers = { Accept: "application/vnd.github.raw", "X-GitHub-Api-Version": "2022-11-28" };
    if (token) headers.Authorization = `Bearer ${token}`;
    const stamp = Date.now();
    Promise.all([
      fetch(`https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/contents/data/traffic.csv?ref=${REPO_BRANCH}&t=${stamp}`, { headers, cache: "no-store" })
        .then(r => r.ok ? r.text() : r.text().then(t => Promise.reject(`traffic.csv ${r.status} ${t.slice(0, 80)}`))),
      // repos.json is optional — workflow may not have written it yet
      fetch(`https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/contents/data/repos.json?ref=${REPO_BRANCH}&t=${stamp}`, { headers, cache: "no-store" })
        .then(r => r.status === 404 ? null : r.ok ? r.json() : Promise.resolve(null))
        .catch(() => null),
    ]).then(([csvText, reposJson]) => {
      if (cancelled) return;
      setRows(parseTrafficCSV(csvText));
      setRepoIndex(reposJson?.repos || null);
      setLoading(false);
    }).catch(e => {
      if (cancelled) return;
      setError(typeof e === "string" ? e : (e && e.message) || "Failed");
      setLoading(false);
    });
    return () => { cancelled = true; };
  }, [token, reloadKey]);

  async function triggerFresh() {
    if (!token) return;
    setTriggering(true);
    setDispatchStatus(null);
    try {
      const res = await fetch(`https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/actions/workflows/track-traffic.yml/dispatches`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          Accept: "application/vnd.github+json",
          "X-GitHub-Api-Version": "2022-11-28",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ ref: REPO_BRANCH }),
      });
      if (res.status === 204) {
        setDispatchStatus({ ok: true, message: "queued — reload in ~30s" });
      } else {
        const txt = await res.text();
        setDispatchStatus({ ok: false, message: `${res.status}: ${txt.slice(0, 80)}` });
      }
    } catch (e) {
      setDispatchStatus({ ok: false, message: (e && e.message) || "dispatch failed" });
    } finally {
      setTriggering(false);
    }
  }

  if (loading) return <div style={{ padding: 56, color: A.dim, textAlign: "center", fontSize: 13 }}>Loading repo traffic…</div>;
  if (error) return (
    <div style={{ background: "rgba(255,107,107,.06)", border: `1px solid rgba(255,107,107,.2)`, borderRadius: 8, padding: 18, maxWidth: 620 }}>
      <div style={{ color: A.danger, fontSize: 13, marginBottom: 8 }}>Couldn't load data/traffic.csv — {error}</div>
      <Btn ghost size="sm" onClick={() => setReloadKey(k => k + 1)}><span style={{display:"inline-flex",alignItems:"center",gap:6}}>{Ic.refresh} Retry</span></Btn>
    </div>
  );

  // Group CSV rows by repo
  const byRepo = {};
  (rows || []).forEach(r => {
    if (!byRepo[r.repo]) byRepo[r.repo] = [];
    byRepo[r.repo].push({
      date: r.date,
      views: +r.views || 0,
      unique_visitors: +r.unique_visitors || 0,
      clones: +r.clones || 0,
      unique_cloners: +r.unique_cloners || 0,
    });
  });
  Object.values(byRepo).forEach(arr => arr.sort((a, b) => a.date.localeCompare(b.date)));

  function aggregateRepo(name, csvRows, meta) {
    const last30 = (csvRows || []).slice(-30);
    const totals = last30.reduce((a, r) => ({
      views: a.views + r.views,
      unique_visitors: a.unique_visitors + r.unique_visitors,
      clones: a.clones + r.clones,
      unique_cloners: a.unique_cloners + r.unique_cloners,
    }), { views: 0, unique_visitors: 0, clones: 0, unique_cloners: 0 });
    const lastActiveRow = [...(csvRows || [])].reverse().find(r => r.views > 0 || r.clones > 0);
    return {
      name,
      ...totals,
      lastActivity: lastActiveRow?.date || null,
      pushedAt: meta?.pushed_at || null,
      archived: !!meta?.archived,
      stars: meta?.stargazers_count || 0,
      sparkViews: last30.map(r => r.views),
      sparkClones: last30.map(r => r.clones),
    };
  }

  // Master list: union of repo-index (discovered) and CSV (anything with traffic).
  // If repo-index is available we trust it; otherwise fall back to CSV-only.
  let repos;
  if (repoIndex && repoIndex.length) {
    const indexed = new Set();
    repos = repoIndex.map(meta => {
      indexed.add(meta.full_name);
      return aggregateRepo(meta.full_name, byRepo[meta.full_name], meta);
    });
    // Edge case: CSV has rows for a repo no longer in the discovered list
    // (renamed, made private, etc). Surface them anyway, with no metadata.
    Object.keys(byRepo).forEach(name => {
      if (!indexed.has(name)) repos.push(aggregateRepo(name, byRepo[name], null));
    });
  } else {
    repos = Object.entries(byRepo).map(([name, rs]) => aggregateRepo(name, rs, null));
  }

  const totalRepos = repos.length;

  // Filter
  if (hideZero) repos = repos.filter(r => r.views > 0 || r.clones > 0);
  if (search.trim()) {
    const q = search.trim().toLowerCase();
    repos = repos.filter(r => r.name.toLowerCase().includes(q));
  }

  // Sort
  repos.sort((a, b) => {
    let cmp;
    if (sortBy === "name") cmp = a.name.localeCompare(b.name);
    else if (sortBy === "lastActivity") cmp = (a.lastActivity || "").localeCompare(b.lastActivity || "");
    else cmp = (a[sortBy] || 0) - (b[sortBy] || 0);
    return sortDir === "asc" ? cmp : -cmp;
  });

  function toggleSort(col) {
    if (sortBy === col) {
      setSortDir(sortDir === "asc" ? "desc" : "asc");
    } else {
      setSortBy(col);
      setSortDir(col === "name" ? "asc" : "desc");
    }
  }

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14, flexWrap: "wrap", gap: 12 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10, fontFamily: "JetBrains Mono, monospace", fontSize: 11, color: A.dim, letterSpacing: ".06em", flexWrap: "wrap" }}>
          <span style={{ width: 8, height: 8, borderRadius: 99, background: A.magenta, boxShadow: `0 0 8px ${A.magenta}` }}/>
          <span>{repos.length}</span>
          <span style={{ color: A.dim2 }}>of</span>
          <span>{totalRepos}</span>
          <span>{totalRepos === 1 ? "repo" : "repos"}</span>
          <span style={{ color: A.dim2 }}>·</span>
          <span>github.com page views + clones</span>
          <span style={{ color: A.dim2 }}>·</span>
          <span>last 30 days</span>
        </div>
        <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
          <input
            type="text"
            placeholder="Filter by name…"
            value={search}
            onChange={e => setSearch(e.target.value)}
            style={{ padding: "6px 10px", background: A.bg, border: `1px solid ${A.line2}`, borderRadius: 6, color: A.text, fontSize: 12, fontFamily: "JetBrains Mono, monospace", width: 180 }}
          />
          <label style={{ display: "inline-flex", alignItems: "center", gap: 6, fontSize: 11, color: A.dim, fontFamily: "JetBrains Mono, monospace", cursor: "pointer" }}>
            <input type="checkbox" checked={hideZero} onChange={e => setHideZero(e.target.checked)} style={{ accentColor: A.cyan }}/>
            hide zero-traffic
          </label>
          {dispatchStatus && <span style={{ fontSize: 11, color: dispatchStatus.ok ? A.green : A.danger, fontFamily: "JetBrains Mono, monospace" }}>{dispatchStatus.message}</span>}
          <Btn ghost size="sm" onClick={triggerFresh} disabled={triggering}>{triggering ? "queueing…" : "Fetch fresh"}</Btn>
          <Btn ghost size="sm" onClick={() => setReloadKey(k => k + 1)}><span style={{display:"inline-flex",alignItems:"center",gap:6}}>{Ic.refresh} Reload</span></Btn>
        </div>
      </div>

      <div style={{ background: A.panel, border: `1px solid ${A.line}`, borderRadius: 8, overflow: "hidden" }}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 90px 90px 90px 110px 200px", alignItems: "center", borderBottom: `1px solid ${A.line}`, background: A.panel2 }}>
          <RepoSortHeader id="name" label="Repo" sortBy={sortBy} sortDir={sortDir} onClick={toggleSort} align="left"/>
          <RepoSortHeader id="views" label="Views" sortBy={sortBy} sortDir={sortDir} onClick={toggleSort} align="right"/>
          <RepoSortHeader id="unique_visitors" label="Unique" sortBy={sortBy} sortDir={sortDir} onClick={toggleSort} align="right"/>
          <RepoSortHeader id="clones" label="Clones" sortBy={sortBy} sortDir={sortDir} onClick={toggleSort} align="right"/>
          <RepoSortHeader id="unique_cloners" label="Uniq cloners" sortBy={sortBy} sortDir={sortDir} onClick={toggleSort} align="right"/>
          <div style={{ padding: "10px 12px", fontFamily: "JetBrains Mono, monospace", fontSize: 10.5, color: A.dim2, letterSpacing: ".12em", textTransform: "uppercase" }}>30-day trend</div>
        </div>

        {repos.length === 0 ? (
          <div style={{ padding: 36, textAlign: "center", color: A.dim2, fontSize: 12 }}>
            {search ? `No repos match "${search}".` : (hideZero ? "No repos with traffic in the last 30 days. Toggle ‘hide zero-traffic’ to see all." : "No data yet.")}
          </div>
        ) : (
          repos.map((r, i) => <RepoStatsRow key={r.name} repo={r} last={i === repos.length - 1}/>)
        )}
      </div>

      <div style={{ marginTop: 18, fontSize: 11.5, color: A.dim2, lineHeight: 1.6 }}>
        Note: this is GitHub.com page views of source repos (people viewing the README, code, etc.) — not visits to 626labs.dev. Site-visit analytics live on the <b style={{ color: A.dim }}>Site</b> tab. Repos auto-discovered daily under <code style={{ background: A.panel2, padding: "1px 5px", borderRadius: 3, fontFamily: "JetBrains Mono, monospace", fontSize: 11 }}>estevanhernandez-stack-ed</code> and <code style={{ background: A.panel2, padding: "1px 5px", borderRadius: 3, fontFamily: "JetBrains Mono, monospace", fontSize: 11 }}>626Labs-LLC</code>{repoIndex ? "" : " (discovery sidecar pending — toggle ‘hide zero-traffic’ off after the next workflow run to see every repo)"}.
      </div>
    </div>
  );
}

function RepoSortHeader({ id, label, sortBy, sortDir, onClick, align }) {
  const active = sortBy === id;
  const arrow = active ? (sortDir === "asc" ? "↑" : "↓") : "·";
  return (
    <button
      onClick={() => onClick(id)}
      style={{
        background: "transparent", border: "none", cursor: "pointer",
        padding: "10px 12px",
        color: active ? A.cyan : A.dim2,
        fontFamily: "JetBrains Mono, monospace", fontSize: 10.5,
        letterSpacing: ".12em", textTransform: "uppercase",
        textAlign: align || "left",
        display: "flex", alignItems: "center", gap: 6,
        justifyContent: align === "right" ? "flex-end" : "flex-start",
      }}
    >
      <span>{label}</span>
      <span style={{ color: active ? A.cyan : A.dim2, opacity: active ? 1 : 0.5 }}>{arrow}</span>
    </button>
  );
}

function RepoStatsRow({ repo, last }) {
  // Split "owner/name" into prominent name + dim owner subscript.
  const slashIdx = repo.name.indexOf("/");
  const ownerPart = slashIdx > 0 ? repo.name.slice(0, slashIdx) : null;
  const namePart = slashIdx > 0 ? repo.name.slice(slashIdx + 1) : repo.name;

  const inactive = !repo.views && !repo.clones && !repo.unique_visitors && !repo.unique_cloners;

  const cell = (color, value) => (
    <div style={{
      padding: "0 12px", textAlign: "right", fontFamily: "JetBrains Mono, monospace",
      fontSize: 13, color: value ? color : A.dim2, fontWeight: value ? 500 : 400,
    }}>{value.toLocaleString()}</div>
  );

  const subtitle = [
    ownerPart,
    repo.lastActivity ? `last active ${repo.lastActivity}` : (inactive ? "no traffic in last 30d" : null),
    repo.archived ? "archived" : null,
  ].filter(Boolean).join(" · ");

  return (
    <div style={{
      display: "grid", gridTemplateColumns: "1fr 90px 90px 90px 110px 200px",
      alignItems: "center", padding: "12px 0",
      borderBottom: last ? "none" : `1px solid ${A.line}`,
      opacity: inactive ? 0.6 : 1,
      transition: "background 120ms, opacity 120ms",
    }}>
      <div style={{ padding: "0 12px", minWidth: 0, overflow: "hidden" }}>
        <a href={`https://github.com/${repo.name}`} target="_blank" rel="noopener" style={{
          color: A.text, textDecoration: "none", fontFamily: "JetBrains Mono, monospace",
          fontSize: 13.5, fontWeight: 500,
          display: "inline-flex", alignItems: "center", gap: 6, maxWidth: "100%",
        }} title={repo.name}>
          <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{namePart}</span>
          <span style={{ color: A.dim2, fontSize: 10, flexShrink: 0 }}>↗</span>
        </a>
        {subtitle && (
          <div style={{ fontSize: 10.5, color: A.dim2, marginTop: 2, fontFamily: "JetBrains Mono, monospace", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }} title={subtitle}>{subtitle}</div>
        )}
      </div>
      {cell(A.cyan, repo.views)}
      {cell(A.magenta, repo.unique_visitors)}
      {cell(A.green, repo.clones)}
      {cell(A.amber, repo.unique_cloners)}
      <div style={{ padding: "0 12px", display: "flex", flexDirection: "column", gap: 2 }}>
        {inactive ? (
          <div style={{ fontSize: 10, color: A.dim2, fontFamily: "JetBrains Mono, monospace", letterSpacing: ".04em" }}>—</div>
        ) : (
          <>
            <MiniSparkline values={repo.sparkViews} w={180} h={20} color={A.cyan}/>
            <MiniSparkline values={repo.sparkClones} w={180} h={14} color={A.green}/>
          </>
        )}
      </div>
    </div>
  );
}

function AnalyticsView({ token }) {
  const [tab, setTab] = React.useState("site");
  return (
    <div>
      <PanelHeader
        title="Analytics"
        subtitle="Site visits via GoatCounter (privacy-friendly, cookieless) and plugin-repo traffic from GitHub"
        actions={
          <TabBar
            value={tab}
            onChange={setTab}
            options={[
              { value: "site", label: "Site" },
              { value: "repos", label: "Plugin repos" },
            ]}
          />
        }
      />
      <div style={{ padding: "18px 26px 32px" }}>
        {tab === "site" && <SiteStats token={token}/>}
        {tab === "repos" && <RepoStats token={token}/>}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// Right rail — live preview, live data, pending diff
// ─────────────────────────────────────────────────────────────
function RightRail({ content, liveStats, nav, selectedId, dirty, original, onPreview, onSave }) {
  const p = content.products.find(x => x.id === selectedId);
  const live = p?.npm ? (liveStats?.[p.npm] || null) : null;
  const diff = React.useMemo(() => computeDiff(original, content), [original, content]);

  return (
    <div style={{ borderLeft: `1px solid ${A.line}`, background: A.panel, overflow: "auto" }}>
      <div style={{ padding: "14px 16px", borderBottom: `1px solid ${A.line}` }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10 }}>
          <span style={{ fontSize: 10.5, color: A.dim2, textTransform: "uppercase", letterSpacing: ".12em", fontFamily: "JetBrains Mono, monospace" }}>Preview</span>
          <div style={{ flex: 1 }}/>
          <Btn size="sm" ghost onClick={onPreview}><span style={{display:"inline-flex",alignItems:"center",gap:6}}>{Ic.eye} Full</span></Btn>
        </div>
        <MiniPreview content={content} selectedId={selectedId}/>
      </div>

      {nav === "products" && p && (
        <div style={{ padding: "14px 16px", borderBottom: `1px solid ${A.line}` }}>
          <div style={{ fontSize: 10.5, color: A.dim2, textTransform: "uppercase", letterSpacing: ".12em", fontFamily: "JetBrains Mono, monospace", marginBottom: 10 }}>Live · {p.title}</div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
            <DataTile ic={Ic.download} label="Weekly" value={live ? live.weekly.toLocaleString() : "—"} tone="cyan"/>
            <DataTile ic={Ic.star} label="Stars" value={live ? live.stars : "—"} tone="magenta"/>
          </div>
          <div style={{ marginTop: 10, padding: "8px 10px", background: A.panel2, borderRadius: 5, fontSize: 10.5, color: A.dim, fontFamily: "JetBrains Mono, monospace" }}>
            latest · <span style={{ color: A.text }}>{live?.release || "—"}</span>
          </div>
        </div>
      )}

      <div style={{ padding: "14px 16px" }}>
        <div style={{ fontSize: 10.5, color: A.dim2, textTransform: "uppercase", letterSpacing: ".12em", fontFamily: "JetBrains Mono, monospace", marginBottom: 10 }}>
          Pending diff {diff.length > 0 && <span style={{ color: A.amber }}>· {diff.length}</span>}
        </div>
        <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 10.5, lineHeight: 1.55, background: "#05070b", padding: 10, borderRadius: 5, border: `1px solid ${A.line}`, maxHeight: 220, overflow: "auto" }}>
          <div style={{ color: A.dim2, marginBottom: 4 }}>content/site.json</div>
          {diff.length === 0 && <div style={{ color: A.dim2, fontStyle: "italic" }}>clean</div>}
          {diff.map((d,i) => (
            <div key={i} style={{ color: d.op === "+" ? A.green : d.op === "-" ? A.danger : A.amber, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
              {d.op} {d.path}: {d.value}
            </div>
          ))}
        </div>
        <Btn primary size="sm" onClick={onSave} disabled={!dirty} style={{ marginTop: 10, width: "100%" }}>
          <span style={{display:"inline-flex",alignItems:"center",gap:6,justifyContent:"center",width:"100%"}}>{Ic.rocket} Commit & deploy</span>
        </Btn>
      </div>
    </div>
  );
}

function DataTile({ ic, label, value, tone }) {
  const c = TONE_COLORS[tone] || TONE_COLORS.cyan;
  return (
    <div style={{ padding: 10, background: A.panel2, borderRadius: 5, border: `1px solid ${A.line}` }}>
      <div style={{ display: "flex", alignItems: "center", gap: 6, color: c.fg, fontSize: 10 }}>{ic}<span style={{ color: A.dim2, fontFamily: "JetBrains Mono, monospace", letterSpacing: ".08em", textTransform: "uppercase" }}>{label}</span></div>
      <div style={{ fontSize: 18, fontWeight: 600, color: A.text, marginTop: 4, fontFamily: "JetBrains Mono, monospace" }}>{value}</div>
    </div>
  );
}

function MiniPreview({ content, selectedId }) {
  return (
    <div style={{ aspectRatio: "16/10", borderRadius: 6, overflow: "hidden", border: `1px solid ${A.line2}`, background: "#05070b", padding: 10, fontSize: 8, lineHeight: 1.3 }}>
      <div style={{ display: "flex", gap: 6, marginBottom: 10, alignItems: "center" }}>
        <div style={{ width: 18, height: 5, background: "linear-gradient(90deg,#17d4fa,#ff5aa3)", borderRadius: 1 }}/>
        {["Work","Thinking","Lab","About"].map((x,i)=><div key={i} style={{ fontSize: 6, color: A.dim2 }}>{x}</div>)}
      </div>
      <div style={{ fontSize: 10, fontWeight: 600, color: A.text, lineHeight: 1.1 }}>{content.hero.headline}</div>
      <div style={{ fontSize: 10, fontWeight: 600, background: "linear-gradient(90deg,#17d4fa,#ff5aa3)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent", lineHeight: 1.1 }}>{content.hero.headlineAccent}</div>
      <div style={{ fontSize: 6.5, color: A.dim, marginTop: 4, lineHeight: 1.4 }}>{(content.hero.subhead||"").slice(0,110)}…</div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(2,1fr)", gap: 3, marginTop: 8 }}>
        {content.products.slice(0,4).map(p => (
          <div key={p.id} style={{ padding: 4, background: p.id === selectedId ? "rgba(23,212,250,.08)" : "rgba(255,255,255,.02)", border: `1px solid ${p.id === selectedId ? A.cyan : A.line}`, borderRadius: 2 }}>
            <div style={{ fontSize: 6.5, color: A.text, fontWeight: 500 }}>{p.title}</div>
            <div style={{ fontSize: 5.5, color: A.dim2, marginTop: 1 }}>{(p.description||"").slice(0,32)}…</div>
          </div>
        ))}
      </div>
    </div>
  );
}

function computeDiff(orig, next) {
  const diff = [];
  const push = (op, path, value) => diff.push({ op, path, value: typeof value === "string" ? JSON.stringify(value.length > 42 ? value.slice(0,42) + "…" : value) : JSON.stringify(value) });
  // Hero
  for (const k of Object.keys(next.hero)) {
    if (JSON.stringify(orig.hero[k]) !== JSON.stringify(next.hero[k])) push("~", `hero.${k}`, next.hero[k]);
  }
  // Sections
  for (const k of Object.keys(next.sections)) {
    if (orig.sections[k]?.enabled !== next.sections[k]?.enabled) push("~", `sections.${k}.enabled`, next.sections[k].enabled);
  }
  // Products — shallow compare by id
  const origMap = Object.fromEntries(orig.products.map(p=>[p.id, p]));
  const nextMap = Object.fromEntries(next.products.map(p=>[p.id, p]));
  for (const id of Object.keys(nextMap)) {
    const o = origMap[id], n = nextMap[id];
    if (!o) { push("+", `products[${id}]`, n.title); continue; }
    for (const k of Object.keys(n)) {
      if (JSON.stringify(o[k]) !== JSON.stringify(n[k])) push("~", `products[${id}].${k}`, n[k]);
    }
  }
  for (const id of Object.keys(origMap)) if (!nextMap[id]) push("-", `products[${id}]`, origMap[id].title);
  // Lab
  if (JSON.stringify(orig.lab) !== JSON.stringify(next.lab)) push("~", "lab[]", `${next.lab.length} cards`);
  return diff;
}

// ─────────────────────────────────────────────────────────────
// Command palette, preview overlay, cheatsheet, guard, toast
// ─────────────────────────────────────────────────────────────
const overlayStyle = {
  position: "fixed", inset: 0, background: "rgba(7,9,13,.75)",
  backdropFilter: "blur(6px)", WebkitBackdropFilter: "blur(6px)",
  display: "grid", placeItems: "center", zIndex: 50,
};

function CommandPalette({ close, onNav, onPreview, onAddProduct, products, onSelectProduct }) {
  const [q, setQ] = React.useState("");
  const [sel, setSel] = React.useState(0);
  const cmds = React.useMemo(() => [
    { label: "Go to Overview", kind: "nav", ic: Ic.home, run: () => onNav("home") },
    { label: "Edit Hero", kind: "nav", ic: Ic.sparkle, run: () => onNav("hero") },
    { label: "Edit Products", kind: "nav", ic: Ic.grid, run: () => onNav("products") },
    { label: "Edit Lab shelf", kind: "nav", ic: Ic.flask, run: () => onNav("lab") },
    { label: "Edit Thinking", kind: "nav", ic: Ic.brain, run: () => onNav("thinking") },
    { label: "Edit Lab runs", kind: "nav", ic: Ic.image, run: () => onNav("labRuns") },
    { label: "Edit Play", kind: "nav", ic: Ic.rocket, run: () => onNav("play") },
    { label: "Edit About", kind: "nav", ic: Ic.heart, run: () => onNav("about") },
    { label: "Edit Support", kind: "nav", ic: Ic.star, run: () => onNav("support") },
    { label: "Edit Contact", kind: "nav", ic: Ic.mail, run: () => onNav("contact") },
    { label: "Edit Sections", kind: "nav", ic: Ic.eye, run: () => onNav("sections") },
    { label: "Edit Stories", kind: "nav", ic: Ic.edit, run: () => onNav("stories") },
    { label: "Go to Ops", kind: "nav", ic: Ic.activity, run: () => onNav("ops") },
    { label: "Go to Analytics", kind: "nav", ic: Ic.activity, run: () => onNav("analytics") },
    { label: "Preview site", kind: "action", ic: Ic.eye, run: onPreview },
    { label: "Add new product…", kind: "action", ic: Ic.plus, run: onAddProduct },
    ...products.map(p => ({ label: `Jump to product · ${p.title}`, kind: "product", ic: Ic.grid, run: () => onSelectProduct(p.id) })),
  ], [products]);
  const filtered = React.useMemo(() => cmds.filter(c => c.label.toLowerCase().includes(q.toLowerCase())), [cmds, q]);
  const run = (i) => { filtered[i]?.run(); };

  React.useEffect(() => { setSel(0); }, [q]);

  return (
    <div style={overlayStyle} onClick={close}>
      <div onClick={(e)=>e.stopPropagation()} style={{ width: 560, maxWidth: "90vw", background: A.panel, border: `1px solid ${A.line2}`, borderRadius: 10, overflow: "hidden", boxShadow: "0 30px 80px rgba(0,0,0,.6)" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "12px 14px", borderBottom: `1px solid ${A.line}` }}>
          <span style={{ color: A.cyan }}>⌘</span>
          <input autoFocus value={q} onChange={e=>setQ(e.target.value)} onKeyDown={e=>{
            if (e.key === "ArrowDown") { e.preventDefault(); setSel(s => Math.min(filtered.length-1, s+1)); }
            else if (e.key === "ArrowUp") { e.preventDefault(); setSel(s => Math.max(0, s-1)); }
            else if (e.key === "Enter") { e.preventDefault(); run(sel); }
          }} placeholder="Search commands, products, sections…" style={{
            flex: 1, background: "transparent", border: "none", outline: "none",
            color: A.text, fontSize: 14, fontFamily: "inherit",
          }}/>
          <span style={{ padding: "2px 6px", background: A.panel2, borderRadius: 3, fontFamily: "JetBrains Mono, monospace", fontSize: 10, color: A.dim2 }}>ESC</span>
        </div>
        <div style={{ maxHeight: 360, overflow: "auto" }}>
          {filtered.length === 0 && <div style={{ padding: 22, color: A.dim2, fontSize: 12, textAlign: "center" }}>No matches</div>}
          {filtered.map((c,i) => (
            <button key={i} onClick={()=>run(i)} onMouseEnter={()=>setSel(i)} style={{
              display: "flex", alignItems: "center", gap: 10, width: "100%", padding: "10px 14px",
              background: i === sel ? "rgba(23,212,250,.08)" : "transparent",
              border: "none", color: A.text, fontFamily: "inherit", fontSize: 13, textAlign: "left", cursor: "pointer",
              borderLeft: `2px solid ${i === sel ? A.cyan : "transparent"}`,
            }}>
              <span style={{ color: i === sel ? A.cyan : A.dim2 }}>{c.ic}</span>
              <span style={{ flex: 1 }}>{c.label}</span>
              <span style={{ fontSize: 10, color: A.dim2, fontFamily: "JetBrains Mono, monospace", textTransform: "uppercase", letterSpacing: ".08em" }}>{c.kind}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

function PreviewOverlay({ content, close }) {
  return (
    <div style={overlayStyle} onClick={close}>
      <div onClick={(e)=>e.stopPropagation()} style={{ width: "94vw", height: "90vh", background: "#05070b", border: `1px solid ${A.line2}`, borderRadius: 12, overflow: "hidden", display: "flex", flexDirection: "column", boxShadow: "0 40px 100px rgba(0,0,0,.7)" }}>
        <div style={{ padding: "10px 14px", display: "flex", alignItems: "center", gap: 10, borderBottom: `1px solid ${A.line}` }}>
          <div style={{ display: "flex", gap: 6 }}>
            <span style={{ width: 10, height: 10, borderRadius: 99, background: "#ff5f57" }}/>
            <span style={{ width: 10, height: 10, borderRadius: 99, background: "#febc2e" }}/>
            <span style={{ width: 10, height: 10, borderRadius: 99, background: "#28c840" }}/>
          </div>
          <div style={{ marginLeft: 10, padding: "3px 10px", background: A.panel, border: `1px solid ${A.line}`, borderRadius: 4, fontSize: 11, fontFamily: "JetBrains Mono, monospace", color: A.dim, flex: 1 }}>
            https://626labs.dev <span style={{ color: A.amber }}>· preview (unsaved)</span>
          </div>
          <Btn ghost size="sm" onClick={close}>Close preview ESC</Btn>
        </div>
        <div style={{ flex: 1, overflow: "auto" }}>
          <SitePreview content={content}/>
        </div>
      </div>
    </div>
  );
}

// Simplified renderer of 626labs.dev matching the real site vocabulary
function SitePreview({ content }) {
  const { hero } = content;
  return (
    <div style={{ minHeight: "100%", background: "#05070b", color: A.text, fontFamily: "Inter, system-ui, sans-serif", position: "relative" }}>
      {/* bg glow */}
      <div style={{ position: "absolute", inset: 0, background: "radial-gradient(600px 400px at 20% 15%, rgba(23,212,250,.12), transparent), radial-gradient(600px 400px at 85% 40%, rgba(255,90,163,.10), transparent)", pointerEvents: "none" }}/>
      <div style={{ position: "relative", maxWidth: 1120, margin: "0 auto", padding: "24px 40px 80px" }}>
        {/* nav */}
        <div style={{ display: "flex", alignItems: "center", gap: 20, padding: "14px 0" }}>
          <div style={{ width: 28, height: 28, borderRadius: 6, background: "linear-gradient(135deg,#17d4fa,#ff5aa3)", fontFamily: "JetBrains Mono, monospace", fontSize: 11, fontWeight: 700, color: A.bg, display: "grid", placeItems: "center" }}>626</div>
          <div style={{ fontSize: 13, fontWeight: 600 }}>626 Labs</div>
          <div style={{ flex: 1 }}/>
          {["Work", "Thinking", "Lab", "About", "Sponsor"].map(x => <span key={x} style={{ fontSize: 12.5, color: A.dim }}>{x}</span>)}
        </div>

        {/* hero */}
        <div style={{ paddingTop: 50, paddingBottom: 30 }}>
          <div style={{ fontSize: 11, color: A.cyan, fontFamily: "JetBrains Mono, monospace", letterSpacing: ".14em", textTransform: "uppercase" }}>{hero.eyebrow}</div>
          <div style={{ fontSize: 64, fontWeight: 700, lineHeight: 1.05, letterSpacing: "-.02em", marginTop: 14, textWrap: "balance" }}>
            {hero.headline}<br/>
            <span style={{ background: "linear-gradient(90deg,#17d4fa,#ff5aa3)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>{hero.headlineAccent}</span>
          </div>
          <div style={{ fontSize: 17, color: A.dim, marginTop: 18, maxWidth: 640, lineHeight: 1.55 }}>{hero.subhead}</div>
          <div style={{ display: "flex", gap: 10, marginTop: 26 }}>
            <span style={{ padding: "11px 18px", background: A.cyan, color: A.bg, borderRadius: 6, fontSize: 13, fontWeight: 600 }}>{hero.primaryCta.label}</span>
            <span style={{ padding: "11px 18px", border: `1px solid ${A.line2}`, color: A.text, borderRadius: 6, fontSize: 13, fontWeight: 500 }}>{hero.secondaryCta.label}</span>
          </div>
          <div style={{ display: "flex", gap: 8, marginTop: 28, flexWrap: "wrap" }}>
            {hero.chips.map((c,i) => <Chip key={i} tone={c.tone}>{c.label}</Chip>)}
          </div>
        </div>

        {/* products */}
        <div style={{ paddingTop: 50 }}>
          <div style={{ fontSize: 11, color: A.dim2, fontFamily: "JetBrains Mono, monospace", letterSpacing: ".14em", textTransform: "uppercase", marginBottom: 18 }}>Work</div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 16 }}>
            {content.products.filter(p=>content.sections?.support?.enabled || true).map(p => (
              <div key={p.id} style={{ padding: 20, background: "rgba(255,255,255,.02)", border: `1px solid ${A.line}`, borderRadius: 10 }}>
                {/* cover */}
                {(p.screenshots||[]).length > 0 && (
                  <div style={{ aspectRatio: "16/10", borderRadius: 6, overflow: "hidden", background: A.panel, marginBottom: 14 }}>
                    <img src={p.screenshots[0].url} alt="" style={{ width: "100%", height: "100%", objectFit: "cover", display: "block" }}/>
                  </div>
                )}
                <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                  <div style={{ fontSize: 18, fontWeight: 600 }}>{p.title}</div>
                  {p.flagship && <Chip tone="magenta">flagship</Chip>}
                  <div style={{ flex: 1 }}/>
                  <StatusDot status={p.status}/>
                </div>
                {p.tagline && <div style={{ fontSize: 13, color: A.cyan, marginTop: 6 }}>{p.tagline}</div>}
                <div style={{ fontSize: 13.5, color: A.dim, marginTop: 10, lineHeight: 1.55 }}>{p.description}</div>
                {p.install && <div style={{ marginTop: 12, padding: "8px 10px", background: A.panel2, border: `1px solid ${A.line}`, borderRadius: 4, fontSize: 11, fontFamily: "JetBrains Mono, monospace", color: A.text }}>{p.install}</div>}
                <div style={{ display: "flex", gap: 6, marginTop: 12, flexWrap: "wrap" }}>
                  {(p.tags||[]).map((t,i) => <Chip key={i} tone={t.tone}>{t.label}</Chip>)}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function CheatsheetOverlay({ close }) {
  const rows = [
    ["⌘K", "Command palette"],
    ["⌘S", "Save & deploy"],
    ["⌘P", "Open full preview"],
    ["⌘V", "Paste screenshots (in product editor)"],
    ["?", "This cheatsheet"],
    ["ESC", "Close overlays"],
  ];
  return (
    <div style={overlayStyle} onClick={close}>
      <div onClick={(e)=>e.stopPropagation()} style={{ width: 420, background: A.panel, border: `1px solid ${A.line2}`, borderRadius: 10, padding: 20 }}>
        <div style={{ fontSize: 15, fontWeight: 600, marginBottom: 16 }}>Keyboard shortcuts</div>
        {rows.map(([k,v], i) => (
          <div key={i} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "9px 0", borderBottom: i < rows.length - 1 ? `1px solid ${A.line}` : "none" }}>
            <span style={{ fontSize: 12.5, color: A.text }}>{v}</span>
            <span style={{ padding: "3px 8px", background: A.panel2, borderRadius: 4, fontFamily: "JetBrains Mono, monospace", fontSize: 11, color: A.dim }}>{k}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function GuardDialog({ target, onDiscard, onSave, onCancel }) {
  return (
    <div style={overlayStyle} onClick={onCancel}>
      <div onClick={(e)=>e.stopPropagation()} style={{ width: 420, background: A.panel, border: `1px solid ${A.line2}`, borderRadius: 10, padding: 22 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 10 }}>
          <span style={{ color: A.amber }}>●</span>
          <div style={{ fontSize: 15, fontWeight: 600 }}>Unsaved changes</div>
        </div>
        <div style={{ fontSize: 12.5, color: A.dim, lineHeight: 1.55, marginBottom: 18 }}>
          You've edited <code style={{ color: A.text }}>content/site.json</code> but haven't deployed yet. Leaving this panel won't lose anything — edits live in memory — but a clean state is easier to reason about.
        </div>
        <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
          <Btn ghost onClick={onCancel}>Stay here</Btn>
          <Btn ghost onClick={onDiscard}>Discard & go</Btn>
          <Btn primary onClick={onSave}><span style={{display:"inline-flex",alignItems:"center",gap:6}}>{Ic.save} Save & go</span></Btn>
        </div>
      </div>
    </div>
  );
}

function Toast({ msg, tone }) {
  const c = tone === "green" ? A.green
          : tone === "red"   ? A.danger
          : tone === "amber" ? A.amber
          : A.cyan;
  return (
    <div style={{
      position: "fixed", bottom: 24, left: "50%", transform: "translateX(-50%)",
      padding: "10px 16px", background: A.panel, border: `1px solid ${A.line2}`, borderLeft: `3px solid ${c}`,
      borderRadius: 6, fontSize: 12.5, color: A.text, boxShadow: "0 16px 32px rgba(0,0,0,.4)",
      display: "flex", alignItems: "center", gap: 10, zIndex: 60, maxWidth: "80vw",
    }}>
      <span style={{ color: c }}>●</span>{msg}
    </div>
  );
}

// Read a File as base64 (strips the "data:…;base64," prefix). Used by
// ScreenshotsEditor to send binary payloads through the Contents API.
function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const r = new FileReader();
    r.onload = () => {
      const res = r.result || "";
      const comma = res.indexOf(",");
      resolve(comma >= 0 ? res.slice(comma + 1) : res);
    };
    r.onerror = () => reject(r.error || new Error("file read failed"));
    r.readAsDataURL(file);
  });
}

Object.assign(window, { AdminApp });
