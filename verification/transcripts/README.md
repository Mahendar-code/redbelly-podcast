# Machine readings used for proof-reading

For each clip, the source range was transcribed separately by three Whisper models: `small.en`, `medium.en` and `large-v3`. These files are their raw readings of the clip, cut to the clip's source range. They are **not** proof-read and contain the models' own mistakes, for example misheard brand names. They are kept so every subtitle decision can be checked.

`differences.txt` lists, for every clip, each place where a model's reading differs from the proof-read subtitle text in `clips.json`. It is written by `python3 tools/compare.py`.

The proof-read text, which is what the subtitles say, is the `text` field of each clip in `clips.json`. Where the models disagreed, the subtitle follows the reading shared by at least two models, or by `large-v3` where the sense of the sentence supports it. Each such call is noted in `CLIPS.md`.
