"""Proof-reading aid: the three Whisper readings of each clip, word-aligned.

For every clip in clips.json, the small.en, medium.en and large-v3 transcriptions of the
clip window are cut to the clip's source range, aligned against the proof-read text, and
every place where any model reads it differently is listed. The plain readings are saved
to verification/transcripts/ so each subtitle decision can be checked later.

usage: compare.py [CLIP_ID ...]
"""
import difflib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from align import norm, whisper_words  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "work"
MODELS = ["small.en", "medium.en", "large-v3"]


def main():
    cfg = json.loads((ROOT / "clips.json").read_text())
    wanted = set(sys.argv[1:])
    out_dir = ROOT / "verification" / "transcripts"
    out_dir.mkdir(parents=True, exist_ok=True)
    for c in cfg["clips"]:
        if wanted and c["id"] not in wanted:
            continue
        print(f"\n=== {c['id']}  {c['start']:.2f} to {c['end']:.2f}")
        readings = {}
        for m in MODELS:
            path = WORK / "tx" / f"{c['id']}.{m}.json"
            if not path.exists():
                continue
            words = whisper_words(path, c["start"] + 0.25, c["end"] - 0.25)
            readings[m] = " ".join(w["w"] for w in words)
            (out_dir / f"{c['id']}.{m}.txt").write_text(readings[m] + "\n", encoding="utf-8")
        text = c["text"].split()
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
