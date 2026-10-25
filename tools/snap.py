"""Find the quietest moment between two words, so a clip never starts or ends mid-word.

usage: snap.py EPISODE FROM_S TO_S
Prints the time (episode seconds) of the lowest 20 ms RMS window between FROM_S and TO_S.
"""
import sys
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
RATE = 16000


def quietest(episode, lo, hi, win=0.02):
    with wave.open(str(ROOT / "work" / "aud" / f"{episode}.wav")) as w:
        w.setpos(int(lo * RATE))
        pcm = np.frombuffer(w.readframes(int((hi - lo) * RATE)), np.int16).astype(np.float32)
    n = int(win * RATE)
    rms = [float(np.sqrt(np.mean(pcm[i:i + n] ** 2))) for i in range(0, len(pcm) - n, n // 2)]
    k = int(np.argmin(rms))
    return round(lo + (k * n // 2 + n / 2) / RATE, 3), round(20 * np.log10(rms[k] / 32768 + 1e-9), 1)


if __name__ == "__main__":
    t, db = quietest(sys.argv[1], float(sys.argv[2]), float(sys.argv[3]))
    print(f"{t:.3f} ({db} dBFS)")
