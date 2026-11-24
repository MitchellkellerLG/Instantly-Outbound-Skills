#!/usr/bin/env python3
"""Write an Instantly Copilot prompt that sets up an AI Sales Agent from a
confirmed brief.

Usage:
  python3 make_prompt.py
      Asks one question at a time, prints the brief, and writes the file
      only after you type yes.
  python3 make_prompt.py --brief-file sales-agent-brief.json --no-ask
      Fills the prompt from a JSON object. Keys are field names such as
      website, icp_industry, proof. Does not ask, and does not open the website.

This script does not open the website and does not send anything. It only
writes a text file. Standard library only.

A value of none, no, or skip on proof, price, guarantee, testimonials, logos,
objections, competitors or difference is stored as a "do not invent" line.
Anything left blank stays in [square brackets].
"""
import argparse
import json
import os
import re
import sys
from collections import namedtuple

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "template.md")

WEBSITE_NONE = "none: do not add a website source"
PRICING_NONE = "not shared: do not quote a price"
GUARANTEE_NONE = "none: do not state a guarantee or a risk reversal"
PROOF_NONE = "none: do not claim results, name clients, or use numbers"
TESTIMONIALS_NONE = "none: do not quote anyone"
LOGOS_NONE = "none: do not name logos"
OBJECTIONS_NONE = "none supplied: do not invent an objection handling"
COMPETITORS_NONE = "none: do not name competitors"
DIFFERENTIATORS_NONE = "none supplied: do not invent a comparison"
NEVER_NONE = "none named: still do not invent promises, prices, guarantees or results"
HANDOFF_NONE = "none supplied: do not invent a handoff. Keep approval on."
AVOID_NONE = "none named"
DISQUALIFIERS_NONE = "none supplied"
PAGES_NONE = "none given"
FILES_NONE = "none"

NONE_LINES = (
    WEBSITE_NONE,
    PRICING_NONE,
    GUARANTEE_NONE,
    PROOF_NONE,
    TESTIMONIALS_NONE,
    LOGOS_NONE,
    OBJECTIONS_NONE,
    COMPETITORS_NONE,
    DIFFERENTIATORS_NONE,
    NEVER_NONE,
    HANDOFF_NONE,
    AVOID_NONE,
    DISQUALIFIERS_NONE,
    PAGES_NONE,
    FILES_NONE,
)

NONE_TOKENS = {
    "none", "no", "n/a", "na", "nothing", "nope", "none yet",
    "dont have any", "don't have any", "do not have any",
    "we don't have one", "we do not have one", "we dont have one",
    "not shared", "won't share", "wont share", "will not share",
}
SKIP_TOKENS = {
    "skip", "later", "move on", "tbd", "dont know", "don't know", "idk",
}
VAGUE = {
    "businesses", "companies", "b2b", "everyone", "everybody", "anyone",
    "everywhere", "global", "worldwide", "decision makers", "decision maker",
    "stakeholders", "when they need help", "we help companies grow",
    "great results", "good results", "it depends", "various", "lots", "many",
    "smbs", "smb", "mid-market", "midmarket", "some", "a few", "yes",
    "we have case studies", "good companies", "people", "customers",
    "our customers", "not sure", "whatever", "professional", "normal",
}

# name shown in the prompt, and what to sync from it by default
INTEGRATIONS = {
    "notion": ("Notion", "the Notion pages about our product, pricing, customers and case studies (I pick them when I connect)"),
    "granola": ("Granola", "my sales and customer call notes"),
    "google-drive": ("Google Drive", "the folder with our sales deck, case studies and one-pagers (I pick it when I connect)"),
    "none": ("Notion or Granola", "the pages or call notes I pick when I connect it"),
}
KNOWN_INTEGRATION_INPUTS = set(INTEGRATIONS) | {"drive", "no", "nothing", "n/a", ""}

Field = namedtuple(
    "Field",
    "key dest flag label question placeholder pushback none_text skip_means_none vague_extra check required group",
)


