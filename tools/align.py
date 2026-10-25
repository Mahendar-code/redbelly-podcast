"""Attach word timings to the proof-read subtitle text.

The proof-read text in clips.json is the source of truth for what the subtitles say.
Timings come from a Whisper transcription of the clip window (work/tx/<id>.<model>.json).
The two word sequences are aligned with difflib: matched words take Whisper's timing,
corrected words share the time span of the words they replace, and words Whisper
dropped are placed in the gap between their neighbours.

usage: align.py MODEL [CLIP_ID ...]
Writes data/words/<id>.json and prints every place the text differs from Whisper.
"""
import difflib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "work"


def norm(word):
    w = word.lower().replace("’", "'")
    w = re.sub(r"[^a-z0-9'$%.]", "", w).strip(".'")
    return {"tokenise": "tokenize", "tokenised": "tokenized", "tokeniser": "tokenizer",
            "tokenisation": "tokenization"}.get(w, w)


def whisper_words(path, start, end):
    data = json.loads(Path(path).read_text())
    out = []
    for seg in data["segments"]:
        for s, e, w, p in seg["words"]:
            if s >= start - 0.3 and e <= end + 0.3 and w.strip():
                out.append({"w": w.strip(), "s": s, "e": e, "p": p})
    return out


def align(text, heard, start, end):
    words = text.split()
    a = [norm(w) for w in words]
    b = [norm(h["w"]) for h in heard]
    timed = [None] * len(words)
    diffs = []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if op == "equal":
            for k in range(i2 - i1):
                timed[i1 + k] = (heard[j1 + k]["s"], heard[j1 + k]["e"])
            continue
        diffs.append({"op": op, "text": " ".join(words[i1:i2]), "whisper": " ".join(h["w"] for h in heard[j1:j2])})
        if op == "replace":
            s, e = heard[j1]["s"], heard[j2 - 1]["e"]
            chars = [max(len(w), 1) for w in words[i1:i2]]
            total, acc = sum(chars), 0
            for k, c in enumerate(chars):
                timed[i1 + k] = (s + (e - s) * acc / total, s + (e - s) * (acc + c) / total)
                acc += c
    # words Whisper did not hear: spread them over the gap between their timed neighbours
    k = 0
    while k < len(words):
        if timed[k] is not None:
            k += 1
            continue
        j = k
        while j < len(words) and timed[j] is None:
            j += 1
        left = timed[k - 1][1] if k > 0 else max(start, (timed[j][0] if j < len(words) else end) - 0.3 * (j - k))
        right = timed[j][0] if j < len(words) else min(end, left + 0.3 * (j - k))
        step = (right - left) / (j - k)
        for n in range(k, j):
            timed[n] = (left + step * (n - k), left + step * (n - k + 1))
        k = j
    out = []
    for w, (s, e) in zip(words, timed):
        s, e = max(s, start), min(e, end)
        out.append({"w": w, "s": round(s, 3), "e": round(max(e, s + 0.05), 3)})
    # keep times monotonic
    for i in range(1, len(out)):
        if out[i]["s"] < out[i - 1]["s"]:
            out[i]["s"] = out[i - 1]["s"]
        out[i]["e"] = max(out[i]["e"], out[i]["s"] + 0.05)
    return out, diffs


def main():
    model = sys.argv[1]
    wanted = set(sys.argv[2:])
    cfg = json.loads((ROOT / "clips.json").read_text())
    (ROOT / "data" / "words").mkdir(parents=True, exist_ok=True)
    for c in cfg["clips"]:
        if wanted and c["id"] not in wanted:
            continue
        heard = whisper_words(WORK / "tx" / f"{c['id']}.{model}.json", c["start"], c["end"])
        words, diffs = align(c["text"], heard, c["start"], c["end"])
        (ROOT / "data" / "words" / f"{c['id']}.json").write_text(json.dumps(
            {"id": c["id"], "timing_model": model, "words": words}, indent=1))
        print(f"{c['id']}: {len(words)} words, {len(diffs)} differences from {model}")
        for d in diffs:
            print(f"   {d['op']:8s} text={d['text']!r:40s} whisper={d['whisper']!r}")


if __name__ == "__main__":
    main()
