"""website-to-lander: extraction, the sections check, the built page's five elements, popup rules and no reference strings.

    python3 -m pytest skills/website-to-lander/scripts/test_website_to_lander.py -q

Offline: the site is a synthetic saved page (evals/fixtures/fernhill-site.html); nothing is fetched.
"""

from __future__ import annotations

import importlib.util
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
SKILL = HERE.parent
FIXTURE = SKILL / "evals" / "fixtures" / "fernhill-site.html"
EXAMPLE = SKILL / "templates" / "sections.example.json"
PROMPT_FIXTURE = SKILL / "evals" / "fixtures" / "fernhill-prompt.md"
WORKFLOW_FIXTURE = SKILL / "evals" / "fixtures" / "fernhill-workflow-prompt.md"
GENERAL = SKILL / "templates" / "sections.general.example.json"
GENERAL_PROMPT_FIXTURE = SKILL / "evals" / "fixtures" / "general-prompt.md"
GENERAL_LINKING_FIXTURE = SKILL / "evals" / "fixtures" / "general-linking.md"

_spec = importlib.util.spec_from_file_location("wtl", HERE / "website_to_lander.py")
wtl = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(wtl)


@pytest.fixture
def run_dir(tmp_path):
    assert wtl.main(["extract", "https://fernhill.example", "--html", str(FIXTURE), "--out", str(tmp_path),
                     "--deliverable", "5 ad creatives"]) == 0
    return tmp_path


@pytest.fixture
def built(run_dir):
    shutil.copy(EXAMPLE, run_dir / "sections.json")
    assert wtl.main(["build", str(run_dir)]) == 0
    return (run_dir / "index.html").read_text(encoding="utf-8")


def test_extract_reads_brand_name_color_font_logo_products_and_proof(run_dir):
    facts = json.loads((run_dir / "brand.json").read_text(encoding="utf-8"))
    assert facts["name"] == "Fernhill Socks" and facts["name_source"] == "og:site_name"
    assert facts["colors"][0]["hex"] == "#2f6b4f" and facts["colors"][0]["source"] == "meta theme-color"
    assert facts["font"]["family"] == "Work Sans" and facts["font"]["google_css_url"].startswith("https://fonts.googleapis.com/")
    assert facts["logo"]["url"] == "https://fernhill.example/logo.svg"
    names = [p["text"] for p in facts["product_candidates"]]
    assert "Trail Merino Crew" in names and "Everyday Ankle Sock" in names
    proof = [p["text"] for p in facts["proof_candidates"]]
    assert any("12,400 customers" in t for t in proof)
    assert any("Three winters" in t for t in proof)
    assert all(p["source"] == "https://fernhill.example" for p in facts["proof_candidates"])


def test_starter_sections_are_prefilled_and_block_until_filled(run_dir):
    s = json.loads((run_dir / "sections.json").read_text(encoding="utf-8"))
    assert s["brand"]["name"] == "Fernhill Socks" and s["brand"]["primary_color"] == "#2f6b4f"
    assert s["deliverable"] == "5 ad creatives"
    assert s["proof"][0]["source"] == "https://fernhill.example"
    errors, _ = wtl.check(s)
    for key in ("headline", "subhead", "best_product", "cta_line", "booking_url", "popup_title", "popup_body", "from_name"):
        assert any(e.startswith(key) for e in errors), key
    assert wtl.main(["build", str(run_dir)]) == 1
    assert not (run_dir / "index.html").exists()


def test_extract_keeps_a_filled_sections_file(run_dir):
    shutil.copy(EXAMPLE, run_dir / "sections.json")
    wtl.main(["extract", "https://fernhill.example", "--html", str(FIXTURE), "--out", str(run_dir)])
    assert json.loads((run_dir / "sections.json").read_text(encoding="utf-8"))["headline"].startswith("Your 5 ad creatives")


def test_the_example_passes_check():
    errors, notes = wtl.check(json.loads(EXAMPLE.read_text(encoding="utf-8")))
    assert errors == []
    assert any("vsl_url" in n for n in notes)


@pytest.mark.parametrize("value", ["Lorem ipsum for the banner", "LOREM IPSUM", "Quis dolor sit amet"])
def test_check_refuses_reference_strings(value):
    s = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    s["banner_text"] = value
    errors, _ = wtl.check(s)
    assert any(e.startswith("banner_text contains") for e in errors), value


