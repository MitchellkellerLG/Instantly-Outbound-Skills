# Linking the general page: Northwind Creative

One page for every lead in the campaign. No per-reply workflow and no page per lead: build it once with `prompt.md` in
Instantly Copilot, publish it, then link it. Nothing here sends anything; a person adds the link and sends.

1. The page link is the published URL plus `?utm_source=instantly&utm_medium=email&utm_campaign=<campaign>`.
2. Add the merge tags so the page greets the lead: append
   `&first_name={{firstName}}&company={{companyName}}`. Instantly fills `{{firstName}}` and `{{companyName}}` when it sends; send yourself a test
   preview and check the link opens with them filled in and encoded [check in your workspace]. A lead without the
   values sees the page as written.
3. Where to put it: in the campaign step that offers the case study on how we rebuilt a sock brand's paid social, or in the reply to a positive answer:
   > Here it is: <page link>. The fastest way to use it is a quick call, 15 minutes, where I walk you through it.
   > Grab a time here: https://agency.example/book/walkthrough
4. Keep Instantly link tracking off; the UTM tags tie visits to the campaign.
