---
name: ai-sales-agent-setup-prompt
description: Grills the user for a concrete sales brief, then writes a ready-to-paste Instantly Copilot prompt that sets up an AI Sales Agent powered by PULSE-1 for their own company. The brief covers ICP, offer, price, guarantee, proof, objections, competitors, tone, and handoff. The prompt builds the Knowledge Base from their website, files and confirmed proof, and walks them through connecting Notion, Granola or Google Drive. Use when someone asks for "the AI Sales Agent setup prompt", "the Pulse setup prompt", "set up the Instantly AI Sales Agent for my company", "set up my Knowledge Base" or "connect Notion to Instantly". Replaces pulse-agent-setup-prompt.
---

# AI Sales Agent setup prompt

You turn a confirmed brief into one prompt the user pastes into Instantly Copilot. You do not log in to Instantly, call its API, or send anything. The user pastes the prompt themselves.

Reading the user's public website is part of intake when you can open a page. Treat what you read as candidates. A finding enters the brief only after the user confirms it.

This skill replaces `pulse-agent-setup-prompt`. It writes the agent setup, the Knowledge Base, and an integration step.

Do not write the prompt, fill `template.md`, or run `make_prompt.py` until the user confirms the brief in section 2. If they ask you to skip the questions, ask the next open question anyway.

## 1. Grill for the brief

Ask one focused question, then stop and wait. A tight batch is allowed only where this section says so. Do not send the full list in one message.

If the user already answered an item in concrete terms, do not ask it again. Use their words. If they said to leave an item open, park it as a gap and move on.

Push back on a vague answer. Ask again until it is concrete, or until they tell you to leave it open. A repeated vague phrase is still vague. Do not copy it into the brief. Park a placeholder, and make them accept that gap in section 2.

When they have none, or they will not share, record the matching line from the list below, word for word. Never invent a price, a guarantee, a number, a testimonial, a logo or a case study. Never turn "none" into "use whatever is on the website".

### Lines to record when they have none

- Website: `none: do not add a website source`
- Price: `not shared: do not quote a price`
- Guarantee: `none: do not state a guarantee or a risk reversal`
- Case studies: `none: do not claim results, name clients, or use numbers`
- Testimonials: `none: do not quote anyone`
- Logos: `none: do not name logos`
- Objections: `none supplied: do not invent an objection handling`
- Competitors: `none: do not name competitors`
- Difference: `none supplied: do not invent a comparison`
- Words to avoid: `none named`
- Never say: `none named: still do not invent promises, prices, guarantees or results`
- Handoff: `none supplied: do not invent a handoff. Keep approval on.`
- Disqualifiers: `none supplied`
- Key pages: `none given`
- Files: `none`

### What concrete means

| Item | A concrete answer | Ask again when you hear |
|---|---|---|
| Industry or niche | independent dental practices | businesses, companies, B2B |
| Company size | 10 to 50 employees, or a revenue range | SMBs, mid-market, with no range |
| Geography | United States and Canada | everywhere, global, with no countries |
| Buyer titles | owner and office manager | decision makers, stakeholders |
| Buy trigger | they just opened a second location | when they need help |
| Disqualifiers | under 5 employees, or already on a retainer | bad fits |
| Offer | monthly bookkeeping with a named bookkeeper | we help companies grow |
| Price | a price or a range they will let the agent quote, or the none line | depends, competitive |
| Guarantee | the exact terms they offer, or the none line | we stand behind our work |
| Proof | a result they supplied, with their number, or the none line | great results, we have case studies |
| Testimonial | the quote they said the agent may use, or the none line | people love us |
| Logo | a name they said the agent may use, or the none line | well-known brands |
| Objection | the objection and the reply they want | price, with no reply |
| Competitors | names they said the agent may use, or the none line | the usual ones |
| Difference | one concrete line, or the none line | better service |
| Booking link | a full URL | I'll send it later, until they park the gap |
| Tone | short, plain, and calm | professional, normal |
| Words to avoid | a list, or the none line | you know |
| Never say or promise | at least one banned claim | nothing, until they accept the none line |
| Handoff | the lead replies, asks for a price, or books | when it makes sense |

### Website first

Ask for the company name and the website together, then stop. If they have no website, record `none: do not add a website source`.

Then read the site if you can:

- Open the homepage. Follow links to pricing, case studies or customers, and booking or contact.
- If a page does not open, say so. That missing page is a gap, not a guess.
- If you cannot open pages at all, say so in one line and ask them to paste the pricing, case study, and booking URLs.

In the next message, list what you found. One line per finding, each with its URL. Ask them to confirm, correct, or reject each line. Ask for any of those URLs you still do not have.

Do not put a finding in the brief until they confirm it. A number, a quote, a logo, a price or a guarantee on the site is not proof the agent may use until they say so.

### Then the rest, in this order

Skip an item only when it is already concrete, or they parked it.

