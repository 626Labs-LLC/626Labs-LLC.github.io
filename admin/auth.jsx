// 626 Labs admin — GitHub fine-grained PAT gate.
// Admin UI renders nothing until a token with write access to this specific
// repo is validated. Token lives only in the visitor's localStorage.

const REPO_OWNER = "626Labs-LLC";
const REPO_NAME = "626Labs-LLC.github.io";
const REPO_BRANCH = "main";
const CONTENT_PATH = "content/site.json";
const TOKEN_KEY = "626labs.admin.token";

function getStoredToken() {
  try { return window.localStorage.getItem(TOKEN_KEY) || ""; } catch { return ""; }
}
function storeToken(t) {
  try { if (t) window.localStorage.setItem(TOKEN_KEY, t); else window.localStorage.removeItem(TOKEN_KEY); } catch {}
}

// Ask GitHub: does this token have push on this specific repo?
// 200 + permissions.push === true means yes.
async function validateToken(token) {
  const res = await fetch(`https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}`, {
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: "application/vnd.github+json",
      "X-GitHub-Api-Version": "2022-11-28",
    },
  });
  if (res.status === 401) return { ok: false, reason: "Token rejected by GitHub (401). Check it's not expired or revoked." };
  if (res.status === 404) return { ok: false, reason: "Token can't see this repo. Make sure the token's repository access includes 626Labs-LLC/626Labs-LLC.github.io." };
  if (!res.ok) return { ok: false, reason: `GitHub returned ${res.status}.` };
  const repo = await res.json();
  if (!repo?.permissions?.push) return { ok: false, reason: "Token has no write permission on this repo. It needs Contents: Read & Write." };
  return { ok: true, login: repo.owner?.login, repo: repo.full_name };
}

// Fetch content/site.json from the repo. Uses the Contents API when a token
// is present (so we get the latest commit's blob + sha for later writes).
async function fetchSiteJson(token) {
  const res = await fetch(`https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/contents/${CONTENT_PATH}?ref=${REPO_BRANCH}`, {
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: "application/vnd.github+json",
      "X-GitHub-Api-Version": "2022-11-28",
    },
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`fetch content/site.json: ${res.status}`);
  const body = await res.json();
  // body.content is base64-encoded
  const json = JSON.parse(decodeURIComponent(escape(window.atob(body.content.replace(/\n/g, "")))));
  return { content: json, sha: body.sha };
}

// Public raw URL for a repo-relative path on the default branch.
// Works for public repos without auth — used to render admin previews of
// assets that have already been committed.
function rawUrl(repoPath) {
  return `https://raw.githubusercontent.com/${REPO_OWNER}/${REPO_NAME}/${REPO_BRANCH}/${repoPath}`;
}

// Upload an asset (screenshot, OG image, favicon) to a repo path via the
// Contents API. `base64Content` is the file's bytes, base64-encoded. Each
// upload is one commit on main. Filenames must be unique — we never PUT
// with a sha, so a collision would 422.
async function uploadAsset(token, repoPath, base64Content, message) {
  const res = await fetch(`https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/contents/${repoPath}`, {
    method: "PUT",
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: "application/vnd.github+json",
      "X-GitHub-Api-Version": "2022-11-28",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      message: message || `admin: upload ${repoPath}`,
      content: base64Content,
      branch: REPO_BRANCH,
    }),
  });
  if (!res.ok) {
    const txt = await res.text();
    throw new Error(`upload ${repoPath}: ${res.status} ${txt}`);
  }
  const body = await res.json();
  return { path: body.content.path, sha: body.content.sha, downloadUrl: body.content.download_url };
}

// Write site.json back via the Contents API — a single commit on main.
async function writeSiteJson(token, content, prevSha, message) {
  const b64 = window.btoa(unescape(encodeURIComponent(JSON.stringify(content, null, 2) + "\n")));
  const res = await fetch(`https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/contents/${CONTENT_PATH}`, {
    method: "PUT",
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: "application/vnd.github+json",
      "X-GitHub-Api-Version": "2022-11-28",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      message: message || "admin: update content/site.json",
      content: b64,
      sha: prevSha,
      branch: REPO_BRANCH,
    }),
  });
  if (!res.ok) {
    const txt = await res.text();
    throw new Error(`write content/site.json: ${res.status} ${txt}`);
  }
  const body = await res.json();
  return { sha: body.content.sha, commit: body.commit.sha };
}

