# The prompt template

`make_prompt.py` fills the {{FIELDS}} inside the block below. You can also copy the block by hand and replace each {{FIELD}} yourself.

Use only facts the user supplied or confirmed. Do not invent a number, a price, a guarantee, a testimonial, a logo or a case study. If they do not have one, paste the matching line below so the agent does not claim it.

- {{WEBSITE}}: `none: do not add a website source`
- {{PRICING}}: `not shared: do not quote a price`
- {{GUARANTEE}}: `none: do not state a guarantee or a risk reversal`
- {{PROOF}}: `none: do not claim results, name clients, or use numbers`
- {{TESTIMONIALS}}: `none: do not quote anyone`
- {{LOGOS}}: `none: do not name logos`
- {{OBJECTIONS}}: `none supplied: do not invent an objection handling`
- {{COMPETITORS}}: `none: do not name competitors`
- {{DIFFERENTIATORS}}: `none supplied: do not invent a comparison`
- {{NEVER}}: `none named: still do not invent promises, prices, guarantees or results`
- {{HANDOFF}}: `none supplied: do not invent a handoff. Keep approval on.`

For {{INTEGRATION}} write the tool that holds the company knowledge: Notion, Granola or Google Drive. For {{INTEGRATION_CONTENT}} write what the agent should learn from it, for example "the Notion pages about our product, pricing, customers and case studies" or "my sales and customer call notes". If they don't use any of them yet, write "Notion or Granola" and "the pages or call notes I pick when I connect it".

Lines marked [check in your workspace] are menu names that may look different in your Instantly account. Copilot will tell you if it can't find one.