def test_check_needs_a_source_for_every_proof_point():
    s = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    s["proof"][1]["source"] = ""
    errors, _ = wtl.check(s)
    assert "proof[1].source is empty: every proof point names where it came from" in errors


def test_check_needs_https_links():
    s = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    s["booking_url"] = "agency.example/book"
    errors, _ = wtl.check(s)
    assert "booking_url must be a full https:// link" in errors


def test_built_page_has_all_five_elements_in_order(built):
    assert wtl.verify(built) == []
    banner = built.index('id="wl-announce"')
    vsl = built.index('data-slot="vsl"')
    line = built.index('class="wl-cta-line"')
    cta = built.index('data-cta="booking-under-video"')
    proof = built.index('id="proof"')
    popup = built.index('id="wl-exit"')
    assert banner < vsl < line < cta < proof < popup
    assert 'href="https://agency.example/case-studies" data-cta="case-studies"' in built
    assert "Grab a time and I&#x27;ll walk you through your 5 creatives" in built
    assert built.count('href="https://agency.example/book/walkthrough"') == 4  # nav, under video, closing band, popup
    assert "Rated 4.8 out of 5 by 12,400 customers." in built


def test_built_page_has_no_reference_strings_and_is_self_contained(built):
    assert not wtl.FORBIDDEN_RE.search(built)
    assert not re.search(r"<script[^>]+src=", built)
    assert "TODO" not in built and "{{" not in built
    assert '<meta name="robots" content="noindex, nofollow">' in built
    assert "prepared for Fernhill Socks by Example Creative Co." in built
    assert '"dismissKey": "wl_exit_dismissed_fernhill-socks"' in built


@pytest.mark.parametrize("cut,fail", [
    (r'<div class="wl-announce".*?</div>\s*</div>', "1 banner"),
    (r'<div class="wl-vsl" data-slot="vsl">', "2 hero"),
    (r'<a [^>]*data-cta="booking-under-video"[^>]*>', "3 booking CTA"),
    (r'<section class="wl-section" id="proof">.*?</section>', "4 proof"),
    (r'<div class="wl-exit" id="wl-exit".*?</div>\s*</div>', "5 exit popup"),
    (r"var TTL = 7 \* 864e5;", "popup rule: TTL"),
    (r"var DESKTOP_DWELL = 8000;", "popup rule: DESKTOP_DWELL"),
])
def test_verify_catches_each_missing_piece(built, cut, fail):
    broken = re.sub(cut, "", built, count=1, flags=re.S)
    assert broken != built
    assert any(f.startswith(fail) for f in wtl.verify(broken)), wtl.verify(broken)


def test_verify_catches_reference_strings_and_external_scripts(built):
    assert any("reference strings" in f for f in wtl.verify(built.replace("</footer>", "Lorem ipsum</footer>")))
    assert any("external script" in f for f in wtl.verify(built.replace("</head>", '<script src="https://x.example/a.js"></script></head>')))


