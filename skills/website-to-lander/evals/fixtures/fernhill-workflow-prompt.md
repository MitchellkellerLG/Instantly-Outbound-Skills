Set up an Instantly workflow (Automation) that builds a walkthrough page for every lead who replies positively,
from the template below. Save it as a Draft and leave it off: a person reviews it and turns it on.
The workflow never sends the reply: a person sends the page link in the same thread.

Trigger:
- Instantly, Lead Interest Status Changed, interest status Interested, all campaigns (or the lead-magnet campaign).
  To fire on any positive label instead, use the trigger for any positive label [check in your workspace].

Steps:
1. Read the lead from the trigger: first name, company name, website and email
   ({{trigger__lead.firstName}}, {{trigger__lead.companyName}}, {{trigger__lead.website}}, {{trigger__lead.email}}).
   No website on the lead: stop and post the lead to the team (step 3) without a page.
2. Build the page with Instantly Copilot [check in your workspace]: a new website named after the company, built from the template below.
   From the lead's website read only the logo, the main brand color, the font and the product the site leads with.
   Proof: only points the lead's own website shows, each with its source page under it; none found, leave the proof
   section out. Do not invent results, reviews, numbers, testimonials or names.
3. Return the page link for the reply: post it to the team's Slack channel (Slack, Send Message) with the lead's name,
   company and email, and a Unibox link to the thread. Where the website step outputs the page link [check in your workspace].
   The person then replies in the same thread: "we're prepping your 5 ad creatives now, here's where they'll be: <page link>".

Template (one page per lead; {company} is the lead's company name, {best product} the product their website leads with):
- Rules: use this copy word for word with those two filled in; where a line still names another company's product,
  use {best product} there instead. Hide the page from search engines (noindex, nofollow).
  Footer, always: "A walkthrough page prepared for {company} by Example Creative Co. {company} names and marks belong to their owner."
  The page is in the lead's brand but is not their website. Every button links to https://agency.example/book/walkthrough.
- 1. Announcement banner: "We make paid social creative for apparel and outdoor brands." with the link "See the case studies" to https://agency.example/case-studies
- 2. Header, sticky: their logo, and a small button "Book the walkthrough".
- 3. Hero, two columns: eyebrow "Prepared for {company}", headline "Your 5 ad creatives for {best product}", subhead "Five scroll-stopping ads built around what your customers already say about the Crew.",
     paragraph "We are prepping your creatives now. The video below shows how we pick the angles, shoot the hooks and test them, so you know what you are getting before the call."; on the right the video placeholder (the video is added before the link is sent), captioned "How we build and test the creatives, in 3 minutes".
- 4. Booking, directly under the video: "Grab a time and I'll walk you through your 5 creatives and how I'd run them on your shop.", then a large button "Book the walkthrough".
- 5. On-the-call card titled "On the call":
     - "Your 5 creatives, one by one, with the angle behind each"
     - "Which two to launch first and the budget to test them"
     - "How we would run them on your shop for the next 30 days"
- 6. Deliverables: a card titled "What you are getting" that says "5 ad creatives for {best product}".
- 7. Proof, titled "What {company} already has going for it": the lead's own sourced points (step 2).
- 8. Closing band, dark: "Your creatives are on the way. The walkthrough is where they start earning." and the button "Book the walkthrough".
- 9. Footer: the line from the rules.
- Exit-intent popup: eyebrow "Before you go, {company}", title "Want the walkthrough of your 5 creatives?", body "15 minutes on a call. We go through each creative, the angle behind it and how we would run the first test on your shop.",
  one button "Book the walkthrough". Desktop: the mouse leaves through the top after 8 seconds. Phone: an upward
  scroll of more than 80 pixels after 25 seconds, or 75 seconds on the page. At most once per 7 days; closes with
  the X, Escape or the backdrop.