def F(key, flag, label, question, placeholder, pushback, group, **kwargs):
    return Field(
        key=key,
        dest=flag.replace("-", "_"),
        flag=flag,
        label=label,
        question=question,
        placeholder=placeholder,
        pushback=pushback,
        none_text=kwargs.get("none_text"),
        skip_means_none=kwargs.get("skip_means_none", False),
        vague_extra=frozenset(kwargs.get("vague_extra", ())),
        check=kwargs.get("check", ""),
        required=kwargs.get("required", True),
        group=group,
    )


FIELDS = [
    F("COMPANY", "company", "Company",
      "Company name. Press enter to leave a placeholder",
      "[your company name]",
      "Use the name customers see, or press enter to leave it for later.",
      "Company", required=False),
    F("WEBSITE", "website", "Website",
      "Company website, including the domain. Type none if you have no site",
      "[your website]",
      "Paste the full site address, such as https://acme.example. Type none if you have no site.",
      "Company", check="link", none_text=WEBSITE_NONE, skip_means_none=True),
    F("PAGES", "pages", "Key pages",
      "Pricing, case study and booking page URLs, separated by commas. Type none if you only have the homepage",
      "[pricing page, case study page, and booking page URLs]",
      "Paste the page URLs, or type none if you only have the homepage.",
      "Company", none_text=PAGES_NONE, skip_means_none=True),
    F("ICP_INDUSTRY", "icp-industry", "Industry or niche",
      "Industry or niche you sell to",
      "[industry or niche]",
      "Name the niche. Example: independent dental practices.",
      "Who we sell to"),
    F("ICP_SIZE", "icp-size", "Company size",
      "Company size you sell to, as a headcount or revenue range",
      "[company size, as a headcount or revenue range]",
      "Give a range. Example: 10 to 50 employees, or 1 to 5 million in yearly revenue.",
      "Who we sell to"),
    F("ICP_GEO", "icp-geo", "Geography",
      "Countries or regions you sell to",
      "[countries or regions]",
      "Name the countries or regions. Example: United States and Canada.",
      "Who we sell to"),
    F("TITLES", "titles", "Buyer titles",
      "Job titles of the people who buy",
      "[buyer job titles]",
      "Name the job titles. Example: owner and office manager.",
      "Who we sell to"),
    F("TRIGGERS", "triggers", "Buy trigger",
      "What triggers them to buy",
      "[what triggers them to buy]",
      "Name the event that makes them look. Example: they just opened a second location.",
      "Who we sell to"),
    F("DISQUALIFIERS", "disqualifiers", "Disqualifiers",
      "Who the agent should skip. Type none if everyone in the niche is a fit",
      "[who to skip]",
      "Name who to skip. Example: under 5 employees, or already on a retainer. Type none if there is no skip list.",
      "Who we sell to", none_text=DISQUALIFIERS_NONE, skip_means_none=True),
    F("OFFER", "offer", "Offer",
      "What you sell, including what the buyer gets and in what form",
      "[what you sell, including what the buyer gets]",
      "Say what the buyer gets, and in what form. Example: a monthly bookkeeping service with a named bookkeeper.",
      "Offer"),
    F("PRICING", "pricing", "Price",
      "Price or price range. Type none if the agent must not quote a price",
      "[price or range, or say it is not shared]",
      "Give the price or a range, or type none if the agent must not quote a price.",
      "Offer", none_text=PRICING_NONE, skip_means_none=True),
    F("GUARANTEE", "guarantee", "Guarantee",
      "Exact guarantee or risk reversal terms. Type none if there is no guarantee",
      "[exact guarantee terms, or none]",
      "Paste the exact terms, or type none. Do not describe a guarantee you do not offer.",
      "Offer", none_text=GUARANTEE_NONE, skip_means_none=True),
    F("PROOF", "proof", "Case studies and results",
      "Case studies or results you can stand behind, with your numbers. Type none if there are none",
      "[case studies with your numbers, or none]",
      "Paste a result you are allowed to use, with the number you have. Or type none and the agent will not claim results.",
      "Proof", none_text=PROOF_NONE, skip_means_none=True,
      vague_extra=("we have results", "we have case studies", "see the website", "on our website")),
    F("TESTIMONIALS", "testimonials", "Testimonials",
      "Testimonials the agent may quote. Type none if there are none",
      "[testimonials you supplied, or none]",
      "Paste a testimonial you are allowed to quote, or type none.",
      "Proof", none_text=TESTIMONIALS_NONE, skip_means_none=True),
    F("LOGOS", "logos", "Logos",
      "Logos the agent may name. Type none if it must not name any",
      "[logos you may name, or none]",
      "Name the logos the agent may mention, or type none.",
      "Proof", none_text=LOGOS_NONE, skip_means_none=True),
    F("OBJECTIONS", "objections", "Objections",
      "Top objections and the reply you want for each. Type none to leave them unanswered",
      "[top objections and how you handle each]",
      "Name one objection and the reply you want. Type none if the agent should not handle objections.",
      "How we sell", none_text=OBJECTIONS_NONE, skip_means_none=True),
    F("COMPETITORS", "competitors", "Competitors",
      "Competitors the agent may name. Type none if it must not name any",
      "[competitors you may mention]",
      "Name the competitors the agent may mention, or type none.",
      "How we sell", none_text=COMPETITORS_NONE, skip_means_none=True),
    F("DIFFERENTIATORS", "differentiators", "Difference",
      "How you are different, in one concrete line. Type none if the agent must not compare",
      "[how you are different]",
      "Say the difference in one concrete line, or type none and the agent will not invent a comparison.",
      "How we sell", none_text=DIFFERENTIATORS_NONE, skip_means_none=True),
    F("BOOKING", "booking", "Booking link",
      "Booking link the email should use",
      "[your booking link]",
      "Paste the booking link. The email needs a real URL.",
      "How we sell", check="link"),
    F("TONE", "tone", "Tone",
      "Tone the agent should use",
      "[the tone you want]",
      "Describe the voice in a few words. Example: short, plain, and calm.",
      "How we sell"),
    F("AVOID", "avoid", "Words to avoid",
      "Words and phrases the agent must not use. Type none if you have no list",
      "[words and phrases to avoid]",
      "List the words to avoid, separated by commas. Type none if you have no list.",
      "How we sell", none_text=AVOID_NONE, skip_means_none=True),
    F("NEVER", "never-say", "Never say or promise",
      "What the agent must never say or promise",
      "[what the agent must never say or promise]",
      "Name at least one thing it must not promise. Example: a savings figure, a deadline, or that they will be accepted.",
      "How we sell", none_text=NEVER_NONE, skip_means_none=True),
    F("HANDOFF", "handoff", "Handoff",
      "When a person takes over",
      "[when to stop and hand off to a human]",
      "Say when a person takes over. Example: the lead replies, asks for a price, or books a call.",
      "How we sell", none_text=HANDOFF_NONE, skip_means_none=True),
    F("FILES", "files", "Files",
      "Files you will upload, separated by commas. Type none if there are no files",
      "[the files you will upload, such as a sales deck or one-pager]",
      "Name the files, or type none.",
      "Sources", required=False, none_text=FILES_NONE, skip_means_none=True),
    F("INTEGRATION", "integration", "Integration",
      "Where company knowledge lives: notion, granola, google-drive, or none",
      "none",
      "Type notion, granola, google-drive, or none.",
      "Sources", required=False, check="integration"),
]


