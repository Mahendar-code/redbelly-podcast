"""Audit the rendered pack: specs, loudness, subtitle accuracy, source timestamps,
speaker framing, spelling and credits. Every value is measured from the files.

Writes qa/results.json (QA.md is written from it by writeups.py). Exits 1 on any failure.

usage: audit.py [--fast]     (--fast skips the re-transcription and face checks)
"""
import json
import re
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import framing  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "work"
OUT = ROOT / "qa"

TARGET_LUFS, LUFS_TOL, MAX_TP = -14.0, 1.0, -1.0
VIDEO_Y, VIDEO_S = 340, 1080

# Spellings the brief names, plus the names and terms used in this pack.
REQUIRED_FORMS = ["Redbelly", "RBNT", "Tokeniser", "Project Acacia"]
WRONG_FORMS = [
    r"\bRed ?[Bb]elly\b(?<!Redbelly)", r"\bRed Belly\b", r"\bRedBelly\b", r"\bRed Valley\b", r"\bRedbilly\b",
    r"\bRed Bay\b", r"\bTokeni[sz]er\b(?<!Tokeniser)", r"\btokeniz", r"\bLiquidize\b", r"\bAkasha\b", r"\bArkesha\b",
    r"\bAkash\b", r"\brbnt\b", r"\bR\.B\.N\.T\b", r"\bGramoil\b", r"\bMontfit\b", r"\bMonford\b",
]
CREDIT_PATTERNS = [r"mahendar", r"made by", r"created by", r"edited by", r"produced by", r"clipped by",
                   r"\bclaude\b", r"anthropic", r"watermark",
                   r"(?<![\w.])@(?!media\b|font-face\b|keyframes\b|supports\b|import\b|page\b)[A-Za-z0-9_]{2,}"]
DASHES = "\u2013\u2014"
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿]")


def sh(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def probe(path):
    """Container and stream facts from ffprobe, flattened into one dict."""
    info = json.loads(sh(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json",
                          str(path)]).stdout)
    by_type = {}
    for stream in info["streams"]:
        by_type.setdefault(stream["codec_type"], stream)
    vid, aud, fmt = by_type["video"], by_type["audio"], info["format"]
    frames, per = vid["avg_frame_rate"].split("/")
    return {
        "width": vid["width"], "height": vid["height"], "fps": round(int(frames) / int(per), 3),
        "vcodec": vid["codec_name"], "pix_fmt": vid["pix_fmt"], "acodec": aud["codec_name"],
        "sample_rate": int(aud["sample_rate"]), "channels": aud["channels"],
        "duration": round(float(fmt["duration"]), 3),
        "v_duration": round(float(vid["duration"]), 3), "a_duration": round(float(aud["duration"]), 3),
        "size_mb": round(int(fmt["size"]) / 1e6, 1),
        "format": fmt["format_name"], "tags": fmt.get("tags", {}),
    }


def loudness(path):
    err = sh(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-vn", "-af", "ebur128=peak=true",
              "-f", "null", "-"]).stderr
    tail = err.split("Summary:")[-1]                 # ebur128 prints its totals last

    def reading(label):
        return float(re.search(label + r":\s+(-?[\d.]+|-inf)", tail).group(1))
    return {"lufs": reading("I"), "lra": reading("LRA"), "true_peak": reading("Peak")}


def pcm(path, start=None, dur=None, rate=8000):
    cmd = ["ffmpeg", "-v", "error"]
    if start is not None:
        cmd += ["-ss", f"{start:.3f}", "-t", f"{dur:.3f}"]
    cmd += ["-i", str(path), "-vn", "-ac", "1", "-ar", str(rate), "-f", "s16le", "-"]
    return np.frombuffer(subprocess.run(cmd, capture_output=True).stdout, np.int16).astype(np.float32)


