"""Tests for the delivered pack, and unit tests for the pipeline code.

run: python3 -m pytest -q

The pack tests only read committed files. Measurements that need the episode files
(loudness, face recognition, source timestamps, independent transcript) come from
pipeline/audit.py; test_audit_passed reads its committed results.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))

import audit  # noqa: E402
import compose  # noqa: E402
import timing  # noqa: E402

PACK = json.loads((ROOT / "pack.json").read_text())
CUTS = PACK["cuts"]
THEMES = {"Redbelly technology", "Project Acacia", "Tokeniser"}
DOCS = ["README.md", "SOURCES.md", "QA.md", "index.html", "pack.json"]
by_slug = pytest.mark.parametrize("cut", CUTS, ids=lambda cut: cut["slug"])


# ------------------------------------------------------------- what the brief asks for

def test_there_are_six_cuts():
    assert len(CUTS) == 6


@by_slug
def test_every_cut_is_fully_described(cut):
    needed = ("slug", "source", "in", "out", "theme", "headline", "person", "person_title", "title_source",
              "takeaway", "post_copy", "transcript")
    assert not [k for k in needed if cut.get(k) in (None, "")]
    assert cut["person"] in PACK["sources"][cut["source"]]["people"]


@by_slug
def test_runs_between_30_and_60_seconds(cut):
    assert 30 <= cut["out"] - cut["in"] <= 60


def test_themes_stay_on_brief_and_cover_all_three():
    assert {cut["theme"] for cut in CUTS} == THEMES


def test_six_different_points_and_headlines():
    assert len({cut["takeaway"].lower() for cut in CUTS}) == 6
    assert len({cut["headline"].lower() for cut in CUTS}) == 6


def test_no_two_cuts_share_any_source_audio():
    for k, first in enumerate(CUTS):
        for second in CUTS[k + 1:]:
            if first["source"] == second["source"]:
                assert first["out"] <= second["in"] or second["out"] <= first["in"]


def test_every_source_is_an_official_redbelly_file():
    for meta in PACK["sources"].values():
        assert meta["page"] == "https://redbelly.network/ama"
        assert re.match(r"https://(storage|firebasestorage)\.googleapis\.com/(v0/b/)?redbelly-website", meta["video"])


def test_sources_are_among_the_newest_episodes():
    newest = PACK["latest_on_ama"]
    assert all(newest - 4 <= PACK["sources"][cut["source"]]["episode_no"] <= newest for cut in CUTS)


@by_slug
def test_post_copy_is_one_line_within_x_limit(cut):
    assert "\n" not in cut["post_copy"] and len(cut["post_copy"]) <= 280


@by_slug
def test_headline_is_short_enough_to_open_on(cut):
    assert len(cut["headline"]) <= 60


# ------------------------------------------------------------- committed files

@by_slug
def test_all_files_for_the_cut_are_committed(cut):
    s = cut["slug"]
    for rel in (f"clips/{s}.mp4", f"subtitles/{s}.srt", f"data/timing/{s}.json", f"data/framing/{s}.json",
                f"assets/stills/{s}.png"):
        assert (ROOT / rel).is_file(), rel


@by_slug
def test_srt_is_valid_and_carries_the_proofread_transcript(cut):
    cues = audit.parse_srt(ROOT / "subtitles" / f"{cut['slug']}.srt")
    assert [q["n"] for q in cues] == list(range(1, len(cues) + 1))
    assert all(q["s"] < q["e"] for q in cues)
    assert all(earlier["e"] <= later["s"] + 1e-3 for earlier, later in zip(cues, cues[1:]))
    assert max(len(q["lines"]) for q in cues) <= 2
    assert cues[-1]["e"] <= cut["out"] - cut["in"] + 0.05
    assert audit.words_of(" ".join(q["text"] for q in cues)) == audit.words_of(cut["transcript"])


@by_slug
def test_word_times_run_forward_inside_the_cut(cut):
    words = json.loads((ROOT / "data" / "timing" / f"{cut['slug']}.json").read_text())["words"]
    assert [w["w"] for w in words] == cut["transcript"].split()
    assert all(cut["in"] <= w["s"] < w["e"] <= cut["out"] for w in words)
    assert all(earlier["s"] <= later["s"] for earlier, later in zip(words, words[1:]))


@by_slug
def test_speaker_framed_in_every_shot_and_holds_are_short(cut):
    shots = json.loads((ROOT / "data" / "framing" / f"{cut['slug']}.json").read_text())["shots"]
    assert all(s["face_inside"] for s in shots if s["kind"] == "speaker")
    held = sum(min(s["end"], cut["out"]) - max(s["start"], cut["in"]) for s in shots if s["kind"] != "speaker")
    assert held <= 3.0


def test_sources_md_gives_time_and_caption_for_each_cut():
    text = (ROOT / "SOURCES.md").read_text()
    for cut in CUTS:
        minutes, seconds = divmod(cut["in"], 60)
        assert f"{int(minutes):02d}:{seconds:04.1f}" in text
        assert cut["post_copy"] in text and f"clips/{cut['slug']}.mp4" in text


def test_readme_shows_every_post_and_the_audit_result():
    text = (ROOT / "README.md").read_text()
    for cut in CUTS:
        assert f"assets/stills/{cut['slug']}.png" in text and f"{PACK['live_page']}#{cut['slug']}" in text
    verdict = json.loads((ROOT / "qa" / "results.json").read_text())["result"]
    assert f"badge/audit-{verdict}-" in text


def test_page_offers_every_clip_and_srt():
    text = (ROOT / "index.html").read_text()
    assert all(f"clips/{c['slug']}.mp4" in text and f"subtitles/{c['slug']}.srt" in text for c in CUTS)


# ------------------------------------------------------------- failure criteria and brand voice

@pytest.mark.parametrize("rel", DOCS + [f"subtitles/{c['slug']}.srt" for c in CUTS])
def test_text_is_free_of_misspellings_credits_dashes_and_emoji(rel):
    assert audit.scan_text(rel, (ROOT / rel).read_text(encoding="utf-8")) == []


@by_slug
def test_mp4_tags_carry_no_credit(cut):
    tags = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format_tags:stream_tags", "-of", "json",
                           str(ROOT / "clips" / f"{cut['slug']}.mp4")], capture_output=True, text=True).stdout
    assert audit.scan_text(cut["slug"], tags) == []


def test_redbelly_terms_use_the_spelling_in_the_brief():
    everything = " ".join(c["transcript"] + " " + c["post_copy"] + " " + c["headline"] for c in CUTS)
    assert "Redbelly" in everything and "Tokeniser" in everything
    assert not re.search(r"Tokenizer|Red Belly|RedBelly|rbnt", everything)


def test_audit_passed():
    results = json.loads((ROOT / "qa" / "results.json").read_text())
    assert results["result"] == "PASS", results["failures"]
    assert results["mode"] == "full"
    assert [r["slug"] for r in results["per_clip"]] == [c["slug"] for c in CUTS]


# ------------------------------------------------------------- pipeline code

def heard(*pairs):
    return [{"w": w, "s": t, "e": t + 0.3, "p": 0.9} for w, t in pairs]


def test_timing_keeps_proofread_words_and_whisper_times():
    words, diffs = timing.align("Redbelly is fast.", heard(("Red", 10.0), ("Belly", 10.3), ("is", 10.6),
                                                           ("fast.", 10.9)), 9.5, 12.0)
    assert [w["w"] for w in words] == ["Redbelly", "is", "fast."]
    assert (words[0]["s"], words[1]["s"]) == (10.0, 10.6)
    assert words[0]["e"] == pytest.approx(10.6) and diffs[0]["op"] == "replace"


def test_timing_fits_a_missed_word_between_its_neighbours():
    words, _ = timing.align("one two three", heard(("one", 1.0), ("three", 2.0)), 0.5, 3.0)
    assert words[0]["e"] <= words[1]["s"] < words[1]["e"] <= words[2]["s"]


def test_timing_leaves_out_fillers():
    words, _ = timing.align("so yes", heard(("so", 1.0), ("um", 1.3), ("yes", 1.6)), 0.5, 3.0)
    assert [w["w"] for w in words] == ["so", "yes"] and words[1]["s"] == 1.6


def test_caption_pages_never_need_a_third_line():
    sentence = ("Tokenisation unlocks distribution, liquidity and efficiency for regulated funds on Redbelly "
                "Network with identity verified at the protocol level.").split()
    words = [{"w": w, "s": k * 0.3, "e": k * 0.3 + 0.25} for k, w in enumerate(sentence)]
    pages = compose.pages(words)
    assert sum(map(len, pages)) == len(words)
    ruler = compose.ImageDraw.Draw(compose.Image.new("RGB", (1, 1)))
    for page in pages:
        text = " ".join(w["w"] for w in page)
        assert len(compose.balanced(ruler, text, compose.font(*compose.CAP_FONT), compose.CAP_MAX_W)) <= 2


def test_srt_clock_format():
    assert compose.srt_time(3723.0456) == "01:02:03,046"
    assert compose.srt_time(-2.5) == "00:00:00,000"


def test_plain_word_error_rate():
    assert audit.wer("a b c d", "a b c d") == 0
    assert audit.wer("a b c d", "a x c") == 0.5


def test_clean_word_error_rate_forgives_spelling_fillers_and_stammers():
    rate, diffs = audit.clean_wer("Tokenised bonds go through guardrails at AP+ events.",
                                  "Um, tokenized bonds go, go through guard rails at AP Plus events.")
    assert rate == 0 and diffs == []
    rate, diffs = audit.clean_wer("Project Acacia is next.", "Project Arcacia is next.")
    assert rate == 0.25 and diffs == ["acacia / arcacia"]


def test_scanner_flags_problems_and_ignores_css():
    assert audit.scan_text("x", "Built on Red Belly by @someone \u2014 made by me")
    assert audit.scan_text("x", "Redbelly, RBNT and Tokeniser. @media (max-width: 9px) {}") == []
