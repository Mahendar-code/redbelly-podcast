"""Build the review page (index.html), poster frames and the link preview image.

The page follows the Redbelly DAO Task Board brand kit: dark slate by default with a
light theme behind a toggle, one red accent, Be Vietnam Pro for copy and JetBrains Mono
for machine values (timestamps, sizes, measurements). It is plain static HTML.

usage: site.py
"""
import html
import json
import os
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
POSTERS = ROOT / "assets" / "posters"
SITE_URL = os.environ.get("SITE_URL", "").rstrip("/")


def esc(s):
    return html.escape(str(s), quote=True)


def ts(t):
    m, s = divmod(t, 60)
    return f"{int(m):02d}:{s:04.1f}"


def poster(clip_id):
    """540x960 PNG of the opening frame (hook, speaker, name and role all on screen)."""
    POSTERS.mkdir(parents=True, exist_ok=True)
    out = POSTERS / f"{clip_id}.png"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "1.2", "-i", str(ROOT / "clips" / f"{clip_id}.mp4"),
                    "-frames:v", "1", "-vf", "scale=540:960:flags=lanczos", str(out)], check=True)
    Image.open(out).convert("RGB").save(out, optimize=True)
    return out


def og_image(cfg):
    """1200x630 link preview: DAO logo, title and the six opening frames."""
    W, H = 1200, 630
    img = Image.new("RGB", (W, H), (12, 19, 23))
    d = ImageDraw.Draw(img)
    fonts = ROOT / "assets" / "fonts"
    logo = Image.open(ROOT / "assets" / "brand" / "dao-logo-on-dark.png").convert("RGBA")
    logo = logo.resize((round(logo.width * 96 / logo.height), 96), Image.LANCZOS)
    img.paste(logo, (56, 40), logo)
    d.text((56, 160), "Podcast Clip Pack", font=ImageFont.truetype(str(fonts / "BeVietnamPro-Bold.ttf"), 54),
           fill=(241, 245, 248))
    mono = ImageFont.truetype(str(fonts / "JetBrainsMono.ttf"), 22)
    mono.set_variation_by_name("Medium")
    d.text((56, 236), "6 CAPTIONED VERTICAL CLIPS  /  REDBELLY INSIGHTS", font=mono, fill=(143, 161, 173))
    tw, th, gap = 168, 299, 16
    x0 = W - 56 - (3 * tw + 2 * gap)
    for i, c in enumerate(cfg["clips"][:6]):
        p = Image.open(POSTERS / f"{c['id']}.png").resize((tw, th), Image.LANCZOS)
        if i < 3:
            img.paste(p, (x0 + i * (tw + gap), 24))
        else:
            img.paste(p, (56 + (i - 3) * (tw + gap), H - th - 24 + 0))
    d.rectangle((0, H - 6, W, H), fill=(239, 83, 80))
    img.save(ROOT / "og.png", optimize=True)


def checks_summary(report, clip_id):
    r = next((x for x in report.get("clips", []) if x["id"] == clip_id), None)
    if not r:
        return 0, 0, None
    passed = sum(v["pass"] for v in r["checks"].values())
    return passed, len(r["checks"]), r


def clip_card(i, c, ep, report):
    passed, total, r = checks_summary(report, c["id"])
    size = f"{r['probe']['size_mb']} MB" if r else ""
    dur = round(c["end"] - c["start"])
    src_link = f"{ep['url']}#t={c['start']:.1f},{c['end']:.1f}"
    status = (f'<span class="status ok"><i></i>{passed}/{total} CHECKS PASS</span>' if r and passed == total
              else f'<span class="status warn"><i></i>{passed}/{total} CHECKS PASS</span>' if r else "")
    notes = "".join(f"<p class=\"note\">{esc(n)}</p>" for n in c.get("notes", []))
    return f"""
<article class="clip" id="{esc(c['id'])}">
  <div class="player">
    <video controls playsinline preload="none" poster="assets/posters/{esc(c['id'])}.png" width="540" height="960">
      <source src="clips/{esc(c['id'])}.mp4" type="video/mp4">
    </video>
  </div>
  <div class="meta">
    <div class="row"><span class="mono num">CLIP {i:02d}</span><span class="mono topic">{esc(c['topic'].upper())}</span>{status}</div>
    <h3>{esc(c['hook'])}</h3>
    <p class="who"><strong>{esc(c['speaker'])}</strong><span>{esc(c['role'])}</span></p>
    <p class="point">{esc(c['point'])}</p>
    <dl class="facts">
      <div><dt>Source</dt><dd>{esc(ep['title'])}, {esc(ep['date'])}</dd></div>
      <div><dt>Timestamp</dt><dd class="mono"><a href="{esc(src_link)}" target="_blank" rel="noopener">{ts(c['start'])} to {ts(c['end'])}</a></dd></div>
      <div><dt>Length</dt><dd class="mono">{dur} s</dd></div>
    </dl>
    <div class="caption">
      <div class="caption-head"><span class="label">Suggested post caption</span><span class="mono count" data-count></span></div>
      <p data-caption>{esc(c['caption'])}</p>
      <button type="button" class="ghost" data-copy>Copy caption</button>
    </div>
    <div class="actions">
      <a class="btn" href="clips/{esc(c['id'])}.mp4" download>Download MP4 <span class="mono">{esc(size)}</span></a>
      <a class="ghost" href="subtitles/{esc(c['id'])}.srt" download>Subtitles SRT</a>
    </div>
    <details>
      <summary>Subtitle text</summary>
      <p class="transcript">{esc(c['text'])}</p>
      {notes}
    </details>
  </div>
</article>"""


