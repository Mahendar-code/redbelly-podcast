# Podcast Clip Pack

Short, subtitled vertical clips from the latest official Redbelly Insights episodes, for the Redbelly and DAO accounts to post on X, YouTube Shorts and Instagram while the show relaunches as Off Paper - Powered by Tokeniser.

There are six clips, each between 30 and 60 seconds. Every one opens on a headline with the speaker's name and title on screen, makes a single point about Redbelly technology, Project Acacia or Tokeniser, and comes with a caption to post alongside it.

The review page is `index.html`, published on Vercel. It plays every clip, says what each one is about, links each clip to the official episode at the second it starts, offers the caption with a copy button and an X character count, and lets you download the MP4 and SRT. The audit results sit at the bottom of the same page.

## What is in the repository

| Brief | File or folder | Contents |
|---|---|---|
| Deliverable 1: six vertical clips with subtitles | `clips/` and `subtitles/` | MP4, 1080x1920, 9:16, 30 fps, H.264 video and AAC audio, subtitles burned in. The same subtitles as SRT files |
| Deliverable 2: source episode, timestamp and post caption for each clip | `SOURCES.md` | One table for the whole pack, then a section per clip with its subtitle text |
| Proof | `QA.md`, `qa/results.json` | Every audit reading, taken from the rendered files |
| Proof | `qa/readings/` | The three model transcriptions of each clip and every place they differ from the subtitles |
| Source of truth | `pack.json` | Sources, in and out points, proof-read transcripts, headlines, speakers, titles and captions |
| Working data | `data/timing/`, `data/framing/` | Word timings for the subtitles, and the crop window chosen for each camera shot |
| Code | `pipeline/` | Everything that cut, framed, subtitled, rendered and audited the clips |
| Tests | `tests/` | `pytest` suite for the committed pack and the pipeline code |
| Look | `assets/` | DAO brand kit logos and icon, fonts with their SIL OFL licences, one still per clip, the share card |

## The six posts

Listed in the order to post them. `SOURCES.md` has the times to a tenth of a second and the full subtitle text.

| Post | Headline | Speaker | Episode and time | Runs | Theme |
|:-:|---|---|---|:-:|---|
| 1 | Proof of stake still gets hacked. What's missing? | Vincent Gramoli, Founder & Chief Science Officer, Redbelly Network | 28, from 33:25 | 48 s | Redbelly technology |
| 2 | Stablecoins work like cash. Redbelly wallets are KYC'd. | Drew Bradford, CEO, Macropod | 27, from 21:58 | 56 s | Redbelly technology |
| 3 | After Project Acacia, tokenised bonds are next | Drew Bradford, CEO, Macropod | 27, from 23:29 | 59 s | Project Acacia |
| 4 | Every regulated asset needs a registry. Enter Tokeniser. | Alan Burt, Executive Chairman, Redbelly Network | 26, from 03:11 | 58 s | Tokeniser |
| 5 | What Project Acacia tested inside a real fund | Matt Mills, Chief Customer Officer, Tokeniser | 26, from 17:39 | 60 s | Project Acacia |
| 6 | What investors see when they log in to Tokeniser | Matt Mills, Chief Customer Officer, Tokeniser | 26, from 23:13 | 54 s | Tokeniser |

Six separate ideas: regulated proof of stake that lines up everyone's incentives, identity-checked wallets, tokenised bonds as the next step after Acacia, the registry as the starting point for Tokeniser, what Acacia tested inside a live fund, and the investor's view of Tokeniser.

## How the moments were picked

