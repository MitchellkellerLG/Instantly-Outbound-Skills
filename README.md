# Instantly Outbound Skills

Free, open skills for running outbound with [Instantly](https://instantly.ai). Each skill is a folder of plain instructions that Claude follows, plus small optional Python helpers (standard library only). They only write text and files on your machine: no API keys, no tracking, and nothing is sent, launched or deployed on your behalf.

## Skills

| Skill | What it does |
|---|---|
| [ai-sales-agent-setup-prompt](skills/ai-sales-agent-setup-prompt/) | Asks you 5 questions and writes one prompt you paste into Instantly Copilot. The prompt sets up an AI Sales Agent (powered by PULSE-1), builds its Knowledge Base from your website, files and case studies, and walks you through connecting Notion, Granola or Google Drive so it stays current. Everything stays in draft until you approve it. |
| [website-to-lander](skills/website-to-lander/) | Builds a booking-optimised landing page from a website, in two modes. **Personal:** one page per prospect who replied, in their brand, plus a Copilot prompt for an Instantly workflow that builds one for every positive reply. **General:** one page for every lead in a campaign, in your brand, around a resource or lead magnet of your choice (a video, or a case study or other document you link). Writes a ready-to-paste Instantly Copilot prompt and a self-contained `index.html`. |

## Put a page live

The website-to-lander pages can be hosted in Instantly (built by Copilot from the prompt) or off Instantly on Cloudflare Pages (free; drag-and-drop upload, your own subdomain, kept out of search results). See [the hosting guide](skills/website-to-lander/references/hosting.md).

## Use a skill in Claude (claude.ai)

1. Download the skill folder as a zip. Either download this repo (Code, then Download ZIP), unzip it, and zip just the skill's folder (for example `skills/ai-sales-agent-setup-prompt`), or run `cd skills && zip -r ai-sales-agent-setup-prompt.zip ai-sales-agent-setup-prompt`.
2. In Claude, open Settings, then Capabilities, and upload the zip under Skills. Skills need to be turned on for your account.
3. Start a new chat and ask for it, for example "Write my AI Sales Agent setup prompt" or "Build the lander for example.com, general mode".
4. Answer the questions, then paste the prompt Claude gives you into Instantly Copilot.

## Use the skills in Claude Code

Add this repo as a plugin marketplace, then install the plugin:

```
/plugin marketplace add <owner>/<repo>
/plugin install instantly-outbound-skills@instantly-outbound-skills
```

Or copy a skill folder into `~/.claude/skills/` yourself.

## Use a skill without Claude

Each skill's `SKILL.md` (and `README.md` where there is one) explains how to use it by hand. For example, the AI Sales Agent skill has a `template.md` you can fill in yourself, and an optional `make_prompt.py` (Python 3, standard library only) that asks the questions and writes the prompt for you.

## Run the tests

```bash
python3 -m pip install pytest
python3 -m pytest skills/website-to-lander/scripts -q
```

The tests run offline against a made-up brand.

## License

MIT. See [LICENSE](LICENSE).
