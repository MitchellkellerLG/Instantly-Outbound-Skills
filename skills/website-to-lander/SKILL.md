---
name: website-to-lander
description: Builds a walkthrough lander from a website, in two modes. personal: one page per prospect who replied to a lead magnet, in their brand. general: one reusable page per campaign, in your brand, around a VSL or a case study of another client. Writes a ready-to-paste Instantly Copilot prompt for the page (the default handoff), plus a per-reply workflow prompt (personal) or a linking note (general). Files only; never deploys or sends. Use for "website to lander" or "Copilot prompt for a lander".
---

# Website to lander

- **Use this when:** a prospect replied to a lead-magnet campaign and needs their own page (personal), or a campaign needs one page every lead can open: your VSL or a case study on how you helped another client (general).
- **You get:** `prompt.md`, a ready-to-paste Instantly Copilot prompt that builds the page in the prospect's brand (banner, hero with video, booking button under the video, on-the-call card, deliverables, sourced proof, closing band, exit popup). Copilot builds the page; the prompt is the default handoff. Also `workflow-prompt.md`, a Copilot prompt that sets up an Instantly workflow building one page per positive reply from the same template. Also one self-contained `index.html` of the same page, and `brand.json` showing where every pulled fact came from. With `clone`, one folder with `prompt.md`, the page and `handoff.md` per replied prospect.
- **Run it:** say "build the lander for <website>" with the mode, the deliverable, your booking link and your case-studies link. With no mode given, ask which one (below).

## Pick a mode first

| Mode | Pick it when | Brand | Per lead | Prompts |
|---|---|---|---|---|
| `personal` (default) | A prospect replied and asked for a one-of-one deliverable ("send me the 5 creatives"). The page is about them. | The prospect's, read from their site | A whole page per prospect, only after a reply | `prompt.md` (the page) and `workflow-prompt.md` (a workflow that builds one per positive reply) |
| `general` | The same thing goes to every lead: a VSL, or a document on how you helped another client. You want one page for the campaign, not one per prospect. | Yours, read from your own site | Nothing but optional `?first_name=` and `?company=` in the link, which fill `merge_eyebrow` and `merge_popup_eyebrow` | `prompt.md` (the page) and `linking.md` (how to link it from the campaign or a reply; no workflow) |

If unsure, ask: "Is this page one-of-one for a prospect who replied, or one page for every lead in the campaign?" `extract --mode general` reads your own site and writes a general starter; `sections.json` carries `"mode"`. A general page needs `vsl_url` or `case_study_url` (with `case_study_title`; `case_study_summary` optional); the case-study card takes the video's place. `clone` is personal only.

Booking rate is the hard part of any lead magnet. A Drive link hands over the freebie and leaves them nowhere to go. A page on your own domain, built in their brand and offering a walkthrough of what you are making them, is what books the call, often before the deliverable is even ready.

## Hard rules

- **Structure only from the template.** The page reuses the layout in `templates/lander.html` (banner, sticky header, two-column hero, proof cards, dark closing band), its type scale and spacing, and its exit-popup behavior. If you modelled the layout on another company's page, add that page's names, product words and URLs to `FORBIDDEN` in the script: `check` refuses `sections.json`, `verify` refuses a page and `prompt` refuses a prompt that contains any of them. If the prospect's own name or site trips the list, stop and say so; do not loosen the list to get a build.
- **Nothing invented.** Brand facts come from the site and sit in `brand.json` with their source. Every proof point names where it came from (`proof[].source`: the page URL or "our case study: <name>"). Never write a result, a review or a number the site or your case studies do not show. The Copilot prompt carries the same rule: it gives Copilot the copy word for word and tells it not to invent results, reviews, numbers or names.
- **Their brand, your page.** A general page is in your own brand and its footer reads "A walkthrough page by <from_name>."; it never shows a lead's name, logo or brand beyond the merge tags. On a personal page the footer always says the page was prepared for the brand by you (`from_name`), and that their names and marks belong to them. The page carries `noindex`, and the prompt tells Copilot to set both. Never present it as the brand's own site.
- **Only after a reply.** A personal page is for a prospect who replied, not for a list; a list gets one general page. `clone` skips and names every entry without `replied_at`.
- **Files only.** The script reads public pages with GET and writes files. It never deploys, publishes, creates a Pages project, touches DNS, changes an Instantly workspace or website, sends anything or places a call. Putting the page live is a person's step, each time.
- No real prospect or customer data in this repo. Run folders live outside it; the fixture and example are synthetic.

