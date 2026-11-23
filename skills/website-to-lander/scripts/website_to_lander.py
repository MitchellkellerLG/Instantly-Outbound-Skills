#!/usr/bin/env python3
"""website-to-lander: read a company's public website and build its walkthrough lander.

    python3 website_to_lander.py extract https://example.com --out DIR [--mode personal|general] [--deliverable TEXT]
                                 [--booking-url URL] [--case-studies-url URL] [--html FILE]
    python3 website_to_lander.py check DIR
    python3 website_to_lander.py prompt DIR [--out FILE]
    python3 website_to_lander.py build DIR [--out FILE]
    python3 website_to_lander.py verify FILE
    python3 website_to_lander.py clone LIST.json --out DIR

extract reads the public site (one page, plus up to six of its stylesheets and its logo) and writes
DIR/brand.json (what the site says, with sources) and DIR/sections.json (the copy file the agent fills).
check lists what is still missing. prompt writes DIR/prompt.md, the Instantly Copilot prompt that builds the
page (the default handoff), and DIR/workflow-prompt.md, the Copilot prompt for a workflow that builds one per positive reply
(personal mode) or DIR/linking.md, how to link the one page from the campaign (general mode). build renders DIR/index.html, one self-contained page, and verifies it.
verify checks a built page: the five elements, the exit-popup rules and no reference-site strings.
clone builds one page per prospect who replied, from a list of filled run folders, into DIR/<slug>/site/index.html,
with DIR/<slug>/handoff.md: hosting (Instantly websites first, Cloudflare Pages as the fallback), the reply and the
same-day calls. Prospects without replied_at are skipped and named.

Standard library only. Reads public pages with GET; never posts, submits a form, deploys or sends.
"""

from __future__ import annotations

import argparse
import base64
import colorsys
import html
import json
import pathlib
import re
import sys
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser

SKILL = pathlib.Path(__file__).resolve().parent.parent
TEMPLATE = SKILL / "templates" / "lander.html"
UA = "Mozilla/5.0 (compatible; website-to-lander/1.0)"
MAX_PAGE = 3_000_000
MAX_CSS = 1_500_000
MAX_LOGO = 300_000
MAX_SHEETS = 6
# Stylesheets from widgets and checkout tools carry their own colors, not the brand's.
THIRD_PARTY_CSS = re.compile(r"fonts\.googleapis|shopifycloud|checkout|wallet|cookie|consent|onetrust|klaviyo|intercom|"
                             r"hubspot|recaptcha|swiper|slick|splide|flickity|font-?awesome|reset|normalize", re.I)

# Strings that must never reach a page, prompt or note: leftover filler text, plus the names, product words and URLs
# of any page you modelled the layout on (add them here). Matched case-insensitively against sections.json (check),
# the built page (verify) and the prompts (prompt).
FORBIDDEN = [
    r"lorem ipsum", r"dolor sit amet",
]
FORBIDDEN_RE = re.compile("|".join(FORBIDDEN), re.I)

# The exit-popup rules the template must carry (verify reads them back from the built page).
POPUP_RULES = {
    "DESKTOP_DWELL": "8000",      # desktop: mouse leaves through the top after 8 seconds
    "MOBILE_DWELL": "25000",      # mobile: upward scroll after 25 seconds
    "MOBILE_SCROLL": "80",        # ... of more than 80 pixels
    "MOBILE_TIME": "75000",       # mobile fallback: 75 seconds on the page
    "TTL": "7 * 864e5",           # at most once per 7 days in the same browser
}

REQUIRED_COPY = [
    "headline", "subhead", "deliverable", "best_product", "banner_text", "banner_link_text", "case_studies_url",
    "eyebrow", "lede", "vsl_caption", "cta_line", "cta_button", "booking_url", "call_gets_title",
    "proof_title", "final_title", "from_name", "popup_eyebrow", "popup_title", "popup_body", "popup_cta",
]


# ---------- colors ----------

def hex_to_rgb(value: str):
    v = value.strip().lstrip("#")
    if len(v) in (3, 4):
        v = "".join(c * 2 for c in v[:3])
    if len(v) == 8:
        v = v[:6]
    if not re.fullmatch(r"[0-9a-fA-F]{6}", v):
        return None
    return tuple(int(v[i:i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb) -> str:
    return "#" + "".join(f"{max(0, min(255, round(c))):02x}" for c in rgb)


def luminance(rgb) -> float:
    def ch(c):
        c = c / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b) -> float:
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def mix(a, b, t: float):
    """t=0 gives a, t=1 gives b."""
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def until_contrast(color, against, target: float, toward):
    c = color
    for step in range(21):
        c = mix(color, toward, step / 20)
        if contrast(c, against) >= target:
            return c
    return c


def is_brand_color(rgb) -> bool:
    h, l, s = colorsys.rgb_to_hls(*(c / 255 for c in rgb))
    return s >= 0.25 and 0.18 <= l <= 0.82


def palette(primary_hex: str) -> dict:
    """Every page color, derived from one brand color on the template's light layout."""
    p = hex_to_rgb(primary_hex) or (34, 34, 34)
    white, ink = (255, 255, 255), (17, 20, 28)
    canvas = mix(white, p, 0.035)
    band = mix(white, p, 0.08)
    dark = mix((13, 16, 24), p, 0.18)
    on_primary = white if contrast(p, white) >= contrast(p, ink) else ink
    return {
        "primary": rgb_to_hex(p),
        "primary_hover": rgb_to_hex(mix(p, white if luminance(p) < 0.4 else ink, 0.12)),
        "primary_top": rgb_to_hex(mix(p, white, 0.14)),
        "on_primary": rgb_to_hex(on_primary),
        "accent": rgb_to_hex(until_contrast(p, canvas, 4.5, ink)),
        "accent_on_dark": rgb_to_hex(until_contrast(p, dark, 4.5, white)),
        "canvas": rgb_to_hex(canvas),
        "band": rgb_to_hex(band),
        "border": rgb_to_hex(mix(band, ink, 0.08)),
        "text": rgb_to_hex(ink),
        "muted": rgb_to_hex(mix(ink, white, 0.32)),
        "dark": rgb_to_hex(dark),
        "glow": "rgb({} {} {} / .10)".format(*(round(c) for c in p)),
    }


# ---------- fetching ----------

def fetch(url: str, limit: int):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=20) as r:
        data = r.read(limit + 1)
        ctype = r.headers.get("Content-Type", "")
        final = r.geturl()
    if len(data) > limit:
        raise ValueError(f"{url}: larger than {limit} bytes")
    return data, ctype, final


def decode(data: bytes, ctype: str) -> str:
    m = re.search(r"charset=([\w-]+)", ctype or "", re.I)
    try:
        return data.decode(m.group(1) if m else "utf-8", errors="replace")
    except LookupError:
        return data.decode("utf-8", errors="replace")


# ---------- parsing ----------