def read_template():
    with open(TEMPLATE, encoding="utf-8") as fh:
        text = fh.read()
    match = re.search(r"```text\n(.*?)```", text, re.S)
    if not match:
        sys.exit("template.md has no ```text block")
    return match.group(1).strip() + "\n"


def fill(template, values):
    def sub(match):
        key = match.group(1)
        if key not in values:
            sys.exit("template.md uses an unknown field: {{%s}}" % key)
        value = values[key]
        # The template often ends a sentence at the field. Keep a single period.
        if template[match.end():match.end() + 1] == "." and value.endswith("."):
            value = value[:-1]
        return value
    prompt = re.sub(r"\{\{(\w+)\}\}", sub, template)
    leftover = re.findall(r"\{\{(\w+)\}\}", prompt)
    if leftover:
        sys.exit("unfilled fields: " + ", ".join(leftover))
    return prompt


def integration(choice, content):
    key = (choice or "").strip().lower().replace(" ", "-")
    if key in ("", "no", "nothing", "n/a"):
        key = "none"
    if key == "drive":
        key = "google-drive"
    name, default = INTEGRATIONS.get(key, ((choice or "").strip(), "[what the agent should learn from %s]" % (choice or "").strip()))
    return name, (content or "").strip() or default


def norm(value):
    text = value.strip().lower().rstrip(".")
    text = text.replace("\u2019", "'")
    return re.sub(r"\s+", " ", text)


