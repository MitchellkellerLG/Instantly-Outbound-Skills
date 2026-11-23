Build a one-page website: Northwind Creative's own walkthrough page, one page for every lead in a campaign.
A lead lands on it from an email or a reply to see the case study on how we rebuilt a sock brand's paid social. Its one job is to get them to book a walkthrough call (15 minutes).
Every button on the page links to https://agency.example/book/walkthrough.

Rules:
- Use only the copy below, word for word. Do not invent results, reviews, numbers, testimonials, client logos or customer names, and do not add sections beyond the ones listed.
- Each proof point shows its source under it, as written.
- In the page settings, hide the page from search engines (noindex, nofollow).
- The footer always reads: "A walkthrough page by Northwind Creative."
- It is one reusable page in our own brand: no lead's name, logo or brand on it, except the merge lines below.

Brand:
- Logo: none. Show the name Northwind Creative as a text wordmark in the header.
- Colors: main #3a4fd6 for buttons and accents, with #ffffff button text. Page background #f8f9fe, text #11141c, muted text #5d5f65. The closing band is #151b3a with #7584e2 accents.
- Font: Inter (Google Fonts) for headings and body.
- Light layout, rounded cards, generous spacing.

Sections, top to bottom:
1. Announcement banner: a thin dismissible bar across the top.
   - Text: "We make paid social creative for apparel and outdoor brands."
   - Link: "See the case studies" to https://agency.example/case-studies
2. Header, sticky: the logo on the left, and on the right a small version of a button "Book the walkthrough" linking to https://agency.example/book/walkthrough.
3. Hero, two columns (on a phone, stacked with the case-study card right under the headline).
   - Left, eyebrow: "A 5-minute read"
   - Left, headline: "How a sock brand doubled its return on ad spend in 60 days"
   - Left, subhead: "The angles, the hooks and the testing plan behind Fernhill Socks' new creative."
   - Left, paragraph: "The case study walks through what we changed and in what order. On the call we map the same plan to your shop."
   - Right: a case-study card titled "Fernhill Socks: 2x return on ad spend in 60 days" with the line "Five new creatives, two angles that won, one testing plan." and a button "Read the case study" linking to https://agency.example/case-studies/fernhill-socks
4. Booking, directly under the case-study card:
   - The line: "Grab a time and I'll walk you through how we'd run the same plan for your shop."
   - Then a large version of a button "Book the walkthrough" linking to https://agency.example/book/walkthrough
5. On-the-call card, next to or under the booking block, titled "On the call":
   - "The three angles we would test first for you"
   - "The budget and timeline for the first test"
   - "What we would need from your team"
6. Deliverables: a short card titled "What you are getting" that says "the case study on how we rebuilt a sock brand's paid social"
7. Proof, titled "Results we can show".
   - One card per point:
     - "Return on ad spend went from 1.6 to 3.2 in 60 days." with its source under it: our case study: Fernhill Socks
     - "Cost per purchase fell 41% on the winning angle." with its source under it: our case study: Fernhill Socks
8. Closing band: a dark full-width panel with the line "Want the same plan for your shop? The walkthrough is where it starts." and a button "Book the walkthrough" linking to https://agency.example/book/walkthrough.
9. Footer: the line from the rules above.

Exit-intent popup, one modal:
- Eyebrow: "Before you go"
- Title: "Want the plan we used, mapped to your shop?"
- Body: "15 minutes on a call. We go through the case study and the first test we would run for you."
- One button: "Book the walkthrough" linking to https://agency.example/book/walkthrough
- Desktop: opens when the mouse leaves through the top of the window, after 8 seconds on the page.
- Phone: opens on an upward scroll of more than 80 pixels after 25 seconds, or after 75 seconds on the page.
- At most once per 7 days in the same browser. Closes with the X, the Escape key or a click on the backdrop. Once closed, or once any booking button is clicked, it does not open again.

Merge tags from the link (the only per-lead parts):
- The page link may carry ?first_name= and ?company=. Fill them in as plain text, at most 60 characters each, never as HTML.
- The eyebrow: when the link has every tag in "Prepared for {company}", show that line with them filled in; otherwise show "A 5-minute read".
- The popup eyebrow: when the link has every tag in "Before you go, {first_name}", show that line with them filled in; otherwise show "Before you go".