def source_offset(clip_mp4, src, start):
    """Locate the clip's opening 10 s of audio in the episode around the stated start time."""
    rate, lead = 8000, 3.0
    a = pcm(clip_mp4, 0.5, 10, rate)
    b = pcm(src, start - lead + 0.5, 10 + 2 * lead, rate)
    a = (a - a.mean()) / (a.std() + 1e-9)
    n = len(a)
    best, lag = -1.0, 0
    # normalised cross-correlation via FFT
    size = 1 << (len(b) + n).bit_length()
    corr = np.fft.irfft(np.fft.rfft(b, size) * np.conj(np.fft.rfft(a, size)), size)[: len(b) - n + 1]
    csum = np.concatenate([[0], np.cumsum(b)])
    csq = np.concatenate([[0], np.cumsum(b * b)])
    mean = (csum[n:] - csum[:-n]) / n
    std = np.sqrt(np.maximum((csq[n:] - csq[:-n]) / n - mean ** 2, 1e-9))
    ncc = corr / (n * std)
    lag = int(np.argmax(ncc))
    best = float(ncc[lag])
    return round(lag / rate - lead, 3), round(best, 3)


def parse_srt(path):
    cues = []
    for block in Path(path).read_text(encoding="utf-8").strip().split("\n\n"):
        lines = block.strip().splitlines()
        m = re.match(r"(\d\d):(\d\d):(\d\d),(\d{3}) --> (\d\d):(\d\d):(\d\d),(\d{3})", lines[1])
        t = [int(x) for x in m.groups()]
        s = t[0] * 3600 + t[1] * 60 + t[2] + t[3] / 1000
        e = t[4] * 3600 + t[5] * 60 + t[6] + t[7] / 1000
        cues.append({"n": int(lines[0]), "s": s, "e": e, "text": " ".join(lines[2:]), "lines": lines[2:]})
    return cues


def words_of(text):
    return [w for w in re.sub(r"[^a-z0-9'$% ]", " ", text.lower().replace("’", "'")).split() if w]


FILLERS = {"um", "uh", "er", "ah", "mm", "hmm", "okay", "ok", "yeah"}


def comparable(text, vocab=()):
    """Words for comparing subtitles with a machine transcript: Australian and US spellings
    folded together, "+" read as "plus", "$100" read as "100", fillers dropped, stammered repeats collapsed, and
    split compounds ("guard rails") joined when the joined form is in the other text."""
    text = text.replace("+", " plus ").replace("$", "").replace("U.S.", "US").replace("U .S.", "US")
    ws = [re.sub(r"iz(e|ed|es|ing|ation|ations|er|ers)$", r"is\1", w) for w in words_of(text)]
    ws = [w for w in ws if w not in FILLERS]
    joined, i = [], 0
    while i < len(ws):
        if i + 1 < len(ws) and ws[i] + ws[i + 1] in vocab:
            joined.append(ws[i] + ws[i + 1])
            i += 2
        else:
            joined.append(ws[i])
            i += 1
    out = []
    for w in joined:
        out.append(w)
        for n in (1, 2, 3):                                   # "we think we think" -> "we think"
            if len(out) >= 2 * n and out[-n:] == out[-2 * n:-n]:
                del out[-n:]
                break
    return out


def edit_ops(ref_words, hyp_words):
    """Levenshtein distance over words, one row at a time."""
    row = list(range(len(hyp_words) + 1))
    for k, rw in enumerate(ref_words, 1):
        prev_diag, row[0] = row[0], k
        for col, hw in enumerate(hyp_words, 1):
            prev_diag, row[col] = row[col], min(row[col] + 1, row[col - 1] + 1, prev_diag + (rw != hw))
    return row[-1]


def wer(ref, hyp):
    """Plain word error rate on lower-cased words."""
    r, h = words_of(ref), words_of(hyp)
    return edit_ops(r, h) / max(len(r), 1)


def clean_wer(ref, hyp):
    """Word error rate after the normalisation in comparable(), plus the remaining differences."""
    r = comparable(ref, set(words_of(hyp)))
    h = comparable(hyp, set(words_of(ref)))
    import difflib
    diffs = [f"{' '.join(r[i1:i2]) or '-'} / {' '.join(h[j1:j2]) or '-'}"
             for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, r, h, autojunk=False).get_opcodes()
             if op != "equal"]
    return edit_ops(r, h) / max(len(r), 1), diffs


def retranscribe(clip_mp4, model_name):
    from faster_whisper import WhisperModel
    tmp = WORK / "audit" / (clip_mp4.stem + ".wav")
    tmp.parent.mkdir(parents=True, exist_ok=True)
    sh(["ffmpeg", "-v", "error", "-y", "-i", str(clip_mp4), "-ac", "1", "-ar", "16000", str(tmp)])
    with wave.open(str(tmp)) as w:
        audio = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    model = WhisperModel(model_name, device="cpu", compute_type="int8", cpu_threads=4)
    segs, _ = model.transcribe(audio, language="en", beam_size=5, vad_filter=True)
    return " ".join(s.text.strip() for s in segs)