// ─────────────────────────────────────────────────────────────
// LockScreen — shown until a valid token is stored
// ─────────────────────────────────────────────────────────────
function LockScreen({ onUnlock }) {
  const [token, setToken] = React.useState("");
  const [busy, setBusy] = React.useState(false);
  const [error, setError] = React.useState(null);

  const submit = async (e) => {
    e.preventDefault();
    if (!token.trim()) return;
    setBusy(true);
    setError(null);
    try {
      const r = await validateToken(token.trim());
      if (!r.ok) { setError(r.reason); setBusy(false); return; }
      storeToken(token.trim());
      onUnlock({ token: token.trim(), login: r.login });
    } catch (ex) {
      setError(ex.message || "Validation failed");
      setBusy(false);
    }
  };

  return (
    <div style={{
      width: "100vw", height: "100vh", display: "grid", placeItems: "center",
      background: "#07090d", color: "#e7edf5", fontFamily: "Inter, system-ui, sans-serif",
      padding: 20,
    }}>
      <div style={{ width: "100%", maxWidth: 460 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 28 }}>
          <div style={{
            width: 36, height: 36, borderRadius: 8,
            background: "linear-gradient(135deg,#17d4fa,#ff5aa3)",
            display: "grid", placeItems: "center",
            color: "#07090d", fontSize: 13, fontWeight: 700,
            fontFamily: "JetBrains Mono, monospace",
          }}>626</div>
          <div>
            <div style={{ fontSize: 15, fontWeight: 600, letterSpacing: "-0.01em" }}>626 Labs · Admin</div>
            <div style={{ fontSize: 11, color: "#5b6b82", fontFamily: "JetBrains Mono, monospace", letterSpacing: "0.06em" }}>
              {REPO_OWNER}/{REPO_NAME}
            </div>
          </div>
        </div>

        <form onSubmit={submit} style={{
          background: "#0c1016", border: "1px solid rgba(255,255,255,.08)", borderRadius: 12,
          padding: 24,
        }}>
          <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 6 }}>Sign in with a GitHub token</div>
          <div style={{ fontSize: 12.5, color: "#8a99ae", lineHeight: 1.55, marginBottom: 20 }}>
            Admin writes directly to <code style={{ color: "#17d4fa", fontFamily: "JetBrains Mono, monospace", fontSize: 12 }}>content/site.json</code> in the hub repo. Paste a fine-grained personal access token with <strong style={{ color: "#e7edf5" }}>Contents: Read &amp; Write</strong> scoped to this repo. Token stays in your browser's localStorage — never leaves your machine except to <code style={{ color: "#17d4fa", fontFamily: "JetBrains Mono, monospace", fontSize: 12 }}>api.github.com</code>.
          </div>

          <label style={{ display: "block", fontSize: 10.5, fontFamily: "JetBrains Mono, monospace", letterSpacing: "0.1em", textTransform: "uppercase", color: "#5b6b82", marginBottom: 6 }}>
            GitHub token
          </label>
          <input
            type="password"
            value={token}
            onChange={(e) => { setToken(e.target.value); setError(null); }}
            placeholder="github_pat_..."
            autoFocus
            spellCheck={false}
            autoComplete="off"
            style={{
              width: "100%", background: "#07090d", border: "1px solid rgba(255,255,255,.14)",
              borderRadius: 6, padding: "10px 12px", color: "#e7edf5", fontSize: 13,
              fontFamily: "JetBrains Mono, ui-monospace, monospace",
              outline: "none", letterSpacing: "0.02em",
            }}
          />

          {error && (
            <div style={{
              marginTop: 12, padding: "10px 12px", borderRadius: 6,
              background: "rgba(255,107,107,.08)", border: "1px solid rgba(255,107,107,.32)",
              color: "#ff8f8f", fontSize: 12, lineHeight: 1.5,
            }}>{error}</div>
          )}

          <button type="submit" disabled={busy || !token.trim()} style={{
            marginTop: 16, width: "100%",
            padding: "10px 16px", borderRadius: 6, border: "none",
            background: busy || !token.trim() ? "#151b25" : "#17d4fa",
            color: busy || !token.trim() ? "#5b6b82" : "#07090d",
            fontSize: 13, fontWeight: 600, cursor: busy || !token.trim() ? "default" : "pointer",
            fontFamily: "inherit", letterSpacing: "0.01em",
          }}>
            {busy ? "Verifying with GitHub…" : "Unlock admin"}
          </button>

          <div style={{ marginTop: 18, paddingTop: 16, borderTop: "1px solid rgba(255,255,255,.06)", fontSize: 11.5, color: "#5b6b82", lineHeight: 1.6 }}>
            <div style={{ marginBottom: 6, color: "#8a99ae", fontWeight: 500 }}>Need a token?</div>
            Generate a <a href="https://github.com/settings/personal-access-tokens/new" target="_blank" rel="noopener" style={{ color: "#17d4fa", textDecoration: "underline" }}>fine-grained PAT</a> with:
            <ul style={{ margin: "6px 0 0 18px", padding: 0 }}>
              <li>Repository access → Only <code style={{ color: "#17d4fa", fontFamily: "JetBrains Mono, monospace", fontSize: 11 }}>626Labs-LLC/626Labs-LLC.github.io</code></li>
              <li>Permissions → Contents: <strong style={{ color: "#e7edf5" }}>Read &amp; write</strong></li>
            </ul>
          </div>
        </form>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// LoadingScreen — shown during token revalidation + site.json fetch
