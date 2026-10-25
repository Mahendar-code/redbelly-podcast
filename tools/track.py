"""Shot detection and speaker tracking for the square crop.

For a source range the episode video is decoded at 30 fps (downscaled for analysis),
cut into camera shots, and the speaker is located in every shot by face recognition:
YuNet finds faces, SFace embeds them, and each face is compared with reference
embeddings of the speaker taken from frames where they are alone on screen.

The result is one fixed crop window per shot, in source pixels, or a "cutaway"
marker for shots where the speaker is not visible.

usage: track.py [CLIP_ID ...]          crop plans for clips.json into data/tracks/
       track.py EPISODE START END REF_TIMES OUT.json [REGION]   ad hoc
  REF_TIMES is a comma separated list of source seconds where the speaker is clearly visible.
"""
import json
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
WORK = Path.cwd() / "work" if (Path.cwd() / "work").is_dir() else ROOT / "work"
MODELS = WORK / "models"

ANALYSIS_W = 960          # analysis width; crops are scaled back to source pixels
FPS = 30
FACE_EVERY = 3            # run face detection on every 3rd frame (10 per second)
SHOT_THRESHOLD = 0.45     # histogram distance that counts as a camera cut
MATCH = 0.40              # SFace cosine similarity that counts as the same person
MIN_SHOT = 0.25           # shorter "shots" are merged into the previous one (flashes, dissolves)
FACE_SPAN = 4.5           # crop window width in face widths


