---
name: ai-sales-agent-setup-prompt
description: Writes a ready-to-paste Instantly Copilot prompt that sets up an AI Sales Agent powered by PULSE-1 for the user's own company, builds its Knowledge Base from their website, files and case studies, and walks them through connecting Notion, Granola or Google Drive so the knowledge syncs daily. Use when someone asks for "the AI Sales Agent setup prompt", "the Pulse setup prompt", "set up the Instantly AI Sales Agent for my company", "set up my Knowledge Base" or "connect Notion to Instantly". Replaces pulse-agent-setup-prompt.
---

# AI Sales Agent setup prompt

You turn a few answers into one prompt the user pastes into Instantly Copilot. You do not log in to anything, call any API or send anything. The user pastes the prompt themselves.

This skill replaces `pulse-agent-setup-prompt`. It writes the same agent setup and adds the Knowledge Base and an integration step.

## 1. Ask for the details

Ask these in one message, numbered, and wait for the answers:

1. Your company website
2. What you sell, in one line (the offer)
3. Who you sell to: industry, company size, region, and the job titles of the people who buy (the ICP)
4. Your booking link (the calendar link a lead uses to book a call)
5. Where does your company knowledge live: Notion, Granola (call notes), Google Drive, or none of them? And what should the agent learn from it (for example "our product and case study pages in Notion")?

Optional, ask in the same message: the company name, the case studies or results they are allowed to mention, and the files they will upload (sales deck, case studies, one-pager).

If they answer "none" for 5, say that connecting Notion or Granola keeps the agent current every day, and write the prompt with "Notion or Granola" so Copilot shows them where to connect one. Google Drive is listed as coming soon in Instantly; keep it if they pick it, the prompt tells Copilot to skip it if it isn't there yet.

Never invent an answer. If the user skips one, leave its [square-bracket] placeholder in the prompt and say so at the end.

## 2. Write the prompt

If you can run Python, run:

```bash
python3 make_prompt.py --website "<website>" --offer "<offer>" --icp "<industry, size, region>" \
  --titles "<job titles>" --booking "<booking link>" --company "<name>" --proof "<case studies>" \
  --files "<files>" --integration notion --integration-content "<what to learn from it>" \
  --no-ask --out ai-sales-agent-setup-prompt.txt
```

`--integration` is notion, granola, google-drive or none. Leave out `--integration-content` to use a sensible default for that tool.

Otherwise, copy the block in `template.md` and replace each {{FIELD}} yourself:
WEBSITE, OFFER, ICP, TITLES, BOOKING, COMPANY, PROOF, FILES, INTEGRATION, INTEGRATION_CONTENT. If there is no proof, use "none yet, so use only what is on the website". `template.md` says what to write for INTEGRATION when they use none.

Keep the rest of the prompt word for word. It keeps everything in draft, leaves autopilot off, has the user sign in to the integration themselves and holds the first 10 leads for the user to approve. Those safety lines must stay.

## 3. Hand it over

Give the user the finished prompt in one copyable block, then four lines:

- Open Instantly, open Copilot, paste the whole prompt and send it
- Copilot shows you where to upload your files and connect your integration. You sign in yourself; never paste a password or key into the chat
- Copilot reads back what it learned and waits for your OK. Check it before you say yes
- Steps marked [check in your workspace] may use a different menu name in your account. If Copilot can't do one, it tells you where to click

List any placeholders still in [square brackets].

## Rules

- Only the user's own facts go in the prompt. No numbers, clients or claims you made up.
- Do not change the draft-only, autopilot-off, sign-in-yourself and approve-by-hand lines.
- Do not promise results, quote prices or credit costs. If asked about cost, say to check pricing in their Instantly account.