def verification_table(cfg, report):
    if not report:
        return "<p>Run <code>python3 tools/verify.py</code> to measure the clips.</p>"
    rows = []
    for r in report["clips"]:
        p, L = r["probe"], r["loudness"]
        c = r["checks"]
        ok = lambda name: "ok" if c.get(name, {}).get("pass") else "warn"  # noqa: E731
        val = lambda name: esc(c.get(name, {}).get("value", "not run"))  # noqa: E731
        face = next((k for k in c if k.startswith("speaker in frame")), None)
        wer = next((k for k in c if k.startswith("subtitles vs independent")), None)
        rows.append(f"""<tr><th scope="row" class="mono">{esc(r['id'])}</th>
<td class="mono">{p['width']}x{p['height']} / {p['fps']:g} fps</td>
<td class="mono">{p['duration']:.1f} s</td>
<td class="mono {ok('loudness -14 LUFS +/-1')}">{L['lufs']:.1f} LUFS / {L['true_peak']:.1f} dBTP</td>
<td class="mono {ok('audio matches stated source timestamp')}">{val('audio matches stated source timestamp')}</td>
<td class="mono {ok(wer) if wer else ''}">{val(wer) if wer else 'not run'}</td>
<td class="mono {ok(face) if face else ''}">{val(face) if face else 'not run'}</td></tr>""")
    pack = "".join(f"<li><span class=\"status {'ok' if v['pass'] else 'warn'}\"><i></i>{'PASS' if v['pass'] else 'FAIL'}</span>"
                   f"{esc(k)}: <span class=\"mono\">{esc(v['value'] if not isinstance(v['value'], list) else '; '.join(map(str, v['value'])))}</span></li>"
                   for k, v in report["pack"].items())
    return f"""
<div class="table-wrap"><table>
<thead><tr><th>Clip</th><th>Video</th><th>Length</th><th>Loudness</th><th>Source timestamp</th><th>Subtitles vs audio</th><th>Speaker in frame</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></div>
<ul class="pack">{pack}</ul>
<p class="muted">Overall: <span class="status {'ok' if report['result'] == 'PASS' else 'warn'}"><i></i>{esc(report['result'])}</span>
Every check, per clip, is in <a href="VERIFICATION.md">VERIFICATION.md</a> and <a href="verification/report.json">report.json</a>.</p>"""


