"""Build index.html (the review page), a still for each clip and the social share card.

Styling follows the Redbelly DAO Task Board brand kit (taskboard.redbellydao.network/brand):
slate surfaces, a single red accent, Be Vietnam Pro for words and JetBrains Mono for
machine values. Dark by default, light on request. Static HTML, no build step.

usage: page.py        (set SITE_URL to give the share card an absolute address)
"""
import html
import json
import os
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
STILLS = ROOT / "assets" / "stills"
SHARE_CARD = ROOT / "assets" / "share-card.png"
BANNER = ROOT / "assets" / "readme-banner.png"
SITE_URL = (os.environ.get("SITE_URL") or "").removesuffix("/")


def h(value):
    return html.escape(str(value), quote=True)


def clock(t):
    minutes, seconds = divmod(t, 60)
    return f"{int(minutes):02d}:{seconds:04.1f}"


def make_still(slug):
    """Half-size PNG of the clip at 1.2 s: headline, speaker, name plate and first caption."""
    STILLS.mkdir(parents=True, exist_ok=True)
    target = STILLS / f"{slug}.png"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "1.2", "-i", str(ROOT / "clips" / f"{slug}.mp4"),
                    "-frames:v", "1", "-vf", "scale=540:960:flags=lanczos", str(target)], check=True)
    Image.open(target).convert("RGB").save(target, optimize=True)


def make_share_card(cuts):
    """1200x630 card for link previews: the six stills side by side under the title."""
    card = Image.new("RGB", (1200, 630), (12, 19, 23))
    draw = ImageDraw.Draw(card)
    fonts = ROOT / "assets" / "fonts"
    logo = Image.open(ROOT / "assets" / "dao-kit" / "dao-logo-on-dark.png").convert("RGBA")
    logo = logo.resize((round(logo.width * 72 / logo.height), 72), Image.LANCZOS)
    card.paste(logo, (1200 - 48 - logo.width, 36), logo)
    draw.text((48, 44), "Podcast Clip Pack", font=ImageFont.truetype(str(fonts / "BeVietnamPro-Bold.ttf"), 50),
              fill=(241, 245, 248))
    mono = ImageFont.truetype(str(fonts / "JetBrainsMono.ttf"), 20)
    mono.set_variation_by_name("Medium")
    draw.text((48, 112), "REDBELLY INSIGHTS  /  6 VERTICAL CLIPS WITH SUBTITLES", font=mono, fill=(143, 161, 173))
    width, gap = 172, 12
    height = round(width * 16 / 9)
    left = (1200 - 6 * width - 5 * gap) // 2
    for k, c in enumerate(cuts[:6]):
        still = Image.open(STILLS / f"{c['slug']}.png").resize((width, height), Image.LANCZOS)
        card.paste(still, (left + k * (width + gap), 630 - 24 - height))
    draw.rectangle((0, 0, 1200, 5), fill=(239, 83, 80))
    card.save(SHARE_CARD, optimize=True)