// ─────────────────────────────────────────────────────────────
function LoadingScreen({ label = "Loading admin…" }) {
  return (
    <div style={{
      width: "100vw", height: "100vh", display: "grid", placeItems: "center",
      background: "#07090d", color: "#8a99ae", fontFamily: "Inter, system-ui, sans-serif",
    }}>
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 14 }}>
        <div style={{
          width: 32, height: 32, borderRadius: 8,
          background: "linear-gradient(135deg,#17d4fa,#ff5aa3)",
          display: "grid", placeItems: "center",
          color: "#07090d", fontSize: 11, fontWeight: 700,
          fontFamily: "JetBrains Mono, monospace",
          animation: "pulse626 2s ease-in-out infinite",
        }}>626</div>
        <div style={{ fontSize: 12, fontFamily: "JetBrains Mono, monospace", letterSpacing: "0.04em" }}>{label}</div>
      </div>
      <style>{`@keyframes pulse626 { 0%,100%{opacity:1} 50%{opacity:.5} }`}</style>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// LoadError — shown when site.json fetch or token revalidate fails
// ─────────────────────────────────────────────────────────────
function LoadError({ error, onRetry, onSignOut }) {
  return (
    <div style={{
      width: "100vw", height: "100vh", display: "grid", placeItems: "center",
      background: "#07090d", color: "#e7edf5", fontFamily: "Inter, system-ui, sans-serif",
      padding: 20,
    }}>
      <div style={{ width: "100%", maxWidth: 460, textAlign: "center" }}>
        <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 10, color: "#ff8f8f" }}>Couldn't load admin</div>
        <div style={{
          padding: "12px 14px", borderRadius: 6,
          background: "rgba(255,107,107,.08)", border: "1px solid rgba(255,107,107,.32)",
          color: "#ff8f8f", fontSize: 12, lineHeight: 1.55, textAlign: "left",
          fontFamily: "JetBrains Mono, ui-monospace, monospace",
          marginBottom: 16,
        }}>{error}</div>
        <div style={{ display: "flex", gap: 10, justifyContent: "center" }}>
          <button onClick={onRetry} style={{
            padding: "10px 20px", borderRadius: 6, border: "1px solid rgba(255,255,255,.14)",
            background: "#10151d", color: "#e7edf5", fontSize: 12.5, fontWeight: 500, cursor: "pointer",
            fontFamily: "inherit",
          }}>Retry</button>
          <button onClick={onSignOut} style={{
            padding: "10px 20px", borderRadius: 6, border: "none",
            background: "#17d4fa", color: "#07090d", fontSize: 12.5, fontWeight: 600, cursor: "pointer",
            fontFamily: "inherit",
          }}>Sign out</button>
        </div>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// AdminGate — top-level component that decides lock vs app
// ─────────────────────────────────────────────────────────────
function AdminGate() {
  const [token, setToken] = React.useState(getStoredToken());
  const [status, setStatus] = React.useState(getStoredToken() ? "checking" : "locked");
  // status: locked | checking | unlocked | error
  const [error, setError] = React.useState(null);
  const [login, setLogin] = React.useState(null);

  React.useEffect(() => {
    if (status === "checking" && token) {
      validateToken(token)
        .then((r) => {
          if (!r.ok) { storeToken(""); setToken(""); setStatus("locked"); return; }
          setLogin(r.login);
          setStatus("unlocked");
        })
        .catch((ex) => {
          storeToken(""); setToken(""); setStatus("locked");
          setError(ex.message);
        });
    }
  }, [status, token]);

  const onUnlock = ({ token: t, login: l }) => {
    setToken(t); setLogin(l); setStatus("unlocked");
  };
  const signOut = () => {
    storeToken(""); setToken(""); setLogin(null); setStatus("locked");
  };

  if (status === "locked") return <LockScreen onUnlock={onUnlock}/>;
  if (status === "checking") return <LoadingScreen label="Verifying token with GitHub…"/>;
  if (status === "error") return <LoadError error={error} onRetry={() => setStatus("checking")} onSignOut={signOut}/>;

  return <AdminApp token={token} login={login} onSignOut={signOut}/>;
}

// ─────────────────────────────────────────────────────────────
// Expose to window so app.jsx can consume
// ─────────────────────────────────────────────────────────────
Object.assign(window, {
  REPO_OWNER, REPO_NAME, REPO_BRANCH, CONTENT_PATH, TOKEN_KEY,
  getStoredToken, storeToken, validateToken,
  fetchSiteJson, writeSiteJson, uploadAsset, rawUrl,
  LockScreen, LoadingScreen, LoadError, AdminGate,
});