class SiteParser(HTMLParser):
    TEXT_TAGS = {"h1", "h2", "h3", "p", "li", "blockquote", "figcaption", "span", "strong", "div", "a"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.meta, self.links, self.imgs, self.styles, self.jsonld = {}, [], [], [], []
        self.title, self.headings, self.texts, self.nav = "", [], [], []
        self._stack, self._buf, self._in_style, self._in_script, self._jsonld = [], [], False, False, False
        self._in_title, self._nav_depth, self._quote_depth = False, 0, 0

    def handle_starttag(self, tag, attrs):
        a = {k: (v or "") for k, v in attrs}
        if tag == "meta":
            key = (a.get("property") or a.get("name") or "").lower()
            if key and "content" in a:
                self.meta.setdefault(key, a["content"])
        elif tag == "link":
            self.links.append(a)
        elif tag == "img":
            self.imgs.append(a)
        elif tag == "style":
            self._in_style = True
        elif tag == "script":
            self._in_script = True
            self._jsonld = "ld+json" in a.get("type", "")
        elif tag == "title":
            self._in_title = True
        if a.get("style"):
            self.styles.append(a["style"])
        if tag in ("nav", "header"):
            self._nav_depth += 1
        if tag == "blockquote":
            self._quote_depth += 1
        if tag in self.TEXT_TAGS:
            self._flush()
            self._stack.append(tag)

    def handle_endtag(self, tag):
        if tag == "style":
            self._in_style = False
        elif tag == "script":
            self._in_script = self._jsonld = False
        elif tag == "title":
            self._in_title = False
        if tag in self.TEXT_TAGS:
            self._flush()
            if tag in self._stack:
                while self._stack and self._stack.pop() != tag:
                    pass
        if tag in ("nav", "header"):
            self._nav_depth = max(0, self._nav_depth - 1)
        if tag == "blockquote":
            self._quote_depth = max(0, self._quote_depth - 1)

    def handle_data(self, data):
        if self._in_style:
            self.styles.append(data)
        elif self._in_script:
            if self._jsonld:
                self.jsonld.append(data)
        elif self._in_title:
            self.title += data
        else:
            self._buf.append(data)

    def _flush(self):
        text = re.sub(r"\s+", " ", "".join(self._buf)).strip()
        self._buf = []
        if not text:
            return
        tag = self._stack[-1] if self._stack else ""
        if tag in ("h1", "h2", "h3"):
            self.headings.append({"tag": tag, "text": text})
        if self._nav_depth and tag == "a" and 2 < len(text) < 40:
            self.nav.append(text)
        self.texts.append({"tag": "blockquote" if self._quote_depth else tag, "text": text})


PROOF_RE = re.compile(
    r"(\d[\d,.]*\s*(\+|%|k\b|m\b|million|thousand|x\b))|"
    r"(\d[\d,.]*\s+(customers|reviews|ratings|users|teams|companies|businesses|brands|countries|stores|orders|people|members))|"
    r"(\b\d(\.\d)?\s*(/|out of)\s*5\b)|(\b\d(\.\d)?[- ]stars?\b)|"
    r"\b(award|trusted by|rated|certified|b corp|since \d{4}|founded in \d{4})\b",
    re.I,
)


def jsonld_items(blocks):
    out = []
    for raw in blocks:
        try:
            data = json.loads(raw)
        except ValueError:
            continue
        stack = [data]
        while stack:
            d = stack.pop()
            if isinstance(d, list):
                stack.extend(d)
            elif isinstance(d, dict):
                out.append(d)
                stack.extend(v for v in d.values() if isinstance(v, (list, dict)))
    return out


def ld_type(d) -> list:
    t = d.get("@type", [])
    return [t] if isinstance(t, str) else [x for x in t if isinstance(x, str)]


def site_name(p: SiteParser, ld, host: str) -> tuple[str, str]:
    if p.meta.get("og:site_name"):
        return p.meta["og:site_name"].strip(), "og:site_name"
    for d in ld:
        if set(ld_type(d)) & {"Organization", "Corporation", "OnlineStore", "Brand"} and isinstance(d.get("name"), str):
            return d["name"].strip(), "JSON-LD Organization name"
    parts = [x.strip() for x in re.split(r"\s+[|\-–—:]\s+", p.title) if x.strip()]
    if parts:
        short = min(parts, key=len)
        if len(short) <= 30:
            return short, "page title"
    label = host.removeprefix("www.").split(".")[0]
    return label.capitalize(), "domain"


def home_link_svg(page_html: str, host: str):
    """The first inline <svg> inside a link to the home page, or under an element marked logo (the header wordmark)."""
    head = page_html[: len(page_html) * 2 // 3]
    root = re.compile(r"""href\s*=\s*["'](?:/|https?://(?:www\.)?%s/?)["']""" % re.escape(host.removeprefix("www.")), re.I)
    for m in re.finditer(r"<svg\b.*?</svg>", head, re.I | re.S):
        svg = m.group(0)
        if len(svg) > 25_000 or len(svg) < 120:
            continue
        before = head[max(0, m.start() - 700):m.start()]
        opener = before.rfind("<a ")
        in_link = opener >= 0 and "</a>" not in before[opener:]
        link = before[opener:] if in_link else ""
        marked = re.search(r"<svg\b[^>]*(logo|wordmark)", svg[:300], re.I)
        if marked or (in_link and (root.search(link) or re.search(r"logo", link, re.I))) or \
                re.search(r"""(class|id|data-testid)\s*=\s*["'][^"']*logo[^"']*["'][^<]*(<(?!/)[^>]*>\s*)*$""", before[-300:], re.I):
            return svg
    return None


def pick_logo(p: SiteParser, ld, page_html: str, base: str):
    for d in ld:
        logo = d.get("logo")
        if isinstance(logo, dict):
            logo = logo.get("url")
        if isinstance(logo, str) and logo:
            return urllib.parse.urljoin(base, logo), "JSON-LD logo", None
    svg = home_link_svg(page_html, urllib.parse.urlparse(base).hostname or "")
    if svg:
        return "", "inline svg in the home link or logo element", svg
    for img in p.imgs:
        hay = " ".join(img.get(k, "") for k in ("src", "alt", "class", "id")).lower()
        if "logo" in hay and img.get("src") and not img["src"].startswith("data:"):
            return urllib.parse.urljoin(base, img["src"]), "img marked logo", None
    best = None
    for link in p.links:
        rel = link.get("rel", "").lower()
        if "apple-touch-icon" in rel or ("icon" in rel and "svg" in link.get("type", "")):
            best = best or link.get("href")
    if best:
        return urllib.parse.urljoin(base, best), "touch icon", None
    if p.meta.get("og:image"):
        return "", "none (og:image is a photo, not a logo)", None
    return "", "none found", None


COLOR_RE = re.compile(r"#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b|rgba?\([^)]*\)|hsla?\([^)]*\)|oklch\([^)]*\)", re.I)
VAR_DEF_RE = re.compile(r"(--[\w-]+)\s*:\s*([^;}{]+)")
BRAND_VAR = re.compile(r"brand|primary|accent|button|btn|cta|main", re.I)
SCALE_VAR = re.compile(r"-(50|[1-9]00|950)$")
RULE_RE = re.compile(r"([^{}]+)\{([^{}]*)\}")
BUTTON_SEL = re.compile(r"btn|button|cta|primary", re.I)
FONT_RE = re.compile(r"font-family\s*:\s*([^;}{]+)", re.I)
GENERIC_FONTS = {"serif", "sans-serif", "monospace", "system-ui", "inherit", "initial", "cursive", "fantasy",
                 "-apple-system", "blinkmacsystemfont", "segoe ui", "roboto", "helvetica", "helvetica neue", "arial",
                 "ui-sans-serif", "ui-serif", "ui-monospace", "apple color emoji", "segoe ui emoji", "noto color emoji",
                 "unset", "var", "times new roman", "georgia", "courier new"}


def oklch_to_rgb(l, c, h):
    import math
    a, b = c * math.cos(math.radians(h)), c * math.sin(math.radians(h))
    l_ = (l + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m_ = (l - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s_ = (l - 0.0894841775 * a - 1.2914855480 * b) ** 3
    lin = (4.0767416621 * l_ - 3.3077115913 * m_ + 0.2309699292 * s_,
           -1.2684380046 * l_ + 2.6097574011 * m_ - 0.3413193965 * s_,
           -0.0041960863 * l_ - 0.7034186147 * m_ + 1.7076147010 * s_)
    def gamma(x):
        x = max(0.0, min(1.0, x))
        return 12.92 * x if x <= 0.0031308 else 1.055 * x ** (1 / 2.4) - 0.055
    return tuple(gamma(x) * 255 for x in lin)


def parse_color(token: str):
    t = token.strip()
    if t.startswith("#"):
        return hex_to_rgb(t)
    nums = [float(x) for x in re.findall(r"-?\d*\.?\d+", t)][:3]
    if len(nums) < 3 or "var(" in t:
        return None
    pct = re.findall(r"(-?\d*\.?\d+)(%?)", t)[:3]
    low = t.lower()
    if low.startswith("rgb"):
        return tuple(min(255.0, n * 2.55 if p == "%" else n) for (_, p), n in zip(pct, nums))
    if low.startswith("hsl"):
        r, g, b = colorsys.hls_to_rgb((nums[0] % 360) / 360, nums[2] / 100, nums[1] / 100)
        return (r * 255, g * 255, b * 255)
    if low.startswith("oklch"):
        l = nums[0] / 100 if pct[0][1] == "%" else nums[0]
        return oklch_to_rgb(l, nums[1], nums[2])
    return None


def resolve_vars(css: str) -> dict:
    """Custom properties with var() references resolved (a few passes; enough for token files)."""
    defs = {}
    for m in VAR_DEF_RE.finditer(css):
        defs.setdefault(m.group(1), m.group(2).strip())
    for _ in range(4):
        changed = False
        for k, v in defs.items():
            nv = re.sub(r"var\((--[\w-]+)\)", lambda m: defs.get(m.group(1), m.group(0)) if m.group(1) != k else m.group(0), v)
            if nv != v:
                defs[k], changed = nv, True
        if not changed:
            break
    return defs


def pick_colors(p: SiteParser, css: str):
    """Rank brand colors: theme-color, then colors on button and CTA rules, then brand-named tokens, then frequency.
    A site with no saturated color falls back to its darkest button color (a monochrome brand)."""
    defs = resolve_vars(css)
    scores, dark, why = Counter(), Counter(), {}

    def add(rgb, weight, reason):
        if not rgb:
            return
        h = rgb_to_hex(rgb)
        if is_brand_color(rgb):
            scores[h] += weight
            why.setdefault(h, reason)
        elif luminance(rgb) < 0.05 and weight >= 6:
            dark[h] += weight
            why.setdefault(h, reason)

    def colors_in(value):
        value = re.sub(r"var\((--[\w-]+)\)", lambda m: defs.get(m.group(1), ""), value)
        return [parse_color(c.group(0)) for c in COLOR_RE.finditer(value)]

    theme = parse_color(p.meta.get("theme-color", "").strip())
    if theme and is_brand_color(theme):
        add(theme, 50, "meta theme-color")
    for name, value in defs.items():
        if THIRD_PARTY_CSS.search(name) or SCALE_VAR.search(name):
            continue  # a widget's token or a framework palette step (--color-blue-500), not a brand choice
        brand_named = bool(BRAND_VAR.search(name))
        for rgb in colors_in(value):
            add(rgb, 8 if brand_named else 2, f"CSS variable {name}")
    for m in RULE_RE.finditer(css):
        sel, body = m.group(1), m.group(2)
        if THIRD_PARTY_CSS.search(sel):
            continue
        button = bool(BUTTON_SEL.search(sel))
        for decl in body.split(";"):
            if ":" not in decl:
                continue
            prop, value = decl.split(":", 1)
            prop = prop.strip().lower()
            if prop.startswith("--"):
                continue
            weight = 6 if button and prop in ("background", "background-color") else (2 if button else 1)
            reason = "background of a button rule" if weight == 6 else "most used saturated color in the site CSS"
            for rgb in colors_in(value):
                add(rgb, weight, reason)
    ranked = [{"hex": h, "score": s, "source": why[h]} for h, s in scores.most_common(6)]
    if not ranked:
        ranked = [{"hex": h, "score": s, "source": why[h] + " (no saturated brand color; monochrome)"} for h, s in dark.most_common(2)]
    return ranked


def pick_font(css: str, links):
    google = [l.get("href", "") for l in links if "fonts.googleapis.com" in l.get("href", "")]
    google_families = []
    for href in google:
        google_families += [urllib.parse.unquote_plus(f.split(":")[0]) for f in re.findall(r"family=([^&]+)", href)]
    counts = Counter()
    for m in FONT_RE.finditer(css):
        first = m.group(1).split(",")[0].strip().strip("'\"").strip()
        low = first.lower()
        if not first or low in GENERIC_FONTS or low.startswith("var(") or re.search(r"icon|awesome|glyph|symbol|emoji", low):
            continue
        counts[first] += 1
    family = google_families[0] if google_families else (counts.most_common(1)[0][0] if counts else "")
    css_url = ""
    if google_families and family in google_families:
        css_url = "https://fonts.googleapis.com/css2?family=" + urllib.parse.quote_plus(family) + ":wght@400;500;600;700&display=swap"
    return {"family": family, "google_css_url": css_url,
            "source": "Google Fonts link" if css_url else ("most used font-family in the site CSS" if family else "none found"),
            "candidates": [f for f, _ in counts.most_common(5)]}


def products(p: SiteParser, ld):
    out = []
    for d in ld:
        if "Product" in ld_type(d) and isinstance(d.get("name"), str):
            out.append({"text": d["name"].strip(), "source": "JSON-LD Product"})
    for h in p.headings:
        if 3 <= len(h["text"]) <= 80:
            out.append({"text": h["text"], "source": f"{h['tag']} heading"})
    for n in p.nav:
        out.append({"text": n, "source": "navigation link"})
    seen, uniq = set(), []
    for item in out:
        key = item["text"].lower()
        if key not in seen:
            seen.add(key)
            uniq.append(item)
    return uniq[:25]


def proof_points(p: SiteParser):
    out, seen = [], set()
    for t in p.texts:
        text = t["text"]
        if not (12 <= len(text) <= 220):
            continue
        if t["tag"] == "blockquote" or PROOF_RE.search(text):
            key = text.lower()
            if key in seen:
                continue
            seen.add(key)
            out.append({"text": text, "kind": "quote" if t["tag"] == "blockquote" else "stat"})
    return out[:15]


def extract(url: str, html_file: str | None = None) -> tuple[dict, bytes | None, str]:
    """Return (brand facts, logo bytes or None, logo file extension)."""
    notes = []
    if html_file:
        page_html, final = pathlib.Path(html_file).read_text(encoding="utf-8", errors="replace"), url
        notes.append(f"read from saved HTML {pathlib.Path(html_file).name}, not fetched")
    else:
        data, ctype, final = fetch(url, MAX_PAGE)
        page_html = decode(data, ctype)
    p = SiteParser()
    p.feed(page_html)
    p.close()
    ld = jsonld_items(p.jsonld)
    host = urllib.parse.urlparse(final).hostname or ""
    css = "\n".join(p.styles)
    sheets = [urllib.parse.urljoin(final, l["href"]) for l in p.links
              if "stylesheet" in l.get("rel", "").lower() and l.get("href") and not THIRD_PARTY_CSS.search(l["href"])]
    if not html_file:
        for href in sheets[:MAX_SHEETS]:
            try:
                data, ctype, _ = fetch(href, MAX_CSS)
                css += "\n" + decode(data, ctype)
            except Exception as e:  # a stylesheet we cannot read only weakens the color pick
                notes.append(f"stylesheet not read: {href} ({type(e).__name__})")
    name, name_source = site_name(p, ld, host)
    logo_url, logo_source, logo_svg = pick_logo(p, ld, page_html, final)
    logo_bytes, logo_ext = None, ""
    if logo_svg:
        if "xmlns" not in logo_svg[:200]:
            logo_svg = logo_svg.replace("<svg", '<svg xmlns="http://www.w3.org/2000/svg"', 1)
        logo_bytes, logo_ext = logo_svg.encode(), "svg"
    elif logo_url and not html_file:
        try:
            data, ctype, _ = fetch(logo_url, MAX_LOGO)
            ext = {"image/svg+xml": "svg", "image/png": "png", "image/jpeg": "jpg", "image/webp": "webp",
                   "image/gif": "gif", "image/x-icon": "ico", "image/vnd.microsoft.icon": "ico"}.get(ctype.split(";")[0].strip())
            ext = ext or pathlib.PurePosixPath(urllib.parse.urlparse(logo_url).path).suffix.lstrip(".").lower()
            if ext in ("svg", "png", "jpg", "jpeg", "webp", "gif", "ico"):
                logo_bytes, logo_ext = data, ext
        except Exception as e:
            notes.append(f"logo not downloaded: {type(e).__name__}; the page shows the name as a wordmark")
    colors = pick_colors(p, css)
    font = pick_font(css, p.links)
    if not colors:
        notes.append("no brand color found; set brand.primary_color in sections.json")
    facts = {
        "url": url,
        "final_url": final,
        "read_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "name": name, "name_source": name_source,
        "description": (p.meta.get("og:description") or p.meta.get("description") or "").strip(),
        "title": p.title.strip(),
        "logo": {"url": logo_url, "source": logo_source, "file": f"logo.{logo_ext}" if logo_bytes else ""},
        "colors": colors,
        "font": font,
        "product_candidates": products(p, ld),
        "proof_candidates": [dict(x, source=final) for x in proof_points(p)],
        "headings": p.headings[:20],
        "notes": notes,
    }
    return facts, logo_bytes, logo_ext


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:40] or "prospect"


def starter_sections(facts: dict, args) -> dict:
    if getattr(args, "mode", "personal") == "general":
        return general_starter(facts, args)
    name = facts["name"]
    todo = "TODO: "
    deliverable = args.deliverable or todo + "the free thing they asked for, e.g. 5 ad creatives"
    return {
        "_how": "Fill every TODO from brand.json and the prospect's reply. Proof items need a source. Never invent results.",
        "brand": {
            "name": name,
            "url": facts["final_url"],
            "logo": facts["logo"]["file"] or facts["logo"]["url"],
            "primary_color": facts["colors"][0]["hex"] if facts["colors"] else "#222222",
            "font_family": facts["font"]["family"],
            "font_css_url": facts["font"]["google_css_url"],
        },
        "slug": slugify(name),
        "best_product": todo + "their best product, picked from brand.json product_candidates",
        "deliverable": deliverable,
        "banner_text": todo + f"one line on the work you have done for brands like {name}",
        "banner_link_text": "See the case studies",
        "case_studies_url": args.case_studies_url or todo + "your case studies page",
        "eyebrow": f"Prepared for {name}",
        "headline": todo + f"what {name} gets, in their words (e.g. Your {deliverable} for <best product>)",
        "subhead": todo + "one sentence on the outcome",
        "lede": todo + "two sentences: what you are preparing and how you do the work",
        "vsl_url": "",
        "vsl_caption": "A short walkthrough of how we do the work",
        "cta_line": todo + f"what the call gets them, e.g. Grab a time and I'll walk you through your {deliverable} and how I'd run them for {name}",
        "cta_button": "Book the walkthrough",
        "booking_url": args.booking_url or todo + "the booking link",
        "call_gets_title": "On the call",
        "call_gets": [todo + "first thing the call gets them", todo + "second", todo + "third"],
        "proof_title": f"What {name} already has going for it",
        "proof_intro": "",
        "proof": [{"text": c["text"], "source": c["source"]} for c in facts["proof_candidates"][:3]] or
                 [{"text": todo + "a proof point from brand.json proof_candidates or your own case studies", "source": ""}],
        "final_title": todo + "the closing line before the last button",
        "popup_eyebrow": f"Before you go, {name}",
        "popup_title": todo + "pitch the walkthrough, not only a time",
        "popup_body": todo + f"one or two sentences on what the walkthrough of the {deliverable} gets them "
                             f"(the page puts the call length first)",
        "call_length": DEFAULT_CALL_LENGTH,
        "popup_cta": "Book the walkthrough",
        "from_name": todo + "your company name, shown in the footer",
    }


# ---------- check ----------

def walk_strings(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if not k.startswith("_"):
                yield from walk_strings(v, f"{path}.{k}" if path else k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk_strings(v, f"{path}[{i}]")
    elif isinstance(obj, str):
        yield path, obj


OPTIONAL_TEXT = ["vsl_url", "proof_intro", "call_length", "mode", "case_study_url", "case_study_title", "case_study_summary",
                 "merge_eyebrow", "merge_popup_eyebrow"]
# personal: one page per replied prospect, in the prospect's brand. general: one reusable page for every lead in a campaign,
# in the sender's own brand, built around a VSL or a case-study document; per lead only ?first_name= and ?company= in the URL.
MODES = ("personal", "general")
MERGE_TAGS = ("first_name", "company")
MERGE_FIELDS = ("merge_eyebrow", "merge_popup_eyebrow")
BRAND_TEXT = ["url", "logo", "primary_color", "font_family", "font_css_url"]
DEFAULT_CALL_LENGTH = "15 minutes"


def page_mode(s: dict) -> str:
    m = s.get("mode")
    return m.strip() if isinstance(m, str) and m.strip() else "personal"


def call_length(s: dict) -> str:
    return (s.get("call_length") or "").strip() or DEFAULT_CALL_LENGTH


def popup_body(s: dict) -> str:
    """The popup states the call length set once in call_length, so it matches the reply and the call opener."""
    length = call_length(s)
    return f"{length[0].upper() + length[1:]} on a call. {s['popup_body']}"


def check(sections: dict) -> tuple[list, list]:
    errors, notes = [], []
    if not isinstance(sections, dict):
        return ["sections.json must be a JSON object"], notes
    for path, value in walk_strings(sections):
        if "TODO" in value:
            errors.append(f"{path} is still a TODO")
        m = FORBIDDEN_RE.search(value)
        if m:
            errors.append(f"{path} contains '{m.group(0)}': reuse a reference page's structure only, never its words, names or URLs")

    def text(obj: dict, key: str, path: str, required: bool) -> str:
        v = obj.get(key)
        if v is not None and not isinstance(v, str):
            errors.append(f"{path} must be text")
            return ""
        if required and not (v or "").strip():
            errors.append(f"{path} is empty")
        return v or ""

    general = page_mode(sections) == "general"
    if page_mode(sections) not in MODES:
        errors.append(f"mode must be one of {', '.join(MODES)}")
    for key in REQUIRED_COPY:
        text(sections, key, key, not (general and key == "best_product"))
    for key in OPTIONAL_TEXT:
        text(sections, key, key, False)
    brand = sections.get("brand")
    if not isinstance(brand, dict):
        errors.append("brand must be an object")
        brand = {}
    text(brand, "name", "brand.name", True)
    for key in BRAND_TEXT:
        text(brand, key, f"brand.{key}", False)
    for key in ("booking_url", "case_studies_url"):
        v = sections.get(key)
        if isinstance(v, str) and v and "TODO" not in v and not re.match(r"https://[^\s/]+\.[^\s]+", v):
            errors.append(f"{key} must be a full https:// link")
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", str(brand.get("primary_color", ""))):
        errors.append("brand.primary_color must be a #rrggbb color")
    gets = sections.get("call_gets")
    if not isinstance(gets, list) or not all(isinstance(g, str) for g in gets):
        errors.append("call_gets must be a list of text lines")
    elif len([g for g in gets if g.strip()]) < 2:
        errors.append("call_gets needs at least two lines on what the call gets them")
    proof = sections.get("proof")
    if not isinstance(proof, list) or not proof:
        errors.append("proof needs at least one item")
        proof = []
    for i, item in enumerate(proof):
        if not isinstance(item, dict):
            errors.append(f"proof[{i}] must be an object with text and source")
            continue
        text(item, "text", f"proof[{i}].text", True)
        v = item.get("source")
        if v is not None and not isinstance(v, str):
            errors.append(f"proof[{i}].source must be text")
        elif not (v or "").strip():
            errors.append(f"proof[{i}].source is empty: every proof point names where it came from")
    vsl = sections.get("vsl_url")
    vsl = vsl.strip() if isinstance(vsl, str) else ""
    doc = sections.get("case_study_url")
    doc = doc.strip() if isinstance(doc, str) else ""
    if doc and "TODO" not in doc and not re.match(r"https://[^\s/]+\.[^\s]+", doc):
        errors.append("case_study_url must be a full https:// link")
    if doc and not str(sections.get("case_study_title") or "").strip():
        errors.append("case_study_title is empty: name the case study the page links to")
    for key in MERGE_FIELDS:
        v = sections.get(key)
        if isinstance(v, str):
            bad = [t for t in re.findall(r"\{(\w+)\}", v) if t not in MERGE_TAGS]
            if bad or not re.search(r"\{(first_name|company)\}", v) and v.strip():
                errors.append(f"{key} may use only {{first_name}} and {{company}}, and at least one of them")
            elif v.strip() and not general:
                errors.append(f"{key} is for general pages only: a personal page already names the prospect")
    if general and not vsl and not doc:
        errors.append("a general page is built around a VSL or a case-study document: set vsl_url or case_study_url")
    elif not vsl and not doc:
        notes.append("no vsl_url: the page shows a video placeholder; record the VSL before sending the link")
    if vsl and not vsl_source(vsl):
        errors.append("vsl_url is not a YouTube, Vimeo or Loom link, an embed link or an .mp4/.webm/.mov file: "
                      "the page would show a placeholder instead of the video")
    if not brand.get("logo"):
        notes.append("no logo: the header shows the brand name as a wordmark")
    if not isinstance(sections.get("slug"), str) or not re.fullmatch(r"[a-z0-9-]+", sections["slug"]):
        errors.append("slug must be lowercase letters, digits and dashes")
    return errors, notes


# ---------- build ----------

def vsl_source(url: str):
    u = url.strip()
    p = urllib.parse.urlparse(u)
    if p.scheme not in ("http", "https"):
        return None
    host = re.sub(r"^(?:www\.|m\.)", "", (p.hostname or "").lower())
    parts = [x for x in p.path.split("/") if x]
    query = urllib.parse.parse_qs(p.query)
    vid = ""
    if host == "youtu.be" and parts:
        vid = parts[0]
    elif host == "youtube.com" and parts == ["watch"]:
        vid = query.get("v", [""])[0]
    elif host == "youtube.com" and len(parts) >= 2 and parts[0] in ("shorts", "live"):
        vid = parts[1]
    if re.fullmatch(r"[\w-]{6,}", vid):
        return "iframe", f"https://www.youtube-nocookie.com/embed/{vid}"
    if host == "vimeo.com" and parts and parts[0].isdigit():
        h = parts[1] if len(parts) > 1 and re.fullmatch(r"[0-9a-f]+", parts[1]) else query.get("h", [""])[0]
        return "iframe", f"https://player.vimeo.com/video/{parts[0]}" + (f"?h={urllib.parse.quote(h)}" if h else "")
    if host == "loom.com" and len(parts) >= 2 and parts[0] == "share":
        return "iframe", f"https://www.loom.com/embed/{parts[1]}"
    if p.scheme == "https" and re.search(r"/embed/|player\.vimeo\.com/video/", u):
        return "iframe", u
    if p.scheme == "https" and re.search(r"\.(mp4|webm|mov)$", p.path, re.I):
        return "video", u
    return None


def vsl_html(url: str, caption: str) -> str:
    cap = html.escape(caption)
    src = vsl_source(url)
    if src and src[0] == "iframe":
        return (f'<iframe src="{html.escape(src[1])}" title="{cap}" loading="lazy" '
                'allow="autoplay; fullscreen; picture-in-picture" allowfullscreen></iframe>')
    if src:
        return f'<video controls preload="metadata" src="{html.escape(src[1])}" aria-label="{cap}"></video>'
    return ('<div class="wl-vsl__placeholder"><span class="wl-vsl__play" aria-hidden="true"></span>'
            f'<span>{cap}</span><small>Video goes here</small></div>')


def hero_media_html(s: dict) -> str:
    """The VSL; on a general page without one, the case-study document card in the same slot."""
    vsl, doc = str(s.get("vsl_url") or "").strip(), str(s.get("case_study_url") or "").strip()
    if vsl or not doc:
        return vsl_html(vsl, str(s.get("vsl_caption", "")))
    summary = str(s.get("case_study_summary") or "").strip()
    return ('<div class="wl-vsl__placeholder wl-vsl__doc">'
            f'<span>{html.escape(str(s.get("case_study_title", "")))}</span>'
            + (f'<small>{html.escape(summary)}</small>' if summary else "")
            + f'<a class="btn btn-primary" href="{html.escape(doc)}" data-cta="case-study-doc" rel="noopener">'
              'Read the case study</a></div>')


def under_note_html(s: dict) -> str:
    if page_mode(s) == "general":
        return ""
    return f'<small>Walked through live: {html.escape(s["deliverable"])} for {html.escape(s["best_product"])}.</small>'


def footer_text(s: dict) -> str:
    name, by = s["brand"]["name"], s["from_name"].strip().rstrip(".")
    if page_mode(s) == "general":
        return f"A walkthrough page by {by}."
    return f"A walkthrough page prepared for {name} by {by}. {name} names and marks belong to their owner."


def merge_attr(s: dict, key: str) -> str:
    v = str(s.get(key) or "").strip()
    return f' data-merge="{html.escape(v)}"' if v and page_mode(s) == "general" else ""


def logo_html(run_dir: pathlib.Path, brand: dict) -> str:
    name = html.escape(brand["name"])
    logo = str(brand.get("logo", "")).strip()
    src = ""
    if logo and not re.match(r"https?://", logo):
        f = (run_dir / logo).resolve()
        if f.is_file() and f.parent == run_dir.resolve():
            mime = {"svg": "image/svg+xml", "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
                    "webp": "image/webp", "gif": "image/gif", "ico": "image/x-icon"}.get(f.suffix.lstrip(".").lower(), "")
            if mime:
                src = f"data:{mime};base64," + base64.b64encode(f.read_bytes()).decode()
    elif logo:
        src = logo
    if src:
        return f'<img class="wl-brand__logo" src="{html.escape(src)}" alt="{name}">'
    return f'<span class="wl-brand__word">{name}</span>'


def render(run_dir: pathlib.Path, s: dict) -> str:
    brand = s["brand"]
    pal = palette(brand["primary_color"])
    family = str(brand.get("font_family") or "").strip().strip("'\"")
    stack = "ui-sans-serif, system-ui, -apple-system, 'Segoe UI', sans-serif"
    font_stack = (f"'{family}', " if family and re.fullmatch(r"[\w .-]+", family) else "") + stack
    font_link = ""
    if re.match(r"https://fonts\.googleapis\.com/", str(brand.get("font_css_url") or "")):
        font_link = (f'<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
                     f'<link rel="stylesheet" href="{html.escape(brand["font_css_url"])}">')
    esc = lambda k: html.escape(str(s.get(k, "")))
    gets = "\n".join(f"          <li>{html.escape(str(g))}</li>" for g in s["call_gets"] if str(g).strip())
    proof_items = []
    for item in s["proof"]:
        src = str(item.get("source", ""))
        cite = (f'<a href="{html.escape(src)}" rel="noopener">{html.escape(urllib.parse.urlparse(src).hostname or src)}</a>'
                if re.match(r"https?://", src) else html.escape(src))
        proof_items.append(f'        <figure class="wl-card wl-proof__item"><blockquote>{html.escape(str(item["text"]))}</blockquote>'
                           f'<figcaption>{cite}</figcaption></figure>')
    config = {
        "slug": s["slug"],
        "seenKey": f"wl_exit_seen_{s['slug']}",
        "dismissKey": f"wl_exit_dismissed_{s['slug']}",
        "bookedKey": f"wl_booked_{s['slug']}",
        "bannerKey": f"wl_banner_dismissed_{s['slug']}",
    }
    values = {
        "title": f"{brand['name']}: {s['deliverable']}",
        "description": s["subhead"],
        "popup_body": popup_body(s),
        "brand_name": brand["name"],
        "font_link_html": font_link,
        "font_stack_css": font_stack,
        "logo_html": logo_html(run_dir, brand),
        "vsl_html": hero_media_html(s),
        "under_note_html": under_note_html(s),
        "footer_text": footer_text(s),
        "merge_eyebrow_attr_html": merge_attr(s, "merge_eyebrow"),
        "merge_popup_eyebrow_attr_html": merge_attr(s, "merge_popup_eyebrow"),
        "call_gets_html": gets,
        "proof_html": "\n".join(proof_items),
        "config_json": json.dumps(config),
        "proof_intro_html": f'<p>{esc("proof_intro")}</p>' if str(s.get("proof_intro", "")).strip() else "",
        "year": str(datetime.now().year),
    }
    values.update({f"c_{k}": v for k, v in pal.items()})
    out = TEMPLATE.read_text(encoding="utf-8")

    def sub(m):
        key = m.group(1)
        if key in values:
            v = values[key]
            return v if key.endswith(("_html", "_css", "_json")) or key.startswith("c_") else html.escape(v)
        if key in s:
            return esc(key)
        raise KeyError(f"template placeholder {{{{{key}}}}} has no value")
    return re.sub(r"\{\{(\w+)\}\}", sub, out)


# ---------- verify ----------

def verify(page: str) -> list:
    """Return the failures for a built page; empty means it passes."""
    fails = []
    pos = lambda pat: (m.start() if (m := re.search(pat, page, re.S)) else -1)
    banner = re.search(r'<div[^>]*id="wl-announce".*?</div>\s*</div>', page, re.S)
    if not banner or not re.search(r'<a[^>]+href="https://[^"]+"[^>]*data-cta="case-studies"', banner.group(0)):
        fails.append("1 banner: no announcement banner linking to the case studies")
    hero, vsl = pos(r'<section[^>]*class="wl-hero'), pos(r'data-slot="vsl"')
    if hero < 0 or vsl < hero:
        fails.append("2 hero: no hero with a VSL slot")
    cta = pos(r'<a[^>]+href="https://[^"]+"[^>]*data-cta="booking-under-video"')
    line = pos(r'class="wl-cta-line"')
    if cta < 0 or line < 0 or not (vsl < line < cta) or cta > pos(r'id="proof"'):
        fails.append("3 booking CTA: no booking link with its call line right under the video")
    proof = re.search(r'<section[^>]*id="proof".*?</section>', page, re.S)
    if not proof or "wl-proof__item" not in proof.group(0):
        fails.append("4 proof: no proof section with at least one item")
    popup = re.search(r'<div[^>]*id="wl-exit".*?</div>\s*</div>', page, re.S)
    if not popup or 'role="dialog"' not in popup.group(0) or not re.search(r'href="https://[^"]+"[^>]*data-cta="booking-popup"', popup.group(0)):
        fails.append("5 exit popup: no dialog with a booking link")
    script = "\n".join(re.findall(r"<script>(.*?)</script>", page, re.S))
    for name, value in POPUP_RULES.items():
        if not re.search(rf"\b{name}\s*=\s*{re.escape(value)}\s*[;,]", script):
            fails.append(f"popup rule: {name} is not {value}")
    for need, why in [(r"e\.clientY\s*>\s*0", "desktop trigger is the mouse leaving through the top"),
                      (r"localStorage", "dismiss and seen state live in localStorage"),
                      (r"'Escape'", "Escape closes the popup"),
                      (r"preview=exit", "?preview=exit shows the popup at once for review")]:
        if not re.search(need, script):
            fails.append(f"popup rule: {why}")
    if re.search(r"<script[^>]+src=", page, re.I):
        fails.append("self-contained: the page loads an external script")
    for m in re.finditer(r'<link[^>]+href="([^"]+)"', page):
        if not m.group(1).startswith(("https://fonts.googleapis.com/", "https://fonts.gstatic.com")):
            fails.append(f"self-contained: the page loads {m.group(1)}")
    m = FORBIDDEN_RE.search(page)
    if m:
        fails.append(f"reference strings: the page contains '{m.group(0)}'")
    if re.search(r"TODO|\{\{\w+\}\}", page):
        fails.append("unfilled: a TODO or template placeholder is left in the page")
    return fails


def general_starter(facts: dict, args) -> dict:
    """A general page: the sender's own site was read, so the brand is yours, not a prospect's."""
    name = facts["name"]
    todo = "TODO: "
    deliverable = args.deliverable or todo + "what the page delivers, e.g. the case study or the 4-minute VSL"
    return {
        "_how": ("A general page: one reusable page for every lead in a campaign, in your own brand (brand.json is read "
                 "from your site). Build it around a VSL (vsl_url) or a case-study document on how you helped another "
                 "client (case_study_url, case_study_title, case_study_summary). Per lead, only ?first_name= and "
                 "?company= in the link fill merge_eyebrow and merge_popup_eyebrow. Proof items need a source. Never "
                 "invent results."),
        "mode": "general",
        "brand": {
            "name": name,
            "url": facts["final_url"],
            "logo": facts["logo"]["file"] or facts["logo"]["url"],
            "primary_color": facts["colors"][0]["hex"] if facts["colors"] else "#222222",
            "font_family": facts["font"]["family"],
            "font_css_url": facts["font"]["google_css_url"],
        },
        "slug": slugify(name),
        "best_product": "",
        "deliverable": deliverable,
        "banner_text": todo + "one line on the work you do and for whom",
        "banner_link_text": "See the case studies",
        "case_studies_url": args.case_studies_url or todo + "your case studies page",
        "eyebrow": todo + "the line above the headline for a visitor with no merge tags, e.g. A 4-minute walkthrough",
        "merge_eyebrow": "Prepared for {company}",
        "headline": todo + "the result you got for another client, in plain words",
        "subhead": todo + "one sentence on how you did it",
        "lede": todo + "two sentences: what the video or the case study shows and what the call adds",
        "vsl_url": "",
        "vsl_caption": "How we did it, in a few minutes",
        "case_study_url": "",
        "case_study_title": "",
        "case_study_summary": "",
        "cta_line": todo + "what the call gets them, e.g. Grab a time and I'll walk you through how we'd do the same for you",
        "cta_button": "Book the walkthrough",
        "booking_url": args.booking_url or todo + "the booking link",
        "call_gets_title": "On the call",
        "call_gets": [todo + "first thing the call gets them", todo + "second", todo + "third"],
        "proof_title": "Results we can show",
        "proof_intro": "",
        "proof": [{"text": c["text"], "source": c["source"]} for c in facts["proof_candidates"][:3]] or
                 [{"text": todo + "a result from your site or a case study, with its source", "source": ""}],
        "final_title": todo + "the closing line before the last button",
        "popup_eyebrow": "Before you go",
        "merge_popup_eyebrow": "Before you go, {first_name}",
        "popup_title": todo + "pitch the walkthrough, not only a time",
        "popup_body": todo + "one or two sentences on what the walkthrough gets them (the page puts the call length first)",
        "call_length": DEFAULT_CALL_LENGTH,
        "popup_cta": "Book the walkthrough",
        "from_name": name,
    }


# ---------- Copilot prompt ----------

def logo_line(run_dir: pathlib.Path, brand: dict) -> str:
    logo = str(brand.get("logo") or "").strip()
    if re.match(r"https://", logo):
        return f"Logo: use the image at {logo}."
    if logo:
        return f"Logo: upload the file {(run_dir / logo).resolve()} (their logo, saved from their site)."
    return f"Logo: none. Show the name {brand['name']} as a text wordmark in the header."


def font_line(brand: dict) -> str:
    family = str(brand.get("font_family") or "").strip().strip("'\"")
    if family and re.match(r"https://fonts\.googleapis\.com/", str(brand.get("font_css_url") or "")):
        return f"Font: {family} (Google Fonts) for headings and body."
    if family:
        return (f"Font: a clean system sans-serif. Their site uses {family}, which is licensed to them; "
                "do not load or copy it.")
    return "Font: a clean system sans-serif."


def quoted(text) -> str:
    t = str(text).strip()
    return t if len(t) > 1 and t[0] == t[-1] == '"' else f'"{t}"'


def copilot_prompt(run_dir: pathlib.Path, s: dict) -> str:
    """The ready-to-paste Instantly Copilot prompt for the page: the same parts as build, the same copy."""
    brand = s["brand"]
    name, booking, by = brand["name"], s["booking_url"], s["from_name"].strip().rstrip(".")
    general = page_mode(s) == "general"
    pal = palette(brand["primary_color"])
    vsl, doc = str(s.get("vsl_url") or "").strip(), str(s.get("case_study_url") or "").strip()
    media = "video" if vsl or not doc else "case-study card"
    if vsl or not doc:
        video = (f"embed the video {vsl}" if vsl else
                 "a 16:9 video placeholder box (the video is added before the link is sent)")
        video += f", captioned {quoted(s['vsl_caption'])}"
    else:
        summary = str(s.get("case_study_summary") or "").strip()
        video = (f"a case-study card titled {quoted(s['case_study_title'])}"
                 + (f" with the line {quoted(summary)}" if summary else "")
                 + f" and a button \"Read the case study\" linking to {doc}")
    gets = "\n".join(f"   - {quoted(g)}" for g in s["call_gets"] if str(g).strip())
    proof = "\n".join(f"     - {quoted(p['text'])} with its source under it: {p['source']}" for p in s["proof"])
    intro = f"\n   - Intro: {quoted(s['proof_intro'])}" if str(s.get("proof_intro") or "").strip() else ""
    footer = footer_text(s)
    button = f"a button {quoted(s['cta_button'])} linking to {booking}"
    if general:
        head = (f"Build a one-page website: {name}'s own walkthrough page, one page for every lead in a campaign.\n"
                f"A lead lands on it from an email or a reply to see {s['deliverable']}. Its one job is to get them to book a "
                f"walkthrough call ({call_length(s)}).")
        page_rule = ("- It is one reusable page in our own brand: no lead's name, logo or brand on it, except the merge "
                     "lines below.")
        note = ""
        gives = f"{quoted(s['deliverable'])}"
    else:
        head = (f"Build a one-page website: a walkthrough page for {name}, prepared by {by}.\n"
                f"A prospect from {name} lands on it after asking for {s['deliverable']}. Its one job is to get them to "
                f"book a walkthrough call ({call_length(s)}).")
        page_rule = ("- The page is in the brand's look but is not their website: no links to their other pages, no copy "
                     "taken from their site beyond what is below.")
        walked = f"Walked through live: {s['deliverable']} for {s['best_product']}."
        note = f"\n   - Then a small note: {quoted(walked)}"
        gives = quoted(f"{s['deliverable']} for {s['best_product']}")
    merges = [(label, str(s.get(key) or "").strip(), s[base]) for label, key, base in
              (("eyebrow", "merge_eyebrow", "eyebrow"), ("popup eyebrow", "merge_popup_eyebrow", "popup_eyebrow"))]
    merges = [m for m in merges if m[1]] if general else []
    merge = ""
    if merges:
        merge = ("\n\nMerge tags from the link (the only per-lead parts):\n"
                 "- The page link may carry ?first_name= and ?company=. Fill them in as plain text, at most 60 "
                 "characters each, never as HTML.\n"
                 + "\n".join(f"- The {label}: when the link has every tag in {quoted(line)}, show that line with them "
                              f"filled in; otherwise show {quoted(fallback)}." for label, line, fallback in merges))
    return f"""{head}
Every button on the page links to {booking}.

Rules:
- Use only the copy below, word for word. Do not invent results, reviews, numbers, testimonials, client logos or customer names, and do not add sections beyond the ones listed.
- Each proof point shows its source under it, as written.
- In the page settings, hide the page from search engines (noindex, nofollow).
- The footer always reads: {quoted(footer)}
{page_rule}

Brand:
- {logo_line(run_dir, brand)}
- Colors: main {pal['primary']} for buttons and accents, with {pal['on_primary']} button text. Page background {pal['canvas']}, text {pal['text']}, muted text {pal['muted']}. The closing band is {pal['dark']} with {pal['accent_on_dark']} accents.
- {font_line(brand)}
- Light layout, rounded cards, generous spacing.

Sections, top to bottom:
1. Announcement banner: a thin dismissible bar across the top.
   - Text: {quoted(s['banner_text'])}
   - Link: {quoted(s['banner_link_text'])} to {s['case_studies_url']}
2. Header, sticky: the logo on the left, and on the right a small version of {button}.
3. Hero, two columns (on a phone, stacked with the {media} right under the headline).
   - Left, eyebrow: {quoted(s['eyebrow'])}
   - Left, headline: {quoted(s['headline'])}
   - Left, subhead: {quoted(s['subhead'])}
   - Left, paragraph: {quoted(s['lede'])}
   - Right: {video}
4. Booking, directly under the {media}:
   - The line: {quoted(s['cta_line'])}
   - Then a large version of {button}{note}
5. On-the-call card, next to or under the booking block, titled {quoted(s['call_gets_title'])}:
{gets}
6. Deliverables: a short card titled "What you are getting" that says {gives}
7. Proof, titled {quoted(s['proof_title'])}.{intro}
   - One card per point:
{proof}
8. Closing band: a dark full-width panel with the line {quoted(s['final_title'])} and {button}.
9. Footer: the line from the rules above.

Exit-intent popup, one modal:
- Eyebrow: {quoted(s['popup_eyebrow'])}
- Title: {quoted(s['popup_title'])}
- Body: {quoted(popup_body(s))}
- One button: {quoted(s['popup_cta'])} linking to {booking}
- Desktop: opens when the mouse leaves through the top of the window, after 8 seconds on the page.
- Phone: opens on an upward scroll of more than 80 pixels after 25 seconds, or after 75 seconds on the page.
- At most once per 7 days in the same browser. Closes with the X, the Escape key or a click on the backdrop. Once closed, or once any booking button is clicked, it does not open again.{merge}
"""


def template_copy(s: dict) -> dict:
    """The run folder's copy with this prospect's name and product swapped for {company} and {best product}."""
    name, product = s["brand"]["name"], str(s.get("best_product") or "").strip()
    tags = {name: "{company}"}
    if product:
        tags[product] = "{best product}"
    pattern = re.compile("|".join(re.escape(k) for k in sorted(tags, key=len, reverse=True)))

    def swap(v):
        if isinstance(v, str):
            return pattern.sub(lambda m: tags[m.group(0)], v)
        if isinstance(v, list):
            return [swap(x) for x in v]
        if isinstance(v, dict):
            return {k: swap(x) for k, x in v.items()}
        return v
    return {k: swap(v) for k, v in s.items() if k not in ("brand", "proof")}


def copilot_workflow_prompt(s: dict) -> str:
    """The Instantly Copilot prompt that sets up a workflow building one page per positive reply, from this template."""
    t = template_copy(s)
    booking, by = s["booking_url"], s["from_name"].strip().rstrip(".")
    gets = "\n".join(f"     - {quoted(g)}" for g in t["call_gets"] if str(g).strip())
    check = "[check in your workspace]"
    return f"""Set up an Instantly workflow (Automation) that builds a walkthrough page for every lead who replies positively,
from the template below. Save it as a Draft and leave it off: a person reviews it and turns it on.
The workflow never sends the reply: a person sends the page link in the same thread.

Trigger:
- Instantly, Lead Interest Status Changed, interest status Interested, all campaigns (or the lead-magnet campaign).
  To fire on any positive label instead, use the trigger for any positive label {check}.

Steps:
1. Read the lead from the trigger: first name, company name, website and email
   ({{{{trigger__lead.firstName}}}}, {{{{trigger__lead.companyName}}}}, {{{{trigger__lead.website}}}}, {{{{trigger__lead.email}}}}).
   No website on the lead: stop and post the lead to the team (step 3) without a page.
2. Build the page with Instantly Copilot {check}: a new website named after the company, built from the template below.
   From the lead's website read only the logo, the main brand color, the font and the product the site leads with.
   Proof: only points the lead's own website shows, each with its source page under it; none found, leave the proof
   section out. Do not invent results, reviews, numbers, testimonials or names.
3. Return the page link for the reply: post it to the team's Slack channel (Slack, Send Message) with the lead's name,
   company and email, and a Unibox link to the thread. Where the website step outputs the page link {check}.
   The person then replies in the same thread: "we're prepping your {s['deliverable']} now, here's where they'll be: <page link>".

Template (one page per lead; {{company}} is the lead's company name, {{best product}} the product their website leads with):
- Rules: use this copy word for word with those two filled in; where a line still names another company's product,
  use {{best product}} there instead. Hide the page from search engines (noindex, nofollow).
  Footer, always: "A walkthrough page prepared for {{company}} by {by}. {{company}} names and marks belong to their owner."
  The page is in the lead's brand but is not their website. Every button links to {booking}.
- 1. Announcement banner: {quoted(t['banner_text'])} with the link {quoted(t['banner_link_text'])} to {s['case_studies_url']}
- 2. Header, sticky: their logo, and a small button {quoted(t['cta_button'])}.
- 3. Hero, two columns: eyebrow {quoted(t['eyebrow'])}, headline {quoted(t['headline'])}, subhead {quoted(t['subhead'])},
     paragraph {quoted(t['lede'])}; on the right the video {str(s.get('vsl_url') or '').strip() or 'placeholder (the video is added before the link is sent)'}, captioned {quoted(t['vsl_caption'])}.
- 4. Booking, directly under the video: {quoted(t['cta_line'])}, then a large button {quoted(t['cta_button'])}.
- 5. On-the-call card titled {quoted(t['call_gets_title'])}:
{gets}
- 6. Deliverables: a card titled "What you are getting" that says "{t['deliverable']} for {{best product}}".
- 7. Proof, titled {quoted(t['proof_title'])}: the lead's own sourced points (step 2).
- 8. Closing band, dark: {quoted(t['final_title'])} and the button {quoted(t['cta_button'])}.
- 9. Footer: the line from the rules.
- Exit-intent popup: eyebrow {quoted(t['popup_eyebrow'])}, title {quoted(t['popup_title'])}, body {quoted(popup_body(t))},
  one button {quoted(t['popup_cta'])}. Desktop: the mouse leaves through the top after 8 seconds. Phone: an upward
  scroll of more than 80 pixels after 25 seconds, or 75 seconds on the page. At most once per 7 days; closes with
  the X, Escape or the backdrop.
"""


def linking_note(s: dict) -> str:
    """For a general page: how to link the one page from the campaign or a reply, with the merge tags."""
    tags = "first_name={{firstName}}&company={{companyName}}"
    merge = any(str(s.get(k) or "").strip() for k in MERGE_FIELDS)
    return f"""# Linking the general page: {s['brand']['name']}

One page for every lead in the campaign. No per-reply workflow and no page per lead: build it once with `prompt.md` in
Instantly Copilot, publish it, then link it. Nothing here sends anything; a person adds the link and sends.

1. The page link is the published URL plus `?utm_source=instantly&utm_medium=email&utm_campaign=<campaign>`.
2. {"Add the merge tags so the page greets the lead: append" if merge else "Optional merge tags (only if you add merge_eyebrow or merge_popup_eyebrow):"}
   `&{tags}`. Instantly fills `{{{{firstName}}}}` and `{{{{companyName}}}}` when it sends; send yourself a test
   preview and check the link opens with them filled in and encoded [check in your workspace]. A lead without the
   values sees the page as written.
3. Where to put it: in the campaign step that offers {s['deliverable']}, or in the reply to a positive answer:
   > Here it is: <page link>. The fastest way to use it is a quick call, {call_length(s)}, where I walk you through it.
   > Grab a time here: {s['booking_url']}
4. Keep Instantly link tracking off; the UTM tags tie visits to the campaign.
"""


def prompt_fails(text: str) -> list:
    """Return the failures for a Copilot prompt; empty means it passes."""
    fails = []
    m = FORBIDDEN_RE.search(text)
    if m:
        fails.append(f"reference strings: the prompt contains '{m.group(0)}'")
    if "TODO" in text:
        fails.append("unfilled: a TODO is left in the prompt")
    for need, why in [("noindex", "the page is hidden from search engines"),
                      (r"A walkthrough page (prepared for|by)", "the footer says who prepared the page"),
                      ("Do not invent", "the nothing-invented rule")]:
        if not re.search(need, text):
            fails.append(f"rule missing: {why}")
    return fails


# ---------- CLI ----------

def load_sections(run_dir: pathlib.Path) -> dict:
    f = run_dir / "sections.json"
    if not f.is_file():
        sys.exit(f"error: {f} not found; run extract first")
    return json.loads(f.read_text(encoding="utf-8"))


def cmd_extract(a) -> int:
    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    facts, logo, ext = extract(a.url, a.html)
    (out / "brand.json").write_text(json.dumps(facts, indent=2) + "\n", encoding="utf-8")
    if logo:
        (out / f"logo.{ext}").write_bytes(logo)
    sec = out / "sections.json"
    if sec.exists() and not a.force:
        print(f"kept {sec} (pass --force to replace it)")
    else:
        sec.write_text(json.dumps(starter_sections(facts, a), indent=2) + "\n", encoding="utf-8")
        print(f"wrote {sec}")
    print(f"wrote {out / 'brand.json'}: {facts['name']} ({facts['name_source']}), "
          f"color {facts['colors'][0]['hex'] if facts['colors'] else 'none'}, font {facts['font']['family'] or 'none'}, "
          f"logo {facts['logo']['source']}, {len(facts['product_candidates'])} product and "
          f"{len(facts['proof_candidates'])} proof candidates")
    for n in facts["notes"]:
        print(f"note: {n}")
    return 0


def cmd_check(a) -> int:
    errors, notes = check(load_sections(pathlib.Path(a.dir)))
    for e in errors:
        print(f"error: {e}")
    for n in notes:
        print(f"note: {n}")
    if not errors:
        print("ok")
    return 1 if errors else 0


def cmd_build(a) -> int:
    run_dir = pathlib.Path(a.dir)
    s = load_sections(run_dir)
    errors, notes = check(s)
    if errors:
        for e in errors:
            print(f"error: {e}")
        print("not built: fix the errors above (check DIR lists them)")
        return 1
    page = render(run_dir, s)
    fails = verify(page)
    if fails:
        for f in fails:
            print(f"fail: {f}")
        return 1
    out = pathlib.Path(a.out) if a.out else run_dir / "index.html"
    out.write_text(page, encoding="utf-8")
    for n in notes:
        print(f"note: {n}")
    print(f"wrote {out} ({len(page.encode()) // 1024} KB), verify passed")
    return 0


def cmd_prompt(a) -> int:
    run_dir = pathlib.Path(a.dir)
    s = load_sections(run_dir)
    errors, notes = check(s)
    if errors:
        for e in errors:
            print(f"error: {e}")
        print("no prompt written: fix the errors above (check DIR lists them)")
        return 1
    general = page_mode(s) == "general"
    text = copilot_prompt(run_dir, s)
    fails = [f"prompt.md: {x}" for x in prompt_fails(text)]
    if general:
        extra, extra_name = linking_note(s), "linking.md"
        m = FORBIDDEN_RE.search(extra)
        fails += [f"linking.md: reference strings: the note contains '{m.group(0)}'"] if m else []
    else:
        extra, extra_name = copilot_workflow_prompt(s), "workflow-prompt.md"
        fails += [f"workflow-prompt.md: {x}" for x in prompt_fails(extra)]
    if fails:
        for f in fails:
            print(f"fail: {f}")
        return 1
    out = pathlib.Path(a.out) if a.out else run_dir / "prompt.md"
    extra_out = out.with_name(extra_name)
    out.write_text(text, encoding="utf-8")
    extra_out.write_text(extra, encoding="utf-8")
    for n in notes:
        print(f"note: {n}")
    print(f"wrote {out}: paste it into Instantly Copilot to build the page")
    if general:
        print(f"wrote {extra_out}: how to link the one general page from the campaign or a reply (no workflow needed)")
    else:
        print(f"wrote {extra_out}: paste it into Instantly Copilot to set up the workflow that builds a page per positive "
              f"reply (a Draft; a person turns it on and sends each reply)")
    return 0


def cmd_verify(a) -> int:
    f = pathlib.Path(a.file)
    if not f.is_file():
        print(f"error: {f} not found; run build first")
        return 1
    fails = verify(f.read_text(encoding="utf-8"))
    for f in fails:
        print(f"fail: {f}")
    if not fails:
        print("ok: banner, hero with VSL slot, booking CTA under the video, proof, exit popup; popup rules; no reference strings")
    return 1 if fails else 0


# ---------- clone ----------

LIST_REQUIRED = ("campaign", "sender_name", "domain")
# Same day after the reply, double dial each time (call, and if no answer call straight back).
CALL_OFFSETS = (("15 minutes", timedelta(minutes=15)), ("1 hour", timedelta(hours=1)), ("4 hours", timedelta(hours=4)))


def parse_replied(value: str) -> datetime:
    t = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if t.tzinfo is None:
        raise ValueError("needs a time zone, for example 2026-11-23T14:05:00Z")
    return t.astimezone(timezone.utc)


def clone_plan(data, base: pathlib.Path) -> tuple[list, list, list]:
    """Returns (errors, notes, ready). Each ready item carries its run folder, sections and reply time."""
    errors, notes, ready = [], [], []
    if not isinstance(data, dict):
        return ["the list must be a JSON object with campaign, sender_name, domain and prospects"], notes, ready
    for key in LIST_REQUIRED:
        if not isinstance(data.get(key), str) or not data[key].strip():
            errors.append(f"{key} is required and must be text")
    domain = data.get("domain")
    if isinstance(domain, str) and domain.strip() and not re.fullmatch(r"[a-z0-9-]+(\.[a-z0-9-]+)+", domain):
        errors.append(f"domain {domain!r} must be a bare domain such as pages.youragency.com")
    prospects = data.get("prospects")
    if not isinstance(prospects, list) or not prospects:
        errors.append("prospects must be a non-empty list")
        prospects = []
    seen = {}
    for i, p in enumerate(prospects):
        who = f"prospects[{i}]"
        if not isinstance(p, dict):
            errors.append(f"{who} must be an object")
            continue
        wrong = [k for k in ("run_dir", "replied_at", "first_name") if p.get(k) is not None and not isinstance(p[k], str)]
        times = p.get("times")
        if times is not None and not (isinstance(times, list) and all(isinstance(t, str) for t in times)):
            wrong.append("times (a list of text)")
        if wrong:
            errors.append(f"{who}: {', '.join(wrong)} must be text")
            continue
        if not str(p.get("run_dir") or "").strip():
            errors.append(f"{who}: run_dir is required (a run folder with a filled sections.json)")
            continue
        run_dir = base / p["run_dir"]
        who = f"{who} ({p['run_dir']})"
        if not p.get("replied_at"):
            notes.append(f"{who}: skipped, no replied_at - build pages only after a reply")
            continue
        try:
            replied = parse_replied(p["replied_at"])
        except ValueError as e:
            errors.append(f"{who}: replied_at {p['replied_at']!r}: {e}")
            continue
        f = run_dir / "sections.json"
        try:
            sections = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            errors.append(f"{who}: cannot read {f}: {e}")
            continue
        errs, nts = check(sections)
        errors += [f"{who}: {e}" for e in errs]
        notes += [f"{who}: {n}" for n in nts]
        if errs:
            continue
        if page_mode(sections) == "general":
            errors.append(f"{who}: a general page is one page for the whole campaign, not one per prospect; "
                          f"run prompt or build on that folder instead")
            continue
        slug = sections["slug"]
        if slug in seen:
            errors.append(f"{who}: slug {slug!r} is already used by {seen[slug]}; set a different slug")
            continue
        seen[slug] = who
        ready.append({**p, "run_dir": run_dir, "sections": sections, "replied": replied})
    return errors, notes, ready


def utm_query(campaign: str) -> str:
    return urllib.parse.urlencode({"utm_source": "instantly", "utm_medium": "email", "utm_campaign": slugify(campaign)})


def handoff(data: dict, p: dict, site_dir: pathlib.Path) -> str:
    s, replied = p["sections"], p["replied"]
    slug, brand, deliverable = s["slug"], s["brand"]["name"], s["deliverable"]
    name = (p.get("first_name") or "").strip()
    greet = f" {name}" if name else ""
    query = utm_query(data["campaign"])
    host = f"{slug}.{data['domain']}"
    project = f"{slugify(s['from_name'])}-{slug}"[:58].strip("-")
    times = [t for t in (p.get("times") or []) if t.strip()]
    length = call_length(s)
    ask = (f"The fastest way to use them is a quick call, {length}, where I walk you through your {deliverable} and how "
           f"I'd run them for {brand}. ")
    ask += (f"Would {times[0]} or {times[1]} work? Or grab a time here: {s['booking_url']}" if len(times) >= 2
            else f"Grab a time here: {s['booking_url']}")
    gets = [str(g) for g in s["call_gets"] if str(g).strip()]
    sender = f"{data['sender_name']} from {s['from_name']}"
    opener = (f"Hi{greet}, it's {sender}{'' if sender.endswith('.') else '.'} You just asked for the {deliverable}. "
              f"Quick one: {length} on a call and I'd walk you through it: {gets[0]}. "
              f"When works today or tomorrow?")
    calls = "\n".join(f"| {i} | {label} after the reply | {(replied + d).strftime('%Y-%m-%d %H:%M')} UTC | double dial |"
                      for i, (label, d) in enumerate(CALL_OFFSETS, 1))
    proof = "\n".join(f"     - {item['text']} ({item['source']})" for item in s["proof"])
    return f"""# {brand}: lead-magnet page handoff

Replied: {replied.strftime('%Y-%m-%d %H:%M')} UTC. Nothing below has been sent, called or deployed.

## 1. Host the page first (a person's step, never run by the skill)

### Instantly website (first choice)

Instantly's websites feature is behind a feature flag and has no public API or instantly-cli route, so a person builds
the site in the Instantly web app, with Instantly Copilot:

1. Open the websites feature and create one site for this prospect, named `{slug}`.
2. Paste the whole `{site_dir.parent / 'prompt.md'}` into Instantly Copilot and let it build the page. Then check
   what it built against this list, in this order, and fix any part it missed or reworded (no Copilot on the workspace:
   paste the whole `{site_dir / 'index.html'}` into a custom HTML block, or rebuild these parts by hand):
   - Banner: "{s['banner_text']}" with "{s['banner_link_text']}" linking to {s['case_studies_url']}
   - Hero: "{s['headline']}", the subhead and lede, and the VSL ({s.get('vsl_url') or 'none yet: record it before sending the link'})
   - Under the video: "{s['cta_line']}" and the button "{s['cta_button']}" linking to {s['booking_url']}
   - Proof, each with its source:
{proof}
   - Exit popup, if the editor has one: "{s['popup_title']}" / "{popup_body(s)}" / button "{s['popup_cta']}" linking
     to {s['booking_url']}. If it has none, say so and use the Cloudflare page below for this prospect instead.
3. Open the published site once at desktop and phone width, then use its URL with `?{query}` on the end as the page link
   in the reply below.

### Fallback: Cloudflare Pages

Fallback page link once deployed: https://{host}/?{query}

```bash
npx wrangler pages project create {project} --production-branch main
npx wrangler pages deploy "{site_dir}" --project-name {project} --branch main
```

Then in the Cloudflare dashboard: Workers & Pages > {project} > Custom domains > Set up a custom domain > `{host}`.
Open the page link yourself once, on a phone too, before you send it.

## 2. Reply now, in the same thread

The page link is the hosted site's URL with `?{query}` on the end (the Instantly site, or https://{host}/ on the
fallback).

> Thanks{greet}, we're prepping your {deliverable} now, here's where they'll be: <page link>
>
> {ask}

Mark the lead Interested in Instantly. Send the page link, never a Drive link or an attachment.

## 3. Call the same day, only because they replied

| # | When | Time | How |
|---|---|---|---|
{calls}

Open with what the call gets them, not with the pitch:

> {opener}

No answer on all three? Leave it to the follow-ups. A voice agent can take these first dials only where the AI calling
rules for you and the lead allow it; check them first.
"""


def cmd_clone(a) -> int:
    f = pathlib.Path(a.list)
    try:
        data = json.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        print(f"error: cannot read {f}: {e}")
        return 1
    errors, notes, ready = clone_plan(data, f.resolve().parent)
    for n in notes:
        print(f"note: {n}")
    out = pathlib.Path(a.out)
    built = []
    for p in ready if not errors else []:
        site = out / p["sections"]["slug"] / "site"
        page = render(p["run_dir"], p["sections"])
        errors += [f"{p['sections']['slug']}: verify: {x}" for x in verify(page)]
        text = copilot_prompt(p["run_dir"], p["sections"])
        errors += [f"{p['sections']['slug']}: prompt: {x}" for x in prompt_fails(text)]
        built.append((p, site, page, text, handoff(data, p, site.resolve())))
    if errors:
        for e in errors:
            print(f"error: {e}")
        print("nothing built: fix the errors above")
        return 1
    if not ready:
        print("nothing to build: no prospect has replied yet")
        return 0
    for p, site, page, prompt, text in built:
        site.mkdir(parents=True, exist_ok=True)
        (site / "index.html").write_text(page, encoding="utf-8")
        (site.parent / "prompt.md").write_text(prompt, encoding="utf-8")
        (site.parent / "handoff.md").write_text(text, encoding="utf-8")
        print(f"built: {p['sections']['brand']['name']} -> {site.parent / 'prompt.md'}, {site / 'index.html'} "
              f"and {site.parent / 'handoff.md'}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("extract", help="read the site, write brand.json and a starter sections.json")
    e.add_argument("url")
    e.add_argument("--out", required=True)
    e.add_argument("--html", help="read this saved HTML file instead of fetching (offline)")
    e.add_argument("--deliverable", default="")
    e.add_argument("--booking-url", default="")
    e.add_argument("--case-studies-url", default="")
    e.add_argument("--force", action="store_true", help="replace an existing sections.json")
    e.add_argument("--mode", choices=MODES, default="personal",
                   help="personal: one page per replied prospect, read from their site (default). general: one page for "
                        "every lead in a campaign, read from your own site, around a VSL or a case-study document")
    c = sub.add_parser("check", help="list what sections.json still needs")
    c.add_argument("dir")
    b = sub.add_parser("build", help="render DIR/index.html and verify it")
    b.add_argument("dir")
    b.add_argument("--out")
    pr = sub.add_parser("prompt", help="write DIR/prompt.md (the Copilot prompt for the page) and DIR/workflow-prompt.md "
                                       "(the Copilot prompt for a workflow that builds one per positive reply)")
    pr.add_argument("dir")
    pr.add_argument("--out")
    v = sub.add_parser("verify", help="check a built page")
    v.add_argument("file")
    k = sub.add_parser("clone", help="build one page and handoff per prospect who replied, from a list of run folders")
    k.add_argument("list")
    k.add_argument("--out", required=True, help="output folder, outside this repo for real prospects")
    a = ap.parse_args(argv)
    return {"extract": cmd_extract, "check": cmd_check, "build": cmd_build, "verify": cmd_verify,
            "clone": cmd_clone, "prompt": cmd_prompt}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
