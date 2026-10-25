# Podcast Clip Pack

Six captioned vertical clips (30 to 60 s) cut from recent Redbelly Insights episodes, about Redbelly technology, Project Acacia or Tokeniser, ready to post on X, YouTube Shorts and Instagram.

## Layout

| Path | Contents |
| --- | --- |
| `index.html` | Static page (deployed on Vercel) to preview and download every clip |
| `clips/` | Final MP4 clips, 9:16, 1080×1920, subtitles burned in |
| `subtitles/` | Matching `.srt` subtitle files |
| `CLIPS.md` | Source episode, timestamp and suggested post caption for each clip |

## Deploy

Static site, no build step. Import the repository in Vercel (framework preset: **Other**, output directory: root). Every push to the connected branch redeploys automatically.

_Status: in production._
