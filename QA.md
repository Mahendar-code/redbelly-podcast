# QA

Every number below is read from the rendered MP4 and SRT files by `python3 pipeline/audit.py`. Nothing here is typed in by hand.

Outcome: **PASS**, from a full audit with 0 failed checks.

## Files at a glance

| Clip | Frame | Rate | Codecs | Runs | Size | Integrated loudness | True peak | Loudness range |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| clip1-ep28-proof-of-stake-incentives | 1080x1920 | 30 fps | h264 + aac | 48.4 s | 18.4 MB | -14.4 LUFS | -2.2 dBTP | 2.6 LU |
| clip2-ep27-kyc-wallets | 1080x1920 | 30 fps | h264 + aac | 55.7 s | 20.8 MB | -14.6 LUFS | -2.2 dBTP | 3.7 LU |
| clip3-ep27-tokenised-bonds | 1080x1920 | 30 fps | h264 + aac | 58.7 s | 19.1 MB | -14.6 LUFS | -2.1 dBTP | 4.2 LU |
| clip4-ep26-registry-to-tokeniser | 1080x1920 | 30 fps | h264 + aac | 58.4 s | 24.7 MB | -14.6 LUFS | -2.3 dBTP | 2.5 LU |
| clip5-ep26-acacia-fund-test | 1080x1920 | 30 fps | h264 + aac | 59.9 s | 18.1 MB | -14.7 LUFS | -2.2 dBTP | 2.9 LU |
| clip6-ep26-investor-portal | 1080x1920 | 30 fps | h264 + aac | 54.3 s | 16.5 MB | -14.9 LUFS | -2.1 dBTP | 3.3 LU |

## Every check, clip by clip

### clip1-ep28-proof-of-stake-incentives

| Check | Outcome | Reading |
| --- | --- | --- |
| aspect 9:16 | pass | 1080x1920 |
| 1080p or higher | pass | 1080p |
| 24 fps or higher | pass | 30.0 fps |
| MP4, H.264 + AAC | pass | h264/yuv420p + aac 48 kHz |
| length 30 to 60 s | pass | 48.4 s |
| audio and video same length | pass | v 48.43 s / a 48.43 s |
| loudness -14 LUFS +/-1 | pass | -14.4 LUFS |
| true peak at most -1 dBTP | pass | -2.2 dBTP |
| no metadata beyond title | pass | compatible_brands, encoder, major_brand, minor_version, title |
| subtitle cues ordered, no overlap | pass | 28 cues |
| subtitles inside clip | pass | last cue ends 48.30 s |
| at most 2 lines per cue | pass | max 2 lines |
| subtitles = proof-read text | pass | 134 words |
| every spoken word inside a cue | pass | 133/133 words |
| audio matches stated source timestamp | pass | offset -0.002 s, correlation 0.98 |
| subtitles vs independent transcript (distil-large-v3) | pass | WER 3.0% (raw 5.2%) |
| speaker in frame (face recognition) | pass | 241/243 sampled frames (99%) |
| names, terms, credits, dashes in subtitles | pass | clean |

### clip2-ep27-kyc-wallets

| Check | Outcome | Reading |
| --- | --- | --- |
| aspect 9:16 | pass | 1080x1920 |
| 1080p or higher | pass | 1080p |
| 24 fps or higher | pass | 30.0 fps |
| MP4, H.264 + AAC | pass | h264/yuv420p + aac 48 kHz |
| length 30 to 60 s | pass | 55.7 s |
| audio and video same length | pass | v 55.73 s / a 55.73 s |
| loudness -14 LUFS +/-1 | pass | -14.6 LUFS |
| true peak at most -1 dBTP | pass | -2.2 dBTP |
| no metadata beyond title | pass | compatible_brands, encoder, major_brand, minor_version, title |
| subtitle cues ordered, no overlap | pass | 31 cues |
| subtitles inside clip | pass | last cue ends 55.73 s |
| at most 2 lines per cue | pass | max 2 lines |
| subtitles = proof-read text | pass | 142 words |
| every spoken word inside a cue | pass | 142/142 words |
| audio matches stated source timestamp | pass | offset -0.002 s, correlation 0.97 |
| subtitles vs independent transcript (distil-large-v3) | pass | WER 9.2% (raw 14.1%) |
| speaker in frame (face recognition) | pass | 276/279 sampled frames (99%) |
| names, terms, credits, dashes in subtitles | pass | clean |