1. Industry or niche.
2. Company size and geography, as one batch.
3. Buyer titles.
4. What triggers them to buy.
5. Disqualifiers.
6. What they sell: the deliverable, the form, and who does the work.
7. Price or range. If they will not share it, record the price none line.
8. Guarantee or risk reversal, exact terms. If they have none, record the guarantee none line. Do not draft one.
9. Case studies and results, with the numbers they supply. If they have none, record the case-study none line and tell them the agent will not claim results.
10. Testimonials and logos, as one batch. Same rule: their words, or the none line.
11. Top objections and the reply they want for each.
12. Competitors they will let the agent name, and the difference, as one batch.
13. The booking link, if they have not already confirmed it.
14. Tone, and words to avoid, as one batch. You may offer a starter avoid list (synergy, revolutionary, game-changer, unlock, circle back) and ask them to add or remove words. Use the list only after they confirm it.
15. What the agent must never say or promise.
16. When the agent must stop and hand the lead to a person.
17. Where company knowledge lives: Notion, Granola, Google Drive, or none. What the agent should learn from it. Files they will upload (sales deck, case studies, one-pager).

If they answer none for 17, say that connecting Notion or Granola keeps the agent current every day, and write the prompt with "Notion or Granola" so Copilot shows them where to connect one. Google Drive is listed as coming soon in Instantly. Keep it if they pick it. The prompt tells Copilot to skip it if it is not there yet.

## 2. Readiness check

When every item is concrete or parked, send one message and stop. Do not include the prompt.

Use this shape. Fill it with their confirmed words and the none lines. Leave a parked item as its square-bracket placeholder from `template.md`. Do not paste a vague phrase in as if it were a fact.

```text
Brief

Company
- Company:
- Website:
- Key pages:

Who we sell to
- Industry or niche:
- Company size:
- Geography:
- Buyer titles:
- Buy trigger:
- Disqualifiers:

Offer
- What you sell:
- Price:
- Guarantee:

Proof
- Case studies and results:
- Testimonials:
- Logos:

How we sell
- Objections and replies:
- Competitors:
- Difference:
- Booking link:
- Tone:
- Words to avoid:
- Never say or promise:
- Handoff:

Sources
- Files:
- Knowledge lives in:
- What the agent should learn from it:

Gaps
- One line per parked item, saying what the agent will not invent because of it. Or "None."
```

Ask them to reply yes to build the prompt, or to name what to change. If a gap is listed, yes means they accept it.

Wait. Build only when the latest reply confirms the brief and does not change a fact. If they change a fact, update the brief, show this check again, and wait. A yes that also edits a line is a change, not a confirmation.

They may accept a missing fact: price withheld, no guarantee, no proof, no testimonial, no logo, no files, no integration, a page they do not have, a booking link not ready. A vague ICP, a vague offer, or a vague handoff stays a placeholder. Do not write the vague phrase into the prompt.

## 3. Write the prompt

Only after that yes.

Write the confirmed answers to `sales-agent-brief.json` (this name is gitignored). Use the field names `company`, `website`, `pages`, `icp_industry`, `icp_size`, `icp_geo`, `titles`, `triggers`, `disqualifiers`, `offer`, `pricing`, `guarantee`, `proof`, `testimonials`, `logos`, `objections`, `competitors`, `differentiators`, `booking`, `tone`, `avoid`, `never_say`, `handoff`, `files`, `integration`, `integration_content`.

For an accepted blank, leave the value empty so the square-bracket placeholder stays. For a none they confirmed, store the none line word for word. `integration` is `notion`, `granola`, `google-drive`, or `none`.

From this skill's folder, run:

```bash
python3 make_prompt.py --brief-file sales-agent-brief.json --no-ask --out ai-sales-agent-setup-prompt.txt
```

`--no-ask` is required here because the grill already happened. Do not use the script's own questions as a substitute for section 1.

If you cannot run Python, copy the block in `template.md` and replace each {{FIELD}} yourself. Same values, same none lines.

Keep the rest of the prompt word for word. It keeps everything in draft, leaves autopilot off, has the user sign in to the integration themselves, and holds the first 10 leads for the user to approve. Those safety lines must stay.

The prompt slots the brief into the agent instructions: who to target, who to skip, the offer, the price, the guarantee, the only proof, the objections, the competitors, the difference, the booking link, the tone, the banned words, the banned promises, and the handoff. Do not drop a confirmed fact on the way into the file.

## 4. Hand it over

Give the user the finished prompt in one copyable block, then four lines:

- Open Instantly, open Copilot, paste the whole prompt and send it
- Copilot shows you where to upload your files and connect your integration. You sign in yourself; never paste a password or key into the chat
- Copilot reads back what it learned and waits for your OK. Check it before you say yes
- Steps marked [check in your workspace] may use a different menu name in your account. If Copilot can't do one, it tells you where to click

Then list any placeholders still in square brackets, and any none lines, so they can see what the agent will refuse to claim.

## Rules

- Only the user's own facts go in the prompt, plus site findings they confirmed.
- Never invent stats, guarantees, case studies, testimonials, logos, prices or client names.
- If proof is none, the prompt must tell the agent not to claim results.
- If there is no guarantee, the prompt must tell the agent not to state one.
- Do not change the draft-only, autopilot-off, sign-in-yourself and approve-by-hand lines.
- Do not promise results, quote prices or credit costs. If asked about cost, say to check pricing in their Instantly account.
- Do not commit `sales-agent-brief.json` or the generated prompt. Both can hold the user's customer details.
