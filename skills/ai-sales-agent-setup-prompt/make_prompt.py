#!/usr/bin/env python3
"""Write an Instantly Copilot prompt that sets up an AI Sales Agent, fills its
Knowledge Base, and connects Notion, Granola or Google Drive.

Usage:
  python3 make_prompt.py                      # asks you each question
  python3 make_prompt.py --website https://acme.example --offer "..." --icp "..." \
      --booking https://cal.example/acme --integration notion \
      [--company Acme] [--titles "..."] [--proof "..."] [--files "..."] \
      [--integration-content "..."] [--out prompt.txt]

--integration is notion, granola, google-drive or none. Any other name is used as written.
Anything you leave blank stays in [square brackets] so you can fill it in later.
Standard library only. Nothing is sent anywhere: it only writes a text file.
"""
import argparse
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "template.md")

FIELDS = [
    # key, flag, question, placeholder when left blank
    ("WEBSITE", "website", "Your company website", "[your website]"),
    ("OFFER", "offer", "What you sell, in one line (the offer)", "[what you sell, in one line]"),
    ("ICP", "icp", "Who you sell to: industry, company size and region", "[industry, company size and region you sell to]"),
    ("BOOKING", "booking", "Your booking link", "[your booking link]"),
    ("INTEGRATION", "integration", "Where your company knowledge lives: notion, granola, google-drive or none", "none"),
    ("COMPANY", "company", "Company name (optional)", "[your company name]"),
    ("TITLES", "titles", "Job titles of the people who buy (optional)", "[job titles of the people who buy]"),
    ("PROOF", "proof", "Case studies or results you can mention (optional)", "none yet, so use only what is on the website"),
    ("FILES", "files", "Files you will upload, e.g. sales deck, case studies, one-pager (optional)", "[the files you will upload, e.g. sales deck, case studies, one-pager]"),
]

# name shown in the prompt, and what to sync from it by default
INTEGRATIONS = {
    "notion": ("Notion", "the Notion pages about our product, pricing, customers and case studies (I pick them when I connect)"),
    "granola": ("Granola", "my sales and customer call notes"),
    "google-drive": ("Google Drive", "the folder with our sales deck, case studies and one-pagers (I pick it when I connect)"),
    "none": ("Notion or Granola", "the pages or call notes I pick when I connect it"),
}


def read_template():
    with open(TEMPLATE, encoding="utf-8") as fh:
        text = fh.read()
    # template.md wraps the prompt in a fenced block; take what is inside it
    match = re.search(r"```text\n(.*?)```", text, re.S)
    if not match:
        sys.exit("template.md has no ```text block")
    return match.group(1)


def fill(template, values):
    def sub(m):
        key = m.group(1)
        if key not in values:
            sys.exit("template.md uses an unknown field: {{%s}}" % key)
        return values[key]
    return re.sub(r"\{\{(\w+)\}\}", sub, template)


def integration(choice, content):
    key = choice.strip().lower().replace(" ", "-")
    if key in ("", "no", "nothing", "n/a"):
        key = "none"
    if key == "drive":
        key = "google-drive"
    name, default = INTEGRATIONS.get(key, (choice.strip(), "[what the agent should learn from %s]" % choice.strip()))
    return name, content.strip() or default


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    for _, flag, question, _ in FIELDS:
        ap.add_argument("--" + flag, help=question)
    ap.add_argument("--integration-content", help="what the agent should learn from the integration (optional)")
    ap.add_argument("--out", default="ai-sales-agent-setup-prompt.txt", help="where to write the prompt")
    ap.add_argument("--no-ask", action="store_true", help="never ask; leave missing fields in [brackets]")
    args = ap.parse_args()

    ask = not args.no_ask and sys.stdin.isatty()
    values = {}
    for key, flag, question, placeholder in FIELDS:
        value = (getattr(args, flag) or "").strip()
        if not value and ask:
            value = input(question + ": ").strip()
        values[key] = value or placeholder

    content = args.integration_content or ""
    values["INTEGRATION"], values["INTEGRATION_CONTENT"] = integration(values["INTEGRATION"], content)

    prompt = fill(read_template(), values)
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(prompt)
    left = sorted(set(re.findall(r"\[(?!check in your workspace)[^\]]+\]", prompt)))
    print("Wrote " + os.path.abspath(args.out))
    if left:
        print("Still to fill in: " + ", ".join(left))
    print("Next: open Instantly Copilot, paste the whole file, and answer its questions.")


if __name__ == "__main__":
    main()