### clip3-ep27-tokenised-bonds

| Check | Outcome | Reading |
| --- | --- | --- |
| aspect 9:16 | pass | 1080x1920 |
| 1080p or higher | pass | 1080p |
| 24 fps or higher | pass | 30.0 fps |
| MP4, H.264 + AAC | pass | h264/yuv420p + aac 48 kHz |
| length 30 to 60 s | pass | 58.7 s |
| audio and video same length | pass | v 58.70 s / a 58.70 s |
| loudness -14 LUFS +/-1 | pass | -14.6 LUFS |
| true peak at most -1 dBTP | pass | -2.1 dBTP |
| no metadata beyond title | pass | compatible_brands, encoder, major_brand, minor_version, title |
| subtitle cues ordered, no overlap | pass | 28 cues |
| subtitles inside clip | pass | last cue ends 58.57 s |
| at most 2 lines per cue | pass | max 2 lines |
| subtitles = proof-read text | pass | 129 words |
| every spoken word inside a cue | pass | 129/129 words |
| audio matches stated source timestamp | pass | offset -0.002 s, correlation 0.98 |
| subtitles vs independent transcript (distil-large-v3) | pass | WER 5.4% (raw 14.7%) |
| speaker in frame (face recognition) | pass | 294/294 sampled frames (100%) |
| names, terms, credits, dashes in subtitles | pass | clean |

### clip4-ep26-registry-to-tokeniser

| Check | Outcome | Reading |
| --- | --- | --- |
| aspect 9:16 | pass | 1080x1920 |
| 1080p or higher | pass | 1080p |
| 24 fps or higher | pass | 30.0 fps |
| MP4, H.264 + AAC | pass | h264/yuv420p + aac 48 kHz |
| length 30 to 60 s | pass | 58.4 s |
| audio and video same length | pass | v 58.40 s / a 58.39 s |
| loudness -14 LUFS +/-1 | pass | -14.6 LUFS |
| true peak at most -1 dBTP | pass | -2.3 dBTP |
| no metadata beyond title | pass | compatible_brands, encoder, major_brand, minor_version, title |
| subtitle cues ordered, no overlap | pass | 42 cues |
| subtitles inside clip | pass | last cue ends 58.39 s |
| at most 2 lines per cue | pass | max 2 lines |
| subtitles = proof-read text | pass | 192 words |
| every spoken word inside a cue | pass | 192/192 words |
| audio matches stated source timestamp | pass | offset -0.002 s, correlation 0.98 |
| subtitles vs independent transcript (distil-large-v3) | pass | WER 3.7% (raw 8.3%) |
| speaker in frame (face recognition) | pass | 292/292 sampled frames (100%) |
| names, terms, credits, dashes in subtitles | pass | clean |

### clip5-ep26-acacia-fund-test

| Check | Outcome | Reading |
| --- | --- | --- |
| aspect 9:16 | pass | 1080x1920 |
| 1080p or higher | pass | 1080p |
| 24 fps or higher | pass | 30.0 fps |
| MP4, H.264 + AAC | pass | h264/yuv420p + aac 48 kHz |
| length 30 to 60 s | pass | 59.9 s |
| audio and video same length | pass | v 59.87 s / a 59.85 s |
| loudness -14 LUFS +/-1 | pass | -14.7 LUFS |
| true peak at most -1 dBTP | pass | -2.2 dBTP |
| no metadata beyond title | pass | compatible_brands, encoder, major_brand, minor_version, title |
| subtitle cues ordered, no overlap | pass | 33 cues |
| subtitles inside clip | pass | last cue ends 59.85 s |
| at most 2 lines per cue | pass | max 2 lines |
| subtitles = proof-read text | pass | 156 words |
| every spoken word inside a cue | pass | 156/156 words |
| audio matches stated source timestamp | pass | offset -0.002 s, correlation 0.98 |
| subtitles vs independent transcript (distil-large-v3) | pass | WER 1.9% (raw 4.5%) |
| speaker in frame (face recognition) | pass | 300/300 sampled frames (100%) |
| names, terms, credits, dashes in subtitles | pass | clean |