def speaker_in_frame(clip_mp4, src, meta, person):
    """Share of sampled output frames whose window shows the speaker: a face that matches the
    speaker's reference and matches them better than the host or any co-guest."""
    faces = framing.Faces()
    speaker = meta["people"][person]
    ref = framing.reference(src, speaker["ref_times"], faces, speaker.get("ref_area") or speaker.get("crop_area"))
    rivals = framing.rival_refs(src, meta, person, faces)
    total = hit = 0
    worst = 1.0
    for i, (_, img) in enumerate(framing.frames(clip_mp4, 0, 999, 1080)):
        if i % 6:
            continue                                      # 5 samples per second
        win = np.ascontiguousarray(img[VIDEO_Y:VIDEO_Y + VIDEO_S])
        scores = [framing.identify(faces, win, f, ref, rivals) for f in faces.detect(win)]
        total += 1
        if any(framing.is_speaker(sim, rival) for sim, rival in scores):
            hit += 1
        worst = min(worst, max((sim for sim, _ in scores), default=0.0))
    return hit, total, round(worst, 3)


def scan_text(path, text):
    issues = []
    # report positions, not the matched words, so a failure message can never trip the scan itself
    for pat in WRONG_FORMS:
        for m in re.finditer(pat, text):
            issues.append(f"{path}: misspelt term at character {m.start()}")
    for pat in CREDIT_PATTERNS:
        for m in re.finditer(pat, text, flags=re.I):
            issues.append(f"{path}: possible personal credit at character {m.start()}")
    for ch in DASHES:
        if ch in text:
            issues.append(f"{path}: contains an en or em dash (brand kit voice rule)")
    if EMOJI.search(text):
        issues.append(f"{path}: contains an emoji (brand kit voice rule)")
    return issues


