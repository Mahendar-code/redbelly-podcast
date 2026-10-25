"""Checks on the delivered pack and unit tests for the tools.

run: python3 -m pytest -q
The pack checks read the committed files only; the measured checks (loudness, face
recognition, source timestamps, independent transcript) live in tools/verify.py and its
committed report, which test_verification_report_passes reads.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import align  # noqa: E402
import render  # noqa: E402
import verify  # noqa: E402

CFG = json.loads((ROOT / "clips.json").read_text())
CLIPS = CFG["clips"]
TEXT_FILES = ["README.md", "CLIPS.md", "VERIFICATION.md", "index.html", "clips.json"]


# ------------------------------------------------------------------ the brief

def test_exactly_six_clips():
    assert len(CLIPS) == 6


@pytest.mark.parametrize("c", CLIPS, ids=lambda c: c["id"])
def test_clip_has_every_field(c):
    for key in ["id", "episode", "start", "end", "topic", "hook", "speaker", "role", "role_source", "point",
                "caption", "text"]:
        assert c.get(key) not in (None, ""), key
    assert c["episode"] in CFG["episodes"]
    assert c["speaker"] in CFG["episodes"][c["episode"]]["speakers"]


@pytest.mark.parametrize("c", CLIPS, ids=lambda c: c["id"])
def test_length_30_to_60_seconds(c):
    assert 30 <= c["end"] - c["start"] <= 60


def test_topics_are_in_scope_and_all_covered():
    topics = {c["topic"] for c in CLIPS}
    assert topics <= {"Redbelly technology", "Project Acacia", "Tokeniser"}
    assert topics == {"Redbelly technology", "Project Acacia", "Tokeniser"}


def test_no_two_clips_make_the_same_point():
    points = [c["point"].lower() for c in CLIPS]
    hooks = [c["hook"].lower() for c in CLIPS]
    assert len(set(points)) == 6 and len(set(hooks)) == 6


def test_source_ranges_do_not_overlap():
    for i, a in enumerate(CLIPS):
        for b in CLIPS[i + 1:]:
            if a["episode"] == b["episode"]:
                assert a["end"] <= b["start"] or b["end"] <= a["start"], (a["id"], b["id"])


def test_sources_are_official_redbelly_hosting():
    for ep in CFG["episodes"].values():
        assert ep["page"] == "https://redbelly.network/ama"
        assert re.match(r"https://(storage|firebasestorage)\.googleapis\.com/(v0/b/)?redbelly-website", ep["url"])


def test_clips_come_from_the_latest_episodes():
    used = {CFG["episodes"][c["episode"]]["number"] for c in CLIPS}
    latest = CFG["latest_published_episode"]
    assert min(used) >= latest - 4, "clips should come from the five most recent published episodes"


@pytest.mark.parametrize("c", CLIPS, ids=lambda c: c["id"])
def test_caption_is_one_line_and_fits_x(c):
    assert "\n" not in c["caption"] and len(c["caption"]) <= 280


@pytest.mark.parametrize("c", CLIPS, ids=lambda c: c["id"])
def test_hook_is_short(c):
    assert len(c["hook"]) <= 60


# ------------------------------------------------------------------ files

@pytest.mark.parametrize("c", CLIPS, ids=lambda c: c["id"])
def test_deliverable_files_exist(c):
    for path in [f"clips/{c['id']}.mp4", f"subtitles/{c['id']}.srt", f"data/words/{c['id']}.json",
                 f"data/tracks/{c['id']}.json", f"assets/posters/{c['id']}.png"]:
        assert (ROOT / path).is_file(), path


@pytest.mark.parametrize("c", CLIPS, ids=lambda c: c["id"])
def test_srt_is_well_formed_and_says_the_proofread_text(c):
    cues = verify.parse_srt(ROOT / "subtitles" / f"{c['id']}.srt")
    assert [q["n"] for q in cues] == list(range(1, len(cues) + 1))
    assert all(q["s"] < q["e"] for q in cues)
    assert all(a["e"] <= b["s"] + 1e-3 for a, b in zip(cues, cues[1:]))
    assert all(len(q["lines"]) <= 2 for q in cues)
    assert cues[-1]["e"] <= c["end"] - c["start"] + 0.05
    assert verify.words_of(" ".join(q["text"] for q in cues)) == verify.words_of(c["text"])


@pytest.mark.parametrize("c", CLIPS, ids=lambda c: c["id"])
def test_word_timings_are_ordered_and_inside_the_clip(c):
    words = json.loads((ROOT / "data" / "words" / f"{c['id']}.json").read_text())["words"]
    assert [w["w"] for w in words] == c["text"].split()
    assert all(c["start"] <= w["s"] < w["e"] <= c["end"] for w in words)
    assert all(a["s"] <= b["s"] for a, b in zip(words, words[1:]))


@pytest.mark.parametrize("c", CLIPS, ids=lambda c: c["id"])
def test_speaker_is_on_camera_in_every_shot(c):
    shots = json.loads((ROOT / "data" / "tracks" / f"{c['id']}.json").read_text())["shots"]
    speaker = [s for s in shots if s["kind"] == "speaker"]
    assert all(s["face_inside"] for s in speaker)
    held = sum(min(s["end"], c["end"]) - max(s["start"], c["start"]) for s in shots if s["kind"] != "speaker")
    assert held <= 3.0, "at most 3 s of held frame while the episode cuts away"


def test_clips_md_lists_every_clip_with_timestamp_and_caption():
    md = (ROOT / "CLIPS.md").read_text()
    for c in CLIPS:
        m, s = divmod(c["start"], 60)
        assert f"{int(m):02d}:{s:04.1f}" in md
        assert c["caption"] in md and f"clips/{c['id']}.mp4" in md


def test_page_links_every_clip_and_subtitle():
    page = (ROOT / "index.html").read_text()
    for c in CLIPS:
        assert f"clips/{c['id']}.mp4" in page and f"subtitles/{c['id']}.srt" in page


# ------------------------------------------------------------------ failure criteria and brand

@pytest.mark.parametrize("path", TEXT_FILES + [f"subtitles/{c['id']}.srt" for c in CLIPS])
def test_no_misspellings_credits_dashes_or_emoji(path):
    assert verify.scan_text(path, (ROOT / path).read_text(encoding="utf-8")) == []


@pytest.mark.parametrize("c", CLIPS, ids=lambda c: c["id"])
def test_video_metadata_carries_no_credit(c):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format_tags:stream_tags", "-of", "json",
                          str(ROOT / "clips" / f"{c['id']}.mp4")], capture_output=True, text=True).stdout
    assert verify.scan_text(c["id"], out) == []


def test_brand_terms_spelled_as_the_brief_requires():
    blob = " ".join(c["text"] + " " + c["caption"] + " " + c["hook"] for c in CLIPS)
    assert "Redbelly" in blob
    assert "Tokeniser" in blob
    assert not re.search(r"Tokenizer|Red Belly|RedBelly|rbnt", blob)


def test_verification_report_passes():
    report = json.loads((ROOT / "verification" / "report.json").read_text())
    assert report["result"] == "PASS", report["failures"]
    assert report["mode"] == "full"
    assert [r["id"] for r in report["clips"]] == [c["id"] for c in CLIPS]


# ------------------------------------------------------------------ tools

def _heard(pairs):
    return [{"w": w, "s": s, "e": s + 0.3, "p": 0.9} for w, s in pairs]


def test_align_takes_text_from_proofread_and_time_from_whisper():
    heard = _heard([("Red", 10.0), ("Belly", 10.3), ("is", 10.6), ("fast.", 10.9)])
    words, diffs = align.align("Redbelly is fast.", heard, 9.5, 12.0)
    assert [w["w"] for w in words] == ["Redbelly", "is", "fast."]
    assert words[0]["s"] == 10.0 and words[0]["e"] == pytest.approx(10.6)
    assert words[1]["s"] == 10.6 and diffs[0]["op"] == "replace"


def test_align_places_words_whisper_missed_between_neighbours():
    heard = _heard([("one", 1.0), ("three", 2.0)])
    words, _ = align.align("one two three", heard, 0.5, 3.0)
    assert words[0]["e"] <= words[1]["s"] < words[1]["e"] <= words[2]["s"]


def test_align_drops_fillers_whisper_heard():
    heard = _heard([("so", 1.0), ("um", 1.3), ("yes", 1.6)])
    words, _ = align.align("so yes", heard, 0.5, 3.0)
    assert [w["w"] for w in words] == ["so", "yes"] and words[1]["s"] == 1.6


def test_caption_pages_fit_two_lines():
    words = [{"w": w, "s": i * 0.3, "e": i * 0.3 + 0.25} for i, w in
             enumerate(("Tokenisation unlocks distribution, liquidity and efficiency for regulated funds "
                        "on Redbelly Network with identity verified at the protocol level.").split())]
    pages = render.pages(words)
    assert sum(len(p) for p in pages) == len(words)
    probe = render.ImageDraw.Draw(render.Image.new("RGB", (1, 1)))
    for p in pages:
        assert len(render.wrap(probe, " ".join(w["w"] for w in p), render.font(*render.CAP_FONT),
                               render.CAP_MAX_W)) <= 2


def test_srt_time_format():
    assert render.srt_time(3723.0456) == "01:02:03,046"
    assert render.srt_time(-1) == "00:00:00,000"


def test_word_error_rate():
    assert verify.wer("a b c d", "a b c d") == 0
    assert verify.wer("a b c d", "a x c") == 0.5


def test_clean_word_error_rate_ignores_spelling_fillers_and_repeats():
    e, diffs = verify.clean_wer("Tokenised bonds go through guardrails at AP+ events.",
                                "Um, tokenized bonds go, go through guard rails at AP Plus events.")
    assert e == 0 and diffs == []
    e, diffs = verify.clean_wer("Project Acacia is next.", "Project Arcacia is next.")
    assert e == 0.25 and diffs == ["acacia / arcacia"]


def test_scan_text_catches_failures():
    assert verify.scan_text("x", "Built on Red Belly by @someone \u2014 made by me")
    assert verify.scan_text("x", "Redbelly, RBNT and Tokeniser. @media (max-width: 9px) {}") == []
