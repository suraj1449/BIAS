import os
from flask import Flask, Response
import datetime
import logging
import threading

import HEATMAP as heatmap
import FUTURE_BIAS as future
import OI_BIAS as oi


app = Flask(__name__)

# Prefer environment variables for deployment:
# KITE_API_KEY / KITE_ACCESS_TOKEN
# Local fallback is still available by replacing the placeholders below.
API_KEY = (os.getenv("KITE_API_KEY") or os.getenv("API_KEY") or "PASTE_YOUR_API_KEY_HERE").strip()
ACCESS_TOKEN = (os.getenv("KITE_ACCESS_TOKEN") or os.getenv("ACCESS_TOKEN") or "PASTE_YOUR_ACCESS_TOKEN_HERE").strip()

_future_init_lock = threading.Lock()
_future_started = False
_clients_configured = False
_client_lock = threading.Lock()


MAIN_HTML = """<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Merged Market Dashboard</title>
<style>
:root,
[data-theme="light"]{
  --bg:#f4f6fb;
  --surface:#ffffff;
  --surface-soft:#edf1f6;
  --border:#d6dee8;
  --text:#1d2430;
  --muted:#647084;
  --accent:#0f766e;
  --accent-soft:#d7f3ef;
  --shadow:0 14px 34px rgba(15, 23, 42, 0.08);
}
[data-theme="dark"]{
  --bg:#0f1722;
  --surface:#141d2b;
  --surface-soft:#1a2536;
  --border:#293548;
  --text:#e7edf7;
  --muted:#9ba9bc;
  --accent:#5eead4;
  --accent-soft:#123c3a;
  --shadow:0 16px 38px rgba(0, 0, 0, 0.32);
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{
  margin:0;
  background:var(--bg);
  color:var(--text);
  font-family:"Segoe UI",Arial,Helvetica,sans-serif;
  transition:background .25s ease,color .25s ease;
}
.topbar{
  position:sticky;
  top:0;
  z-index:20;
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:16px;
  padding:14px 22px;
  background:rgba(255,255,255,.92);
  border-bottom:1px solid var(--border);
  backdrop-filter:blur(10px);
}
[data-theme="dark"] .topbar{
  background:rgba(20,29,43,.92);
}
.brand{
  font-size:18px;
  font-weight:700;
  letter-spacing:.04em;
}
.topbar-right{
  display:flex;
  align-items:center;
  gap:14px;
  flex-wrap:wrap;
}
.nav{
  display:flex;
  align-items:center;
  gap:10px;
  flex-wrap:wrap;
}
.nav a{
  text-decoration:none;
  color:var(--text);
  background:var(--surface);
  border:1px solid var(--border);
  padding:8px 12px;
  border-radius:8px;
  font-size:13px;
  font-weight:600;
  transition:background .2s ease,border-color .2s ease,color .2s ease,transform .2s ease;
}
.nav a:hover{
  border-color:var(--accent);
  color:var(--accent);
  transform:translateY(-1px);
}
.theme-toggle{
  border:1px solid var(--border);
  background:var(--surface);
  color:var(--text);
  padding:8px 14px;
  border-radius:8px;
  font-size:13px;
  font-weight:600;
  cursor:pointer;
  transition:background .2s ease,border-color .2s ease,color .2s ease;
}
.theme-toggle:hover{
  border-color:var(--accent);
  color:var(--accent);
}
.page{
  padding:20px;
}
.dashboard-section{
  scroll-margin-top:88px;
  background:var(--surface);
  border:1px solid var(--border);
  border-radius:12px;
  box-shadow:var(--shadow);
  margin-bottom:18px;
  overflow:hidden;
}
.section-head{
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:12px;
  padding:14px 18px;
  background:var(--surface-soft);
  border-bottom:1px solid var(--border);
  flex-wrap:wrap;
}
.section-head h2{
  margin:0;
  font-size:18px;
  font-weight:700;
}
.section-head span{
  color:var(--muted);
  font-size:13px;
}
.frame-wrap{
  padding:14px;
  background:var(--surface);
}
iframe{
  width:100%;
  height:calc(100vh - 165px);
  min-height:760px;
  border:1px solid var(--border);
  border-radius:10px;
  background:#ffffff;
  display:block;
}
#oi-frame{height:900px;min-height:900px}
[data-theme="dark"] iframe{
  background:#0f1722;
}
@media (max-width: 900px){
  .topbar{
    padding:12px 14px;
  }
  .page{
    padding:14px;
  }
  .section-head h2{
    font-size:16px;
  }
  iframe{
    height:calc(100vh - 185px);
    min-height:620px;
  }
  #oi-frame{height:760px;min-height:760px}
}
</style>
</head>
<body>
  <header class="topbar">
    <div class="brand">Merged Market Dashboard</div>
    <div class="topbar-right">
      <nav class="nav">
        <a href="#heatmap-section">HEATMAP</a>
        <a href="#future-section">FUTURE_BIAS</a>
        <a href="#oi-section">OI_BIAS</a>
      </nav>
      <button class="theme-toggle" id="theme-toggle" type="button">Night Theme</button>
    </div>
  </header>

  <main class="page">
    <section id="heatmap-section" class="dashboard-section">
      <div class="section-head">
        <h2>HEATMAP.py</h2>
        <span>Section 1 of 3</span>
      </div>
      <div class="frame-wrap">
        <iframe id="heatmap-frame" src="heatmap" loading="eager"></iframe>
      </div>
    </section>

    <section id="future-section" class="dashboard-section">
      <div class="section-head">
        <h2>FUTURE_BIAS.py</h2>
        <span>Section 2 of 3</span>
      </div>
      <div class="frame-wrap">
        <iframe id="future-frame" src="future" loading="lazy"></iframe>
      </div>
    </section>

    <section id="oi-section" class="dashboard-section">
      <div class="section-head">
        <h2>OI_BIAS.py</h2>
        <span>Section 3 of 3</span>
      </div>
      <div class="frame-wrap">
        <iframe id="oi-frame" src="oi" loading="lazy"></iframe>
      </div>
    </section>
  </main>

<script>
const frameIds = ["heatmap-frame", "future-frame", "oi-frame"];
const autoSizeFrameIds = new Set(["oi-frame"]);
let activeTheme = "light";

function labelForTheme(theme) {
  return theme === "light" ? "Night Theme" : "Day Theme";
}

function mapTheme(frameId, theme) {
  if (frameId === "oi-frame") {
    return theme === "light" ? "day" : "night";
  }
  return theme;
}

function syncFrameTheme(frame) {
  try {
    const targetTheme = mapTheme(frame.id, activeTheme);
    const frameWindow = frame.contentWindow;
    const frameDoc = frame.contentDocument;
    if (frameWindow && frameWindow.__MERGED_DASHBOARD && typeof frameWindow.__MERGED_DASHBOARD.setTheme === "function") {
      frameWindow.__MERGED_DASHBOARD.setTheme(targetTheme);
    } else if (frameDoc && frameDoc.documentElement) {
      frameDoc.documentElement.setAttribute("data-theme", targetTheme);
    }
  } catch (err) {
    console.warn("Theme sync failed for", frame.id, err);
  }
}

function resizeFrame(frame) {
  if (!frame || !autoSizeFrameIds.has(frame.id)) {
    return;
  }
  try {
    const doc = frame.contentDocument;
    if (!doc || !doc.documentElement || !doc.body) {
      return;
    }
    const html = doc.documentElement;
    const body = doc.body;
    const nextHeight = Math.max(
      body.scrollHeight,
      body.offsetHeight,
      html.scrollHeight,
      html.offsetHeight,
      html.clientHeight
    );
    if (nextHeight && Math.abs(frame.offsetHeight - nextHeight) > 1) {
      frame.style.height = nextHeight + "px";
    }
  } catch (err) {
    console.warn("Frame resize failed for", frame.id, err);
  }
}

function installFrameResize(frame) {
  if (!frame || !autoSizeFrameIds.has(frame.id)) {
    return;
  }
  resizeFrame(frame);
  frame.setAttribute("scrolling", "no");
  try {
    const win = frame.contentWindow;
    const doc = frame.contentDocument;
    if (!win || !doc || !doc.documentElement) {
      return;
    }
    if (frame.__mergedMutationObserver) {
      frame.__mergedMutationObserver.disconnect();
    }
    if (frame.__mergedResizeObserver) {
      frame.__mergedResizeObserver.disconnect();
    }
    frame.__mergedMutationObserver = new win.MutationObserver(function () {
      win.requestAnimationFrame(function () {
        resizeFrame(frame);
      });
    });
    frame.__mergedMutationObserver.observe(doc.documentElement, {
      childList: true,
      subtree: true,
      attributes: true,
      characterData: true,
    });
    frame.__mergedResizeObserver = new win.ResizeObserver(function () {
      resizeFrame(frame);
    });
    frame.__mergedResizeObserver.observe(doc.documentElement);
    if (doc.body) {
      frame.__mergedResizeObserver.observe(doc.body);
    }
    win.setTimeout(function () { resizeFrame(frame); }, 0);
    win.setTimeout(function () { resizeFrame(frame); }, 250);
    win.setTimeout(function () { resizeFrame(frame); }, 1000);
  } catch (err) {
    console.warn("Frame resize observer failed for", frame.id, err);
  }
}

window.__resizeMergedFrame = function (frameId) {
  const frame = typeof frameId === "string" ? document.getElementById(frameId) : frameId;
  resizeFrame(frame);
};

function syncAllFrames() {
  frameIds.forEach((id) => {
    const frame = document.getElementById(id);
    if (frame) {
      syncFrameTheme(frame);
      resizeFrame(frame);
    }
  });
}

function applyTheme(theme) {
  activeTheme = theme;
  document.documentElement.setAttribute("data-theme", theme);
  document.getElementById("theme-toggle").textContent = labelForTheme(theme);
  syncAllFrames();
}

document.getElementById("theme-toggle").addEventListener("click", function () {
  applyTheme(activeTheme === "light" ? "dark" : "light");
});

frameIds.forEach((id) => {
  const frame = document.getElementById(id);
  frame.addEventListener("load", function () {
    syncFrameTheme(frame);
    installFrameResize(frame);
  });
});

window.addEventListener("resize", function () {
  frameIds.forEach(function (id) {
    resizeFrame(document.getElementById(id));
  });
});

applyTheme("light");
</script>
</body>
</html>
"""