def fails_check(field, value):
    if field.check == "link":
        return "." not in value or any(ch.isspace() for ch in value)
    if field.check == "integration":
        key = value.strip().lower().replace(" ", "-")
        return key not in KNOWN_INTEGRATION_INPUTS
    return False


def is_vague(field, value):
    if field.none_text and value == field.none_text:
        return False
    token = norm(value)
    return token in VAGUE or token in field.vague_extra


def gap_for(field, value):
    if field.none_text and value == field.none_text:
        return None
    if field.key == "INTEGRATION":
        return None
    if value == field.placeholder or (value.startswith("[") and value.endswith("]")):
        return "%s (%s) is still blank. The prompt will keep the placeholder." % (field.label, field.flag)
    if is_vague(field, value) or (field.check == "link" and fails_check(field, value)):
        return "%s (%s) is still vague. Type yes only if you want that wording in the prompt." % (field.label, field.flag)
    return None


def collect_gaps(values):
    return [gap for gap in (gap_for(field, values[field.key]) for field in FIELDS) if gap]


def format_brief(values):
    lines = ["Brief"]
    current = None
    for field in FIELDS:
        if field.group != current:
            current = field.group
            lines.append("")
            lines.append(current)
        lines.append("- %s (%s): %s" % (field.label, field.flag, values[field.key]))
    lines.append("- What to learn (integration-content): %s" % values["INTEGRATION_CONTENT"])
    return "\n".join(lines)


def field_by_token(answer):
    token = answer.strip().lower().lstrip("-").replace("_", "-")
    for field in FIELDS:
        names = {
            field.flag,
            field.dest.replace("_", "-"),
            field.key.lower().replace("_", "-"),
            field.label.lower(),
        }
        if token in names:
            return field
    return None


def coerce(field, raw):
    """Map a provided answer. Does not push back; the chat already did that."""
    raw = (raw or "").strip()
    if not raw:
        return field.placeholder
    token = norm(raw)
    if token in NONE_TOKENS and field.none_text:
        return field.none_text
    if token in SKIP_TOKENS:
        if field.skip_means_none and field.none_text:
            return field.none_text
        return field.placeholder
    return raw


def ask_one(field, input_fn=None, print_fn=None):
    ask = input_fn or input
    out = print_fn or print
    pushes = 0
    empties = 0
    while True:
        value = ask(field.question + ": ").strip()
        if not value:
            if not field.required:
                return field.placeholder
            empties += 1
            if empties >= 3:
                return field.placeholder
            out(field.pushback)
            continue
        token = norm(value)
        if token in NONE_TOKENS and field.none_text:
            return field.none_text
        if token in SKIP_TOKENS or (token in NONE_TOKENS and not field.none_text):
            if field.skip_means_none and field.none_text:
                return field.none_text
            if pushes < 1 and field.required:
                out(field.pushback)
                pushes += 1
                continue
            return field.placeholder
        if (is_vague(field, value) or fails_check(field, value)) and pushes < 1:
            out(field.pushback)
            pushes += 1
            continue
        return value


