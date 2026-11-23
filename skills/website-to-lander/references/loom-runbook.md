# Loom runbook: the lead-magnet booking page

Keep this open on a second screen while you record. It takes about 5 minutes. Everything runs offline from files on disk; nothing is deployed or sent. The agency (Example Creative Co.) and all three brands (Fernhill Socks, Saltmarrow Swim, Quillfen Tea House) are made up.

## Before you hit record

1. Build the demo pages from the repo folder (synthetic brands, offline):

   ```bash
   D=/tmp/loom-pages
   S=skills/website-to-lander
   mkdir -p $D/fernhill-socks $D/saltmarrow-swim
   cp $S/templates/clone.example.json $D/list.json
   cp $S/templates/sections.example.json $D/fernhill-socks/sections.json
   sed -e 's/Fernhill Socks/Saltmarrow Swim/g' -e 's/fernhill-socks/saltmarrow-swim/' -e 's/fernhill\.example/saltmarrow.example/g' \
       -e 's/the Trail Merino Crew/the Tidewalk UV rash guard/g' -e 's/#2f6b4f/#1f5f8b/' \
       $S/templates/sections.example.json > $D/saltmarrow-swim/sections.json
   python3 $S/scripts/website_to_lander.py clone $D/list.json --out $D/out
   ```

   That rehearses step 3 below; you run the clone again on camera.
2. Open a **Chrome Incognito window** (Ctrl+Shift+N). The exit popup fires at most once per 7 days per page, and Incognito forgets that when you close it. Rehearsing in a normal window will use up the popup.
3. In the Incognito window, open these two tabs (paste each path into the address bar):
   - `file:///tmp/loom-pages/out/fernhill-socks/site/index.html`
   - `file:///tmp/loom-pages/out/saltmarrow-swim/site/index.html`
4. Open in your editor: `/tmp/loom-pages/list.json` and `/tmp/loom-pages/out/fernhill-socks/handoff.md`.
5. Have a terminal ready in the repo folder (the skill lives at `skills/website-to-lander/`).
6. Backup if the popup misbehaves live: add `?preview=exit` to the end of a page URL and it opens at once.

## The recording

1. **The problem (talking head or the Fernhill tab).**
   Say: "If your lead magnet gets replies but no booked calls, stop sending the freebie as a Google Drive link. They open it, look, and have no way to find out more about you. They almost never reply a second time. Booking rate is the number one struggle with any lead magnet."

2. **Show the reply list (`list.json`).**
   Viewer sees: the campaign, then three prospects. Two have a `replied_at` time; the third (Quillfen Tea House) does not.
   Say: "One page per prospect, built from their own website: their brand, their best product, the deliverable and our booking link. And we only build pages for people who replied, so we're not making pages nobody will see."

3. **Run the clone in the terminal.**
   Type: `python3 skills/website-to-lander/scripts/website_to_lander.py clone /tmp/loom-pages/list.json --out /tmp/loom-pages/out`
   Viewer sees: `built:` for Fernhill Socks and Saltmarrow Swim, and `skipped, no replied_at` for Quillfen.
   Say: "Two replied, two pages. Quillfen didn't reply, so no page. Each one is its own folder with its own handoff."

4. **Switch to the Fernhill tab. Walk the page top to bottom.**
   - Point at the **banner** at the top. Say: "A banner to case studies for brands like theirs, so if they want to know who we are, it's one click."
   - Point at the **headline**. Say: "Their brand, their best product - the Trail Merino Crew - and the 5 creatives we're prepping."
   - Point at the **video**. Say: "A short VSL on how we do the work, not just their free creatives. This is a placeholder; yours is a 2 minute Loom."
   - Point at the **line and button under the video**. Read it out: "Grab a time and I'll walk you through your 5 creatives and how I'd run them on your shop." Say: "The button says what the call gets them. Not 'book a call' - the walkthrough."
   - Scroll to the **proof**. Say: "Proof from their own site, each with its source. Nothing made up."

5. **Trigger the exit popup.**
   Do: wait about 8 seconds on the page, then move the mouse slowly up and out through the top of the browser window, past the tabs.
   Viewer sees: the page dims and the popup appears: "Want the walkthrough of your 5 creatives?" with one "Book the walkthrough" button.
   Say: "They'll get a notification halfway through reading and forget your email. This popup is your last shot, and it pitches the walkthrough too instead of just asking for a time. It fires once, and on a phone it fires on a scroll back up or after a while on the page."
   Do: press Escape to close it.

6. **Switch to the Saltmarrow Swim tab.**
   Viewer sees: the same layout, now in Saltmarrow Swim's color for the Tidewalk UV rash guard.
   Say: "Same structure, different prospect. The agent clones one the moment someone replies."
   Optional: shrink the window narrow (or open DevTools phone view, Ctrl+Shift+M) to show it on a phone.

7. **Show `handoff.md` (Fernhill), section 1: host the page.**
   Viewer sees: "Instantly website (first choice)" with the steps, then "Fallback: Cloudflare Pages".

8. **Host it in Instantly websites (the main path).**
   Needs a demo site you build in your workspace by pasting the prospect's `prompt.md` into Instantly Copilot, per the handoff steps (the websites feature has no API route, so nothing here creates it). Until it exists, skip to 8b.
   Do: in the Instantly app, open the websites area and the demo site for the fictional brand; open its live URL in a new tab.
   Viewer sees: the same five elements - banner, video, the walkthrough button, proof, and the exit popup if the editor supports it.
   Say: "We host it right inside Instantly, next to the campaign, so the page and the emails live in one place."
   If the Instantly editor can't do the exit popup, say so plainly: "Instantly's editor doesn't do exit popups yet, so for that one we use the Cloudflare version."

   8b. **Fallback: scroll to "Fallback: Cloudflare Pages" in `handoff.md`.**
   Viewer sees: two `wrangler` commands and the custom domain step.
   Say: "If you'd rather host it yourself, each page goes on its own subdomain with Cloudflare Pages. Two commands and one custom domain click." (Do not run them on camera.)

9. **Scroll to section 2, the reply.**
   Say: "The reply goes out right away: 'We're prepping your 5 ad creatives now, here's where they'll be', the page link on our own domain, then two times and the booking link. You'll start getting bookings off that link before the creatives even show up."

10. **Scroll to section 3, "Call the same day".**
    Viewer sees: three rows at 15 minutes, 1 hour and 4 hours after the reply, each "double dial", and the opener.
    Say: "Then call the same day, 3 times: 15 minutes, 1 hour, 4 hours after the reply, double dial every time. Open with what the call gets them: going through their creatives together and how you'd run them. A fresh reply is the warmest that lead will ever be. Can't staff the calls? A voice agent can take the first dials, just check the AI calling rules where you are first."

11. **The AI agent (close).**
    Open `skills/website-to-lander/SKILL.md` at "Make the reply agent book from the page".
    Say: "And the AI agent answering your replies gets the same rules: a 'send it' is Interested, reply right away with their page, never a Drive link, say it's being prepped, pitch the walkthrough, two times plus the link, and hand off for the calls."
    End: "If you're sending lead lists or strategy docs, put them on a page like this instead of attaching a file."

## After recording

- Close the Incognito window (resets the popup for next time).
- `rm -rf /tmp/loom-pages`.