def test_logo_file_is_inlined(run_dir):
    s = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    (run_dir / "logo.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"></svg>')
    s["brand"]["logo"] = "logo.svg"
    (run_dir / "sections.json").write_text(json.dumps(s))
    assert wtl.main(["build", str(run_dir)]) == 0
    assert 'src="data:image/svg+xml;base64,' in (run_dir / "index.html").read_text(encoding="utf-8")


@pytest.mark.parametrize("url,want", [
    ("https://www.youtube.com/watch?v=abcDEF12345", "https://www.youtube-nocookie.com/embed/abcDEF12345"),
    ("https://youtu.be/abcDEF12345", "https://www.youtube-nocookie.com/embed/abcDEF12345"),
    ("https://www.youtube.com/watch?feature=share&v=abcDEF12345", "https://www.youtube-nocookie.com/embed/abcDEF12345"),
    ("https://m.youtube.com/watch?v=abcDEF12345", "https://www.youtube-nocookie.com/embed/abcDEF12345"),
    ("https://youtube.com/shorts/abcDEF12345", "https://www.youtube-nocookie.com/embed/abcDEF12345"),
    ("https://vimeo.com/123456", "https://player.vimeo.com/video/123456\""),
    ("https://vimeo.com/123456/9f8e7d6c5b", "https://player.vimeo.com/video/123456?h=9f8e7d6c5b"),
    ("https://www.loom.com/share/0a1b2c3d", "https://www.loom.com/embed/0a1b2c3d"),
    ("https://cdn.example/vsl.mp4", "<video"),
    ("", "Video goes here"),
])
def test_vsl_slot(url, want):
    assert want in wtl.vsl_html(url, "How we do the work")


@pytest.mark.parametrize("url", ["https://drive.google.com/file/d/abc123/view", "https://agency.example/our-video",
                                 "https://www.youtube.com/watch?feature=share", "http://player.example/embed/abc",
                                 "http://cdn.example/vsl.mp4"])
def test_check_refuses_a_vsl_link_that_would_show_the_placeholder(url):
    s = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    s["vsl_url"] = url
    errors, _ = wtl.check(s)
    assert any(e.startswith("vsl_url is not") for e in errors), url
    assert "Video goes here" in wtl.vsl_html(url, "x")


@pytest.mark.parametrize("key", ["lede", "eyebrow", "final_title", "proof_title", "vsl_caption", "call_gets_title",
                                 "popup_eyebrow", "banner_link_text"])
def test_build_stops_with_an_error_when_page_copy_is_missing(run_dir, key, capsys):
    s = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    del s[key]
    (run_dir / "sections.json").write_text(json.dumps(s), encoding="utf-8")
    assert wtl.main(["build", str(run_dir)]) == 1
    assert f"error: {key} is empty" in capsys.readouterr().out
    assert not (run_dir / "index.html").exists()


def test_built_page_is_utf8_whatever_the_locale(run_dir):
    text = "Loved in Kyoto \u2192 \u4eac\u90fd \U0001F9E6"
    s = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    s["proof"][0]["text"] = text
    (run_dir / "sections.json").write_text(json.dumps(s, ensure_ascii=False), encoding="utf-8")
    env = {**os.environ, "PYTHONUTF8": "0", "PYTHONCOERCECLOCALE": "0", "LC_ALL": "C", "LANG": "C"}
    r = subprocess.run([sys.executable, str(HERE / "website_to_lander.py"), "build", str(run_dir)],
                       env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert r.returncode == 0, r.stdout + r.stderr
    page = (run_dir / "index.html").read_bytes()
    assert b'<meta charset="utf-8">' in page
    assert text.encode("utf-8") in page


@pytest.mark.parametrize("color", ["#2f6b4f", "#ffd400", "#111111", "#ff5a5f", "#e8f0ff"])
def test_palette_keeps_text_readable(color):
    p = wtl.palette(color)
    rgb = wtl.hex_to_rgb
    assert wtl.contrast(rgb(p["on_primary"]), rgb(p["primary"])) >= 3
    assert wtl.contrast(rgb(p["accent"]), rgb(p["canvas"])) >= 4.5
    assert wtl.contrast(rgb(p["accent_on_dark"]), rgb(p["dark"])) >= 4.5
    assert wtl.contrast(rgb(p["text"]), rgb(p["canvas"])) >= 7


def clone_list(tmp_path, prospects=None, **top):
    """Two synthetic replied prospects (Fernhill Socks, Saltmarrow Swim) and one that never replied."""
    example = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    for folder, name, slug in (("fern", "Fernhill Socks", "fernhill-socks"), ("salt", "Saltmarrow Swim", "saltmarrow-swim")):
        s = json.loads(json.dumps(example).replace("Fernhill Socks", name))
        s["slug"] = slug
        (tmp_path / folder).mkdir(exist_ok=True)
        (tmp_path / folder / "sections.json").write_text(json.dumps(s), encoding="utf-8")
    data = {"campaign": "5 free creatives DTC", "sender_name": "Ana", "domain": "pages.agency.example",
            "prospects": prospects if prospects is not None else [
                {"run_dir": "fern", "replied_at": "2026-11-23T14:05:00Z", "first_name": "Maya",
                 "times": ["Tuesday at 1pm ET", "Wednesday at 11am ET"]},
                {"run_dir": "salt", "replied_at": "2026-11-23T16:40:00+00:00"},
                {"run_dir": "quill"},
            ]}
    data.update(top)
    path = tmp_path / "list.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return str(path)


def test_clone_builds_one_page_and_handoff_per_replied_prospect_only(tmp_path, capsys):
    out = tmp_path / "out"
    assert wtl.main(["clone", clone_list(tmp_path), "--out", str(out)]) == 0
    assert "prospects[2] (quill): skipped, no replied_at" in capsys.readouterr().out
    assert sorted(p.name for p in out.iterdir()) == ["fernhill-socks", "saltmarrow-swim"]
    for slug in ("fernhill-socks", "saltmarrow-swim"):
        assert sorted(p.name for p in (out / slug).iterdir()) == ["handoff.md", "prompt.md", "site"]
        assert wtl.prompt_fails((out / slug / "prompt.md").read_text(encoding="utf-8")) == []
        assert wtl.main(["verify", str(out / slug / "site" / "index.html")]) == 0
    assert "Saltmarrow Swim" in (out / "saltmarrow-swim" / "site" / "index.html").read_text(encoding="utf-8")


def test_clone_handoff_hosts_first_then_replies_then_calls(tmp_path):
    out = tmp_path / "out"
    wtl.main(["clone", clone_list(tmp_path), "--out", str(out)])
    text = (out / "fernhill-socks" / "handoff.md").read_text(encoding="utf-8")
    order = ["## 1. Host the page first", "### Instantly website (first choice)", "### Fallback: Cloudflare Pages",
             "npx wrangler pages deploy", "## 2. Reply now", "## 3. Call the same day"]
    assert [text.index(h) for h in order] == sorted(text.index(h) for h in order)
    assert "named `fernhill-socks`" in text
    assert f"Paste the whole `{(out / 'fernhill-socks' / 'prompt.md').resolve()}` into Instantly Copilot" in text
    assert "Thanks Maya, we're prepping your 5 ad creatives now, here's where they'll be: <page link>" in text
    assert "?utm_source=instantly&utm_medium=email&utm_campaign=5-free-creatives-dtc" in text
    assert "Would Tuesday at 1pm ET or Wednesday at 11am ET work? Or grab a time here: https://agency.example/book/walkthrough" in text
    assert "`fernhill-socks.pages.agency.example`" in text


def test_clone_calls_the_same_day_at_15_minutes_1_hour_and_4_hours(tmp_path):
    out = tmp_path / "out"
    wtl.main(["clone", clone_list(tmp_path), "--out", str(out)])
    text = (out / "fernhill-socks" / "handoff.md").read_text(encoding="utf-8")
    rows = re.findall(r"^\| \d \| (.+?) after the reply \| (.+?) UTC \| double dial \|$", text, re.M)
    assert rows == [("15 minutes", "2026-11-23 14:20"), ("1 hour", "2026-11-23 15:05"), ("4 hours", "2026-11-23 18:05")]
    nameless = (out / "saltmarrow-swim" / "handoff.md").read_text(encoding="utf-8")
    assert "> Thanks, we're prepping your 5 ad creatives now" in nameless
    assert "> Hi, it's Ana from Example Creative Co. You just asked" in nameless
    assert "there," not in nameless
    assert "walk you through it: Your 5 creatives, one by one" in text


@pytest.mark.parametrize("prospects,top,want", [
    ([{"run_dir": "fern", "replied_at": "2026-11-23T14:05:00"}], {}, "needs a time zone"),
    ([{"run_dir": "fern", "replied_at": "2026-11-23T14:05:00Z", "times": "Tuesday 1pm"}], {}, "times (a list of text) must be text"),
    ([{"run_dir": "fern", "replied_at": "2026-11-23T14:05:00Z", "first_name": 7}], {}, "first_name must be text"),
    ([{"run_dir": "missing", "replied_at": "2026-11-23T14:05:00Z"}], {}, "cannot read"),
    (["fern"], {}, "prospects[0] must be an object"),
    ([], {}, "prospects must be a non-empty list"),
    ([{"run_dir": "fern", "replied_at": "2026-11-23T14:05:00Z"}], {"campaign": 5}, "campaign is required and must be text"),
    ([{"run_dir": "fern", "replied_at": "2026-11-23T14:05:00Z"}], {"domain": "https://x.example"}, "must be a bare domain"),
    ([{"run_dir": "fern", "replied_at": "2026-11-23T14:05:00Z"}, {"run_dir": "fern", "replied_at": "2026-11-23T15:00:00Z"}],
     {}, "is already used by"),
])
def test_clone_reports_bad_input_as_an_error_and_writes_nothing(tmp_path, capsys, prospects, top, want):
    out = tmp_path / "out"
    assert wtl.main(["clone", clone_list(tmp_path, prospects, **top), "--out", str(out)]) == 1
    printed = capsys.readouterr().out
    assert any(line.startswith("error: ") and want in line for line in printed.splitlines()), printed
    assert not out.exists()


def test_clone_refuses_an_unfilled_or_mistyped_run_folder(tmp_path, capsys):
    path = clone_list(tmp_path)
    s = json.loads((tmp_path / "salt" / "sections.json").read_text(encoding="utf-8"))
    s["headline"] = "TODO: the headline"
    (tmp_path / "salt" / "sections.json").write_text(json.dumps(s), encoding="utf-8")
    f = json.loads((tmp_path / "fern" / "sections.json").read_text(encoding="utf-8"))
    f["brand"] = "Fernhill"
    (tmp_path / "fern" / "sections.json").write_text(json.dumps(f), encoding="utf-8")
    out = tmp_path / "out"
    assert wtl.main(["clone", path, "--out", str(out)]) == 1
    printed = capsys.readouterr().out
    assert "error: prospects[1] (salt): headline is still a TODO" in printed
    assert "error: prospects[0] (fern): brand must be an object" in printed
    assert not out.exists()


@pytest.mark.parametrize("key,value,want", [
    ("from_name", 42, "from_name must be text"),
    ("subhead", ["x"], "subhead must be text"),
    ("call_gets", "your 5 creatives", "call_gets must be a list of text lines"),
    ("proof", [{"text": 5, "source": "https://fernhill.example"}], "proof[0].text must be text"),
    ("proof", ["Rated 4.8"], "proof[0] must be an object with text and source"),
    ("brand", {"name": 7, "primary_color": "#2f6b4f"}, "brand.name must be text"),
    ("call_length", 15, "call_length must be text"),
])
def test_clone_refuses_a_mistyped_field_in_any_folder_and_writes_nothing(tmp_path, capsys, key, value, want):
    path = clone_list(tmp_path)
    s = json.loads((tmp_path / "salt" / "sections.json").read_text(encoding="utf-8"))
    s[key] = value
    (tmp_path / "salt" / "sections.json").write_text(json.dumps(s), encoding="utf-8")
    out = tmp_path / "out"
    assert wtl.main(["clone", path, "--out", str(out)]) == 1
    printed = capsys.readouterr().out
    assert f"error: prospects[1] (salt): {want}" in printed, printed
    assert "Traceback" not in printed
    assert not out.exists()
    assert wtl.main(["build", str(tmp_path / "salt")]) == 1
    assert f"error: {want}" in capsys.readouterr().out


def test_call_length_is_set_once_for_the_popup_reply_and_opener(tmp_path):
    path = clone_list(tmp_path)
    s = json.loads((tmp_path / "fern" / "sections.json").read_text(encoding="utf-8"))
    s["call_length"] = "25 minutes"
    (tmp_path / "fern" / "sections.json").write_text(json.dumps(s), encoding="utf-8")
    out = tmp_path / "out"
    assert wtl.main(["clone", path, "--out", str(out)]) == 0
    page = (out / "fernhill-socks" / "site" / "index.html").read_text(encoding="utf-8")
    popup = page[page.index('id="wl-exit-body"'):]
    assert popup.split("</p>")[0].startswith('id="wl-exit-body">25 minutes on a call. We go through each creative')
    text = (out / "fernhill-socks" / "handoff.md").read_text(encoding="utf-8")
    reply = text[text.index("## 2. Reply now"):text.index("## 3. Call the same day")]
    opener = text[text.index("## 3. Call the same day"):]
    assert "a quick call, 25 minutes, where I walk you through" in reply
    assert "25 minutes on a call and I'd walk you through it" in opener
    assert "15 minutes on a call" in (out / "saltmarrow-swim" / "site" / "index.html").read_text(encoding="utf-8")
    assert not re.search(r"20 minute|Fifteen minutes", text + page)


def test_blank_call_length_falls_back_to_15_minutes(tmp_path):
    path = clone_list(tmp_path)
    s = json.loads((tmp_path / "fern" / "sections.json").read_text(encoding="utf-8"))
    s["call_length"] = "   "
    (tmp_path / "fern" / "sections.json").write_text(json.dumps(s), encoding="utf-8")
    out = tmp_path / "out"
    assert wtl.main(["clone", path, "--out", str(out)]) == 0
    page = (out / "fernhill-socks" / "site" / "index.html").read_text(encoding="utf-8")
    assert 'id="wl-exit-body">15 minutes on a call. We go through' in page
    assert "a quick call, 15 minutes, where" in (out / "fernhill-socks" / "handoff.md").read_text(encoding="utf-8")


# ---------- the Instantly Copilot prompt ----------

@pytest.fixture
def prompted(run_dir):
    shutil.copy(EXAMPLE, run_dir / "sections.json")
    assert wtl.main(["prompt", str(run_dir)]) == 0
    return (run_dir / "prompt.md").read_text(encoding="utf-8")


def test_prompt_for_the_synthetic_site_matches_the_eval_fixture(prompted, run_dir):
    assert prompted == PROMPT_FIXTURE.read_text(encoding="utf-8")
    assert (run_dir / "workflow-prompt.md").read_text(encoding="utf-8") == WORKFLOW_FIXTURE.read_text(encoding="utf-8")


def test_prompt_has_every_part_in_order_with_the_sections_copy(prompted):
    order = ["1. Announcement banner", "2. Header", "3. Hero", "Right: a 16:9 video placeholder", "4. Booking, directly under the video",
             "5. On-the-call card", "6. Deliverables", "7. Proof", "8. Closing band", "9. Footer", "Exit-intent popup"]
    assert [prompted.index(h) for h in order] == sorted(prompted.index(h) for h in order)
    s = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    for key in ("banner_text", "banner_link_text", "case_studies_url", "eyebrow", "headline", "subhead", "lede", "vsl_caption",
                "cta_line", "cta_button", "booking_url", "call_gets_title", "proof_title", "proof_intro", "final_title",
                "popup_eyebrow", "popup_title", "popup_cta"):
        assert s[key] in prompted, key
    for line in s["call_gets"]:
        assert f'"{line}"' in prompted
    for item in s["proof"]:
        assert f"{item['text'].strip(chr(34))}\" with its source under it: {item['source']}" in prompted
    assert '"5 ad creatives for the Trail Merino Crew"' in prompted
    assert '"15 minutes on a call. We go through each creative' in prompted
    assert "Colors: main #2f6b4f for buttons and accents" in prompted and "Font: Work Sans (Google Fonts)" in prompted


def test_prompt_keeps_the_nothing_invented_footer_and_noindex_rules(prompted):
    assert wtl.prompt_fails(prompted) == []
    assert "Use only the copy below, word for word. Do not invent results, reviews, numbers" in prompted
    assert "noindex, nofollow" in prompted
    assert ('"A walkthrough page prepared for Fernhill Socks by Example Creative Co. '
            'Fernhill Socks names and marks belong to their owner."') in prompted
    assert "after 8 seconds" in prompted and "more than 80 pixels after 25 seconds, or after 75 seconds" in prompted
    assert "At most once per 7 days" in prompted and "Escape" in prompted
    assert not wtl.FORBIDDEN_RE.search(prompted) and "TODO" not in prompted


def test_prompt_is_refused_for_an_unfilled_run_folder(run_dir, capsys):
    assert wtl.main(["prompt", str(run_dir)]) == 1
    printed = capsys.readouterr().out
    assert "error: headline is still a TODO" in printed and "no prompt written" in printed
    assert not (run_dir / "prompt.md").exists() and not (run_dir / "workflow-prompt.md").exists()


def test_prompt_check_catches_reference_strings_and_missing_rules():
    assert any("reference strings" in f for f in wtl.prompt_fails("Do not invent. noindex. prepared for lorem ipsum"))
    assert any("nothing-invented" in f for f in wtl.prompt_fails("noindex. prepared for x"))


def test_prompt_uses_the_video_logo_and_licensed_font_as_given(run_dir):
    s = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    s["vsl_url"] = "https://www.loom.com/share/0a1b2c3d"
    s["brand"]["logo"] = "logo.svg"
    s["brand"]["font_family"], s["brand"]["font_css_url"] = "Brand Grotesk", ""
    (run_dir / "sections.json").write_text(json.dumps(s), encoding="utf-8")
    out = run_dir / "copilot.md"
    assert wtl.main(["prompt", str(run_dir), "--out", str(out)]) == 0
    text = out.read_text(encoding="utf-8")
    assert "Right: embed the video https://www.loom.com/share/0a1b2c3d" in text
    assert f"Logo: upload the file {(run_dir / 'logo.svg').resolve()}" in text
    assert "Their site uses Brand Grotesk, which is licensed to them; do not load or copy it." in text
    s["brand"]["logo"] = "https://cdn.example/logo.png"
    assert "Logo: use the image at https://cdn.example/logo.png." in wtl.copilot_prompt(run_dir, s)


def test_workflow_prompt_builds_a_page_per_positive_reply_from_the_template(run_dir, prompted):
    flow = (run_dir / "workflow-prompt.md").read_text(encoding="utf-8")
    assert wtl.prompt_fails(flow) == []
    # the Instantly trigger and lead fields
    assert "Instantly, Lead Interest Status Changed, interest status Interested" in flow
    for field in ("firstName", "companyName", "website", "email"):
        assert "{{trigger__lead." + field + "}}" in flow
    # the template: this prospect's name and product swapped out, the rest word for word
    assert "Fernhill" not in flow and "Trail Merino Crew" not in flow
    assert 'headline "Your 5 ad creatives for {best product}"' in flow
    assert 'eyebrow "Prepared for {company}"' in flow
    assert "https://agency.example/book/walkthrough" in flow and "https://agency.example/case-studies" in flow
    assert '"A walkthrough page prepared for {company} by Example Creative Co.' in flow
    # nothing invented, nothing sent, nothing turned on, unconfirmed steps marked
    assert "Do not invent results" in flow and "only points the lead's own website shows" in flow
    assert "Save it as a Draft and leave it off" in flow and "never sends the reply" in flow
    assert flow.count("[check in your workspace]") == 3
    order = ["Trigger:", "1. Read the lead", "2. Build the page", "3. Return the page link", "Template"]
    assert [flow.index(h) for h in order] == sorted(flow.index(h) for h in order)


def test_template_copy_swaps_the_prospect_name_and_product_only():
    s = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    t = wtl.template_copy(s)
    assert "brand" not in t and "proof" not in t
    assert t["popup_eyebrow"] == "Before you go, {company}"
    assert t["headline"] == "Your 5 ad creatives for {best product}"
    assert t["call_gets"] == s["call_gets"] and t["booking_url"] == s["booking_url"]


def test_template_copy_swaps_a_product_that_contains_the_brand_name():
    s = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    s["brand"]["name"] = "Fernhill"
    s["best_product"] = "Fernhill Trail Crew"
    s["headline"] = "Your 5 ad creatives for Fernhill Trail Crew"
    s["popup_eyebrow"] = "Before you go, Fernhill"
    t = wtl.template_copy(s)
    assert t["headline"] == "Your 5 ad creatives for {best product}"
    assert t["popup_eyebrow"] == "Before you go, {company}"


def test_template_copy_swaps_a_brand_name_that_contains_the_product():
    s = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    s["brand"]["name"] = "Fernhill Socks"
    s["best_product"] = "Socks"
    s["headline"] = "Your 5 ad creatives for Socks"
    s["popup_eyebrow"] = "Before you go, Fernhill Socks"
    t = wtl.template_copy(s)
    assert t["headline"] == "Your 5 ad creatives for {best product}"
    assert t["popup_eyebrow"] == "Before you go, {company}"


# ---------- general mode: one page for every lead in a campaign ----------

@pytest.fixture
def general_dir(tmp_path):
    d = tmp_path / "general"
    d.mkdir()
    shutil.copy(GENERAL, d / "sections.json")
    return d


def test_the_general_example_passes_check():
    errors, notes = wtl.check(json.loads(GENERAL.read_text(encoding="utf-8")))
    assert errors == [] and not any("vsl_url" in n for n in notes)


def test_general_prompt_and_linking_note_match_the_eval_fixtures(general_dir):
    assert wtl.main(["prompt", str(general_dir)]) == 0
    prompt = (general_dir / "prompt.md").read_text(encoding="utf-8")
    assert prompt == GENERAL_PROMPT_FIXTURE.read_text(encoding="utf-8")
    assert (general_dir / "linking.md").read_text(encoding="utf-8") == GENERAL_LINKING_FIXTURE.read_text(encoding="utf-8")
    assert not (general_dir / "workflow-prompt.md").exists()  # one page for the campaign: no per-reply workflow


def test_general_prompt_is_in_the_senders_brand_with_only_merge_tags_per_lead(general_dir):
    wtl.main(["prompt", str(general_dir)])
    prompt = (general_dir / "prompt.md").read_text(encoding="utf-8")
    assert wtl.prompt_fails(prompt) == []
    assert "Northwind Creative's own walkthrough page, one page for every lead in a campaign" in prompt
    assert "one reusable page in our own brand: no lead's name, logo or brand on it, except the merge lines below" in prompt
    assert '"A walkthrough page by Northwind Creative."' in prompt and "prepared for" not in prompt
    assert ('a case-study card titled "Fernhill Socks: 2x return on ad spend in 60 days"' in prompt
            and "linking to https://agency.example/case-studies/fernhill-socks" in prompt)
    assert "4. Booking, directly under the case-study card" in prompt
    assert "with its source under it: our case study: Fernhill Socks" in prompt
    assert "?first_name= and ?company=" in prompt and "never as HTML" in prompt
    assert 'every tag in "Prepared for {company}", show that line with them filled in; otherwise show "A 5-minute read"' in prompt
    assert "Walked through live" not in prompt
    linking = (general_dir / "linking.md").read_text(encoding="utf-8")
    assert "&first_name={{firstName}}&company={{companyName}}" in linking
    assert "No per-reply workflow" in linking and "Nothing here sends anything" in linking
    assert "[check in your workspace]" in linking


def test_general_page_builds_with_the_case_study_card_merge_lines_and_own_footer(general_dir):
    assert wtl.main(["build", str(general_dir)]) == 0
    page = (general_dir / "index.html").read_text(encoding="utf-8")
    assert wtl.verify(page) == []
    assert 'data-cta="case-study-doc"' in page and 'href="https://agency.example/case-studies/fernhill-socks"' in page
    assert '<p class="wl-eyebrow" data-merge="Prepared for {company}">A 5-minute read</p>' in page
    assert 'data-merge="Before you go, {first_name}">Before you go</p>' in page
    assert "A walkthrough page by Northwind Creative." in page and "prepared for" not in page
    assert "Walked through live" not in page


def test_personal_page_has_no_merge_lines(built):
    assert "data-merge=" not in built
    assert "Walked through live: 5 ad creatives for the Trail Merino Crew." in built


@pytest.mark.parametrize("change,want", [
    ({"vsl_url": "", "case_study_url": ""}, "a general page is built around a VSL or a case-study document"),
    ({"case_study_url": "agency.example/cs"}, "case_study_url must be a full https:// link"),
    ({"case_study_title": ""}, "case_study_title is empty"),
    ({"merge_eyebrow": "For {last_name}"}, "merge_eyebrow may use only {first_name} and {company}"),
    ({"merge_eyebrow": "For you"}, "merge_eyebrow may use only {first_name} and {company}"),
    ({"mode": "team"}, "mode must be one of personal, general"),
])
def test_general_check_refuses_bad_input(change, want):
    s = json.loads(GENERAL.read_text(encoding="utf-8"))
    s.update(change)
    errors, _ = wtl.check(s)
    assert any(e.startswith(want) for e in errors), errors


def test_general_page_can_be_built_around_a_vsl_instead():
    s = json.loads(GENERAL.read_text(encoding="utf-8"))
    s.update({"vsl_url": "https://www.loom.com/share/0a1b2c3d", "case_study_url": "", "case_study_title": ""})
    assert wtl.check(s)[0] == []
    prompt = wtl.copilot_prompt(pathlib.Path("."), s)
    assert "Right: embed the video https://www.loom.com/share/0a1b2c3d" in prompt


def test_merge_lines_are_for_general_pages_only():
    s = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    s["merge_eyebrow"] = "Prepared for {company}"
    errors, _ = wtl.check(s)
    assert "merge_eyebrow is for general pages only: a personal page already names the prospect" in errors


def test_extract_general_starts_from_your_own_site(tmp_path):
    assert wtl.main(["extract", "https://fernhill.example", "--html", str(FIXTURE), "--out", str(tmp_path),
                     "--mode", "general"]) == 0
    s = json.loads((tmp_path / "sections.json").read_text(encoding="utf-8"))
    assert s["mode"] == "general" and s["from_name"] == s["brand"]["name"] == "Fernhill Socks"
    assert s["merge_eyebrow"] == "Prepared for {company}"
    errors, _ = wtl.check(s)
    assert not any(e.startswith("best_product") for e in errors)
    assert "a general page is built around a VSL or a case-study document: set vsl_url or case_study_url" in errors


def test_clone_refuses_a_general_page(tmp_path, capsys):
    path = clone_list(tmp_path)
    shutil.copy(GENERAL, tmp_path / "salt" / "sections.json")
    out = tmp_path / "out"
    assert wtl.main(["clone", path, "--out", str(out)]) == 1
    assert "a general page is one page for the whole campaign, not one per prospect" in capsys.readouterr().out
    assert not out.exists()
