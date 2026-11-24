#!/usr/bin/env python3
"""Checks that the sales-agent brief is what the Copilot prompt is built from."""
import json
import os
import re
import tempfile
import unittest

import make_prompt as mp

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))

SAFETY = (
    "Keep everything in draft: do not launch anything, do not send any email, "
    "do not attach sending accounts and do not turn on autopilot.",
    "I sign in and approve access myself. Never ask me for a password or API key.",
    "Keep approval on, so nothing goes out until I approve it. Autopilot stays off",
    "Prepare the first batch of 10 leads with their emails drafted, then stop.",
    "Before you build anything, list what you are going to set up and anything that is missing, and wait for my OK.",
)

SENTINELS = {
    "company": "COMPANY_SENTINEL",
    "website": "https://acme.example",
    "pages": "https://acme.example/pricing",
    "icp_industry": "INDUSTRY_SENTINEL",
    "icp_size": "SIZE_SENTINEL",
    "icp_geo": "GEO_SENTINEL",
    "titles": "TITLES_SENTINEL",
    "triggers": "TRIGGERS_SENTINEL",
    "disqualifiers": "DISQUALIFIERS_SENTINEL",
    "offer": "OFFER_SENTINEL",
    "pricing": "PRICING_SENTINEL",
    "guarantee": "GUARANTEE_SENTINEL",
    "proof": "PROOF_SENTINEL",
    "testimonials": "TESTIMONIALS_SENTINEL",
    "logos": "LOGOS_SENTINEL",
    "objections": "OBJECTIONS_SENTINEL",
    "competitors": "COMPETITORS_SENTINEL",
    "differentiators": "DIFFERENTIATORS_SENTINEL",
    "booking": "https://cal.example/acme",
    "tone": "TONE_SENTINEL",
    "avoid": "AVOID_SENTINEL",
    "never_say": "NEVER_SENTINEL",
    "handoff": "HANDOFF_SENTINEL",
    "files": "FILES_SENTINEL",
    "integration": "notion",
    "integration_content": "CONTENT_SENTINEL",
}

REPEATED = (
    "INDUSTRY_SENTINEL",
    "SIZE_SENTINEL",
    "GEO_SENTINEL",
    "TITLES_SENTINEL",
    "TRIGGERS_SENTINEL",
    "DISQUALIFIERS_SENTINEL",
    "OFFER_SENTINEL",
    "PRICING_SENTINEL",
    "GUARANTEE_SENTINEL",
    "PROOF_SENTINEL",
    "TESTIMONIALS_SENTINEL",
    "LOGOS_SENTINEL",
    "OBJECTIONS_SENTINEL",
    "COMPETITORS_SENTINEL",
    "DIFFERENTIATORS_SENTINEL",
    "TONE_SENTINEL",
    "AVOID_SENTINEL",
    "NEVER_SENTINEL",
    "HANDOFF_SENTINEL",
    "https://cal.example/acme",
)


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def field(key):
    for item in mp.FIELDS:
        if item.key == key:
            return item
    raise AssertionError(key)


def silent_ask(value):
    def _ask(_prompt):
        return value
    return _ask