def probe(src):
    out = subprocess.check_output([
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height", "-of", "csv=p=0", str(src)]).decode()
    w, h = (int(v) for v in out.strip().split(","))
    return w, h


def frames(src, start, end, width):
    """Yield (t, frame) for t from start to end at 30 fps, frame resized to `width`."""
    w, h = probe(src)
    height = round(h * width / w / 2) * 2
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{start:.3f}", "-to", f"{end:.3f}", "-i", str(src),
           "-vf", f"fps={FPS},scale={width}:{height}", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    size = width * height * 3
    i = 0
    try:
        while True:
            buf = proc.stdout.read(size)
            if len(buf) < size:
                break
            yield start + i / FPS, np.frombuffer(buf, np.uint8).reshape(height, width, 3)
            i += 1
    finally:
        proc.kill()
        proc.wait()


class Faces:
    def __init__(self):
        self.det = cv2.FaceDetectorYN.create(str(MODELS / "yunet.onnx"), "", (320, 320), 0.7, 0.3, 5000)
        self.rec = cv2.FaceRecognizerSF.create(str(MODELS / "sface.onnx"), "")

    def detect(self, img):
        h, w = img.shape[:2]
        self.det.setInputSize((w, h))
        _, faces = self.det.detect(img)
        return [] if faces is None else list(faces)

    def embed(self, img, face):
        aligned = self.rec.alignCrop(img, face)
        feat = self.rec.feature(aligned)
        return feat / np.linalg.norm(feat)


def reference(src, times, faces, region=None):
    """Mean embedding of the largest face at each reference time (inside region, if given)."""
    feats = []
    scale = probe(src)[0] / ANALYSIS_W
    for t in times:
        for _, img in frames(src, t, t + 0.05, ANALYSIS_W):
            found = faces.detect(img)
            if region:
                found = [f for f in found if region[0] <= (f[0] + f[2] / 2) * scale < region[2]]
            if found:
                big = max(found, key=lambda f: f[2] * f[3])
                feats.append(faces.embed(img, big))
            break
    if not feats:
        raise SystemExit(f"no face found at reference times {times}")
    ref = np.mean(feats, axis=0)
    return ref / np.linalg.norm(ref)


def hist(img):
    small = cv2.resize(img, (160, 90))
    hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
    h = cv2.calcHist([hsv], [0, 1], None, [32, 16], [0, 180, 0, 256])
    return cv2.normalize(h, h).flatten()


def analyse(src, start, end, ref_times, region=None):
    faces = Faces()
    ref = reference(src, ref_times, faces, region)
    src_w, src_h = probe(src)
    scale = src_w / ANALYSIS_W

    cuts = [start]
    samples = []          # (t, [(sim, cx, cy, fw, fh), ...]) in source pixels
    prev = None
    for i, (t, img) in enumerate(frames(src, start, end, ANALYSIS_W)):
        hs = hist(img)
        if prev is not None and cv2.compareHist(prev, hs, cv2.HISTCMP_BHATTACHARYYA) > SHOT_THRESHOLD:
            if t - cuts[-1] >= MIN_SHOT:
                cuts.append(t)
        prev = hs
        if i % FACE_EVERY == 0:
            found = []
            for f in faces.detect(img):
                sim = float(np.dot(faces.embed(img, f).ravel(), ref.ravel()))
                x, y, w, h = (float(v) * scale for v in f[:4])
                found.append((sim, x + w / 2, y + h / 2, w, h))
            samples.append((t, found))
    cuts.append(end)
    return cuts, samples, (src_w, src_h)


def plan(cuts, samples, size, region=None, side=None):
    """One crop window per shot. region limits the crop to part of the frame (split screens)."""
    src_w, src_h = size
    rx0, ry0, rx1, ry1 = region or (0, 0, src_w, src_h)
    shots = []
    for a, b in zip(cuts[:-1], cuts[1:]):
        inside = [s for s in samples if a <= s[0] < b]
        hits = []
        for _, found in inside:
            best = max(found, key=lambda f: f[0], default=None)
            if best and best[0] >= MATCH and rx0 <= best[1] < rx1:
                hits.append(best)
        shot = {"start": round(a, 3), "end": round(b, 3), "samples": len(inside), "matched": len(hits)}
        if not inside or len(hits) < max(1, 0.5 * len(inside)):
            shot["kind"] = "cutaway"
        else:
            cx = float(np.median([h[1] for h in hits]))
            cy = float(np.median([h[2] for h in hits]))
            fw = float(np.median([h[3] for h in hits]))
            # window about 4.5 face widths wide: a medium close-up in close shots, and in wide or
            # two-person shots a tighter window on the speaker (never below 55% of frame height)
            s = side or min(ry1 - ry0, rx1 - rx0, max(FACE_SPAN * fw, 0.55 * src_h))
            s = int(s) // 2 * 2
            x = int(np.clip(cx - s / 2, rx0, rx1 - s))
            y = int(np.clip(cy - 0.40 * s, ry0, ry1 - s))
            spread = [abs(h[1] - cx) for h in hits]
            shot.update(kind="speaker", crop=[x, y, s],
                        similarity=round(float(np.median([h[0] for h in hits])), 3),
                        face_px=round(fw), drift_px=round(max(spread)))
            # every matched face centre must sit inside the crop with a margin
            shot["face_inside"] = all(x + 0.1 * s <= h[1] <= x + 0.9 * s and y <= h[2] <= y + s for h in hits)
        shots.append(shot)
    return shots


def track_clip(clip, episode):
    """Crop plan for one clip of clips.json, written to data/tracks/<id>.json."""
    src = WORK / "src" / f"{clip['episode']}.mp4"
    spk = episode["speakers"][clip["speaker"]]
    region = spk.get("region")
    cuts, samples, size = analyse(src, clip["start"], clip["end"], spk["refs"], spk.get("ref_region") or region)
    shots = plan(cuts, samples, size, region, spk.get("side"))
    out = ROOT / "data" / "tracks" / f"{clip['id']}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"id": clip["id"], "episode": clip["episode"], "speaker": clip["speaker"],
                               "size": size, "shots": shots}, indent=1))
    return shots


def main():
    if len(sys.argv) > 1 and sys.argv[1].startswith("ep"):
        # ad hoc: track.py EPISODE START END REF_TIMES OUT.json [REGION_JSON]
        episode, start, end, refs, out = sys.argv[1:6]
        src = WORK / "src" / f"{episode}.mp4"
        region = json.loads(sys.argv[6]) if len(sys.argv) > 6 else None
        cuts, samples, size = analyse(src, float(start), float(end), [float(r) for r in refs.split(",")], region)
        shots = plan(cuts, samples, size, region)
        json.dump({"episode": episode, "size": size, "shots": shots}, open(out, "w"), indent=1)
        for s in shots:
            print(s)
        return
    cfg = json.loads((ROOT / "clips.json").read_text())
    wanted = set(sys.argv[1:])
    for c in cfg["clips"]:
        if wanted and c["id"] not in wanted:
            continue
        print(c["id"])
        for s in track_clip(c, cfg["episodes"][c["episode"]]):
            print("  ", {k: v for k, v in s.items() if k != "samples"})


if __name__ == "__main__":
    main()