CHILD_FONT_STYLE = """
<style id="merged-dashboard-overrides">
html, body {
  overflow-x: hidden !important;
}
html, body, button, input, select, textarea, table, th, td, div, span, label {
  font-family: "Segoe UI", Arial, Helvetica, sans-serif !important;
}
.theme-btn,
.theme-toggle{
  display:none !important;
}
</style>
"""


def credentials_ready():
    return (
        API_KEY.strip()
        and ACCESS_TOKEN.strip()
        and API_KEY != "PASTE_YOUR_API_KEY_HERE"
        and ACCESS_TOKEN != "PASTE_YOUR_ACCESS_TOKEN_HERE"
    )


def apply_credentials(module):
    if hasattr(module, "set_kite_credentials"):
        module.set_kite_credentials(API_KEY, ACCESS_TOKEN)
    else:
        module.API_KEY = API_KEY
        module.ACCESS_TOKEN = ACCESS_TOKEN


def ensure_clients_configured():
    global _clients_configured
    with _client_lock:
        if _clients_configured:
            return
        if not credentials_ready():
            raise RuntimeError(
                "Update API_KEY and ACCESS_TOKEN at the top of MERGED_DASHBOARD.py before running the merged app."
            )
        apply_credentials(heatmap)
        apply_credentials(future)
        apply_credentials(oi)
        _clients_configured = True