class MakePromptTest(unittest.TestCase):
    def test_sentinels_are_slotted_into_the_prompt(self):
        with tempfile.TemporaryDirectory() as tmp:
            brief_path = os.path.join(tmp, "brief.json")
            out_path = os.path.join(tmp, "prompt.txt")
            with open(brief_path, "w", encoding="utf-8") as fh:
                json.dump(SENTINELS, fh)
            argv = ["--brief-file", brief_path, "--no-ask", "--out", out_path, "--proof", "PROOF_SENTINEL"]
            mp.main(argv)
            with open(out_path, encoding="utf-8") as fh:
                prompt = fh.read()
        for sentinel in SENTINELS.values():
            if sentinel == "notion":
                self.assertIn("Notion", prompt)
            else:
                self.assertIn(sentinel, prompt)
        for sentinel in REPEATED:
            self.assertGreaterEqual(prompt.count(sentinel), 2, sentinel)
        self.assertNotIn("{{", prompt)
        for line in SAFETY:
            self.assertIn(line, prompt)
        self.assertIn("Do not invent stats, guarantees, case studies", prompt)
        self.assertIn("Never invent numbers, clients, logos, quotes or case studies.", prompt)
        self.assertIn("CONTENT_SENTINEL", prompt)

    def test_none_proof_forbids_claims(self):
        args = mp.parser().parse_args(["--no-ask", "--proof", "none", "--pricing", "no", "--guarantee", "skip"])
        values = mp.build_values(args, ask=False)
        self.assertEqual(values["PROOF"], mp.PROOF_NONE)
        self.assertEqual(values["PRICING"], mp.PRICING_NONE)
        self.assertEqual(values["GUARANTEE"], mp.GUARANTEE_NONE)
        prompt = mp.fill(mp.read_template(), mp.prompt_values(values))
        self.assertIn(mp.PROOF_NONE, prompt)
        self.assertIn("do not claim results", prompt)
        self.assertNotIn("use only what is on the website", prompt)
        self.assertIsNone(mp.gap_for(field("PROOF"), values["PROOF"]))

    def test_blank_fields_stay_in_brackets(self):
        args = mp.parser().parse_args(["--no-ask"])
        values = mp.build_values(args, ask=False)
        prompt = mp.fill(mp.read_template(), mp.prompt_values(values))
        left = mp.placeholders(prompt)
        self.assertIn("[your website]", left)
        self.assertIn("[industry or niche]", left)
        self.assertNotIn("square brackets", " ".join(left))
        gaps = mp.collect_gaps(values)
        self.assertTrue(any("icp-industry" in gap for gap in gaps))

    def test_a_value_that_ends_with_a_period_is_not_doubled(self):
        args = mp.parser().parse_args([
            "--no-ask",
            "--offer", "A count on site.",
            "--differentiators", "It happens in the shop.",
            "--objections", "They already do this. Reply: ask how long it took.",
        ])
        prompt = mp.fill(mp.read_template(), mp.prompt_values(mp.build_values(args, ask=False)))
        self.assertIn("Sell only this: A count on site.", prompt)
        self.assertNotIn("site..", prompt)
        self.assertIn("The only difference you may state: It happens in the shop.", prompt)
        self.assertNotIn("shop..", prompt)
        self.assertNotIn("took..", prompt)

    def test_template_fields_are_all_filled(self):
        block = mp.read_template()
        keys = set(re.findall(r"\{\{(\w+)\}\}", block))
        args = mp.parser().parse_args(["--no-ask"])
        values = mp.prompt_values(mp.build_values(args, ask=False))
        self.assertTrue(keys <= set(values))

    def test_ask_pushes_back_on_a_vague_niche(self):
        answers = iter(["businesses", "independent dental practices"])
        notes = []
        value = mp.ask_one(
            field("ICP_INDUSTRY"),
            input_fn=lambda _prompt: next(answers),
            print_fn=notes.append,
        )
        self.assertEqual(value, "independent dental practices")
        self.assertTrue(any("Name the niche" in note for note in notes))
        self.assertIsNone(mp.gap_for(field("ICP_INDUSTRY"), value))

    def test_second_vague_answer_stays_a_gap(self):
        answers = iter(["businesses", "companies"])
        value = mp.ask_one(
            field("ICP_INDUSTRY"),
            input_fn=lambda _prompt: next(answers),
            print_fn=lambda _msg: None,
        )
        self.assertEqual(value, "companies")
        self.assertIsNotNone(mp.gap_for(field("ICP_INDUSTRY"), value))

    def test_skip_on_industry_ends_as_a_placeholder(self):
        answers = iter(["skip", "skip"])
        value = mp.ask_one(
            field("ICP_INDUSTRY"),
            input_fn=lambda _prompt: next(answers),
            print_fn=lambda _msg: None,
        )
        self.assertEqual(value, field("ICP_INDUSTRY").placeholder)

    def test_empty_website_three_times_leaves_a_placeholder(self):
        answers = iter(["", "", ""])
        value = mp.ask_one(
            field("WEBSITE"),
            input_fn=lambda _prompt: next(answers),
            print_fn=lambda _msg: None,
        )
        self.assertEqual(value, "[your website]")

    def test_bad_link_is_asked_again(self):
        answers = iter(["calendar", "https://cal.example/acme"])
        value = mp.ask_one(
            field("BOOKING"),
            input_fn=lambda _prompt: next(answers),
            print_fn=lambda _msg: None,
        )
        self.assertEqual(value, "https://cal.example/acme")

    def test_confirm_applies_an_edit_before_yes(self):
        args = mp.parser().parse_args(["--no-ask", "--offer", "old offer", "--integration", "notion"])
        values = mp.build_values(args, ask=False)
        answers = iter(["offer", "OFFER_SENTINEL", "yes"])
        updated = mp.confirm(values, input_fn=lambda _prompt: next(answers), print_fn=lambda _msg: None)
        self.assertEqual(updated["OFFER"], "OFFER_SENTINEL")
        self.assertEqual(updated["INTEGRATION"], "Notion")

    def test_flag_overrides_brief_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "brief.json")
            with open(path, "w", encoding="utf-8") as fh:
                json.dump({"proof": "from the file", "website": "https://acme.example"}, fh)
            args = mp.parser().parse_args(["--no-ask", "--brief-file", path, "--proof", "none"])
            values = mp.build_values(args, ask=False)
        self.assertEqual(values["PROOF"], mp.PROOF_NONE)
        self.assertEqual(values["WEBSITE"], "https://acme.example")

    def test_docs_carry_the_none_lines_and_the_grill(self):
        skill = _read(os.path.join(HERE, "SKILL.md"))
        template = _read(os.path.join(HERE, "template.md"))
        readme = _read(os.path.join(HERE, "README.md"))
        root = _read(os.path.join(ROOT, "README.md"))
        for line in mp.NONE_LINES:
            if line in (mp.AVOID_NONE, mp.DISQUALIFIERS_NONE, mp.PAGES_NONE, mp.FILES_NONE):
                self.assertIn(line, skill)
                continue
            self.assertIn(line, skill)
            self.assertIn(line, template)
        self.assertIn("Do not write the prompt", skill)
        self.assertIn("one focused question", skill)
        self.assertIn("Do not send the full list in one message", skill)
        self.assertNotIn("Ask these in one message", skill)
        self.assertNotIn("You answer 5 questions", readme)
        self.assertNotIn("Asks you 5 questions", root)
        self.assertNotIn("Answer the 5 questions", root)
        for text in (skill, template, readme, root, _read(os.path.join(HERE, "make_prompt.py"))):
            self.assertNotIn("\u2014", text)
            self.assertNotIn("\u2013", text)
            for banned in ("LeadGrow", "Legion", "Skool"):
                self.assertNotIn(banned, text)


if __name__ == "__main__":
    unittest.main()