### clip6-ep26-investor-portal

| Check | Outcome | Reading |
| --- | --- | --- |
| aspect 9:16 | pass | 1080x1920 |
| 1080p or higher | pass | 1080p |
| 24 fps or higher | pass | 30.0 fps |
| MP4, H.264 + AAC | pass | h264/yuv420p + aac 48 kHz |
| length 30 to 60 s | pass | 54.3 s |
| audio and video same length | pass | v 54.33 s / a 54.33 s |
| loudness -14 LUFS +/-1 | pass | -14.9 LUFS |
| true peak at most -1 dBTP | pass | -2.1 dBTP |
| no metadata beyond title | pass | compatible_brands, encoder, major_brand, minor_version, title |
| subtitle cues ordered, no overlap | pass | 39 cues |
| subtitles inside clip | pass | last cue ends 54.33 s |
| at most 2 lines per cue | pass | max 2 lines |
| subtitles = proof-read text | pass | 176 words |
| every spoken word inside a cue | pass | 176/176 words |
| audio matches stated source timestamp | pass | offset -0.002 s, correlation 0.96 |
| subtitles vs independent transcript (distil-large-v3) | pass | WER 2.3% (raw 2.3%) |
| speaker in frame (face recognition) | pass | 272/272 sampled frames (100%) |
| names, terms, credits, dashes in subtitles | pass | clean |

## Where the independent transcript reads it differently

Each entry is `subtitle / distil-large-v3`; a dash means that side has nothing there. These are the spots to listen to if you want to check a subtitle by ear.

- clip1-ep28-proof-of-stake-incentives: `greedy / gritty`; `stake / stakes`; `rationals / rationales`; `masses / mass`
- clip2-ep27-kyc-wallets: `westpac or nab / westpacel`; `kyc / k c`; `my / a`; `- / in`; `ecosphere / ecosystem`; `the / -`; `could / can`; `- / and`; `kyc'd / co seed`
- clip3-ep27-tokenised-bonds: `the / a`; `- / was the`; `acacia / arcacia`; `out / up`; `cab / cap`; `- / fantastic`
- clip4-ep26-registry-to-tokeniser: `- / do`; `our / -`; `- / or`; `grave / grade`; `what everyone / whatever`; `let's / us`
- clip5-ep26-acacia-fund-test: `acacia / amazing`; `- / aud`; `- / yep`
- clip6-ep26-investor-portal: `and / -`; `holdings / holding`; `- / it's`; `really / -`

## The pack as a whole

| Check | Outcome | Reading |
| --- | --- | --- |
| six clips | pass | 6 |
| loudness spread | pass | 0.5 LU (-14.9 to -14.4 LUFS) |
| six distinct points | pass | 6 |
| no overlapping source ranges | pass | none |
| covers Redbelly technology, Project Acacia, Tokeniser | pass | Project Acacia, Redbelly technology, Tokeniser |
| docs: names, terms, credits, dashes, emoji | pass | clean |

## How the less obvious checks work

Source timestamp. Ten seconds of each clip's audio are slid along the official episode audio around the time given in `SOURCES.md`, and the best match must land at zero offset. That proves the listed time points at exactly this audio.

Subtitles against the audio. The finished clip is transcribed from scratch by `distil-large-v3`, a model that played no part in writing the subtitles, and the two texts are compared word by word. Before counting, -ise and -ize endings are treated alike, a plus sign is read as the word plus, a compound split in two is joined, and filler words and stammered repeats are set aside, since clean verbatim subtitles leave those out. The unadjusted rate is shown next to it.

Proof-read text. The words in each SRT file must be exactly the transcript stored in `pack.json`, and every timed word must fall inside one of the cues.

Speaker in frame. Five frames a second of the finished clip go through face detection (YuNet) and face recognition (SFace), and each must show the named speaker.

Spelling, credits and voice. Subtitles, docs and the page are searched for wrong spellings of Redbelly names and terms, for personal names, handles or signatures, and for the long dashes and emoji the DAO brand kit rules out.

