#!/usr/bin/env python3
"""Render the interior pages of the Dent-Aura site from shared shell + content partials.

The site has no bundler, so this script is the single source of truth for the
header, footer and <head> of every page except index.html (which is hand-authored).
Run it after editing anything in scripts/pages/, then commit the generated HTML.

    python scripts/build-pages.py
"""
import io
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARTIALS = os.path.join(ROOT, "scripts", "pages")

SITE = "https://dent-aura-mumbai.netlify.app"
CLINIC_ID = SITE + "/#clinic"
OG_IMAGE = SITE + "/assets/img/og-card.jpg"  # 1200x630, built by scripts/build-images.py
WA = ("https://wa.me/919082727843?text=Hi%20Dent-Aura%2C%20I%27d%20like%20to"
      "%20book%20an%20appointment.")
TEL = "+919082727843"

NAV = [
    ("/services", "Services"),
    ("/#aesthetics", "Skin &amp; Aesthetics"),
    ("/#doctors", "Doctors"),
    ("/fees", "Fees"),
    ("/#testimonials", "Reviews"),
    ("/contact", "Contact"),
]

WA_SVG = ('<svg width="17" height="17" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48'
          ' 2 2 6.48 2 12c0 1.85.5 3.58 1.35 5.07L2 22l5.1-1.33A9.94 9.94 0 0012 22c5.52 0 10-4.48'
          ' 10-10S17.52 2 12 2zm5.2 14.2c-.22.62-1.3 1.2-1.8 1.27-.46.07-1.03.1-1.66-.1-.38-.12-.87'
          '-.28-1.5-.56-2.64-1.14-4.36-3.8-4.5-3.98-.13-.18-1.08-1.44-1.08-2.75 0-1.3.68-1.94.92-2.2'
          '.24-.27.53-.33.7-.33h.5c.16 0 .38-.06.6.46.22.53.75 1.83.82 1.96.07.13.11.29.02.47-.09.18'
          '-.13.29-.26.44-.13.16-.28.35-.4.47-.13.13-.27.27-.12.53.16.27.7 1.16 1.51 1.88 1.04.93'
          ' 1.92 1.22 2.19 1.36.27.13.42.11.58-.07.16-.18.68-.79.86-1.06.18-.27.36-.22.6-.13.24.09'
          ' 1.53.72 1.79.85.27.13.45.2.51.31.07.13.07.71-.15 1.33z"/></svg>')

SHELL = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <meta name="description" content="{description}">
    <link rel="canonical" href="{canonical}">

    <meta property="og:type" content="website">
    <meta property="og:site_name" content="Dent-Aura Dental And Cosmetic Clinic">
    <meta property="og:title" content="{og_title}">
    <meta property="og:description" content="{description}">
    <meta property="og:url" content="{canonical}">
    <meta property="og:image" content="{og_image}">
    <meta property="og:image:alt" content="Dent-Aura Dental and Cosmetic Clinic, Sion, Mumbai">
    <meta property="og:image:width" content="1200">
    <meta property="og:image:height" content="630">
    <meta property="og:image:type" content="image/jpeg">
    <meta property="og:locale" content="en_IN">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{og_title}">
    <meta name="twitter:description" content="{description}">
    <meta name="twitter:image" content="{og_image}">

    <script type="application/ld+json">
{schema}
    </script>

    <link rel="icon" type="image/jpeg" href="/assets/logo.jpg">
    <link rel="apple-touch-icon" href="/assets/logo.jpg">
    <meta name="theme-color" content="#0F2438">
    <meta name="color-scheme" content="light">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600;700&family=Inter:wght@400;500;600;700&family=IBM+Plex+Mono:wght@500&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="/assets/site.css">
  </head>
  <body>

    <a class="skip-link" href="#main">Skip to main content</a>
    <header>
      <nav class="nav">
        <a href="/" class="brand">
          <img class="brand-mark" src="/assets/logo.jpg" alt="Dent-Aura logo" width="74" height="74">
          <span class="brand-word">Dent-Aura<span>DENTAL &amp; COSMETIC CLINIC</span></span>
        </a>
        <ul class="nav-links" id="nav-links">
{nav}
        </ul>
        <div class="nav-cta">
          <a class="btn btn-primary" href="{wa}" target="_blank" rel="noopener">
            {wa_svg}
            Book on WhatsApp
          </a>
        </div>
        <button class="nav-toggle" aria-label="Toggle menu" aria-controls="nav-links" aria-expanded="false" type="button">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#0F2438" stroke-width="2"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>
        </button>
      </nav>
    </header>

    <main id="main">
      <section class="page-hero">
        <div class="wrap">
          <nav class="breadcrumbs" aria-label="Breadcrumb">
            <ol>
{crumbs}
            </ol>
          </nav>
          <div class="eyebrow" style="margin-top:18px;">{eyebrow}</div>
          <h1>{h1}</h1>
          <p>{lede}</p>
          <div class="hero-ctas">
            <a class="btn btn-primary" href="{wa}" target="_blank" rel="noopener">{wa_svg} Book on WhatsApp</a>
            <a class="btn btn-ghost" style="color:#fff;border-color:rgba(255,255,255,0.35);" href="tel:{tel}">Call +91 90827 27843</a>
          </div>
        </div>
      </section>

