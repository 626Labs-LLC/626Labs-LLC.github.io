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

  const save = async () => {
    if (!dirty || saving || !content) return;
    setSaving(true);
    try {
      const msg = "admin: update content/site.json\n\nfrom: 626labs.dev/admin-dashboard.html";
      const { sha } = await writeSiteJson(token, content, contentSha, msg);
      setContentSha(sha);
      setOriginal(content);
      setToast({ msg: "Saved. Pages will redeploy shortly.", tone: "green" });
      setTimeout(() => setToast(null), 3500);
    } catch (ex) {
      setToast({ msg: `Save failed: ${ex.message}`, tone: "red" });
      setTimeout(() => setToast(null), 6000);
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
      <Sidebar nav={nav} onNav={safeNav} content={content}/>

      <div style={{ overflow: "auto", background: A.bg, position: "relative" }}>
        {nav === "home" && <HomeView content={content} liveStats={liveStats} onNav={safeNav} onAddProduct={addProduct} onSelect={(id)=>{setSelProduct(id); safeNav("products");}}/>}
        {nav === "hero" && <HeroView hero={content.hero} onChange={h => setContent(c => ({...c, hero: h}))}/>}
        {nav === "products" && <ProductsView products={content.products} liveStats={liveStats} selectedId={selProduct} onSelect={setSelProduct} onUpdate={updateProduct} onAdd={addProduct} onDelete={deleteProduct}/>}
        {nav === "lab" && <LabView lab={content.lab} onChange={l => setContent(c => ({...c, lab: l}))}/>}
        {nav === "play" && <PlayView play={content.play || {}} onChange={p => setContent(c => ({...c, play: p}))}/>}
        {nav === "sections" && <SectionsView sections={content.sections} onChange={s => setContent(c => ({...c, sections: s}))}/>}
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

function Sidebar({ nav, onNav, content }) {
  const items = [
    { id: "home", label: "Overview", ic: Ic.home, kbd: "1" },
    { id: "hero", label: "Hero", ic: Ic.sparkle, kbd: "2" },
    { id: "products", label: "Products", ic: Ic.grid, kbd: "3", badge: content.products.length },
    { id: "lab", label: "Lab shelf", ic: Ic.flask, kbd: "4", badge: content.lab.length },
    { id: "play", label: "Play", ic: Ic.rocket, kbd: "5", badge: content.play?.widgets?.length ?? 0 },
    { id: "sections", label: "Sections", ic: Ic.brain, kbd: "6" },
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
      <div style={{ padding: "2px 12px 4px", fontSize: 10, color: A.dim2, fontFamily: "JetBrains Mono, monospace" }}>build #247 · main@a3f912e</div>
      <a href="https://626labs.dev" target="_blank" style={{ padding: "2px 12px", fontSize: 10, color: A.cyan, fontFamily: "JetBrains Mono, monospace", textDecoration: "none" }}>open site ↗</a>

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
function ProductsView({ products, liveStats, selectedId, onSelect, onUpdate, onAdd, onDelete }) {
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
        {selected && <ProductEditor key={selected.id} p={selected} onUpdate={(patch)=>onUpdate(selected.id, patch)} onDelete={()=>onDelete(selected.id)}/>}
      </div>
    </div>
  );
}

function ProductEditor({ p, onUpdate, onDelete }) {
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
        onChange={(s) => onUpdate({ screenshots: s })}
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
function ScreenshotsEditor({ shots, onChange }) {
  const [over, setOver] = React.useState(false);
  const [dragIdx, setDragIdx] = React.useState(null);
  const [cropping, setCropping] = React.useState(null);
  const fileRef = React.useRef(null);

  const ingestFiles = async (files) => {
    const next = [...shots];
    for (const f of files) {
      if (!f.type.startsWith("image/")) continue;
      const url = URL.createObjectURL(f);
      next.push({ id: `shot-${Date.now()}-${Math.random().toString(36).slice(2,6)}`, url, name: f.name || "pasted.png", size: f.size });
      if (next.length >= 6) break;
    }
    onChange(next);
  };

  const onDrop = (e) => {
    e.preventDefault(); setOver(false);
    ingestFiles([...e.dataTransfer.files]);
  };

  // Paste handler bound to document while editor is mounted
  React.useEffect(() => {
    const onPaste = (e) => {
      const items = [...(e.clipboardData?.items || [])];
      const imgs = items.filter(it => it.type.startsWith("image/")).map(it => it.getAsFile()).filter(Boolean);
      if (imgs.length) {
        e.preventDefault();
        ingestFiles(imgs);
      }
    };
    window.addEventListener("paste", onPaste);
    return () => window.removeEventListener("paste", onPaste);
  }, [shots]);

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
        <input ref={fileRef} type="file" accept="image/*" multiple style={{ display: "none" }} onChange={e=>ingestFiles([...e.target.files])}/>
        <Btn size="sm" onClick={()=>fileRef.current?.click()}><span style={{display:"inline-flex",alignItems:"center",gap:6}}>{Ic.upload} Upload</span></Btn>
      </div>

      {/* Dropzone — always visible, taller when empty */}
      <div
        onDragOver={(e)=>{e.preventDefault(); setOver(true);}}
        onDragLeave={()=>setOver(false)}
        onDrop={onDrop}
        onClick={()=>fileRef.current?.click()}
        style={{
          border: `2px dashed ${over ? A.cyan : A.line2}`,
          background: over ? "rgba(23,212,250,.06)" : A.panel,
          borderRadius: 8, padding: shots.length ? "12px 14px" : "28px 20px",
          marginBottom: 12, cursor: "pointer",
          display: "flex", alignItems: "center", gap: 14, justifyContent: "center",
          transition: "border-color .12s, background .12s",
        }}>
        <span style={{ color: over ? A.cyan : A.dim2 }}>{Ic.upload}</span>
        <div>
          <div style={{ fontSize: 12.5, color: A.text, fontWeight: 500 }}>Drop images here, paste from clipboard, or click to browse</div>
          <div style={{ fontSize: 11, color: A.dim, marginTop: 2 }}>PNG / JPG · max 6 · first image is the card cover</div>
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
              {s.url ? (
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

function SectionsView({ sections, onChange }) {
  const rows = [
    { key: "thinking", label: "Thinking behind it", desc: "Framework thesis + Self-Evolving Plugin Framework link" },
    { key: "labRuns", label: "How the lab runs", desc: "Private Agent OS dashboard screenshots + caption" },
    { key: "lab", label: "Also from the lab", desc: "JS-shuffled shelf of 8 other projects" },
    { key: "play", label: "Play", desc: "Embedded games — Birthday Bacon Trail widget" },
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
    { label: "Edit Play", kind: "nav", ic: Ic.rocket, run: () => onNav("play") },
    { label: "Edit Sections", kind: "nav", ic: Ic.brain, run: () => onNav("sections") },
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
  const c = tone === "green" ? A.green : A.cyan;
  return (
    <div style={{
      position: "fixed", bottom: 24, left: "50%", transform: "translateX(-50%)",
      padding: "10px 16px", background: A.panel, border: `1px solid ${A.line2}`, borderLeft: `3px solid ${c}`,
      borderRadius: 6, fontSize: 12.5, color: A.text, boxShadow: "0 16px 32px rgba(0,0,0,.4)",
      display: "flex", alignItems: "center", gap: 10, zIndex: 60,
    }}>
      <span style={{ color: c }}>●</span>{msg}
    </div>
  );
}

Object.assign(window, { AdminApp });