def make_banner(cuts, results):
    """1600x680 banner for the top of the GitHub README: title block left, the six stills right."""
    W, H = 1600, 680
    card = Image.new("RGB", (W, H), (12, 19, 23))
    draw = ImageDraw.Draw(card)
    fonts = ROOT / "assets" / "fonts"
    bold = lambda size: ImageFont.truetype(str(fonts / "BeVietnamPro-Bold.ttf"), size)  # noqa: E731
    regular = ImageFont.truetype(str(fonts / "BeVietnamPro-Regular.ttf"), 26)
    mono = ImageFont.truetype(str(fonts / "JetBrainsMono.ttf"), 21)
    mono.set_variation_by_name("Medium")
    draw.rectangle((0, 0, W, 6), fill=(239, 83, 80))

    # right: 3 x 2 grid of stills on a slightly raised panel
    tw, gap = 170, 14
    th = round(tw * 16 / 9)
    gx, gy = W - 64 - (3 * tw + 2 * gap), (H - (2 * th + gap)) // 2
    draw.rounded_rectangle((gx - 18, gy - 18, gx + 3 * tw + 2 * gap + 18, gy + 2 * th + gap + 18), radius=8,
                           fill=(20, 31, 38), outline=(38, 54, 65))
    for k, c in enumerate(cuts[:6]):
        still = Image.open(STILLS / f"{c['slug']}.png").resize((tw, th), Image.LANCZOS)
        card.paste(still, (gx + (k % 3) * (tw + gap), gy + (k // 3) * (th + gap)))

    # left: label, logo, title, line, facts
    x = 72
    logo = Image.open(ROOT / "assets" / "dao-kit" / "dao-logo-on-dark.png").convert("RGBA")
    logo = logo.resize((round(logo.width * 96 / logo.height), 96), Image.LANCZOS)
    card.paste(logo, (x - 6, 64), logo)
    draw.ellipse((x, 205, x + 12, 217), fill=(239, 83, 80))
    draw.text((x + 24, 198), "REDBELLY INSIGHTS", font=mono, fill=(194, 206, 214))
    draw.text((x, 236), "Podcast", font=bold(84), fill=(241, 245, 248))
    draw.text((x, 330), "Clip Pack", font=bold(84), fill=(241, 245, 248))
    draw.text((x, 446), "Six subtitled vertical clips on Redbelly", font=regular, fill=(194, 206, 214))
    draw.text((x, 482), "technology, Project Acacia and Tokeniser.", font=regular, fill=(194, 206, 214))
    verdict = results.get("result", "")
    facts = ["1080x1920", "30 FPS", "-14 LUFS"] + (["AUDIT " + verdict] if verdict else [])
    fx = x
    for fact in facts:
        w = draw.textlength(fact, font=mono)
        draw.rounded_rectangle((fx, 560, fx + w + 28, 602), radius=4, outline=(52, 68, 79), fill=(20, 31, 38))
        draw.text((fx + 14, 569), fact, font=mono, fill=(255, 179, 174) if fact.startswith("AUDIT") else (241, 245, 248))
        fx += w + 40
    card.save(BANNER, optimize=True)


def audit_row(results, slug):
    return next((r for r in results.get("per_clip", []) if r["slug"] == slug), None)


def post_card(n, c, source, results):
    row = audit_row(results, c["slug"])
    passed = sum(v["pass"] for v in row["checks"].values()) if row else 0
    total = len(row["checks"]) if row else 0
    badge = ""
    if row:
        tone = "good" if passed == total else "hold"
        badge = f'<span class="flag {tone}"><b></b>{passed} OF {total} CHECKS</span>'
    size = f'{row["probe"]["size_mb"]} MB' if row else ""
    jump = f"{source['video']}#t={c['in']:.1f},{c['out']:.1f}"
    notes = "".join(f"<p class=\"aside\">{h(x)}</p>" for x in c.get("editor_notes", []))
    return f"""
<li class="post" id="{h(c['slug'])}">
  <figure class="frame">
    <video controls playsinline preload="none" poster="assets/stills/{h(c['slug'])}.png" width="540" height="960">
      <source src="clips/{h(c['slug'])}.mp4" type="video/mp4">
    </video>
  </figure>
  <div class="body">
    <p class="kicker"><span class="mono">POST {n}</span><span class="mono theme">{h(c['theme'].upper())}</span>{badge}</p>
    <h3>{h(c['headline'])}</h3>
    <p class="byline">{h(c['person'])} <span>{h(c['person_title'])}</span></p>
    <p class="says">{h(c['takeaway'])}</p>
    <table class="facts">
      <tr><th>From</th><td>Episode {h(source['episode_no'])}, aired {h(source['aired'])}</td></tr>
      <tr><th>In and out</th><td class="mono"><a href="{h(jump)}" target="_blank" rel="noopener">{clock(c['in'])} to {clock(c['out'])}</a></td></tr>
      <tr><th>Runs</th><td class="mono">{round(c['out'] - c['in'])} s</td></tr>
    </table>
    <div class="copybox">
      <p class="copyhead"><span class="mono tag">POST WITH</span><span class="mono tally" data-tally></span></p>
      <p class="copytext" data-copytext>{h(c['post_copy'])}</p>
      <button type="button" class="quiet" data-copy>Copy text</button>
    </div>
    <p class="grab">
      <a class="solid" href="clips/{h(c['slug'])}.mp4" download>MP4 <span class="mono">{h(size)}</span></a>
      <a class="quiet" href="subtitles/{h(c['slug'])}.srt" download>SRT subtitles</a>
    </p>
    <details>
      <summary>Read the subtitles</summary>
      <p class="said">{h(c['transcript'])}</p>
      {notes}
    </details>
  </div>
</li>"""


def qa_section(results):
    if not results:
        return "<p>No audit yet. Run <code>python3 pipeline/audit.py</code>.</p>"
    body = []
    for r in results["per_clip"]:
        p, L, ch = r["probe"], r["loudness"], r["checks"]

        def cell(prefix):
            key = next((k for k in ch if k.startswith(prefix)), None)
            if not key:
                return '<td class="mono">not run</td>'
            return f'<td class="mono{"" if ch[key]["pass"] else " hold"}">{h(ch[key]["value"])}</td>'

        body.append(f"""<tr><th scope="row" class="mono">{h(r['slug'])}</th>
<td class="mono">{p['width']}x{p['height']}, {p['fps']:g} fps, {p['duration']:.1f} s</td>
<td class="mono">{L['lufs']:.1f} LUFS, peak {L['true_peak']:.1f} dBTP</td>
{cell("audio matches stated source")}{cell("subtitles vs independent")}{cell("speaker in frame")}</tr>""")
    pack = "".join(
        f"<li><span class=\"flag {'good' if v['pass'] else 'hold'}\"><b></b>{'PASS' if v['pass'] else 'FAIL'}</span>"
        f"{h(k)} <span class=\"mono\">{h('; '.join(map(str, v['value'])) if isinstance(v['value'], list) else v['value'])}</span></li>"
        for k, v in results["pack_checks"].items())
    tone = "good" if results["result"] == "PASS" else "hold"
    return f"""
<div class="scroller"><table class="grid">
<thead><tr><th>Clip</th><th>File</th><th>Audio level</th><th>Matches source at stated time</th><th>Subtitles against audio</th><th>Speaker on screen</th></tr></thead>
<tbody>{''.join(body)}</tbody></table></div>
<ul class="packlist">{pack}</ul>
<p class="soft"><span class="flag {tone}"><b></b>{h(results['result'])}</span> Full readings for every clip are in <a href="QA.md">QA.md</a> and <a href="qa/results.json">qa/results.json</a>.</p>"""


STYLE = """
@font-face{font-family:"Be Vietnam Pro";font-weight:400;font-display:swap;src:url(assets/fonts/BeVietnamPro-Regular.ttf)}
@font-face{font-family:"Be Vietnam Pro";font-weight:500;font-display:swap;src:url(assets/fonts/BeVietnamPro-Medium.ttf)}
@font-face{font-family:"Be Vietnam Pro";font-weight:600;font-display:swap;src:url(assets/fonts/BeVietnamPro-SemiBold.ttf)}
@font-face{font-family:"Be Vietnam Pro";font-weight:700;font-display:swap;src:url(assets/fonts/BeVietnamPro-Bold.ttf)}
@font-face{font-family:"JetBrains Mono";font-weight:100 800;font-display:swap;src:url(assets/fonts/JetBrainsMono.ttf)}
:root{--ground:#0a1014;--panel:#141f26;--panel-2:#17222a;--band:#1d3140;--rule:#263641;--rule-soft:#223039;
--ink:#f1f5f8;--ink-2:#c2ced6;--ink-3:#8fa1ad;--red:#EF5350;--red-hi:#f95a56;--accent-ink:#ffb3ae;--good:#86EFAC;--hold:#FCD34D;
--sans:"Be Vietnam Pro",ui-sans-serif,system-ui,sans-serif;--mono:"JetBrains Mono",ui-monospace,monospace;color-scheme:dark}
:root[data-theme="light"]{--ground:#EDF1F4;--panel:#FFFFFF;--panel-2:#F4F6F8;--band:#DDE6ED;--rule:#D3DBE1;--rule-soft:#DAE1E7;
--ink:#0F1A22;--ink-2:#394853;--ink-3:#596975;--red-hi:#D93E3B;--accent-ink:#B3272A;--good:#15803D;--hold:#A16207;color-scheme:light}
*{box-sizing:border-box}
body{margin:0;background:var(--ground);color:var(--ink);font:400 16px/1.5 var(--sans);-webkit-text-size-adjust:100%}
a{color:var(--accent-ink)}
a:focus-visible,button:focus-visible,summary:focus-visible{outline:2px solid var(--red);outline-offset:2px}
.mono{font-family:var(--mono);font-weight:500;letter-spacing:.03em}
.shell{max-width:1120px;margin:0 auto;padding:0 16px}
.bar{position:sticky;top:0;z-index:5;background:var(--panel);border-bottom:1px solid var(--rule)}
.bar .shell{display:flex;align-items:center;gap:16px;min-height:64px}
.bar img{height:40px;width:auto}
.bar .where{display:flex;gap:22px;margin:0 auto 0 12px;font:500 12px/1 var(--mono);letter-spacing:.1em;text-transform:uppercase}
.bar .where a{color:var(--ink-2);text-decoration:none;padding:8px 0;border-bottom:2px solid transparent}
.bar .where a:hover{color:var(--ink);border-bottom-color:var(--red)}
.actions{display:flex;flex-wrap:wrap;gap:12px;margin:26px 0 0!important}
.ghostlight{display:inline-flex;align-items:center;min-height:40px;padding:8px 14px;border-radius:4px;border:1px solid #34444f;color:#f1f5f8;font:600 15px/1.2 var(--sans);text-decoration:none}
.ghostlight:hover{border-color:var(--red)}
.strip{background:var(--panel);border-bottom:1px solid var(--rule)}
.strip ol{list-style:none;margin:0;padding:18px 0;display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:12px}
.strip a{display:grid;grid-template-columns:52px minmax(0,1fr);gap:10px;align-items:center;text-decoration:none;color:var(--ink);padding:6px;border-radius:4px;border:1px solid transparent}
.strip a:hover{border-color:var(--rule);background:var(--panel-2)}
.strip img{width:52px;height:auto;aspect-ratio:9/16;border-radius:2px;display:block}
.strip small{display:block;font:500 11px/1.2 var(--mono);letter-spacing:.08em;color:var(--accent-ink)}
.strip span{display:block;font-size:13px;line-height:1.3;margin-top:3px}
.dark-only{display:block}.light-only{display:none}
:root[data-theme="light"] .dark-only{display:none}:root[data-theme="light"] .light-only{display:block}
.lead{background:#1d3140;color:#f1f5f8;border-bottom:1px solid var(--rule)}
.lead .shell{padding-top:56px;padding-bottom:48px;display:grid;grid-template-columns:minmax(0,1.4fr) minmax(0,1fr);gap:40px;align-items:end}
.lead h1{margin:0 0 14px;font-size:clamp(34px,6vw,48px);line-height:1.08;letter-spacing:-.02em;font-weight:700}
.lead p{margin:0;color:#c2ced6;font-size:18px;line-height:1.55;max-width:68ch}
.chips{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:1px;background:#263641;border:1px solid #263641;border-radius:8px;overflow:hidden}
.chips li{background:#141f26;padding:14px 16px}
.chips b{display:block;font:600 22px/1.2 var(--mono);color:#f1f5f8}
.chips span{font-size:13px;color:#8fa1ad}
.part{padding:48px 0;border-bottom:1px solid var(--rule);scroll-margin-top:64px}
.post{scroll-margin-top:80px}
.part h2{margin:0 0 6px;font-size:30px;line-height:1.2;font-weight:600;letter-spacing:-.01em}
.part .intro{margin:0 0 24px;color:var(--ink-2);max-width:68ch}
.inpack{list-style:none;margin:0;padding:0;display:grid;gap:12px}
.inpack li{display:grid;grid-template-columns:48px minmax(0,1fr) auto;gap:16px;align-items:center;background:var(--panel);border:1px solid var(--rule);border-radius:8px;padding:16px 18px}
.inpack .no{font:700 20px/1 var(--mono);color:var(--red)}
.inpack h3{margin:0;font-size:17px;font-weight:600}
.inpack p{margin:2px 0 0;color:var(--ink-2);font-size:15px}
.posts{list-style:none;margin:0;padding:0;display:grid;gap:20px}
.post{display:grid;grid-template-columns:minmax(0,288px) minmax(0,1fr);gap:28px;background:var(--panel);border:1px solid var(--rule);border-radius:8px;padding:20px}
.frame{margin:0}
.frame video{display:block;width:100%;height:auto;aspect-ratio:9/16;border-radius:4px;background:#070c0f}
.kicker{display:flex;flex-wrap:wrap;gap:8px 16px;align-items:center;margin:0;font-size:13px;color:var(--ink-2)}
.kicker .theme{color:var(--accent-ink)}
.flag{display:inline-flex;align-items:center;gap:8px;font:500 12px/1 var(--mono);letter-spacing:.06em}
.flag b{width:8px;height:8px;border-radius:9999px;background:var(--ink-3)}
.flag.good b{background:var(--good)}.flag.hold b{background:var(--hold)}
.post h3{margin:10px 0 6px;font-size:23px;line-height:1.25;font-weight:600}
.byline{margin:0 0 12px;font-weight:600}
.byline span{font-weight:400;color:var(--ink-2);margin-left:6px}
.says{margin:0 0 16px;max-width:68ch}
.facts{border-collapse:collapse;margin:0 0 16px;font-size:15px}
.facts th{text-align:left;font:700 11px/1 var(--mono);letter-spacing:.1em;text-transform:uppercase;color:var(--ink-3);padding:6px 18px 6px 0;vertical-align:baseline}
.facts td{padding:6px 0}
.copybox{background:var(--panel-2);border:1px solid var(--rule);border-radius:8px;padding:14px 16px;margin:0 0 14px}
.copyhead{display:flex;justify-content:space-between;margin:0}
.tag{font-size:11px;font-weight:700;letter-spacing:.1em;color:var(--ink-3)}
.tally{font-size:12px;color:var(--ink-3)}
.copytext{margin:6px 0 12px;font-size:17px}
.grab{display:flex;flex-wrap:wrap;gap:10px;margin:0 0 12px}
.solid,.quiet{display:inline-flex;align-items:center;gap:8px;min-height:40px;padding:8px 14px;border-radius:4px;font:600 15px/1.2 var(--sans);text-decoration:none;cursor:pointer}
.solid{background:var(--red);border:1px solid var(--red);color:#fff}.solid:hover{background:var(--red-hi)}
.solid .mono{font-size:12px;opacity:.9}
.quiet{background:transparent;border:1px solid var(--rule);color:var(--ink)}.quiet:hover{border-color:var(--red)}
.icon{width:40px;height:40px;padding:0;justify-content:center}
.icon .moon{display:none}:root[data-theme="light"] .icon .sun{display:none}:root[data-theme="light"] .icon .moon{display:block}
details{border-top:1px solid var(--rule-soft);padding-top:10px}
summary{cursor:pointer;font-weight:600}
.said,.aside{color:var(--ink-2);max-width:68ch}.aside{font-size:14px}
.scroller{overflow-x:auto;border:1px solid var(--rule);border-radius:8px}
.grid{border-collapse:collapse;width:100%;min-width:900px;font-size:14px}
.grid th,.grid td{text-align:left;padding:10px 12px;border-bottom:1px solid var(--rule-soft);vertical-align:top}
.grid thead th{font:700 11px/1.3 var(--mono);letter-spacing:.1em;text-transform:uppercase;color:var(--ink-3);background:var(--panel-2)}
.grid tbody th{font-weight:500}
.grid td.hold{color:var(--hold)}
.packlist{list-style:none;margin:18px 0;padding:0;display:grid;gap:8px}
.packlist li{display:flex;flex-wrap:wrap;gap:6px 12px;align-items:baseline}
.soft{color:var(--ink-2)}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:14px}
.cards article{background:var(--panel);border:1px solid var(--rule);border-radius:8px;padding:18px 20px}
.cards h3{margin:0 0 8px;font-size:17px;font-weight:600}
.cards p{margin:0 0 10px;color:var(--ink-2)}.cards p:last-child{margin:0}
.end{padding:28px 0 44px;color:var(--ink-3);font-size:14px}
code{font-family:var(--mono);font-size:.92em}
@media (max-width:1060px){.strip ol{grid-template-columns:repeat(3,minmax(0,1fr))}}
@media (max-width:820px){.bar .where{display:none}.bar .icon{margin-left:auto}.strip ol{display:flex;overflow-x:auto;scroll-snap-type:x mandatory}.strip li{flex:0 0 200px;scroll-snap-align:start}}
@media (max-width:820px){.lead .shell{grid-template-columns:1fr}.post{grid-template-columns:1fr}.frame{max-width:340px}
.inpack li{grid-template-columns:36px minmax(0,1fr)}.inpack li a{grid-column:2}}
"""

SCRIPT = """
(function(){
  var doc=document.documentElement, toggle=document.querySelector('[data-theme-switch]');
  function apply(mode){doc.setAttribute('data-theme',mode);if(toggle){var label=mode==='dark'?'Switch to light theme':'Switch to dark theme';toggle.setAttribute('aria-label',label);toggle.setAttribute('title',label);toggle.setAttribute('aria-pressed',String(mode==='light'))}}
  var stored=null;try{stored=localStorage.getItem('clip-pack-theme')}catch(e){}
  apply(stored==='light'?'light':'dark');
  if(toggle){toggle.addEventListener('click',function(){var next=doc.getAttribute('data-theme')==='dark'?'light':'dark';apply(next);try{localStorage.setItem('clip-pack-theme',next)}catch(e){}})}
  Array.prototype.forEach.call(document.querySelectorAll('.copybox'),function(box){
    var text=box.querySelector('[data-copytext]'),tally=box.querySelector('[data-tally]'),btn=box.querySelector('[data-copy]');
    tally.textContent=Array.from(text.textContent).length+' OF 280 FOR X';
    btn.addEventListener('click',function(){
      var done=function(){btn.textContent='Copied';setTimeout(function(){btn.textContent='Copy text'},1500)};
      if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(text.textContent).then(done,function(){})}
      else{var range=document.createRange();range.selectNodeContents(text);var sel=window.getSelection();sel.removeAllRanges();sel.addRange(range);document.execCommand('copy');done()}
    });
  });
  var vids=document.querySelectorAll('video');
  Array.prototype.forEach.call(vids,function(v){v.addEventListener('play',function(){Array.prototype.forEach.call(vids,function(o){if(o!==v){o.pause()}})})});
})();
"""


def build(cfg, results):
    src = cfg["sources"]
    cuts = cfg["cuts"]
    episodes = ", ".join(str(n) for n in sorted({src[c["source"]]["episode_no"] for c in cuts}, reverse=True))
    runtime = sum(round(c["out"] - c["in"]) for c in cuts)
    share = f"{SITE_URL}/assets/share-card.png" if SITE_URL else "assets/share-card.png"
    blurb = ("Six subtitled vertical clips from recent Redbelly Insights episodes on Redbelly technology, "
             "Project Acacia and Tokeniser, each with its source time and a caption ready to post.")
    posts = "".join(post_card(n, c, src[c["source"]], results) for n, c in enumerate(cuts, 1))
    strip = "".join(
        f'<li><a href="#{h(c["slug"])}"><img src="assets/stills/{h(c["slug"])}.png" alt="" width="52" height="92" '
        f'loading="lazy"><div><small>POST {n}</small><span>{h(c["headline"])}</span></div></a></li>'
        for n, c in enumerate(cuts, 1))
    making = "".join(
        f'<article><h3>{h(m["title"])}</h3>{"".join(f"<p>{h(para)}</p>" for para in m["body"])}</article>'
        for m in cfg["making_of"])
    return f"""<!doctype html>
<html lang="en-AU" data-theme="dark">
<head>
<meta charset="utf-8">
<title>Podcast Clip Pack</title>
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="description" content="{h(blurb)}">
<link rel="icon" type="image/png" sizes="192x192" href="assets/dao-kit/favicon.png">
<link rel="icon" type="image/svg+xml" href="assets/dao-kit/favicon.svg">
<link rel="apple-touch-icon" href="assets/dao-kit/favicon.png">
<meta content="website" property="og:type">
<meta property="og:title" content="Podcast Clip Pack">
<meta property="og:description" content="{h(blurb)}">
<meta property="og:image" content="{h(share)}">
<meta content="summary_large_image" name="twitter:card">
<style>{STYLE}</style>
</head>
<body>
<header class="bar"><div class="shell">
  <img class="dark-only" src="assets/dao-kit/dao-logo-on-dark.png" alt="Redbelly DAO" width="56" height="40">
  <img class="light-only" src="assets/dao-kit/dao-logo-on-light.png" alt="Redbelly DAO" width="56" height="40">
  <nav class="where" aria-label="Sections"><a href="#posts">Posts</a><a href="#qa">QA</a><a href="#making-of">Making of</a><a href="SOURCES.md">Sources</a></nav>
  <button type="button" class="quiet icon" data-theme-switch aria-pressed="false" aria-label="Switch to light theme" title="Switch to light theme"><svg class="sun" viewBox="0 0 24 24" width="20" height="20" aria-hidden="true" focusable="false"><circle cx="12" cy="12" r="4.5" fill="none" stroke="currentColor" stroke-width="2"/><path d="M12 2v2.5M12 19.5V22M2 12h2.5M19.5 12H22M4.9 4.9l1.8 1.8M17.3 17.3l1.8 1.8M4.9 19.1l1.8-1.8M17.3 6.7l1.8-1.8" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg><svg class="moon" viewBox="0 0 24 24" width="20" height="20" aria-hidden="true" focusable="false"><path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/></svg></button>
</div></header>
<main>
<section class="lead"><div class="shell">
  <div>
    <h1>Podcast Clip Pack</h1>
    <p>The strongest short moments from the latest Redbelly Insights episodes, cut to stand on their own. Every clip is vertical, subtitled, opens on a headline with the speaker's name and title, and makes one point about Redbelly technology, Project Acacia or Tokeniser. Made for the Redbelly and DAO accounts on X, YouTube Shorts and Instagram as the show relaunches as Off Paper - Powered by Tokeniser.</p>
    <p class="actions"><a class="solid" href="#posts">Play the six posts</a><a class="ghostlight" href="SOURCES.md">Source list and captions</a></p>
  </div>
  <ul class="chips">
    <li><b>6</b><span>clips from episodes {h(episodes)}</span></li>
    <li><b>{runtime} s</b><span>of footage in total</span></li>
    <li><b>1080x1920</b><span>9:16 at 30 fps, MP4</span></li>
    <li><b>-14 LUFS</b><span>same level on every clip</span></li>
  </ul>
</div></section>

<nav class="strip" aria-label="Jump to a post"><div class="shell"><ol>{strip}</ol></div></nav>

<section class="part"><div class="shell">
  <h2>In this pack</h2>
  <p class="intro">Both things the brief asks for, plus the audit that backs them up.</p>
  <ol class="inpack">
    <li><span class="no">1</span><div><h3>Six vertical clips with subtitles</h3><p>Subtitles burned into each MP4, and the same lines as an SRT file.</p></div><a href="#posts">Watch</a></li>
    <li><span class="no">2</span><div><h3>Sources and post captions</h3><p>Episode, exact in and out times and a one line caption for each clip.</p></div><a href="SOURCES.md">SOURCES.md</a></li>
    <li><span class="no">+</span><div><h3>Audit</h3><p>Specs, loudness, subtitle accuracy, source times and framing, read from the files.</p></div><a href="#qa">Results</a></li>
  </ol>
</div></section>

<section class="part" id="posts"><div class="shell">
  <h2>Six posts, in order</h2>
  <p class="intro">The time under each clip links to the official episode file at the moment the clip starts.</p>
  <ol class="posts">{posts}</ol>
</div></section>

<section class="part" id="qa"><div class="shell">
  <h2>Checked from the files</h2>
  <p class="intro">Read by <code>pipeline/audit.py</code> from the finished clips. Each clip's audio is matched against the official episode at the time listed for it, its subtitles are compared with a fresh transcript from a separate model, and face recognition looks for the speaker five times a second.</p>
  {qa_section(results)}
</div></section>

<section class="part" id="making-of"><div class="shell">
  <h2>Behind the cuts</h2>
  <p class="intro">Everything here can be rebuilt from the official episode files with the scripts in <code>pipeline/</code>.</p>
  <div class="cards">{making}</div>
</div></section>
</main>
<footer class="end"><div class="shell">
  <p>Footage and sound come only from official Redbelly Insights episodes at <a href="https://redbelly.network/ama">redbelly.network/ama</a>. No music or outside material is added. Look and logo from the Redbelly DAO Task Board brand kit. Be Vietnam Pro and JetBrains Mono are used under the SIL Open Font License.</p>
</div></footer>
<script>{SCRIPT}</script>
</body>
</html>
"""


def main():
    cfg = json.loads((ROOT / "pack.json").read_text())
    path = ROOT / "qa" / "results.json"
    results = json.loads(path.read_text()) if path.exists() else {}
    for c in cfg["cuts"]:
        make_still(c["slug"])
    make_share_card(cfg["cuts"])
    make_banner(cfg["cuts"], results)
    (ROOT / "index.html").write_text(build(cfg, results), encoding="utf-8")
    print("wrote index.html, assets/share-card.png, assets/readme-banner.png and", len(cfg["cuts"]), "stills")


if __name__ == "__main__":
    main()
