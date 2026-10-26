"""Proof-reading aid: the three Whisper readings of each clip, word-aligned.

For every cut in pack.json, the small.en, medium.en and large-v3 transcriptions of the
clip window are cut to the clip's source range, aligned against the proof-read transcript,
and every place where any model reads it differently is listed. The plain readings go to
qa/readings/ so each subtitle decision can be checked later.

usage: readings.py [SLUG ...]
"""
import difflib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from timing import norm, whisper_words  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "work"
MODELS = ["small.en", "medium.en", "large-v3"]


def main():
    cfg = json.loads((ROOT / "pack.json").read_text())
    wanted = set(sys.argv[1:])
    out_dir = ROOT / "qa" / "readings"
    out_dir.mkdir(parents=True, exist_ok=True)
    for c in cfg["cuts"]:
        if wanted and c["slug"] not in wanted:
            continue
        print(f"\n=== {c['slug']}  {c['in']:.2f} to {c['out']:.2f}")
        readings = {}
        for m in MODELS:
            path = WORK / "tx" / f"{c['slug']}.{m}.json"
            if not path.exists():
                continue
            words = whisper_words(path, c["in"] + 0.25, c["out"] - 0.25)
            readings[m] = " ".join(w["w"] for w in words)
            (out_dir / f"{c['slug']}.{m}.txt").write_text(readings[m] + "\n", encoding="utf-8")
        text = c["transcript"].split()
        a = [norm(w) for w in text]
        for m, r in readings.items():
            b = [norm(w) for w in r.split()]
            sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
            diffs = [(op, " ".join(text[i1:i2]), " ".join(r.split()[j1:j2]))
                     for op, i1, i2, j1, j2 in sm.get_opcodes() if op != "equal"]
            print(f"  {m:10s} agreement {sm.ratio():.1%}, {len(diffs)} differences")
            for op, t, h in diffs:
                print(f"      {op:8s} text={t!r:45s} {m}={h!r}")


if __name__ == "__main__":
    main()
