# Put the page live

The page is one self-contained `index.html` (styles, script and logo inside it). You can host it in Instantly or off Instantly on Cloudflare Pages. Either way, putting it live is your step: the skill only writes files.

The page carries `<meta name="robots" content="noindex, nofollow">`, so search engines leave it out. Keep that tag wherever you host it. Personal pages are made for one prospect and should never show up in search.

## Option 1: in Instantly, with Copilot

Use this if your workspace has Instantly's websites feature (it is not on every workspace yet).

1. In Instantly, open the websites feature and create a site (personal: one per prospect, named after the slug; general: one per campaign).
2. Paste the whole `prompt.md` into Instantly Copilot and let it build the page. Check it against the parts in [SKILL.md](../SKILL.md) ("The page") and fix anything it missed or reworded.
3. Make sure the page is set to noindex. Copilot is told to set it; check the page settings [check in your workspace].
4. If the editor cannot do the exit popup, or you have no Copilot, use option 2 instead.
5. Open the published page at desktop and phone width, then use its URL with the UTM tags as the page link.

## Option 2: off Instantly, on Cloudflare Pages (free)

You need a free Cloudflare account. To use your own domain, the domain's DNS should be on Cloudflare too.

### Upload in the dashboard (no command line)

1. Build the page: `python3 scripts/website_to_lander.py build DIR` (or `clone`, which writes `OUT/<slug>/site/index.html`). Put `index.html` in a folder of its own. Leave out `brand.json`, `sections.json` and the prompts: everything in the folder goes public.
2. Optional, extra protection against search engines: add a file named `_headers` to the same folder containing these two lines:

   ```
   /*
     X-Robots-Tag: noindex
   ```
3. In the Cloudflare dashboard, open Workers & Pages, choose Create, then Pages, then upload your files (direct upload) [the button names may differ slightly]. Name the project (for example `<your-name>-<slug>`), drag in the folder and deploy. You get a `<project>.pages.dev` link.
4. Custom domain: open the project, then Custom domains, then Set up a custom domain, and enter a subdomain such as `<slug>.yourdomain.com`. Cloudflare adds the DNS record when the domain is on Cloudflare; otherwise it shows the CNAME to add at your DNS provider.
5. Open the page yourself once, on a phone too, before you send the link. Add `?preview=exit` to see the exit popup straight away.

### Or with the command line

```bash
npx wrangler login
npx wrangler pages project create <project> --production-branch main
npx wrangler pages deploy <folder with index.html> --project-name <project> --branch main
```

Then add the custom domain as in step 4.

### Clean up

A personal page is for one deal. Delete the project (project, Settings, Delete) when the deal closes or goes cold. A general page stays up for as long as the campaign runs.
