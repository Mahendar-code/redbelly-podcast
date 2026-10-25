"""Word-timestamped transcript of an audio file (or a window of it) with faster-whisper.

usage: transcribe.py MODEL AUDIO.wav OUT.json [START_S END_S]
"""
import json
import os
import sys
import wave

import numpy as np
from faster_whisper import WhisperModel

GLOSSARY_PROMPT = "A Redbelly Insights podcast about Redbelly Network, Tokeniser and Project Acacia."


def load_wav(path):
    """16 kHz mono PCM WAV as float32, without going through PyAV."""
    with wave.open(path) as w:
        assert w.getframerate() == 16000 and w.getnchannels() == 1, "expects 16 kHz mono"
        pcm = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
    return pcm.astype(np.float32) / 32768.0


def main():
    model_name, wav, out = sys.argv[1:4]
    audio = load_wav(wav)
    offset = 0.0
    if len(sys.argv) > 5:
        # transcribe only this window of the episode; times stay in episode seconds
        offset, stop = float(sys.argv[4]), float(sys.argv[5])
        audio = audio[int(offset * 16000):int(stop * 16000)]
    model = WhisperModel(model_name, device="cpu", compute_type="int8",
                         cpu_threads=int(os.environ.get("WHISPER_THREADS", "4")))
    segments, info = model.transcribe(
        audio,
        language="en",
        word_timestamps=True,
        vad_filter=True,
        beam_size=5,
        initial_prompt=GLOSSARY_PROMPT if os.environ.get("WHISPER_PROMPT", "1") == "1" else None,
        condition_on_previous_text=False,
    )
    data = []
    for s in segments:
        data.append({
            "start": round(s.start + offset, 2),
            "end": round(s.end + offset, 2),
            "text": s.text.strip(),
            "words": [[round(w.start + offset, 2), round(w.end + offset, 2), w.word, round(w.probability, 3)]
                      for w in s.words],
        })
        print(f"[{s.start + offset:7.1f}] {s.text.strip()}", flush=True)
    json.dump({"model": model_name, "offset": offset, "duration": info.duration, "segments": data},
              open(out, "w"), indent=1)


if __name__ == "__main__":
    main()