```text
Set up an AI Sales Agent for my company, powered by PULSE-1, and teach it my business through the Knowledge Base. Keep everything in draft: do not launch anything, do not send any email, do not attach sending accounts and do not turn on autopilot.

The facts below are the only facts you may use about my company. Do not invent stats, guarantees, case studies, testimonials, logos, prices, client names or promises. If a line says none, or still has a placeholder in square brackets, leave that point out.

About my company
- Company: {{COMPANY}}
- Website: {{WEBSITE}}
- Key pages (pricing, case studies, booking): {{PAGES}}
- What we sell: {{OFFER}}
- Price: {{PRICING}}
- Guarantee or risk reversal (exact terms only): {{GUARANTEE}}

Who we sell to
- Industry or niche: {{ICP_INDUSTRY}}
- Company size: {{ICP_SIZE}}
- Geography: {{ICP_GEO}}
- Buyer titles: {{TITLES}}
- What triggers them to buy: {{TRIGGERS}}
- Disqualifiers (skip these leads): {{DISQUALIFIERS}}

Proof we are allowed to use
- Case studies and results: {{PROOF}}
- Testimonials: {{TESTIMONIALS}}
- Logos we may name: {{LOGOS}}

How we sell
- Top objections and how we handle them: {{OBJECTIONS}}
- Competitors we may name: {{COMPETITORS}}
- How we are different: {{DIFFERENTIATORS}}
- Call to action: a booked call at {{BOOKING}}
- Tone: {{TONE}}
- Words to avoid: {{AVOID}}
- Never say or promise: {{NEVER}}
- When to hand off to a human: {{HANDOFF}}
- Files I will upload: {{FILES}}
- Where the rest of our knowledge lives: {{INTEGRATION}}

Step 1. Build my Knowledge Base
- Add {{WEBSITE}} to my Knowledge Base as a source and set it to refresh weekly, unless that line says none [check in your workspace: the Knowledge Base, or "Teach Instantly AI about your business"].
- Add these pages as sources too, unless that line says none given: {{PAGES}}.
- Show me where to upload files, then wait while I upload these: {{FILES}}. If that line says none, skip the upload. Otherwise tell me when you can see them.
- The case studies, testimonials, logos, price and guarantee above are the only proof and promises the agent may use. Do not add a stat, a quote, a logo, a price or a guarantee you find on the site unless it is already written above.

Step 2. Connect {{INTEGRATION}} so my knowledge stays up to date
- Show me where to connect {{INTEGRATION}} to my Knowledge Base, and wait while I connect it [check in your workspace: "Teach Instantly AI about your business", under integrations]. I sign in and approve access myself. Never ask me for a password or API key.
- Once it is connected, add only this as a source: {{INTEGRATION_CONTENT}}. Set it to sync daily if that option is there.
- If {{INTEGRATION}} is not available in my workspace yet, say so, skip this step and go on. I can connect it later.

Step 3. Check what you learned
- Tell me in short lines: what we sell, who it is for, the buy trigger, the disqualifiers, the price you may quote, the guarantee you may state, the proof you may use, which sources you used, and anything you could not find.
- If any line is richer than the facts above, cut it back. Do not add a stat, a guarantee or a case study that is not in the facts above.
- If the Knowledge Base lists what is still missing, show me that list [check in your workspace: "What's still missing"]. Do not fill the gaps with guesses; I will answer them or add a source.
- Wait for my OK before step 4.

Step 4. Create the agent
- Create a new AI Sales Agent aimed at the people above. Sell only this: {{OFFER}}. Its one goal is a booked call at {{BOOKING}}. It uses the facts in this prompt and the Knowledge Base for every email.
- Target only this industry: {{ICP_INDUSTRY}}. Company size: {{ICP_SIZE}}. Geography: {{ICP_GEO}}. Titles: {{TITLES}}. Buy trigger: {{TRIGGERS}}.
- Skip anyone who matches a disqualifier, even if they look like a good lead. Disqualifiers: {{DISQUALIFIERS}}.
- Make sure Pulse is turned on, so the agent ranks the leads and reaches out to the ones most likely to reply positively first [check in your workspace: the agent's settings, under lead quality].
- Keep approval on, so nothing goes out until I approve it. Autopilot stays off [check in your workspace: approval or autopilot setting].

Step 5. Guidance rules
Add these to the agent as guidance rules, word for word, one rule each [check in your workspace: guidance rules]:
1. Write like someone who knows this market. Tone: {{TONE}}. Short sentences, plain words. Do not use these words: {{AVOID}}.
2. The first line is about them (their company, their role, this buy trigger: {{TRIGGERS}}, or something on their site), never a compliment.
3. One ask per email: a short call at {{BOOKING}}. Lead with what they get, not with us.
4. At most 3 emails per lead. Every follow-up says something new. Never "just bumping this" and never repeat the first email.
5. Only use this proof. Case studies and results: {{PROOF}}. Testimonials: {{TESTIMONIALS}}. Logos: {{LOGOS}}. Never invent numbers, clients, logos, quotes or case studies. If any of those say none, do not claim results.
6. Quote a price only when it matches this line: {{PRICING}}. State a guarantee only when it matches this line, and only in these terms: {{GUARANTEE}}. Never invent a price, a guarantee, a risk reversal or a promised result.
7. Never say or promise any of this: {{NEVER}}.
8. Answer only these objections, and only in this way: {{OBJECTIONS}}.
9. Name a competitor only from this list: {{COMPETITORS}}. The only difference you may state: {{DIFFERENTIATORS}}.
10. Hand the lead to a human when this is true: {{HANDOFF}}. Stop the email thread once you hand it off.
11. Every email ends with a short, plain line that lets them opt out.

Step 6. First batch, approved by hand
- Prepare the first batch of 10 leads with their emails drafted, then stop.
- Show me each lead, one line on why it fits (industry, size, geography, title, buy trigger, and not a disqualifier), and the draft. I approve or skip each one myself [check in your workspace: where the agent's leads wait for approval].

Before you build anything, list what you are going to set up and anything that is missing, and wait for my OK. When you are done, tell me what is set up, what is still in draft, which Knowledge Base sources are connected and how often each one refreshes, and anything you could not do, with the exact place to click so I can do it myself.
```