def main():
    fast = "--fast" in sys.argv
    cfg = json.loads((ROOT / "pack.json").read_text())
    OUT.mkdir(exist_ok=True)
    report = {"per_clip": [], "pack_checks": {}}
    failures = []

    for c in cfg["cuts"]:
        meta = cfg["sources"][c["source"]]
        mp4 = ROOT / "clips" / f"{c['slug']}.mp4"
        srt = ROOT / "subtitles" / f"{c['slug']}.srt"
        src = WORK / "src" / f"{c['source']}.mp4"
        r = {"slug": c["slug"], "checks": {}}
        p = probe(mp4)
        L = loudness(mp4)
        cues = parse_srt(srt)
        words = json.loads((ROOT / "data" / "timing" / f"{c['slug']}.json").read_text())["words"]
        r["probe"], r["loudness"] = p, L
        srt_text = " ".join(q["text"] for q in cues)

        def check(name, ok, value):
            r["checks"][name] = {"pass": bool(ok), "value": value}
            if not ok:
                failures.append(f"{c['slug']}: {name} ({value})")

        check("aspect 9:16", p["width"] * 16 == p["height"] * 9, f"{p['width']}x{p['height']}")
        check("1080p or higher", min(p["width"], p["height"]) >= 1080, f"{min(p['width'], p['height'])}p")
        check("24 fps or higher", p["fps"] >= 24, f"{p['fps']} fps")
        check("MP4, H.264 + AAC", "mp4" in p["format"] and p["vcodec"] == "h264" and p["acodec"] == "aac",
              f"{p['vcodec']}/{p['pix_fmt']} + {p['acodec']} {p['sample_rate'] // 1000} kHz")
        check("length 30 to 60 s", 30 <= p["duration"] <= 60, f"{p['duration']:.1f} s")
        check("audio and video same length", abs(p["v_duration"] - p["a_duration"]) < 0.1,
              f"v {p['v_duration']:.2f} s / a {p['a_duration']:.2f} s")
        check("loudness -14 LUFS +/-1", abs(L["lufs"] - TARGET_LUFS) <= LUFS_TOL, f"{L['lufs']:.1f} LUFS")
        check("true peak at most -1 dBTP", L["true_peak"] <= MAX_TP, f"{L['true_peak']:.1f} dBTP")
        check("no metadata beyond title", set(p["tags"]) <= {"title", "major_brand", "minor_version",
                                                             "compatible_brands", "encoder"},
              ", ".join(sorted(p["tags"])))

        # subtitles
        ordered = all(q["s"] < q["e"] for q in cues) and all(a["e"] <= b["s"] + 1e-3 for a, b in zip(cues, cues[1:]))
        check("subtitle cues ordered, no overlap", ordered, f"{len(cues)} cues")
        check("subtitles inside clip", cues[-1]["e"] <= p["duration"] + 0.05, f"last cue ends {cues[-1]['e']:.2f} s")
        check("at most 2 lines per cue", all(len(q["lines"]) <= 2 for q in cues),
              f"max {max(len(q['lines']) for q in cues)} lines")
        check("subtitles = proof-read text", words_of(srt_text) == words_of(c["transcript"]),
              f"{len(words_of(srt_text))} words")
        uncovered = [w["w"] for w in words
                     if not any(q["s"] - 0.05 <= w["s"] - c["in"] and w["e"] - c["in"] <= q["e"] + 0.05 for q in cues)]
        check("every spoken word inside a cue", not uncovered, f"{len(words) - len(uncovered)}/{len(words)} words")

        # source timestamp: the clip audio must sit exactly at the stated start in the episode
        lag, corr = source_offset(mp4, src, c["in"])
        check("audio matches stated source timestamp", abs(lag) <= 0.05 and corr >= 0.6,
              f"offset {lag:+.3f} s, correlation {corr:.2f}")

        if not fast:
            heard = retranscribe(mp4, cfg["audit_model"])
            r["independent_transcript"] = heard
            e, diffs = clean_wer(c["transcript"], heard)
            r["independent_differences"] = diffs
            check(f"subtitles vs independent transcript ({cfg['audit_model']})", e <= 0.10,
                  f"WER {e:.1%} (raw {wer(c['transcript'], heard):.1%})")
            hit, total, worst = speaker_in_frame(mp4, src, meta, c["person"])
            check("speaker in frame (face recognition)", hit / total >= 0.97,
                  f"{hit}/{total} sampled frames ({hit / total:.0%})")

        text_issues = scan_text(srt.name, srt_text) + scan_text(f"{c['slug']} metadata", json.dumps(p["tags"]))
        check("names, terms, credits, dashes in subtitles", not text_issues, "; ".join(text_issues) or "clean")
        report["per_clip"].append(r)

    # pack-level checks
    lufs = [r["loudness"]["lufs"] for r in report["per_clip"]]
    spread = round(max(lufs) - min(lufs), 2)
    pack = report["pack_checks"]
    pack["six clips"] = {"pass": len(cfg["cuts"]) == 6, "value": len(cfg["cuts"])}
    pack["loudness spread"] = {"pass": spread <= 1.0, "value": f"{spread} LU ({min(lufs)} to {max(lufs)} LUFS)"}
    points = [c["takeaway"].strip().lower() for c in cfg["cuts"]]
    pack["six distinct points"] = {"pass": len(set(points)) == len(points), "value": len(set(points))}
    overlaps = [(a["slug"], b["slug"]) for i, a in enumerate(cfg["cuts"]) for b in cfg["cuts"][i + 1:]
                if a["source"] == b["source"] and a["in"] < b["out"] and b["in"] < a["out"]]
    pack["no overlapping source ranges"] = {"pass": not overlaps, "value": overlaps or "none"}
    topics = sorted({c["theme"] for c in cfg["cuts"]})
    pack["covers Redbelly technology, Project Acacia, Tokeniser"] = {
        "pass": {"Redbelly technology", "Project Acacia", "Tokeniser"} <= set(topics), "value": ", ".join(topics)}

    doc_issues = []
    for path in ["README.md", "SOURCES.md", "index.html", "pack.json"]:
        f = ROOT / path
        if f.exists():
            doc_issues += scan_text(path, f.read_text(encoding="utf-8"))
    pack["docs: names, terms, credits, dashes, emoji"] = {"pass": not doc_issues, "value": doc_issues or "clean"}
    for k, v in pack.items():
        if not v["pass"]:
            failures.append(f"pack: {k} ({v['value']})")

    report["failures"] = failures
    report["result"] = "PASS" if not failures else "FAIL"
    report["mode"] = "fast" if fast else "full"
    (OUT / "results.json").write_text(json.dumps(report, indent=1))
    print(report["result"])
    for f in failures:
        print("  FAIL", f)
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
