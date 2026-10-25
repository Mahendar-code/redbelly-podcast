"""Render the vertical clips described in clips.json.

Layout (1080x1920, Redbelly DAO Task Board brand kit "Kinetic Consensus"):
  - progress bar in brand red along the top edge
  - header: source label and topic in JetBrains Mono, DAO logo, hook in Be Vietnam Pro Bold
  - 1080x1080 speaker window, one fixed crop per camera shot (tools/track.py)
  - speaker name and role on a slate lower third inside the window
  - captions in their own band under the window, the spoken word on a brand-red box
  - bottom band left clear for the X, Shorts, Reels and TikTok controls

usage: render.py [CLIP_ID ...]      (no argument renders every clip)
"""
import json
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
import track  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "work"
FONTS = ROOT / "assets" / "fonts"

W, H, FPS = 1080, 1920, 30
VIDEO_Y, VIDEO_S = 340, 1080
CAPTION_Y = 1530                      # vertical centre of the caption band
MARGIN = 60

# Brand kit tokens (assets/brand/tokens.css, dark theme)
SURFACE = (12, 19, 23)                # #0c1317
SLATE = (20, 31, 38)                  # #141f26
EDGE = (38, 54, 65)                   # #263641
ON_SURFACE = (241, 245, 248)          # #f1f5f8
ON_VARIANT = (194, 206, 214)          # #c2ced6
OUTLINE = (143, 161, 173)             # #8fa1ad
BRAND = (239, 83, 80)                 # #EF5350
PRIMARY = (255, 179, 174)             # #ffb3ae, accent text on dark


@lru_cache(None)
def font(name, size):
    if name == "mono":
        f = ImageFont.truetype(str(FONTS / "JetBrainsMono.ttf"), size)
        f.set_variation_by_name("Medium")
        return f
    return ImageFont.truetype(str(FONTS / f"BeVietnamPro-{name}.ttf"), size)


def text_w(draw, text, f, tracking=0.0):
    if not tracking:
        return draw.textlength(text, font=f)
    return sum(draw.textlength(c, font=f) for c in text) + tracking * f.size * (len(text) - 1)


def draw_tracked(draw, xy, text, f, fill, tracking):
    x, y = xy
    for c in text:
        draw.text((x, y), c, font=f, fill=fill)
        x += draw.textlength(c, font=f) + tracking * f.size


def wrap(draw, text, f, width):
    lines, line = [], ""
    for word in text.split():
        trial = f"{line} {word}".strip()
        if draw.textlength(trial, font=f) <= width or not line:
            line = trial
        else:
            lines.append(line)
            line = word
    return lines + [line]


def load_logo(height):
    logo = Image.open(ROOT / "assets" / "brand" / "dao-logo-on-dark.png").convert("RGBA")
    return logo.resize((round(logo.width * height / logo.height), height), Image.LANCZOS)


def base_canvas(clip, episode):
    """Everything that does not change during the clip, as an RGB image."""
    img = Image.new("RGB", (W, H), SURFACE)
    d = ImageDraw.Draw(img)

    # source label: status dot plus monospace label, as the kit specifies for status
    mono = font("mono", 26)
    d.ellipse((MARGIN, 82, MARGIN + 14, 96), fill=BRAND)
    draw_tracked(d, (MARGIN + 28, 74), f"REDBELLY INSIGHTS  EP{episode['number']}", mono, ON_VARIANT, 0.05)
    draw_tracked(d, (MARGIN, 118), clip["topic"].upper(), mono, PRIMARY, 0.05)

    logo = load_logo(104)
    img.paste(logo, (W - MARGIN - logo.width + 12, 46), logo)

    hook_font = font("Bold", 58)
    lines = wrap(d, clip["hook"], hook_font, W - 2 * MARGIN)
    if len(lines) > 2:
        hook_font = font("Bold", 50)
        lines = wrap(d, clip["hook"], hook_font, W - 2 * MARGIN)
    assert len(lines) <= 2, f"hook too long for two lines: {clip['hook']}"
    y = 178 if len(lines) == 2 else 212
    for line in lines:
        d.text((MARGIN, y), line, font=hook_font, fill=ON_SURFACE)
        y += round(hook_font.size * 1.18)

    d.rectangle((0, VIDEO_Y - 1, W, VIDEO_Y - 1), fill=EDGE)
    d.rectangle((0, VIDEO_Y + VIDEO_S, W, VIDEO_Y + VIDEO_S), fill=EDGE)

    cta = "Full episode: redbelly.network/ama"
    f = font("mono", 24)
    draw_tracked(d, ((W - text_w(d, cta, f, 0.03)) / 2, 1690), cta, f, OUTLINE, 0.03)
    return img