def inject_child_overrides(html, light_theme):
    helper = """
<script>
window.__MERGED_DASHBOARD = {
  setTheme: function(themeValue) {
    document.documentElement.setAttribute("data-theme", themeValue);
    if (typeof theme !== "undefined") {
      theme = themeValue;
    }
    if (typeof _isDark !== "undefined") {
      _isDark = themeValue === "dark";
    }
    var themeBtn = document.getElementById("themeBtn");
    if (themeBtn) {
      themeBtn.textContent = themeValue === "day" ? "Day" : "Night";
    }
    var themeIcon = document.getElementById("theme-icon");
    var themeLabel = document.getElementById("theme-lbl");
    if (themeIcon) {
      themeIcon.textContent = themeValue === "dark" ? "DAY" : "NIGHT";
    }
    if (themeLabel) {
      themeLabel.textContent = themeValue === "dark" ? "Day" : "Night";
    }
    window.dispatchEvent(new Event("resize"));
    if (typeof window.__MERGED_DASHBOARD.notifyParentSize === "function") {
      window.__MERGED_DASHBOARD.notifyParentSize();
    }
  },
  notifyParentSize: function() {
    try {
      if (window.frameElement && window.parent && typeof window.parent.__resizeMergedFrame === "function") {
        window.parent.__resizeMergedFrame(window.frameElement.id);
      }
    } catch (err) {}
  }
};
window.__MERGED_DASHBOARD.setTheme("%s");
</script>
""" % light_theme
    html = html.replace("</head>", CHILD_FONT_STYLE + "\n</head>", 1)
    html = html.replace("</body>", helper + "\n</body>", 1)
    return html