## The loop

| # | Step | Do |
|---|---|---|
| 1 | Extract | `python3 scripts/website_to_lander.py extract <url> --out DIR [--mode general] --deliverable "5 ad creatives" --booking-url <link> --case-studies-url <link>`. Personal reads the prospect's site; general reads your own. DIR is outside this repo. Writes `brand.json`, `logo.<ext>` when one is found, and a starter `sections.json` with `TODO:` marks. A site that blocks the fetch: save the page from a browser and pass `--html FILE`. |
| 2 | Confirm the brand | Open the live site (or a screenshot of it) next to `brand.json`. Colors are ranked candidates, not a verdict: set `brand.primary_color` to the color the site uses for its buttons or main accent. Check the logo file is their logo; clear `brand.logo` to fall back to a wordmark. Fonts the site hosts itself are named but not loaded (they are licensed to the brand), so the page falls back to a system font; Google Fonts load. |
| 3 | Fill the sections | Edit `DIR/sections.json`: pick `best_product` from `product_candidates`, write the headline, subhead, lede, CTA line, the three "on the call" lines and the popup pitch in plain words, and keep only proof you can source. The fields are below. |
| 4 | Check | `python3 scripts/website_to_lander.py check DIR` until `ok`; say each `note:` (a missing VSL shows a placeholder: record it before sending the link). |
| 5 | Prompt | `python3 scripts/website_to_lander.py prompt DIR` writes `DIR/prompt.md`, the Instantly Copilot prompt for the page: every part in order with the copy from `sections.json`, the brand colors and font, the footer and `noindex` rules and the popup timing. It refuses a `TODO` or a reference string. This is the default handoff: paste it into Instantly Copilot and Copilot builds the page. It also writes `DIR/workflow-prompt.md` (personal, below) or `DIR/linking.md` (general: the link with UTM and merge tags, and where it goes). |
| 6 | Build | `python3 scripts/website_to_lander.py build DIR` writes `DIR/index.html`, the same page as one self-contained file, and verifies it. `verify FILE` rechecks any page. Use it to check Copilot's page against, or where Copilot is not on the workspace. |
| 7 | Look | Open `DIR/index.html` (or the page Copilot built) in a browser at desktop and phone width. Add `?preview=exit` to see the built page's popup at once (preview never stores anything). |
| 8 | Clone (many prospects) | List the filled run folders in one file (`templates/clone.example.json`), adding `replied_at` as each prospect replies. `python3 scripts/website_to_lander.py clone LIST.json --out OUT` checks every folder first and writes nothing on any `error:`; then it writes `OUT/<slug>/prompt.md` (the Copilot prompt), `OUT/<slug>/site/index.html` (the folder you host on the fallback) and `OUT/<slug>/handoff.md`. |
| 9 | Hand off | The person who puts it live follows `handoff.md` in order: host the page (below), reply in the same thread, then the same-day calls. |

## The page

The prompt and the built page carry the same parts, in this order: banner, header, hero with the video, booking under the video, the on-the-call card, the deliverables line, proof, the closing band, the footer and the exit popup.

