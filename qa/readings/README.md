# Model readings behind the subtitles

Each clip was transcribed three times, by Whisper `small.en`, `medium.en` and `large-v3`. The `.txt` files here are those raw readings, trimmed to the clip's in and out points. They have not been corrected, so they still contain the models' slips, misheard brand names among them. They are kept so that any subtitle line can be traced back to what the models heard.

`differences.txt`, written by `python3 pipeline/readings.py`, lists for each clip every word where a model's reading and the final subtitle transcript disagree.

The final words are the `transcript` of each cut in `pack.json`. Where the models disagreed, the subtitle takes the reading at least two of them share, or the `large-v3` reading when the meaning of the sentence backs it. Calls that needed judgement are written up as editor's notes in `SOURCES.md`.
