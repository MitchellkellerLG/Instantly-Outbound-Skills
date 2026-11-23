# The prompt template

`make_prompt.py` fills the {{FIELDS}} inside the block below. You can also copy the block by hand and replace each {{FIELD}} yourself.

Lines marked [check in your workspace] are menu names that may look different in your Instantly account. Copilot will tell you if it can't find one.

For {{INTEGRATION}} write the tool that holds your company knowledge: Notion, Granola or Google Drive. For {{INTEGRATION_CONTENT}} write what the agent should learn from it, for example "the Notion pages about our product, pricing, customers and case studies" or "my sales and customer call notes". If you don't use any of them yet, write "Notion or Granola" and "the pages or call notes I pick when I connect it".

```text
Set up an AI Sales Agent for my company, powered by PULSE-1, and teach it my business through the Knowledge Base. Keep everything in draft: do not launch anything, do not send any email, do not attach sending accounts and do not turn on autopilot.

About my company
- Company: {{COMPANY}}
- Website: {{WEBSITE}}
- What we sell (the offer): {{OFFER}}
- Who we sell to (ICP): {{ICP}}
- The people to email: {{TITLES}}
- Booking link: {{BOOKING}}
- Case studies and results we're allowed to use: {{PROOF}}
- Files I will upload: {{FILES}}
- Where the rest of our knowledge lives: {{INTEGRATION}}

Step 1. Build my Knowledge Base
- Add {{WEBSITE}} to my Knowledge Base as a source and set it to refresh weekly [check in your workspace: the Knowledge Base, or "Teach Instantly AI about your business"].
- Show me where to upload files, then wait while I upload these: {{FILES}}. Tell me when you can see them.
- Treat the case studies and results above as the only proof the agent may use.

Step 2. Connect {{INTEGRATION}} so my knowledge stays up to date
- Show me where to connect {{INTEGRATION}} to my Knowledge Base, and wait while I connect it [check in your workspace: "Teach Instantly AI about your business", under integrations]. I sign in and approve access myself. Never ask me for a password or API key.
- Once it is connected, add only this as a source: {{INTEGRATION_CONTENT}}. Set it to sync daily if that option is there.
- If {{INTEGRATION}} is not available in my workspace yet, say so, skip this step and go on. I can connect it later.

Step 3. Check what you learned
- Tell me in 6 short lines: what we sell, who it is for, the main problem it solves, the proof you found, which sources you used, and anything you could not find.
- If the Knowledge Base lists what is still missing, show me that list [check in your workspace: "What's still missing"]. Do not fill the gaps with guesses; I will answer them or add a source.
- Wait for my OK before step 4.

Step 4. Create the agent
- Create a new AI Sales Agent aimed at the ICP above. Its one goal is a booked call at {{BOOKING}}. It uses my Knowledge Base for every email.
- Let it find leads that fit the ICP and skip anyone who doesn't, even if they look like a good lead.
- Make sure Pulse is turned on, so the agent ranks the leads and reaches out to the ones most likely to reply positively first [check in your workspace: the agent's settings, under lead quality].
- Keep approval on, so nothing goes out until I approve it. Autopilot stays off [check in your workspace: approval or autopilot setting].

Step 5. Guidance rules
Add these to the agent as guidance rules, word for word, one rule each [check in your workspace: guidance rules]:
1. Write like someone who knows this market: short sentences, plain words, no hype words.
2. The first line is about them (their company, their role or something on their site), never a compliment.
3. One ask per email: a short call at {{BOOKING}}. Lead with what they get, not with us.
4. At most 3 emails per lead. Every follow-up says something new. Never "just bumping this" and never repeat the first email.
5. Only use proof from my Knowledge Base. Never invent numbers, clients, logos or quotes. If there is no proof for a point, leave the point out.
6. Never promise a result and never quote a price unless the Knowledge Base says it.
7. Every email ends with a short, plain line that lets them opt out.

Step 6. First batch, approved by hand
- Prepare the first batch of 10 leads with their emails drafted, then stop.
- Show me each lead, one line on why it fits the ICP, and the draft. I approve or skip each one myself [check in your workspace: where the agent's leads wait for approval].

Before you build anything, list what you are going to set up and anything that is missing, and wait for my OK. When you are done, tell me what is set up, what is still in draft, which Knowledge Base sources are connected and how often each one refreshes, and anything you could not do, with the exact place to click so I can do it myself.
```
