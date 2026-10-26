"""Write SOURCES.md (deliverable 2) and QA.md from pack.json and qa/results.json.

usage: writeups.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def clock(t):
    """Episode seconds as mm:ss.s."""
    minutes, seconds = divmod(t, 60)
    return f"{int(minutes):02d}:{seconds:04.1f}"


def seconds(c):
    return round(c["out"] - c["in"])


def sources_md(cfg):
    src = cfg["sources"]
    lines = [
        "# Sources and post captions",
        "",
        "Where each of the six clips comes from, and what to post with it. All six are taken from official "
        "Redbelly Insights episodes listed at [redbelly.network/ama](https://redbelly.network/ama). Each clip is a "
        "single unbroken stretch of its episode, so nothing a speaker says has been moved, joined or trimmed out "
        "of the middle.",
        "",
        "Times are `mm:ss.s` into the official episode file. The time link opens that file at the first second "
        "of the clip.",
        "",
        "## At a glance",
        "",
        "| Post | Clip file | Episode | From the episode at | Runs | Who is speaking | Post caption |",
        "| :-: | --- | --- | --- | :-: | --- | --- |",
    ]
    for n, c in enumerate(cfg["cuts"], 1):
        s = src[c["source"]]
        lines.append(
            f"| {n} | [`{c['slug']}.mp4`](clips/{c['slug']}.mp4) | Episode {s['episode_no']}, aired {s['aired']} | "
            f"[{clock(c['in'])} to {clock(c['out'])}]({s['video']}#t={c['in']:.1f},{c['out']:.1f}) | "
            f"{seconds(c)} s | {c['person']} ({c['person_title']}) | {c['post_copy']} |")
    lines += ["", "## Clip by clip", ""]
    for n, c in enumerate(cfg["cuts"], 1):
        s = src[c["source"]]
        lines += [
            f"### Post {n}: {c['headline']}",
            "",
            f"Video `clips/{c['slug']}.mp4`, with the same subtitles as a separate file in "
            f"`subtitles/{c['slug']}.srt`.",
            "",
            f"| | |",
            f"| --- | --- |",
            f"| Episode | {s['title']}, aired {s['aired']} |",
            f"| Official file | {s['video']} |",
            f"| In and out | {clock(c['in'])} to {clock(c['out'])} ({c['in']:.2f} s to {c['out']:.2f} s), "
            f"{seconds(c)} seconds |",
            f"| Speaker | {c['person']}, {c['person_title']} (title as given at {c['title_source']}) |",
            f"| Theme | {c['theme']} |",
            f"| What it says | {c['takeaway']} |",
            f"| Post caption | {c['post_copy']} |",
            "",
        ]
        for note in c.get("editor_notes", []):
            lines.append(f"Editor's note: {note}")
            lines.append("")
        lines += ["What the subtitles say:", "", f"> {c['transcript']}", ""]
    return "\n".join(lines)


def qa_md(cfg, results):
    lines = [
        "# QA",
        "",
        "Every number below is read from the rendered MP4 and SRT files by `python3 pipeline/audit.py`. "
        "Nothing here is typed in by hand.",
        "",
        f"Outcome: **{results['result']}**, from a {results['mode']} audit with "
        f"{len(results['failures'])} failed checks.",
        "",
        "## Files at a glance",
        "",
        "| Clip | Frame | Rate | Codecs | Runs | Size | Integrated loudness | True peak | Loudness range |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for r in results["per_clip"]:
        p, L = r["probe"], r["loudness"]
        lines.append(f"| {r['slug']} | {p['width']}x{p['height']} | {p['fps']:g} fps | {p['vcodec']} + "
                     f"{p['acodec']} | {p['duration']:.1f} s | {p['size_mb']} MB | {L['lufs']:.1f} LUFS | "
                     f"{L['true_peak']:.1f} dBTP | {L['lra']:.1f} LU |")
    lines += ["", "## Every check, clip by clip", ""]
    for r in results["per_clip"]:
        lines += [f"### {r['slug']}", "", "| Check | Outcome | Reading |", "| --- | --- | --- |"]
        for name, v in r["checks"].items():
            lines.append(f"| {name} | {'pass' if v['pass'] else 'FAIL'} | {v['value']} |")
        lines.append("")
    if any("independent_differences" in r for r in results["per_clip"]):
        lines += ["## Where the independent transcript reads it differently", "",
                  f"Each entry is `subtitle / {cfg['audit_model']}`; a dash means that side has nothing there. "
                  "These are the spots to listen to if you want to check a subtitle by ear.", ""]
        for r in results["per_clip"]:
            diffs = r.get("independent_differences", [])
            lines.append(f"- {r['slug']}: " + ("; ".join(f"`{d}`" for d in diffs) if diffs else "identical"))
        lines.append("")
    lines += ["## The pack as a whole", "", "| Check | Outcome | Reading |", "| --- | --- | --- |"]
    for name, v in results["pack_checks"].items():
        reading = "; ".join(map(str, v["value"])) if isinstance(v["value"], list) else v["value"]
        lines.append(f"| {name} | {'pass' if v['pass'] else 'FAIL'} | {reading} |")
    lines += [
        "",
        "## How the less obvious checks work",
        "",
        "Source timestamp. Ten seconds of each clip's audio are slid along the official episode audio around "
        "the time given in `SOURCES.md`, and the best match must land at zero offset. That proves the listed "
        "time points at exactly this audio.",
        "",
        "Subtitles against the audio. The finished clip is transcribed from scratch by "
        f"`{cfg['audit_model']}`, a model that played no part in writing the subtitles, and the two texts are "
        "compared word by word. Before counting, -ise and -ize endings are treated alike, a plus sign is read "
        "as the word plus, a compound split in two is joined, and filler words and stammered repeats are set "
        "aside, since clean verbatim subtitles leave those out. The unadjusted rate is shown next to it.",
        "",
        "Proof-read text. The words in each SRT file must be exactly the transcript stored in `pack.json`, and "
        "every timed word must fall inside one of the cues.",
        "",
        "Speaker in frame. Five frames a second of the finished clip go through face detection (YuNet) and "
        "face recognition (SFace), and each must show the named speaker.",
        "",
        "Spelling, credits and voice. Subtitles, docs and the page are searched for wrong spellings of "
        "Redbelly names and terms, for personal names, handles or signatures, and for the long dashes and "
        "emoji the DAO brand kit rules out.",
        "",
    ]
    return "\n".join(lines)


def main():
    cfg = json.loads((ROOT / "pack.json").read_text())
    (ROOT / "SOURCES.md").write_text(sources_md(cfg) + "\n", encoding="utf-8")
    results_path = ROOT / "qa" / "results.json"
    if results_path.exists():
        results = json.loads(results_path.read_text())
        (ROOT / "QA.md").write_text(qa_md(cfg, results) + "\n", encoding="utf-8")
    print("wrote SOURCES.md" + (" and QA.md" if results_path.exists() else ""))


if __name__ == "__main__":
    main()