| Element | What it does | From `sections.json` |
|---|---|---|
| 1. Announcement banner | Top bar, one line plus a link to your case studies and past work for brands like theirs. Dismissible; the dismiss is kept in localStorage. | `banner_text`, `banner_link_text`, `case_studies_url` |
| 2. Hero with VSL slot | Eyebrow, headline, subhead and lede on the left; the video on the right (under the headline on a phone). YouTube (watch, youtu.be, shorts, live), Vimeo (unlisted hash kept) and Loom links and any https embed link become embeds, an https `.mp4`, `.webm` or `.mov` a player, nothing a placeholder; `check` refuses any other link. | `eyebrow`, `headline`, `subhead`, `lede`, `vsl_url`, `vsl_caption` |
| 3. Booking CTA under the video | The sentence that says what the call gets them, then the button. Also in the header and the closing band. | `cta_line`, `cta_button`, `booking_url`, `call_gets_title`, `call_gets` |
| 4. Proof | Cards, each with its source. | `proof_title`, `proof_intro`, `proof[]` (`text`, `source`) |
| 5. Exit-intent popup | Pitches the walkthrough, not only a time; one button to the booking link. The body opens with the call length ("15 minutes on a call."). | `popup_eyebrow`, `popup_title`, `popup_body`, `popup_cta`, `call_length` |

Brand: `brand.name`, `brand.logo` (a file in DIR, an https URL, or empty for a wordmark), `brand.primary_color` (every other color is derived from it with readable contrast), `brand.font_family`, `brand.font_css_url` (Google Fonts only). Also `slug` (names the localStorage keys), `best_product`, `deliverable`, `final_title` (closing band), `from_name` (footer) and `call_length` (default "15 minutes"; set once, it is the length in the popup, the reply and the call opener so they always match).

**Popup rules** (built into the template, enforced by `verify`):

- Desktop (a mouse and a window at least 900px wide): fires when the mouse leaves through the top of the window, after 8 seconds on the page.
- Mobile: fires on an upward scroll of more than 80 pixels after 25 seconds, or after 75 seconds on the page.
- At most once per 7 days in the same browser. Closing it (button, Escape or the backdrop) stores the dismiss in localStorage; a click on any booking link suppresses it there for good.

## One page per positive reply: the workflow prompt (personal)

`prompt` also writes `workflow-prompt.md`: paste it into Instantly Copilot to set up an Instantly workflow that builds a page for every positive reply from this run folder's page as the template.

- Trigger: Instantly, Lead Interest Status Changed, interest status Interested; any positive label is the variant.
- Steps: read the lead's first name, company, website and email from the trigger; Copilot builds the page from the template with the lead's company, their website's logo, color, font and lead product, the deliverable and your booking link; then the page link goes to the team in Slack for the reply.
- The template is the run folder's copy with the prospect's name swapped for `{company}` and `best_product` for `{best product}`; write the rest of the copy so it fits any lead in the campaign. Proof comes only from each lead's own website, with its source, or the section is left out.
- Steps that may look different in your workspace (the Copilot website step, where it outputs the page link, the any-positive-label trigger) are marked `[check in your workspace]`.
- The prompt asks for a Draft that stays off and never sends the reply: turning it on is the operator's step, and a person sends each reply (below).

## Host it: in Instantly or off Instantly on Cloudflare Pages

The page is one self-contained HTML file (styles and script inline, the logo embedded). `handoff.md` prints these steps filled in for each prospect. Putting it live is a person's step; this skill never does it. [The hosting guide](references/hosting.md) walks through both options, including a Cloudflare Pages upload with no command line and keeping the page out of search results.

**Instantly website (first choice).** The websites feature is behind a feature flag on some workspaces and has no public API or instantly-cli route, so a person builds the site in the Instantly web app:

1. Open the websites feature and create one site per replied prospect, named after the prospect's slug.
2. Paste the whole `prompt.md` into Instantly Copilot and let it build the page. Check what it built against the parts above (banner and case-studies link, hero and VSL, the line and button under the video, the on-the-call card, proof with sources, closing band, footer, exit popup) and fix any part it missed or reworded. No Copilot on the workspace: paste `index.html` into a custom HTML block if the editor takes one, or rebuild the parts from `sections.json`. If the page ends up with no exit popup, say so and use the Cloudflare page for that prospect instead.
3. Open the published site once at desktop and phone width (`?preview=exit` shows the popup), then use its URL plus `?utm_source=instantly&utm_medium=email&utm_campaign=<campaign>` as the page link in the reply.