def build_heatmap_html():
    html = heatmap.HTML
    html = html.replace('data-theme="dark"', 'data-theme="light"', 1)
    html = html.replace("/api/data", "/heatmap/api/data")
    return inject_child_overrides(html, "light")


def build_future_html():
    html = future.HTML
    html = html.replace('<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=Barlow+Condensed:wght@400;600;700&display=swap" rel="stylesheet">', "")
    html = html.replace("/api/data/", "/future/api/data/")
    html = html.replace("/api/stream/", "/future/api/stream/")
    return inject_child_overrides(html, "light")


def build_oi_html():
    html = oi.HTML_TEMPLATE
    html = html.replace("/api/oi", "/oi/api/oi")
    html = html.replace("/api/ltp", "/oi/api/ltp")
    return inject_child_overrides(html, "day")


def ensure_future_started():
    global _future_started
    with _future_init_lock:
        if _future_started:
            return
        ensure_clients_configured()

        logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(message)s")
        for key in future.INTERVALS:
            thread = threading.Thread(
                target=future._refresh_loop,
                args=(key,),
                daemon=True,
                name="merged-refresh-" + key,
            )
            thread.start()

        _future_started = True


@app.route("/healthz")
def healthz():
    return {
        "ok": True,
        "credentials_ready": credentials_ready(),
        "future_started": _future_started,
    }


@app.route("/")
def merged_home():
    ensure_clients_configured()
    ensure_future_started()
    return Response(MAIN_HTML, mimetype="text/html")


@app.route("/heatmap")
def heatmap_page():
    ensure_clients_configured()
    return Response(build_heatmap_html(), mimetype="text/html")


@app.route("/heatmap/api/data")
def heatmap_api_data():
    ensure_clients_configured()
    return heatmap.api_data()


@app.route("/future")
def future_page():
    ensure_clients_configured()
    ensure_future_started()
    return Response(build_future_html(), mimetype="text/html")


@app.route("/future/api/data/<iv>")
def future_api_data(iv):
    ensure_clients_configured()
    ensure_future_started()
    return future.api_data(iv)


@app.route("/future/api/stream/<iv>")
def future_api_stream(iv):
    ensure_clients_configured()
    ensure_future_started()
    return future.api_stream(iv)


@app.route("/oi")
def oi_page():
    ensure_clients_configured()
    return Response(build_oi_html(), mimetype="text/html")


@app.route("/oi/api/oi")
def oi_api_data():
    ensure_clients_configured()
    return oi.api_oi()


@app.route("/oi/api/ltp")
def oi_api_ltp():
    ensure_clients_configured()
    return oi.api_ltp()


if __name__ == "__main__":
    ensure_clients_configured()
    ensure_future_started()
    port = int(os.getenv("PORT", "5002"))
    print("=" * 64)
    print("  Merged Market Dashboard")
    print("  http://localhost:" + str(port))
    print("  Sections: HEATMAP -> FUTURE_BIAS -> OI_BIAS")
    print("  Credentials source: env KITE_API_KEY / KITE_ACCESS_TOKEN")
    print("=" * 64)
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