def lower_third(clip):
    """Speaker name and role as an RGBA overlay positioned inside the video window."""
    name_f, role_f = font("Bold", 42), font("Regular", 28)
    probe = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    role_lines = wrap(probe, clip["role"], role_f, W - 2 * 40 - 70)
    tw = max([probe.textlength(clip["speaker"], font=name_f)] + [probe.textlength(r, font=role_f) for r in role_lines])
    bw, bh = int(tw) + 34 + 30, 30 + 52 + 38 * len(role_lines) + 22
    box = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
    mask = Image.new("L", (bw, bh), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, bw - 1, bh - 1), radius=8, fill=255)
    fill = Image.new("RGBA", (bw, bh), SLATE + (235,))
    ImageDraw.Draw(fill).rectangle((0, 0, 5, bh), fill=BRAND + (255,))
    box.paste(fill, (0, 0), mask)
    d = ImageDraw.Draw(box)
    d.text((34, 24), clip["speaker"], font=name_f, fill=ON_SURFACE)
    y = 24 + 58
    for r in role_lines:
        d.text((34, y), r, font=role_f, fill=ON_VARIANT)
        y += 38
    return box, (40, VIDEO_Y + VIDEO_S - 40 - bh)


# ---------------------------------------------------------------- captions

CAP_FONT = ("ExtraBold", 64)
CAP_MAX_W = W - 2 * MARGIN
CAP_MAX_WORDS = 6
CAP_PAUSE = 0.45
WEAK = {"a", "an", "the", "of", "to", "in", "on", "and", "or", "but", "that", "is", "are", "for", "with", "by",
        "at", "as", "be", "your", "our", "their", "its", "it's", "this", "these", "so", "if", "then", "very", "we",
        "i", "you", "they", "there", "can", "will", "would", "from", "not"}


def balanced(draw, text, f, width):
    """One line if it fits, otherwise the two-line split with the most even line widths."""
    words = text.split()
    if draw.textlength(text, font=f) <= width:
        return [text]
    best = None
    for k in range(1, len(words)):
        a, b = " ".join(words[:k]), " ".join(words[k:])
        wa, wb = draw.textlength(a, font=f), draw.textlength(b, font=f)
        if wa <= width and wb <= width:
            score = max(wa, wb) + (40 if wb > wa else 0)      # prefer the top line a little longer
            if best is None or score < best[0]:
                best = (score, [a, b])
    return best[1] if best else wrap(draw, text, f, width)


def pages(words):
    """Group timed words into caption pages: at most two balanced lines, broken at
    sentence ends, clause commas and pauses, and never ending on a weak word if avoidable."""
    f = font(*CAP_FONT)
    probe = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    out, cur = [], []

    def fits(ws):
        return len(balanced(probe, " ".join(x["w"] for x in ws), f, CAP_MAX_W)) <= 2

    for w in words:
        if cur:
            gap = w["s"] - cur[-1]["e"]
            last = cur[-1]["w"]
            sentence_end = last[-1] in ".?!"
            clause_end = last[-1] in ",;:" and len(cur) >= 3
            full = len(cur) >= CAP_MAX_WORDS or not fits(cur + [w])
            if sentence_end or clause_end or gap > CAP_PAUSE:
                out.append(cur)
                cur = []
            elif full:
                # carry trailing weak words over so a page does not end on "the" or "of"
                carry = []
                while len(cur) > 2 and cur[-1]["w"].lower().strip(",.") in WEAK:
                    carry.insert(0, cur.pop())
                out.append(cur)
                cur = carry
        cur.append(w)
    if cur:
        out.append(cur)
    return out