CSS = """
@font-face{font-family:"Be Vietnam Pro";font-weight:400;font-display:swap;src:url(assets/fonts/BeVietnamPro-Regular.ttf) format("truetype")}
@font-face{font-family:"Be Vietnam Pro";font-weight:500;font-display:swap;src:url(assets/fonts/BeVietnamPro-Medium.ttf) format("truetype")}
@font-face{font-family:"Be Vietnam Pro";font-weight:600;font-display:swap;src:url(assets/fonts/BeVietnamPro-SemiBold.ttf) format("truetype")}
@font-face{font-family:"Be Vietnam Pro";font-weight:700;font-display:swap;src:url(assets/fonts/BeVietnamPro-Bold.ttf) format("truetype")}
@font-face{font-family:"JetBrains Mono";font-weight:100 800;font-display:swap;src:url(assets/fonts/JetBrainsMono.ttf) format("truetype")}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--background-deep);color:var(--on-surface);font:400 16px/1.5 var(--font-sans)}
a{color:var(--primary)}
a:focus-visible,button:focus-visible,summary:focus-visible{outline:2px solid var(--brand);outline-offset:2px}
.mono{font-family:var(--font-mono);font-weight:500;letter-spacing:.02em}
.wrap{max-width:1180px;margin:0 auto;padding:0 var(--space-margin-mobile)}
header.top{border-bottom:1px solid var(--panel-edge);background:var(--surface)}
header.top .wrap{display:flex;align-items:center;justify-content:space-between;gap:16px;height:72px}
.logo{height:44px;width:auto;display:block}
.logo-light{display:none}
[data-theme="light"] .logo-dark{display:none}
[data-theme="light"] .logo-light{display:block}
.hero{background:var(--surface-steel);border-bottom:1px solid var(--panel-edge)}
[data-theme="light"] .hero{background:#1d3140;color:#f1f5f8}
[data-theme="light"] .hero .lede,[data-theme="light"] .hero .specs{color:#c2ced6}
.hero .wrap{padding-top:48px;padding-bottom:48px}
.hero h1{font-size:clamp(32px,6vw,48px);line-height:1.1;letter-spacing:-.02em;margin:12px 0 12px;font-weight:700}
.lede{font-size:18px;line-height:1.55;max-width:70ch;color:var(--on-surface-variant);margin:0 0 20px}
.specs{display:flex;flex-wrap:wrap;gap:8px 24px;color:var(--on-surface-variant);font-size:14px;margin:0;padding:0;list-style:none}
.status{display:inline-flex;align-items:center;gap:8px;font-family:var(--font-mono);font-weight:500;font-size:13px;letter-spacing:.05em}
.status i{width:8px;height:8px;border-radius:9999px;background:var(--outline);display:inline-block}
.status.ok i{background:var(--ok)}
.status.warn i{background:var(--warn)}
.status.brand i{background:var(--brand)}
section{padding:48px 0;border-bottom:1px solid var(--panel-edge)}
h2{font-size:32px;line-height:1.2;letter-spacing:-.01em;font-weight:600;margin:0 0 8px}
.section-lede{color:var(--on-surface-variant);max-width:70ch;margin:0 0 28px}
.deliverables{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:16px}
.card{background:var(--surface-slate);border:1px solid var(--panel-edge);border-radius:var(--radius-lg);padding:20px}
.card h3{margin:0 0 6px;font-size:18px;font-weight:600}
.card p{margin:0 0 12px;color:var(--on-surface-variant)}
.label{font-family:var(--font-mono);font-weight:700;font-size:12px;letter-spacing:.1em;text-transform:uppercase;color:var(--outline)}
.clips{display:grid;gap:24px}
.clip{display:grid;grid-template-columns:minmax(0,300px) minmax(0,1fr);gap:28px;background:var(--surface-slate);border:1px solid var(--panel-edge);border-radius:var(--radius-lg);padding:20px}
.player video{width:100%;height:auto;aspect-ratio:9/16;border-radius:var(--radius-base);background:#070c0f;display:block}
.row{display:flex;flex-wrap:wrap;align-items:center;gap:8px 16px;font-size:13px}
.num{color:var(--on-surface-variant)}
.topic{color:var(--primary)}
.clip h3{font-size:24px;line-height:1.25;font-weight:600;margin:10px 0 8px}
.who{margin:0 0 12px;display:flex;flex-wrap:wrap;gap:4px 10px}
.who span{color:var(--on-surface-variant)}
.point{margin:0 0 16px;max-width:70ch}
.facts{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px;margin:0 0 16px}
.facts div{border-top:1px solid var(--surface-container-high);padding-top:8px}
.facts dt{font-family:var(--font-mono);font-weight:700;font-size:12px;letter-spacing:.1em;text-transform:uppercase;color:var(--outline)}
.facts dd{margin:2px 0 0}
.caption{background:var(--surface-container);border:1px solid var(--panel-edge);border-radius:var(--radius-lg);padding:14px 16px;margin:0 0 16px}
.caption-head{display:flex;justify-content:space-between;gap:12px}
.count{font-size:12px;color:var(--outline)}
.caption p{margin:6px 0 12px;font-size:17px}
.actions{display:flex;flex-wrap:wrap;gap:10px;margin:0 0 12px}
.btn,.ghost{display:inline-flex;align-items:center;gap:8px;min-height:40px;padding:8px 14px;border-radius:var(--radius-base);font:600 15px/1.2 var(--font-sans);text-decoration:none;cursor:pointer}
.btn{background:var(--brand);color:#fff;border:1px solid var(--brand)}
.btn:hover{background:var(--brand-hover)}
.btn .mono{font-size:12px;font-weight:500;opacity:.9}
.ghost{background:transparent;color:var(--on-surface);border:1px solid var(--outline-variant)}
.ghost:hover{border-color:var(--brand)}
details{border-top:1px solid var(--surface-container-high);padding-top:10px}
summary{cursor:pointer;font-weight:600}
.transcript{color:var(--on-surface-variant);max-width:70ch}
.note{color:var(--on-surface-variant);font-size:14px;max-width:70ch}
.table-wrap{overflow-x:auto;border:1px solid var(--panel-edge);border-radius:var(--radius-lg)}
table{border-collapse:collapse;width:100%;min-width:860px;font-size:14px}
th,td{text-align:left;padding:10px 12px;border-bottom:1px solid var(--surface-container-high);vertical-align:top}
thead th{font-family:var(--font-mono);font-weight:700;font-size:12px;letter-spacing:.1em;text-transform:uppercase;color:var(--outline);background:var(--surface-container)}
tbody th{font-weight:500}
td.warn{color:var(--warn)}
.pack{list-style:none;padding:0;margin:20px 0;display:grid;gap:8px}
.pack li{display:flex;flex-wrap:wrap;gap:6px 12px;align-items:baseline}
.muted{color:var(--on-surface-variant)}
.method{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px}
.method .card p:last-child{margin-bottom:0}
footer{padding:32px 0 48px;color:var(--outline);font-size:14px}
code{font-family:var(--font-mono);font-size:.92em}
@media (max-width:760px){.clip{grid-template-columns:1fr}.player{max-width:340px}}
@media (prefers-reduced-motion:reduce){*{scroll-behavior:auto!important}}
"""