**Off Instantly: Cloudflare Pages** (documented, never run here). One project and subdomain per page; needs a free Cloudflare account with your domain on it. Upload the `site` folder in the dashboard (see [the hosting guide](references/hosting.md)), or with `npx wrangler login` once:

```bash
npx wrangler pages project create <from_name>-<slug> --production-branch main
npx wrangler pages deploy OUT/<slug>/site --project-name <from_name>-<slug> --branch main
```

Then in the Cloudflare dashboard: Workers & Pages > the project > Custom domains > Set up a custom domain > `<slug>.<domain>`. The page keeps its `noindex` tag wherever it is hosted. Delete a prospect's project when the deal closes or goes cold.

## The reply (right away, in the same thread)

> Thanks {first_name}, we're prepping your {deliverable} now, here's where they'll be: {page link}
>
> The fastest way to use them is a quick call, {call_length}, where I walk you through your {deliverable} and how I'd run them for {brand}. Would {time 1} or {time 2} work? Or grab a time here: {booking link}

With no `first_name` it opens "Thanks," and the call opener "Hi,". Mark the lead Interested. The page link carries the UTM tags so visits tie back to the campaign; keep Instantly link tracking off. The page often books the call before the deliverable is ready.

## Call the same day

Only people who replied get called; a fresh reply is the warmest that lead will get. `handoff.md` has the times in UTC.

| Dial | When | How |
|---|---|---|
| 1 | 15 minutes after the reply | double dial: call, and if no answer call straight back |
| 2 | 1 hour after the reply | double dial |
| 3 | 4 hours after the reply | double dial |

Open with what the call gets them (the first `call_gets` line), not with the pitch. A voice agent can take the first dials only where the AI calling rules for you and the lead allow it; check them first.

## Make the reply agent book from the page

Give the AI agent answering replies these rules (in your Instantly reply agent's instructions, or as AI Sales Agent guidance rules):

1. A "send it" or "yes" to the magnet is Interested. Reply in the same thread right away with the prospect's page link, never a Drive link or an attachment.
2. Say it is being prepped, never that it is done, and name what the call gets them.
3. Offer two specific times in their time zone plus the booking link.
4. Hand the reply to a person: build the page (this skill) and start the same-day dials.

## Demo

[The Loom runbook](references/loom-runbook.md) records the whole flow in about 5 minutes from synthetic brands, offline.

## How this chains

- Runs after a reply on a lead-magnet campaign (personal) or before a campaign launches (general). The reply agent or the person answering sends the link.
- Pairs with [`ai-sales-agent-setup-prompt`](../ai-sales-agent-setup-prompt/SKILL.md): the AI Sales Agent books the call, this page is where the link in the email goes.

## Testing

Offline; the site is a synthetic saved page.

```bash
python3 -m pytest skills/website-to-lander/scripts/test_website_to_lander.py -q
python3 skills/website-to-lander/scripts/website_to_lander.py extract https://fernhill.example --html skills/website-to-lander/evals/fixtures/fernhill-site.html --out /tmp/wtl
cp skills/website-to-lander/templates/sections.example.json /tmp/wtl/sections.json
python3 skills/website-to-lander/scripts/website_to_lander.py prompt /tmp/wtl
python3 skills/website-to-lander/scripts/website_to_lander.py build /tmp/wtl
```

`/tmp/wtl/prompt.md` and `/tmp/wtl/workflow-prompt.md` match `evals/fixtures/fernhill-prompt.md` and `evals/fixtures/fernhill-workflow-prompt.md`, the expected prompts for the synthetic brand. For general mode, `templates/sections.general.example.json` (a synthetic sender) gives `evals/fixtures/general-prompt.md` and `general-linking.md`. The tests and CI check all four.

The clone flow on synthetic brands is in the [Loom runbook](references/loom-runbook.md), "Before you hit record".

## Feedback

If this skill makes a mistake, you hit a problem or want a feature, open an issue on this repo. Leave out real prospect names, emails and links.