def page_layout(page):
    f = font(*CAP_FONT)
    probe = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    lines = balanced(probe, " ".join(w["w"] for w in page), f, CAP_MAX_W)
    space = probe.textlength(" ", font=f)
    boxes, k = [], 0
    line_h = 84
    top = CAPTION_Y - line_h * len(lines) / 2
    for li, line in enumerate(lines):
        n = len(line.split())
        lw = probe.textlength(line, font=f)
        x = (W - lw) / 2
        for word in page[k:k + n]:
            ww = probe.textlength(word["w"], font=f)
            boxes.append((x, top + li * line_h, ww))
            x += ww + space
        k += n
    return boxes


@lru_cache(maxsize=64)
def caption_image(page_key, active):
    """RGBA strip for the caption band with word `active` highlighted (-1 for none)."""
    page = [dict(w=w, s=s, e=e) for w, s, e in page_key]
    f = font(*CAP_FONT)
    strip_top = CAPTION_Y - 120
    img = Image.new("RGBA", (W, 240), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for i, ((x, y, ww), word) in enumerate(zip(page_layout(page), page)):
        y -= strip_top
        if i == active:
            d.rounded_rectangle((x - 8, y + 4, x + ww + 8, y + 82), radius=4, fill=BRAND + (255,))
        d.text((x, y), word["w"], font=f, fill=ON_SURFACE + (255,))
    return np.array(img), strip_top


def caption_at(cap_pages, t):
    """Page and active word index on screen at clip time t."""
    for pi, page in enumerate(cap_pages):
        nxt = cap_pages[pi + 1][0]["s"] if pi + 1 < len(cap_pages) else page[-1]["e"] + 0.6
        shown_until = min(nxt, page[-1]["e"] + 0.6)
        if page[0]["s"] <= t < shown_until:
            active = -1
            for wi, w in enumerate(page):
                end = page[wi + 1]["s"] if wi + 1 < len(page) else w["e"]
                if w["s"] <= t < max(end, w["e"]):
                    active = wi
            return page, active
    return None, -1


def srt_time(t):
    ms = round(max(t, 0) * 1000)
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def write_srt(cap_pages, path, duration):
    out = []
    for i, page in enumerate(cap_pages):
        nxt = cap_pages[i + 1][0]["s"] if i + 1 < len(cap_pages) else duration
        end = min(nxt, page[-1]["e"] + 0.6, duration)
        text = "\n".join(balanced(ImageDraw.Draw(Image.new("RGB", (1, 1))), " ".join(w["w"] for w in page),
                                  font(*CAP_FONT), CAP_MAX_W))
        out.append(f"{i + 1}\n{srt_time(page[0]['s'])} --> {srt_time(end)}\n{text}\n")
    path.write_text("\n".join(out), encoding="utf-8")


# ---------------------------------------------------------------- compositing

def blend(dst, rgba, x, y):
    h, w = rgba.shape[:2]
    region = dst[y:y + h, x:x + w]
    a = rgba[:, :, 3:4].astype(np.float32) / 255.0
    region[:] = (rgba[:, :, :3][:, :, ::-1] * a + region * (1 - a)).astype(np.uint8)


def loudness(src, start, dur):
    """First loudnorm pass on the source range; returns the measured values."""
    cmd = ["ffmpeg", "-hide_banner", "-ss", f"{start:.3f}", "-t", f"{dur:.3f}", "-i", str(src),
           "-vn", "-af", "loudnorm=I=-14:TP=-2:LRA=11:print_format=json", "-f", "null", "-"]
    err = subprocess.run(cmd, capture_output=True, text=True).stderr
    return json.loads(err[err.rindex("{"):err.rindex("}") + 1])


def render(clip, episode, out_dir):
    src = WORK / "src" / f"{clip['episode']}.mp4"
    plan = json.loads((ROOT / "data" / "tracks" / f"{clip['id']}.json").read_text())
    words = json.loads((ROOT / "data" / "words" / f"{clip['id']}.json").read_text())["words"]
    start, end = clip["start"], clip["end"]
    dur = round(end - start, 3)

    # clip-relative word times
    rel = [dict(w=w["w"], s=round(w["s"] - start, 3), e=round(w["e"] - start, 3)) for w in words]
    cap_pages = pages(rel)
    write_srt(cap_pages, out_dir / "subtitles" / f"{clip['id']}.srt", dur)

    canvas = cv2.cvtColor(np.array(base_canvas(clip, episode)), cv2.COLOR_RGB2BGR)
    lt_img, (lt_x, lt_y) = lower_third(clip)
    lt = np.array(lt_img)

    m = loudness(src, start, dur)
    # two-pass EBU R128 to -14 LUFS, then a peak limiter at -2.5 dBFS so the AAC encode stays under -1 dBTP
    afilter = (f"loudnorm=I=-14:TP=-2:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
               f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:"
               f"linear=true,aresample=48000,alimiter=limit=0.75:attack=2:release=50:level=disabled,"
               f"afade=t=in:d=0.04,afade=t=out:st={dur - 0.15:.3f}:d=0.15")
    out = out_dir / "clips" / f"{clip['id']}.mp4"
    enc = subprocess.Popen([
        "ffmpeg", "-v", "error", "-y",
        "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-ss", f"{start:.3f}", "-t", f"{dur:.3f}", "-i", str(src),
        "-map", "0:v", "-map", "1:a", "-af", afilter,
        "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-profile:v", "high", "-level", "4.2",
        "-pix_fmt", "yuv420p", "-g", "60", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
        "-map_metadata", "-1", "-map_chapters", "-1", "-metadata", f"title={clip['hook']}",
        "-movflags", "+faststart", "-t", f"{dur:.3f}", str(out)], stdin=subprocess.PIPE)

    shots = plan["shots"]
    held = None
    n_frames = round(dur * FPS)
    src_w, src_h = track.probe(src)
    if shots[0]["kind"] != "speaker":
        # the episode is still on the host for the first moment: hold the speaker's first frame
        first = next(s for s in shots if s["kind"] == "speaker")
        x, y, s = first["crop"]
        _, frame = next(track.frames(src, first["start"] + 0.05, first["start"] + 0.2, src_w))
        held = (cv2.resize(frame[y:y + s, x:x + s], (VIDEO_S, VIDEO_S), interpolation=cv2.INTER_LANCZOS4), None)
    for i, (t_abs, frame) in enumerate(track.frames(src, start, end + 0.2, src_w)):
        if i >= n_frames:
            break
        t = i / FPS
        shot = next((s for s in shots if s["start"] <= t_abs < s["end"]), shots[-1])
        img = canvas.copy()
        if shot["kind"] == "speaker":
            x, y, s = shot["crop"]
            win = frame[y:y + s, x:x + s]
            win = cv2.resize(win, (VIDEO_S, VIDEO_S), interpolation=cv2.INTER_AREA if s > VIDEO_S else cv2.INTER_LANCZOS4)
            held = (win, t)
        else:
            # speaker not on camera: hold their last frame with a slow push-in, audio carries on
            k = 1 if held[1] is None else 1 + 0.02 * (t - held[1])
            c = VIDEO_S / k
            o = (VIDEO_S - c) / 2
            win = cv2.resize(held[0][int(o):int(o + c), int(o):int(o + c)], (VIDEO_S, VIDEO_S),
                             interpolation=cv2.INTER_LANCZOS4)
        img[VIDEO_Y:VIDEO_Y + VIDEO_S] = win
        blend(img, lt, lt_x, lt_y)
        page, active = caption_at(cap_pages, t)
        if page:
            key = tuple((w["w"], w["s"], w["e"]) for w in page)
            cap, top = caption_image(key, active)
            blend(img, cap, 0, top)
        img[0:8, 0:max(1, round(W * (t + 1 / FPS) / dur))] = BRAND[::-1]
        enc.stdin.write(img.tobytes())
    enc.stdin.close()
    assert enc.wait() == 0, f"encode failed for {clip['id']}"
    return out


def main():
    cfg = json.loads((ROOT / "clips.json").read_text())
    wanted = set(sys.argv[1:])
    for c in cfg["clips"]:
        if wanted and c["id"] not in wanted:
            continue
        ep = cfg["episodes"][c["episode"]]
        print("rendering", c["id"], flush=True)
        print("  ->", render(c, ep, ROOT))


if __name__ == "__main__":
    main()