JS = """
(function(){
  var root=document.documentElement, btn=document.querySelector('[data-theme-toggle]');
  function set(t){root.setAttribute('data-theme',t);if(btn){btn.textContent=t==='dark'?'Light theme':'Dark theme';btn.setAttribute('aria-pressed',t==='light')}}
  var saved=null;try{saved=localStorage.getItem('theme')}catch(e){}
  set(saved==='light'?'light':'dark');
  if(btn){btn.addEventListener('click',function(){var t=root.getAttribute('data-theme')==='dark'?'light':'dark';set(t);try{localStorage.setItem('theme',t)}catch(e){}})}
  document.querySelectorAll('.caption').forEach(function(box){
    var p=box.querySelector('[data-caption]'),c=box.querySelector('[data-count]'),b=box.querySelector('[data-copy]');
    var n=Array.from(p.textContent).length;c.textContent=n+' / 280';
    b.addEventListener('click',function(){
      var done=function(){b.textContent='Copied';setTimeout(function(){b.textContent='Copy caption'},1600)};
      if(navigator.clipboard){navigator.clipboard.writeText(p.textContent).then(done,function(){})}
      else{var r=document.createRange();r.selectNodeContents(p);var s=getSelection();s.removeAllRanges();s.addRange(r);document.execCommand('copy');done()}
    });
  });
  document.querySelectorAll('video').forEach(function(v){v.addEventListener('play',function(){document.querySelectorAll('video').forEach(function(o){if(o!==v)o.pause()})})});
})();
"""