The brief asks for the latest episodes. On [redbelly.network/ama](https://redbelly.network/ama) the newest Redbelly Insights episode is 29, from 9 July 2026, so Episodes 25 to 29 were downloaded from the links on that page and read through starting from the newest. The six clips come from Episodes 28, 27 and 26.

A moment was kept only if it was about Redbelly technology, Project Acacia or Tokeniser, made one point a newcomer can follow without context, and did not repeat a point another clip already makes.

Clips are never edited internally. Each one plays straight through from its first word to its last, so nothing a speaker said can be rearranged into something they did not mean. The in and out points sit in the silence between words.

Speaker names and titles come from official pages: [redbelly.network/about-us](https://redbelly.network/about-us) for Vincent Gramoli and Alan Burt, [tokeniser.com/about](https://tokeniser.com/about) for Matt Mills, and [macropod.com/about](https://www.macropod.com/about) for Drew Bradford.

## Subtitles

Whisper `small.en`, `medium.en` and `large-v3` each transcribed every clip on their own. The subtitle text was settled word by word against the three readings. Where they disagree it follows the reading that two of them share, or `large-v3` when the sentence only makes sense that way, and each such call is noted in `SOURCES.md`.

Names and terms were checked one by one: Redbelly, Redbelly Network, RBNT, Tokeniser, Project Acacia, Liquidise, Macropod, AUDM, TAF Capital, CBA, Westpac, NAB, and the RBA's Brad Jones and Ellis Connolly. Spelling is Australian throughout, as in tokenise and incentivise.

The subtitles are clean verbatim. Every word the speaker says is there, except stammered repeats and fillers such as um. Brief back-channel words from the host are not subtitled.

Each clip has the subtitles burned in, a phrase at a time with the current word on a red box, and the same lines in an SRT file for platforms that prefer to add their own.

## Picture and sound

The episodes are filmed 16:9. For every camera shot inside a clip, face recognition (YuNet to find faces, SFace to tell people apart) picks out the person speaking, and a square window is set on them for the length of that shot, so it never drifts. Where the episode shows the host for a moment while the guest keeps talking, the guest's nearest frame is held and the sound runs on: 1.8 seconds at the start of post 3, 0.7 seconds at the start of post 5 and 2.3 seconds near the end of post 6. `SOURCES.md` lists each one.

The sound is the episode's own and nothing else. Each clip is measured, brought to -14 LUFS integrated and passed through a limiter that keeps true peaks below -2 dBTP, so the six play at the same volume. No music has been added.

## Look

The clips and the page follow the [Redbelly DAO Task Board brand kit](https://taskboard.redbellydao.network/brand). In practice that means:

- slate backgrounds with brand red `#EF5350` as the only accent, and `#ffb3ae` for accent text on dark
- Be Vietnam Pro for all words, JetBrains Mono only for numbers and labels such as episode, time and size
- the kit's own DAO logo files, light ink on dark, never on a plate and never over footage
- plain wording with no long dashes and no emoji, which the audit checks for

Each frame reads from the top: a red progress line, the episode label, theme and DAO logo, the headline, the speaker in a 1080x1080 window with a name plate, and the captions in their own band. The bottom strip is left empty for the buttons and text X, Shorts, Reels and TikTok lay over a video.

## Audit and tests

`python3 pipeline/audit.py` reads every rendered clip and exits with an error if anything is out of line. It writes `qa/results.json`, which `QA.md` and the page are built from. For each clip it checks:

- frame size 1080x1920 at 9:16, 30 fps, MP4 with H.264 and AAC, a length of 30 to 60 seconds, and sound and picture of equal length
- integrated loudness within 1 LU of -14 LUFS, true peak no higher than -1 dBTP, and less than 1 LU between the loudest and quietest clip
- that the clip's audio lines up with the official episode at exactly the time listed in `SOURCES.md`, by cross-correlation
- that a fourth model, `distil-large-v3`, which had no part in writing the subtitles, hears the same words as the subtitles say
- that the SRT holds exactly the proof-read transcript, every timed word falls inside a cue, and cues never overlap or run past two lines
- that the named speaker is on screen, by face recognition five times a second
- that subtitles, tags, docs and page contain no misspelt Redbelly terms or names, no personal names, handles or signatures, and no long dashes or emoji

`python3 -m pytest -q` tests the committed pack (files, SRTs, word timings, crop plans, docs, the failure criteria in the brief) and the pipeline code itself (alignment, caption layout, the audit maths).

## Publishing the page

Nothing needs compiling; Vercel just serves the files as they are.

1. In Vercel choose Add New Project and import this repository.
2. Set Framework Preset to Other and leave the build and output settings empty.
3. Deploy. From then on, every push to `main` updates the live page.

`vercel.json` serves the Markdown and SRT files as plain text and lets browsers cache the clips. The same folder also works on any other static host. To give the share card a full address, rebuild the page with `SITE_URL=https://your-domain python3 pipeline/page.py`.

## Rebuilding from scratch

You need Python 3.10 or newer, `ffmpeg`, and `pip install faster-whisper opencv-python-headless pillow numpy pytest`, plus the [YuNet](https://github.com/opencv/opencv_zoo/tree/main/models/face_detection_yunet) and [SFace](https://github.com/opencv/opencv_zoo/tree/main/models/face_recognition_sface) models from the OpenCV model zoo saved as `work/models/yunet.onnx` and `work/models/sface.onnx`. The `work/` folder holds downloads and is not committed.

```bash
# official episode files named in pack.json, plus 16 kHz mono audio for the speech models
mkdir -p work/src work/aud work/tx
python3 -c 'import json;[print(k,v["video"]) for k,v in json.load(open("pack.json"))["sources"].items()]' |
  while read key url; do curl -sSL "$url" -o work/src/$key.mp4
    ffmpeg -v error -i work/src/$key.mp4 -vn -ac 1 -ar 16000 work/aud/$key.wav; done

# three readings of a clip, for example post 1
for m in small.en medium.en large-v3; do
  python3 pipeline/asr.py $m work/aud/rbi28.wav work/tx/clip1-ep28-proof-of-stake-incentives.$m.json 1996 2062
done
python3 pipeline/readings.py      # where each reading differs from the transcript in pack.json

python3 pipeline/timing.py large-v3
python3 pipeline/framing.py
python3 pipeline/compose.py
python3 pipeline/audit.py
python3 pipeline/writeups.py      # SOURCES.md and QA.md
python3 pipeline/page.py          # index.html, stills, share card
python3 -m pytest -q
```

| Script | What it does |
|---|---|
| `pipeline/asr.py` | Transcribes an episode, or a window of it, with word times |
| `pipeline/readings.py` | Lines the three readings of each clip up against the proof-read transcript |
| `pipeline/cutpoints.py` | Finds the quietest instant between two words, for clean in and out points |
| `pipeline/timing.py` | Lays the proof-read words onto the speech model's word times |
| `pipeline/framing.py` | Finds camera shots and the speaker's face, one crop window per shot |
| `pipeline/compose.py` | Draws the 1080x1920 frame, captions and name plate, levels the audio, encodes MP4 and SRT |
| `pipeline/audit.py` | Measures the finished clips and fails on anything out of line |
| `pipeline/writeups.py` | Writes `SOURCES.md` and `QA.md` |
| `pipeline/page.py` | Writes `index.html`, the stills and the share card |

Every frame and every second of sound in the clips comes from official Redbelly Insights episodes published at [redbelly.network/ama](https://redbelly.network/ama).