def apply_integration(values, choice, content):
    if not choice or choice == field_by_token("integration").placeholder:
        choice = "none"
    values["_integration_raw"] = choice
    name, resolved = integration(choice, content)
    values["INTEGRATION"] = name
    values["INTEGRATION_CONTENT"] = resolved


def load_brief(path):
    if not path:
        return {}
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        sys.exit("brief file must be a JSON object")
    return data


def lookup_brief(brief, field):
    for key in (field.key, field.dest, field.flag):
        if key in brief and brief[key] is not None:
            return str(brief[key])
    return None


def build_values(args, ask, input_fn=None, print_fn=None):
    ask_input = input_fn or input
    brief = load_brief(getattr(args, "brief_file", None))
    values = {}
    for field in FIELDS:
        provided = getattr(args, field.dest, None)
        if provided is None:
            provided = lookup_brief(brief, field)
        if provided is not None and str(provided).strip():
            values[field.key] = coerce(field, str(provided))
        elif ask:
            values[field.key] = ask_one(field, input_fn=input_fn, print_fn=print_fn)
        else:
            values[field.key] = field.placeholder

    content = getattr(args, "integration_content", None)
    if content is None:
        for key in ("INTEGRATION_CONTENT", "integration_content", "integration-content"):
            if brief.get(key):
                content = brief[key]
                break
    content = "" if content is None else str(content).strip()
    if not content and ask:
        content = ask_input("What should the agent learn from it? Press enter for the default: ").strip()
    apply_integration(values, values["INTEGRATION"], content)
    return values


def confirm(values, input_fn=None, print_fn=None):
    ask_input = input_fn or input
    out = print_fn or print
    while True:
        out(format_brief(values))
        out("")
        gaps = collect_gaps(values)
        if gaps:
            out("Gaps")
            for gap in gaps:
                out("- " + gap)
            out("")
            out("Type yes to write the prompt and accept these gaps. Type a field name to change one.")
        else:
            out("Type yes to write the prompt. Type a field name to change one.")
        answer = ask_input("> ").strip()
        token = answer.lower()
        if token in ("yes", "y"):
            return values
        if token.replace("_", "-") in ("integration-content", "content"):
            content = ask_input("What should the agent learn from it? Press enter for the default: ").strip()
            apply_integration(values, values.get("_integration_raw", ""), content)
            continue
        field = field_by_token(token)
        if not field:
            out("Type yes, or a field such as offer, proof, or icp-industry.")
            continue
        if field.key == "INTEGRATION":
            choice = ask_one(field, input_fn=input_fn, print_fn=print_fn)
            apply_integration(values, choice, "")
            continue
        values[field.key] = ask_one(field, input_fn=input_fn, print_fn=print_fn)


def prompt_values(values):
    return {key: value for key, value in values.items() if not key.startswith("_")}


def placeholders(prompt):
    return sorted(set(re.findall(r"\[(?!check in your workspace)[^\]]+\]", prompt)))


def parser():
    ap = argparse.ArgumentParser(description="Write an Instantly Copilot prompt from a confirmed sales brief.")
    for field in FIELDS:
        ap.add_argument("--" + field.flag, dest=field.dest, help=field.question)
    ap.add_argument("--integration-content", help="what the agent should learn from the integration")
    ap.add_argument("--brief-file", help="JSON object of answers. Flags override the file.")
    ap.add_argument("--out", default="ai-sales-agent-setup-prompt.txt", help="where to write the prompt")
    ap.add_argument("--no-ask", action="store_true", help="never ask; leave missing fields in [brackets]")
    return ap


def main(argv=None):
    args = parser().parse_args(argv)
    ask = not args.no_ask and sys.stdin.isatty()
    values = build_values(args, ask)
    if ask:
        values = confirm(values)
    prompt = fill(read_template(), prompt_values(values))
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(prompt)
    left = placeholders(prompt)
    print("Wrote " + os.path.abspath(args.out))
    if left:
        print("Still to fill in: " + ", ".join(left))
    print("Next: open Instantly Copilot, paste the whole file, and answer its questions.")
    return prompt


if __name__ == "__main__":
    main()