def page(cfg, report):
    eps = cfg["episodes"]
    used = sorted({eps[c["episode"]]["number"] for c in cfg["clips"]}, reverse=True)
    ep_list = ", ".join(str(n) for n in used)
    cards = "".join(clip_card(i, c, eps[c["episode"]], report) for i, c in enumerate(cfg["clips"], 1))
    total_s = sum(round(c["end"] - c["start"]) for c in cfg["clips"])
    og = f"{SITE_URL}/og.png" if SITE_URL else "og.png"
    desc = ("Six captioned vertical clips from the latest Redbelly Insights episodes, about Redbelly technology, "
            "Project Acacia and Tokeniser, with source timestamps and post captions.")
    method = cfg["method"]
    method_cards = "".join(f'<div class="card"><h3>{esc(m["title"])}</h3>{"".join(f"<p>{esc(p)}</p>" for p in m["body"])}</div>'
                           for m in method)
    return f"""<!doctype html>
<html lang="en" data-theme="dark">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Podcast Clip Pack</title>
<meta name="description" content="{esc(desc)}">
<meta property="og:title" content="Podcast Clip Pack">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:type" content="website">
<meta property="og:image" content="{esc(og)}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#0c1317">
<link rel="icon" href="assets/brand/icon.png" type="image/png">
<link rel="stylesheet" href="assets/brand/tokens.css">
<style>{CSS}</style>
</head>
<body>
<header class="top"><div class="wrap">
  <a href="#top" aria-label="Podcast Clip Pack"><img class="logo logo-dark" src="assets/brand/dao-logo-on-dark.png" alt="Redbelly DAO" width="62" height="44"><img class="logo logo-light" src="assets/brand/dao-logo-on-light.png" alt="Redbelly DAO" width="62" height="44"></a>
  <button type="button" class="ghost" data-theme-toggle aria-pressed="false">Light theme</button>
</div></header>
<main id="top">
<div class="hero"><div class="wrap">
  <span class="status brand"><i></i>REDBELLY INSIGHTS  /  EPISODES {esc(ep_list)}</span>
  <h1>Podcast Clip Pack</h1>
  <p class="lede">Six captioned vertical clips of 30 to 60 seconds, cut from the latest official Redbelly Insights episodes. Each one makes a single point about Redbelly technology, Project Acacia or Tokeniser, opens with a hook and the speaker's name and role, and comes with a one line post caption. Ready to post on X, YouTube Shorts and Instagram while the show relaunches as Off Paper - Powered by Tokeniser.</p>
  <ul class="specs mono"><li>6 CLIPS</li><li>{total_s} S IN TOTAL</li><li>1080x1920  9:16</li><li>30 FPS  H.264 + AAC</li><li>-14 LUFS</li><li>SUBTITLES BURNED IN + SRT</li></ul>
</div></div>

<section><div class="wrap">
  <h2>Deliverables</h2>
  <p class="section-lede">Both deliverables in the brief, plus the measurements behind them.</p>
  <div class="deliverables">
    <div class="card"><span class="label">Deliverable 1</span><h3>Six vertical clips with subtitles</h3><p>MP4, 1080x1920, 30 fps, subtitles burned in. Each clip also has an SRT file.</p><a href="#clips">Watch and download</a></div>
    <div class="card"><span class="label">Deliverable 2</span><h3>Source list and post captions</h3><p>Source episode, exact timestamp and a suggested post caption for every clip.</p><a href="CLIPS.md">CLIPS.md</a></div>
    <div class="card"><span class="label">Verification</span><h3>Measured, not assumed</h3><p>Specs, loudness, subtitle accuracy, source timestamps and speaker framing, measured from the files.</p><a href="#verification">See the results</a></div>
  </div>
</div></section>

<section id="clips"><div class="wrap">
  <h2>The clips</h2>
  <p class="section-lede">In posting order. The timestamp link opens the official episode video at the start of the clip.</p>
  <div class="clips">{cards}</div>
</div></section>

<section id="verification"><div class="wrap">
  <h2>Verification</h2>
  <p class="section-lede">Measured by <code>tools/verify.py</code> from the rendered files. The source timestamp check cross-correlates each clip's audio with the official episode at the stated time. Subtitles are compared with an independent transcript of the finished clip. The speaker check runs face recognition on five frames per second.</p>
  {verification_table(cfg, report)}
</div></section>

<section id="method"><div class="wrap">
  <h2>How the pack was made</h2>
  <p class="section-lede">Everything here can be rebuilt from the official episode files with the scripts in <code>tools/</code>.</p>
  <div class="method">{method_cards}</div>
</div></section>
</main>
<footer><div class="wrap">
  <p>All footage and audio are from official Redbelly Insights episodes published at <a href="https://redbelly.network/ama">redbelly.network/ama</a>. No music or third party material has been added. Styled with the Redbelly DAO Task Board brand kit. Be Vietnam Pro and JetBrains Mono are used under the SIL Open Font License.</p>
</div></footer>
<script>{JS}</script>
</body>
</html>
"""


def main():
    cfg = json.loads((ROOT / "clips.json").read_text())
    rp = ROOT / "verification" / "report.json"
    report = json.loads(rp.read_text()) if rp.exists() else {}
    for c in cfg["clips"]:
        poster(c["id"])
    og_image(cfg)
    (ROOT / "index.html").write_text(page(cfg, report), encoding="utf-8")
    print("wrote index.html, og.png and", len(cfg["clips"]), "posters")


if __name__ == "__main__":
    main()
