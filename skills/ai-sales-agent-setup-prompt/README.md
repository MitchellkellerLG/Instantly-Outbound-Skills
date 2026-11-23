# AI Sales Agent setup prompt

A small skill that writes one prompt for Instantly Copilot. The prompt sets up an AI Sales Agent, powered by PULSE-1, for your own company, and teaches it your business through the Knowledge Base.

This replaces the earlier `pulse-agent-setup-prompt` skill. If you have that one, remove it and use this.

You answer 5 questions (your website, what you sell, who you sell to, your booking link, and where your company knowledge lives). You get back a prompt that tells Copilot to:

- Build your Knowledge Base: your website (refreshed weekly), the files you upload, and your case studies
- Show you where to connect Notion, Granola or Google Drive, so your knowledge syncs daily. You sign in yourself
- Tell you what it learned and what is still missing, and wait for your OK
- Build the AI Sales Agent around your offer and the people you sell to, with Pulse on
- Add 7 guidance rules for how the emails are written
- Draft the first 10 leads and stop, so you approve each one yourself

Everything stays in draft. Nothing is launched or sent until you approve it in Instantly.

## Use it in Claude (easiest)

1. Download this zip. Don't unzip it.
2. In Claude, go to Settings, then Capabilities, and upload the zip under Skills. Skills need to be turned on for your account.
3. Start a new chat and type: "Write my AI Sales Agent setup prompt"
4. Answer the questions, then copy the prompt Claude gives you.

In Claude Code, unzip it into your skills folder (`~/.claude/skills/`) instead.

## Use it without Claude

Open `template.md`, copy the block, and replace each {{FIELD}} with your own details.

Or, if you have Python: `python3 make_prompt.py` asks you the questions and writes `ai-sales-agent-setup-prompt.txt`.

## Then, in Instantly

1. Open Copilot and paste the whole prompt
2. Upload your files and connect Notion, Granola or Google Drive when Copilot shows you where. Google Drive is listed as coming soon; if it isn't there yet, Copilot skips it
3. Read what Copilot says it learned, fix anything wrong, then say OK
4. Steps marked [check in your workspace] may have a different menu name in your account; Copilot tells you where to click if it can't do one
5. Approve or skip each of the first 10 leads yourself

Approving leads may use credits in your plan. Check the pricing in your own Instantly account.

## What's in the zip

- `SKILL.md` - the instructions Claude follows
- `template.md` - the prompt itself, with {{FIELDS}} to fill
- `make_prompt.py` - optional helper that fills the template for you
- `README.md` - this file

No logins, keys or tracking. The skill only writes text.