{body}
    </main>

    <footer>
      <div class="wrap">
        <div class="foot-grid">
          <div>
            <div class="foot-brand">
              <img src="/assets/logo.jpg" alt="Dent-Aura logo" width="46" height="46" style="object-fit:contain;border-radius:8px;">
              <span class="brand-word" style="color:#fff;">Dent-Aura</span>
            </div>
            <p style="font-size:14px;line-height:1.7;max-width:34ch;color:#9AA7B4;">Dental &amp; cosmetic clinic in Sion, Mumbai — general dentistry, cosmetic dentistry, orthodontics, implants and select skin &amp; hair aesthetics.</p>
          </div>
          <div>
            <h5>Explore</h5>
            <ul>
              <li><a href="/services">Dental services</a></li>
              <li><a href="/services/root-canal-treatment">Root canal treatment</a></li>
              <li><a href="/services/dental-implants">Dental implants</a></li>
              <li><a href="/services/braces-and-aligners">Braces &amp; aligners</a></li>
              <li><a href="/fees">Treatment fees</a></li>
              <li><a href="/#aesthetics">Skin &amp; Aesthetics</a></li>
              <li><a href="/contact">Contact &amp; directions</a></li>
            </ul>
          </div>
          <div>
            <h5>Contact</h5>
            <ul>
              <li>Sion Railway Station, Sindhi Colony, Sion, Mumbai 400022 (next to McDonald's)</li>
              <li><a href="tel:{tel}">+91 90827 27843</a></li>
              <li><a href="https://www.instagram.com/dentaura_32/" target="_blank" rel="noopener">@dentaura_32</a></li>
            </ul>
          </div>
        </div>
        <div class="foot-bottom">
          <span>© <span id="year"></span> Dent-Aura Dental And Cosmetic Clinic. All rights reserved.</span>
          <div class="foot-social">
            <a href="https://www.instagram.com/dentaura_32/" target="_blank" rel="noopener" aria-label="Instagram">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="#fff"><path d="M12 2.2c3.2 0 3.6 0 4.9.07 1.2.06 2 .25 2.4.42.6.24 1 .53 1.5 1s.76.9 1 1.5c.17.4.36 1.2.42 2.4.06 1.3.07 1.7.07 4.9s0 3.6-.07 4.9c-.06 1.2-.25 2-.42 2.4-.24.6-.53 1-1 1.5s-.9.76-1.5 1c-.4.17-1.2.36-2.4.42-1.3.06-1.7.07-4.9.07s-3.6 0-4.9-.07c-1.2-.06-2-.25-2.4-.42a4 4 0 01-1.5-1 4 4 0 01-1-1.5c-.17-.4-.36-1.2-.42-2.4C2.2 15.6 2.2 15.2 2.2 12s0-3.6.07-4.9c.06-1.2.25-2 .42-2.4a4 4 0 011-1.5 4 4 0 011.5-1c.4-.17 1.2-.36 2.4-.42C8.4 2.2 8.8 2.2 12 2.2z"/></svg>
            </a>
            <a href="https://wa.me/919082727843" target="_blank" rel="noopener" aria-label="WhatsApp">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="#fff"><path d="M12 2C6.48 2 2 6.48 2 12c0 1.85.5 3.58 1.35 5.07L2 22l5.1-1.33A9.94 9.94 0 0012 22c5.52 0 10-4.48 10-10S17.52 2 12 2z"/></svg>
            </a>
          </div>
        </div>
      </div>
    </footer>

    <a class="wa-float" href="{wa}" target="_blank" rel="noopener" aria-label="Chat on WhatsApp">
      <svg width="28" height="28" viewBox="0 0 24 24" fill="#fff"><path d="M12 2C6.48 2 2 6.48 2 12c0 1.85.5 3.58 1.35 5.07L2 22l5.1-1.33A9.94 9.94 0 0012 22c5.52 0 10-4.48 10-10S17.52 2 12 2zm5.2 14.2c-.22.62-1.3 1.2-1.8 1.27-.46.07-1.03.1-1.66-.1-.38-.12-.87-.28-1.5-.56-2.64-1.14-4.36-3.8-4.5-3.98-.13-.18-1.08-1.44-1.08-2.75 0-1.3.68-1.94.92-2.2.24-.27.53-.33.7-.33h.5c.16 0 .38-.06.6.46.22.53.75 1.83.82 1.96.07.13.11.29.02.47-.09.18-.13.29-.26.44-.13.16-.28.35-.4.47-.13.13-.27.27-.12.53.16.27.7 1.16 1.51 1.88 1.04.93 1.92 1.22 2.19 1.36.27.13.42.11.58-.07.16-.18.68-.79.86-1.06.18-.27.36-.22.6-.13.24.09 1.53.72 1.79.85.27.13.45.2.51.31.07.13.07.71-.15 1.33z"/></svg>
    </a>

    <script src="/assets/site.js" defer></script>
  </body>
</html>
"""

# ---------------------------------------------------------------- page table
# out:         file written, relative to repo root
# url:         canonical path (Netlify serves .html without the extension)
# trail:       breadcrumb ancestors, [(url, label), ...]; current page appended
# procedure:   name of the MedicalProcedure this page is about, if any
PAGES = [
    dict(
        out="services/index.html", url="/services", partial="services",
        title="Dental Services in Sion, Mumbai | Dent-Aura Clinic",
        description=("Every dental treatment at Dent-Aura, Sion — check-ups, fillings, root canal, "
                     "crowns, extractions, braces, whitening, dentures and implants. Book on WhatsApp."),
        eyebrow="What we treat", h1="Dental services at our Sion clinic",
        lede=("Seven treatment categories under one roof, two minutes from Sion Railway Station. "
              "Pick the area that matches what's bothering you, or message us and describe it."),
        trail=[], label="Services",
    ),
    dict(
        out="services/root-canal-treatment.html", url="/services/root-canal-treatment",
        partial="root-canal",
        title="Root Canal Treatment in Sion, Mumbai | Dent-Aura",
        description=("Single-sitting and multi-visit root canal treatment in Sion, Mumbai. What RCT "
                     "involves, whether it hurts, healing time and when a crown is needed."),
        eyebrow="Restorative dentistry", h1="Root canal treatment in Sion, Mumbai",
        lede=("A root canal saves a tooth that would otherwise need removing. Here's what actually "
              "happens during the procedure, how long it takes and what recovery looks like."),
        trail=[("/services", "Services")], label="Root Canal Treatment",
        procedure="Root Canal Treatment",
    ),
    dict(
        out="services/dental-implants.html", url="/services/dental-implants",
        partial="implants",
        title="Dental Implants in Sion, Mumbai | Dent-Aura Clinic",
        description=("Single and multiple tooth implants in Sion, Mumbai. How implants work, who is "
                     "suitable, the treatment timeline and how they compare to bridges and dentures."),
        eyebrow="Replacing missing teeth", h1="Dental implants in Sion, Mumbai",
        lede=("An implant replaces the root of a missing tooth, so the replacement tooth is anchored "
              "in bone rather than resting on the teeth beside it."),
        trail=[("/services", "Services")], label="Dental Implants",
        procedure="Dental Implants",
    ),
    dict(
        out="services/braces-and-aligners.html", url="/services/braces-and-aligners",
        partial="braces",
        title="Braces &amp; Clear Aligners in Sion, Mumbai | Dent-Aura",
        description=("Metal braces, ceramic braces and clear aligners in Sion, Mumbai. How to choose, "
                     "how long treatment takes and what to expect at each stage."),
        eyebrow="Orthodontics", h1="Braces and clear aligners in Sion, Mumbai",
        lede=("Straightening teeth is about more than appearance — crowded or badly aligned teeth are "
              "harder to clean and wear unevenly over time."),
        trail=[("/services", "Services")], label="Braces &amp; Aligners",
        procedure="Braces and Clear Aligners",
    ),
    dict(
        out="fees.html", url="/fees", partial="fees",
        title="Treatment Fees | Dent-Aura Dental Clinic, Sion, Mumbai",
        description=("How pricing works at Dent-Aura, Sion — what affects the cost of a root canal, "
                     "crown, implant or braces, and how to get a written estimate before you commit."),
        eyebrow="Costs and estimates", h1="How treatment fees work at Dent-Aura",
        lede=("Dental costs vary with the tooth, the materials and how much work the tooth needs. "
              "We give you a written estimate before any treatment starts."),
        trail=[], label="Fees",
    ),
    dict(
        out="contact.html", url="/contact", partial="contact",
        title="Contact &amp; Directions | Dent-Aura, Sion, Mumbai",
        description=("Dent-Aura Dental and Cosmetic Clinic, Sindhi Colony, Sion, Mumbai 400022 — next "
                     "to McDonald's, 2 minutes from Sion Station. Hours, phone and directions."),
        eyebrow="Find us", h1="Contact Dent-Aura, Sion",
        lede=("We're in Sindhi Colony, right next to McDonald's and about a two-minute walk from Sion "
              "Railway Station. Call, WhatsApp, or just walk in during clinic hours."),
        trail=[], label="Contact",
    ),
]


MANIFEST = json.load(io.open(
    os.path.join(ROOT, "assets", "img", "manifest.json"), encoding="utf-8"))

# Partials write [[photo:stem|alt text|caption]] and get a responsive <figure>.
# Run scripts/build-images.py first — the widths come from its manifest.
PHOTO = re.compile(
    r"^(?P<indent>[ \t]*)\[\[photo:(?P<stem>[a-z0-9-]+)\|(?P<alt>[^|\]]+)"
    r"\|(?P<caption>[^\]]*)\]\]$", re.M)

FIGURE_SIZES = "(max-width:900px) 92vw, 640px"


def expand_photos(body):
    def repl(m):
        stem = m.group("stem")
        if stem not in MANIFEST:
            raise SystemExit("unknown photo %r — run scripts/build-images.py" % stem)
        info = MANIFEST[stem]
        i = m.group("indent")
        srcset = ", ".join("/assets/img/%s-%d.webp %dw" % (stem, w, w)
                           for w in info["widths"])
        caption = m.group("caption").strip()
        cap = ("\n{i}  <figcaption>{c}</figcaption>".format(i=i, c=caption)) if caption else ""
        return (
            '{i}<figure class="figure-shot">\n'
            '{i}  <picture>\n'
            '{i}    <source type="image/webp" sizes="{sizes}"\n'
            '{i}      srcset="{srcset}">\n'
            '{i}    <img src="/assets/img/{stem}.jpg" alt="{alt}"\n'
            '{i}      loading="lazy" decoding="async" width="{w}" height="{h}">\n'
            '{i}  </picture>{cap}\n'
            '{i}</figure>'
        ).format(i=i, sizes=FIGURE_SIZES, srcset=srcset, stem=stem,
                 alt=m.group("alt").strip(), w=info["width"], h=info["height"], cap=cap)

    return PHOTO.sub(repl, body)


def strip_tags(text):
    """Schema values must be plain text, not HTML entities."""
    return (text.replace("&amp;", "&").replace("&mdash;", "—")
                .replace("&nbsp;", " ").strip())


def build_schema(page):
    crumbs = [{"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"}]
    for i, (url, label) in enumerate(page["trail"], start=2):
        crumbs.append({"@type": "ListItem", "position": i,
                       "name": strip_tags(label), "item": SITE + url})
    crumbs.append({"@type": "ListItem", "position": len(crumbs) + 1,
                   "name": strip_tags(page["label"]), "item": SITE + page["url"]})

    graph = [{"@type": "BreadcrumbList", "itemListElement": crumbs}]

    if page.get("procedure"):
        graph.append({
            "@type": "MedicalWebPage",
            "@id": SITE + page["url"] + "#page",
            "url": SITE + page["url"],
            "name": strip_tags(page["title"]),
            "about": {"@type": "MedicalProcedure", "name": page["procedure"]},
            "provider": {"@id": CLINIC_ID},
        })
    else:
        graph.append({
            "@type": "WebPage",
            "@id": SITE + page["url"] + "#page",
            "url": SITE + page["url"],
            "name": strip_tags(page["title"]),
            "isPartOf": {"@id": CLINIC_ID},
        })

    faqs = extract_faqs(page["_body"])
    if faqs:
        graph.append({
            "@type": "FAQPage",
            "mainEntity": [
                {"@type": "Question", "name": q,
                 "acceptedAnswer": {"@type": "Answer", "text": a}}
                for q, a in faqs
            ],
        })

    doc = {"@context": "https://schema.org", "@graph": graph}
    return "\n".join("    " + line for line in
                     json.dumps(doc, indent=2, ensure_ascii=False).split("\n"))


FAQ_BLOCK = re.compile(r"<details>\s*<summary>(.*?)</summary>(.*?)</details>", re.S)
TAG = re.compile(r"<[^>]+>")


def extract_faqs(body):
    """Only emit FAQPage schema for Q&A that is genuinely rendered on the page."""
    out = []
    for q, a in FAQ_BLOCK.findall(body):
        question = strip_tags(TAG.sub("", q))
        answer = strip_tags(" ".join(TAG.sub(" ", a).split()))
        if question and answer:
            out.append((question, answer))
    return out


def render(page):
    nav = "\n".join(
        '          <li><a href="{0}"{2}>{1}</a></li>'.format(
            url, label, ' aria-current="page"' if url == page["url"] else "")
        for url, label in NAV)

    items = [('/', 'Home')] + page["trail"]
    crumbs = "\n".join(
        '              <li><a href="{0}">{1}</a></li>'.format(u, l) for u, l in items)
    crumbs += '\n              <li><span aria-current="page">{0}</span></li>'.format(page["label"])

    return SHELL.format(
        title=page["title"], og_title=page["title"], description=page["description"],
        canonical=SITE + page["url"], og_image=OG_IMAGE, schema=page["_schema"],
        nav=nav, crumbs=crumbs, eyebrow=page["eyebrow"], h1=page["h1"],
        lede=page["lede"], body=page["_body"], wa=WA, wa_svg=WA_SVG, tel=TEL)


def main():
    written = []
    for page in PAGES:
        src = os.path.join(PARTIALS, page["partial"] + ".html")
        page["_body"] = expand_photos(io.open(src, encoding="utf-8").read().rstrip("\n"))
        page["_schema"] = build_schema(page)

        dest = os.path.join(ROOT, page["out"])
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        io.open(dest, "w", encoding="utf-8", newline="\n").write(render(page))
        written.append(page["out"])
        print("wrote", page["out"])
    return written


if __name__ == "__main__":
    main()
