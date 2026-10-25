# Podcast Clip Pack

Six captioned vertical clips of 30 to 60 seconds, cut from the latest official Redbelly Insights episodes. Each clip makes one point about Redbelly technology, Project Acacia or Tokeniser, opens with a hook and the speaker's name and role, and comes with a one line post caption. They are ready for the Redbelly and DAO accounts to post on X, YouTube Shorts and Instagram while the show relaunches as Off Paper - Powered by Tokeniser.

**Review page:** [`index.html`](index.html), deployed as a static site on Vercel (see [Deploy](#deploy)). It has a player for every clip, the hook, speaker and role, the point each clip makes, the source episode and timestamp linked to the official episode file at that exact moment, the post caption with a copy button and X character count, MP4 and SRT downloads, and the measured verification results.

## Deliverables

| # | Deliverable in the brief | Where |
|---|---|---|
| 1 | Six vertical clips with subtitles. 9:16, 1080p or higher, 24 fps or higher, MP4 or MOV | [`clips/`](clips): MP4, 1080x1920, 30 fps, H.264 + AAC, subtitles burned in. The same subtitles as separate SRT files in [`subtitles/`](subtitles) |
| 2 | Source episode and timestamp for each clip, with a suggested post caption | [`CLIPS.md`](CLIPS.md) |

Supporting files:

| Path | What it is |
|---|---|
| [`VERIFICATION.md`](VERIFICATION.md), [`verification/report.json`](verification/report.json) | Every check, measured from the rendered files |
| [`verification/transcripts/`](verification/transcripts) | The three machine readings of every clip used to proof-read the subtitles, and where each one differs from the final text |
| [`clips.json`](clips.json) | Single source of truth: episodes, source ranges, proof-read subtitle text, hooks, names, roles, points and captions |
| [`data/words/`](data/words), [`data/tracks/`](data/tracks) | Word timings behind the subtitles, and the crop window used for each camera shot |
| [`tools/`](tools) | The scripts that made and checked the pack |
| [`tests/`](tests) | `pytest` checks on the delivered pack and unit tests for the tools |
| [`assets/`](assets) | Redbelly DAO brand kit logos and tokens, fonts (SIL OFL), poster frames |

## The clips

In posting order. Exact timestamps to a tenth of a second, the post captions and the full subtitle text are in [`CLIPS.md`](CLIPS.md).

| # | Clip | Hook | Speaker | Source | Length | Topic |
|---|---|---|---|---|---|---|
| 1 | [`01_aussie_dollars_onshore.mp4`](clips/01_aussie_dollars_onshore.mp4) | We spend Aussie dollars. Why settle in US dollars? | Effie Dimitropoulos, CEO, AUDD Stablecoin | Episode 29 (9 July 2026), 43:43.1 to 44:29.1 | 46 s | Redbelly technology |
| 2 | [`02_regulated_proof_of_stake.mp4`](clips/02_regulated_proof_of_stake.mp4) | Proof of stake still gets hacked. What's missing? | Vincent Gramoli, Founder & Chief Science Officer, Redbelly Network | Episode 28 (11 June 2026), 33:25.3 to 34:13.7 | 48 s | Redbelly technology |
| 3 | [`03_tokenised_bonds_next.mp4`](clips/03_tokenised_bonds_next.mp4) | After Project Acacia, tokenised bonds are next | Drew Bradford, CEO, Macropod | Episode 27 (28 May 2026), 23:29.5 to 24:28.2 | 59 s | Project Acacia |
| 4 | [`04_registry_to_tokeniser.mp4`](clips/04_registry_to_tokeniser.mp4) | Every regulated asset needs a registry. Enter Tokeniser. | Alan Burt, Executive Chairman, Redbelly Network | Episode 26 (26 March 2026), 03:11.7 to 04:10.1 | 58 s | Tokeniser |
| 5 | [`05_acacia_fund_processes.mp4`](clips/05_acacia_fund_processes.mp4) | What Project Acacia tested inside a real fund | Matt Mills, Chief Customer Officer, Tokeniser | Episode 26 (26 March 2026), 17:39.0 to 18:38.8 | 60 s | Project Acacia |
| 6 | [`06_tokeniser_investor_portal.mp4`](clips/06_tokeniser_investor_portal.mp4) | What investors see when they log in to Tokeniser | Matt Mills, Chief Customer Officer, Tokeniser | Episode 26 (26 March 2026), 23:13.7 to 24:08.0 | 54 s | Tokeniser |

Two clips per topic, five different speakers, four episodes, and six different points: keeping digital dollars onshore, aligning incentives in proof of stake, tokenised bonds after Acacia, why every asset starts with a registry, what Acacia tested inside a fund, and what investors see in Tokeniser.

## How the moments were chosen

- **Latest first.** [redbelly.network/ama](https://redbelly.network/ama) lists Episode 29 (9 July 2026) as the most recent Redbelly Insights episode. Episodes 25 to 29 were downloaded from the official links on that page and transcribed, newest first. The clips come from Episodes 29, 28, 27 and 26.
- **On brief.** Only passages about Redbelly technology, Project Acacia or Tokeniser were considered, and each had to make one point that holds up for someone who has never heard of Redbelly. No two clips make the same point.
- **One continuous passage per clip.** Nothing inside a clip is cut, reordered or joined, so no quote can be edited into a different meaning. Clips start and end on sentence boundaries, at the quietest moment between words.
- **Names and roles from official pages.** Vincent Gramoli and Alan Burt from [redbelly.network/about-us](https://redbelly.network/about-us), Matt Mills from [tokeniser.com/about](https://tokeniser.com/about), Drew Bradford from [macropod.com/about](https://www.macropod.com/about), and Effie Dimitropoulos from the episode's own on-screen title.

## Subtitles

- Each clip's source range was transcribed by three Whisper models (`small.en`, `medium.en`, `large-v3`). The subtitle text was proof-read against all three: where they disagree, the subtitle follows the reading shared by at least two, or `large-v3` where the sense of the sentence supports it. Every reading and every difference is in [`verification/transcripts/`](verification/transcripts), and the judgement calls are noted per clip in `CLIPS.md`.
- Names and terms are checked: Redbelly, Redbelly Network, RBNT, Tokeniser, Project Acacia, Liquidise, AUDM, AUDD, Macropod, TAF Capital, and the RBA's Brad Jones and Ellis Connolly. Australian spelling is used throughout (tokenise, incentivise).
- The subtitles are clean verbatim: every word the speaker says, minus stammered repeats and fillers such as "um". Short host back-channel words are not subtitled.
- Burned in phrase by phrase with the spoken word on a brand-red box, and also shipped as SRT for platforms that take a separate caption file.

## Framing and audio

- The episodes are 16:9. Every camera shot in a clip is found automatically and the speaker is located in it by face recognition (YuNet detection, SFace recognition against reference frames of that speaker), so the window sits on the person speaking and never on the host. The window is fixed for each shot, so it never drifts or wobbles.
- Where the episode itself is on the host for a moment while the guest speaks (1.8 s at the start of clip 3, 0.7 s at the start of clip 5, 2.3 s in clip 6), the speaker's nearest frame is held and the audio carries on. These are listed in `CLIPS.md`.
- Only the episode's own audio is used. Each clip is normalised with two-pass EBU R128 loudness to -14 LUFS integrated, with a peak limiter that keeps the true peak below -2 dBTP after encoding, so all six play at the same level. No music or third party material is added.

## Brand

Clips and page follow the [Redbelly DAO Task Board brand kit](https://taskboard.redbellydao.network/brand) ("Kinetic Consensus"):

- **Colour:** slate surfaces and one accent, brand red `#EF5350`. Accent text on dark is `#ffb3ae`. The page ships the kit's dark theme with its light theme behind a toggle, using the kit's own `tokens.css`.
- **Type:** Be Vietnam Pro for every heading, caption and line of copy. JetBrains Mono only for machine values: episode numbers, timestamps, sizes, measurements.
- **Logo:** the kit's `dao-logo-on-dark.png` on slate, with no plate, never over footage.
- **Voice:** plain and direct, no en or em dashes and no emoji anywhere, checked automatically.
- **Layout of each clip:** progress bar, source label and topic, DAO logo and the hook at the top; the speaker in a 1080x1080 window with name and role on a slate lower third; captions in their own band below. The bottom of the frame is left clear for the buttons and text that X, Shorts, Reels and TikTok draw over a video.

## Verification

`python3 tools/verify.py` measures every rendered file and exits with an error if anything fails. Results are in [`VERIFICATION.md`](VERIFICATION.md) and on the review page. For each clip it checks:

- 9:16, 1080x1920, 30 fps, MP4 with H.264 and AAC, length 30 to 60 seconds, audio and video the same length
- loudness of -14 LUFS within 1 LU, true peak at or below -1 dBTP, and a loudness spread across the pack within 1 LU
- **the source timestamp:** the clip's audio is cross-correlated with the official episode at the time stated in `CLIPS.md`, and must match at zero offset
- **subtitles against the audio:** each finished clip is transcribed again by a fourth model, `distil-large-v3`, which was not used to make the subtitles, and compared with the subtitle text
- subtitles say exactly the proof-read text, every spoken word falls inside a cue, cues are ordered with no overlap and at most two lines
- **the speaker in frame:** face recognition on five frames per second of the finished clip
- no misspelt names or Redbelly terms, no personal credits, handles or signatures in subtitles, metadata, docs or page, and no dashes or emoji

`python3 -m pytest -q` runs the checks on the committed pack (files, SRTs, word timings, crop plans, docs, failure criteria) and unit tests for the alignment, caption layout and verification code.

## Deploy

The repository root is a static site with no build step.

- **Vercel:** Add New Project, import this repository, Framework Preset **Other**, leave Build Command and Output Directory empty, Root Directory `./`. Every push to `main` redeploys the site.
- **Netlify or Cloudflare Pages:** no build command, publish directory `/`.
- **GitHub Pages:** Settings, Pages, deploy from branch `main`, folder `/ (root)`.

`vercel.json` sets clean URLs and caching for the clips. For an absolute link preview image, rebuild the page with the live address: `SITE_URL=https://your-domain python3 tools/site.py`.

## Rebuilding the pack

Requirements: Python 3.10+, `ffmpeg`, and `pip install faster-whisper opencv-python-headless pillow numpy pytest`. Face models: [YuNet](https://github.com/opencv/opencv_zoo/tree/main/models/face_detection_yunet) and [SFace](https://github.com/opencv/opencv_zoo/tree/main/models/face_recognition_sface) from the OpenCV model zoo, saved as `work/models/yunet.onnx` and `work/models/sface.onnx`.

```bash
# 1. official episode files from redbelly.network/ama (URLs are in clips.json) and 16 kHz audio
mkdir -p work/src work/aud
python3 -c 'import json;[print(k,v["url"]) for k,v in json.load(open("clips.json"))["episodes"].items()]' |
  while read ep url; do curl -sSL "$url" -o work/src/$ep.mp4; ffmpeg -v error -i work/src/$ep.mp4 -vn -ac 1 -ar 16000 work/aud/$ep.wav; done

# 2. transcribe each clip window with the three models, e.g.
python3 tools/transcribe.py large-v3 work/aud/ep28.wav work/tx/02_regulated_proof_of_stake.large-v3.json 1996 2062
python3 tools/compare.py          # three readings against the proof-read text in clips.json

# 3. timings, crop plans, render, verify, docs, page
python3 tools/align.py large-v3   # data/words/
python3 tools/track.py            # data/tracks/
python3 tools/render.py           # clips/ and subtitles/
python3 tools/verify.py           # verification/report.json
python3 tools/docs.py             # CLIPS.md and VERIFICATION.md
python3 tools/site.py             # index.html, posters, og.png
python3 -m pytest -q
```

| Script | Job |
|---|---|
| `tools/transcribe.py` | Word-timestamped Whisper transcription of an episode or a window of it |
| `tools/compare.py` | Lines up the three readings of each clip against the proof-read text |
| `tools/snap.py` | Finds the quietest point between two words for a clean cut |
| `tools/align.py` | Puts the proof-read words on Whisper's timings |
| `tools/track.py` | Shot detection and face recognition, one crop window per shot |
| `tools/render.py` | Branded 1080x1920 frame, captions, loudness, H.264 encode, SRT |
| `tools/verify.py` | Measures every output and fails on any violation |
| `tools/docs.py`, `tools/site.py` | `CLIPS.md`, `VERIFICATION.md`, the review page, posters and link preview |

All footage and audio are from official Redbelly Insights episodes published at [redbelly.network/ama](https://redbelly.network/ama).
