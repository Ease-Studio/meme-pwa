"""Generate the Meme Express gallery pages and sitemap.

Builds one page per meme template (from its JSON file), one page per search keyword
(templates from the meme CSV), the gallery index that links to all of them,
sitemap.xml, and robots.txt if the folder doesn't have one yet.

SEO on every page: a unique <title> and meta description, a canonical URL, Open Graph
tags, JSON-LD structured data, one <h1> with headings in order, descriptive alt text
and captions, breadcrumbs, and links between related pages.

Run it from the website folder:  python generate_gallery_pages.py
"""

import html
import json
import math
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple
from urllib.parse import urljoin, urlsplit
from xml.sax.saxutils import escape as xml_escape

from search import search


# -------------------------------------------------------------------------------------
# Site settings
# -------------------------------------------------------------------------------------

SITE_NAME = "Meme Express"
SITE_TAGLINE = "A Good Meme Maker • Go Fun The World!"
SITE_URL = "https://meme-express.io.vn/"  # the generated pages are served from the site root
LOGO_PATH = "/assets/icon.png"
PLAY_STORE_URL = "https://play.google.com/store/apps/details?id=com.ease_studio.meme"
IPHONE_INSTALL_VIDEO_URL = "https://youtube.com/shorts/jJvhzI0J0w4?feature=share"
BOOTSTRAP_CSS = "https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/css/bootstrap.min.css"

CSV_FILE = "/Users/nguyenduyy/AndroidStudioProjects/meme/scripts/python/memes_output.csv"
TEMPLATE_IMAGE_URL = "https://storage.googleapis.com/y_meme_templates/{id}.jpg"

GALLERY_INDEX_FILE = "./gallery.html"
SITEMAP_FILE = "./sitemap.xml"
ROBOTS_FILE = "./robots.txt"  # only written if the folder doesn't have one yet

# Pages this script doesn't build but that belong in sitemap.xml:
# (path on the site, local file whose modification date becomes <lastmod>)
OTHER_SITEMAP_PAGES = [
    ("", "./index.html"),
    ("about.html", "./about.html"),
    ("privacy_policy.html", "./privacy_policy.html"),
]

MAX_TITLE = 60              # search results cut off longer titles...
MAX_META_DESCRIPTION = 155  # ...and longer descriptions
EAGER_IMAGES = 4            # images at the top of the gallery index load right away, the rest lazily

PAGE_CSS = """
body { background: #f8f9fa; }
footer { margin-top: 80px; padding: 30px 0; color: #666; border-top: 1px solid #ddd; }
footer a { color: #495057; }
"""


# -------------------------------------------------------------------------------------
# Text helpers
# -------------------------------------------------------------------------------------

def clean(value) -> str:
    """Text with whitespace collapsed; None and NaN (empty CSV cells) become ""."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return ""
    return " ".join(str(value).split())


def esc(value) -> str:
    """Escape text or a URL for HTML element content and attributes."""
    return html.escape(clean(value), quote=True)


def truncate(text, limit: int) -> str:
    """Shorten to at most `limit` characters: at a sentence end if one is near, else at a word."""
    text = clean(text)
    if len(text) <= limit:
        return text
    head = text[:limit]
    sentence_end = max(head.rfind(". "), head.rfind("! "), head.rfind("? "))
    if sentence_end >= limit * 0.6:
        return head[: sentence_end + 1]
    return text[: limit - 1].rsplit(" ", 1)[0].rstrip(" ,;:.-–—") + "…"


def fit_title(*options: str) -> str:
    """The first option short enough to show in full in search results, else the shortest."""
    for option in options:
        if len(option) <= MAX_TITLE:
            return option
    return min(options, key=len)


def meme_subject(name: str) -> str:
    """'Drake' -> 'Drake Meme'. Names that already say 'meme' keep their wording."""
    base = re.sub(r"\s*\btemplates?\s*$", "", name, flags=re.IGNORECASE).strip() or name
    return base if re.search(r"\bmemes?\b", base, re.IGNORECASE) else f"{base} Meme"


def count_label(count: int, noun: str) -> str:
    """count_label(3, 'Cat meme') -> '3 Cat memes'."""
    return f"{count} {noun}{'' if count == 1 else 's'}"


def mentions(text: str, word: str) -> bool:
    """Whole-word match that also accepts -s, -es, -ing and -ed ('two choices' mentions 'Choice')."""
    return re.search(rf"\b{re.escape(word)}(?:s|es|ing|ed)?\b", text, re.IGNORECASE) is not None


def absolute_url(url) -> str:
    url = clean(url)
    return urljoin(SITE_URL, url) if url else ""


def origin_of(url: str) -> str:
    parts = urlsplit(url)
    return f"{parts.scheme}://{parts.netloc}" if parts.scheme and parts.netloc else ""


def newest_date(*paths) -> Optional[str]:
    """Latest modification date (YYYY-MM-DD, UTC) among the files that exist."""
    times = [os.path.getmtime(p) for p in paths if os.path.exists(p)]
    if not times:
        return None
    return datetime.fromtimestamp(max(times), tz=timezone.utc).date().isoformat()


# -------------------------------------------------------------------------------------
# Pages
# -------------------------------------------------------------------------------------

@dataclass(eq=False)
class Page:
    kind: str                     # "gallery" (one meme), "search" (one keyword) or "index"
    output_path: Path
    name: str                     # meme name, search keyword, or index title
    image: str = ""               # main image: card thumbnail, og:image, sitemap
    alt: str = ""                 # alt text for the main image
    lastmod: Optional[str] = None
    meme: dict = field(default_factory=dict)          # gallery pages: the meme's JSON
    rows: List[dict] = field(default_factory=list)    # search pages: the matching templates
    related: List["Page"] = field(default_factory=list, repr=False)

    @property
    def file_name(self) -> str:
        return self.output_path.name

    @property
    def url(self) -> str:
        return urljoin(SITE_URL, self.file_name)

    @property
    def label(self) -> str:
        """The page's subject, used for the <h1>, link text and breadcrumbs."""
        if self.kind == "gallery":
            return f"{meme_subject(self.name)} Template"
        if self.kind == "search":
            return f"{self.name} Memes"
        return self.name

    @property
    def keywords(self) -> List[str]:
        raw = self.meme.get("keywords") or []
        if isinstance(raw, str):
            raw = raw.split(",")
        return [k for k in (clean(k) for k in raw) if k]


@dataclass(eq=False)
class Site:
    gallery_pages: List[Page]
    search_pages: List[Page]
    index: Page


def load_gallery_page(json_file: str, output_path: str) -> Page:
    with open(json_file, "r", encoding="utf-8") as f:
        meme = json.load(f)
    name = clean(meme.get("name")) or "Unknown Meme"
    return Page(
        kind="gallery",
        output_path=Path(output_path),
        name=name,
        image=clean(meme.get("template_url")),
        alt=f"{meme_subject(name)} template",
        lastmod=newest_date(json_file, __file__),
        meme=meme,
    )


def load_search_page(keyword: str, output_path: str) -> Optional[Page]:
    rows, seen = [], set()
    for row in search(csv_file=CSV_FILE, keywords=[keyword]):
        meme_id, title = clean(row.get("id")), clean(row.get("title"))
        if not meme_id or not title or meme_id in seen:
            continue
        seen.add(meme_id)
        rows.append({
            "title": title,
            "description": clean(row.get("description")),
            "image": TEMPLATE_IMAGE_URL.format(id=meme_id),
        })
    if not rows:
        # An empty page would be thin content and a dead end, so it isn't built or linked.
        print(f"Skipped {output_path}: no templates match '{keyword}'")
        return None
    return Page(
        kind="search",
        output_path=Path(output_path),
        name=clean(keyword),
        image=rows[0]["image"],
        alt=f"{meme_subject(rows[0]['title'])} template",
        lastmod=newest_date(CSV_FILE, __file__),
        rows=rows,
    )


def link_related_pages(site: Site) -> None:
    """Connect each meme page with the search pages its name or keywords mention."""
    for page in site.gallery_pages:
        text = " ".join([page.name] + page.keywords)
        for search_page in site.search_pages:
            if mentions(text, search_page.name):
                page.related.append(search_page)
                search_page.related.append(page)


# -------------------------------------------------------------------------------------
# Shared HTML
# -------------------------------------------------------------------------------------

WEBSITE_ID = SITE_URL + "#website"


def render_json_ld(nodes: List[dict]) -> str:
    data = {
        "@context": "https://schema.org",
        "@graph": [{"@type": "WebSite", "@id": WEBSITE_ID, "url": SITE_URL, "name": SITE_NAME}] + nodes,
    }
    text = json.dumps(data, ensure_ascii=False, indent=2)
    # Escape <, > and & so text such as "</script>" inside the data can't end the tag early.
    text = text.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    return f'<script type="application/ld+json">\n{text}\n</script>'


def webpage_node(page: Page, schema_type: str, description: str, **extra) -> dict:
    """JSON-LD for the page itself (WebPage or CollectionPage)."""
    node = {
        "@type": schema_type,
        "@id": page.url + "#webpage",
        "url": page.url,
        "name": page.label,
        "description": description,
        "inLanguage": "en",
        "isPartOf": {"@id": WEBSITE_ID},
        "breadcrumb": {"@id": page.url + "#breadcrumb"},
    }
    if page.image:
        node["primaryImageOfPage"] = {
            "@type": "ImageObject",
            "contentUrl": absolute_url(page.image),
            "caption": page.alt,
        }
    if page.lastmod:
        node["dateModified"] = page.lastmod
    node.update({key: value for key, value in extra.items() if value})
    return node


def render_breadcrumbs(site: Site, page: Page) -> Tuple[str, dict]:
    """Visible breadcrumb trail plus the matching BreadcrumbList JSON-LD."""
    trail = [("Home", "/", SITE_URL)]  # (label, link, absolute URL)
    if page is not site.index:
        trail.append((site.index.label, site.index.file_name, site.index.url))
    trail.append((page.label, None, page.url))

    items = "".join(
        f'<li class="breadcrumb-item"><a href="{esc(link)}">{esc(label)}</a></li>'
        if link else
        f'<li class="breadcrumb-item active" aria-current="page">{esc(label)}</li>'
        for label, link, _ in trail
    )
    visible = f'<nav aria-label="breadcrumb">\n    <ol class="breadcrumb small mb-3">{items}</ol>\n</nav>'
    structured = {
        "@type": "BreadcrumbList",
        "@id": page.url + "#breadcrumb",
        "itemListElement": [
            {"@type": "ListItem", "position": position, "name": label, "item": url}
            for position, (label, _, url) in enumerate(trail, start=1)
        ],
    }
    return visible, structured


def render_head(page: Page, title: str, description: str, ld_nodes: List[dict]) -> str:
    image = absolute_url(page.image)
    lines = [
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f"<title>{esc(title)}</title>",
        f'<meta name="description" content="{esc(description)}">',
        '<meta name="robots" content="index, follow, max-image-preview:large">',
        f'<link rel="canonical" href="{esc(page.url)}">',
        f'<link rel="icon" type="image/png" href="{esc(LOGO_PATH)}">',
        "",
        '<meta property="og:type" content="website">',
        f'<meta property="og:site_name" content="{esc(SITE_NAME)}">',
        '<meta property="og:locale" content="en_US">',
        f'<meta property="og:url" content="{esc(page.url)}">',
        f'<meta property="og:title" content="{esc(page.label)}">',
        f'<meta property="og:description" content="{esc(description)}">',
    ]
    if image:
        lines += [
            f'<meta property="og:image" content="{esc(image)}">',
            f'<meta property="og:image:alt" content="{esc(page.alt)}">',
            '<meta name="twitter:card" content="summary_large_image">',
        ]
    else:
        lines.append('<meta name="twitter:card" content="summary">')

    image_origin = origin_of(image)
    if image_origin and image_origin != origin_of(SITE_URL):
        # Connect to the image host early so the first image shows sooner.
        lines.append(f'<link rel="preconnect" href="{esc(image_origin)}">')

    lines += [
        "",
        f'<link href="{BOOTSTRAP_CSS}" rel="stylesheet">',
        f"<style>{PAGE_CSS}</style>",
        "",
        render_json_ld(ld_nodes),
    ]
    return "\n".join(lines)


def render_nav() -> str:
    return f"""<nav class="navbar navbar-dark bg-dark" aria-label="Site">
    <div class="container">
        <a class="navbar-brand d-flex align-items-center text-wrap" href="/">
            <img src="{esc(LOGO_PATH)}" alt="{esc(SITE_NAME)} logo" width="40" height="40" class="me-3">
            <div>
                <div class="fw-bold">
                    {esc(SITE_NAME)}
                    <small class="text-light opacity-75">• {esc(SITE_TAGLINE)}</small>
                </div>
            </div>
        </a>
    </div>
</nav>"""


def render_footer(site: Site, current: Page) -> str:
    """Links to every other generated page, so crawlers can reach the whole set from anywhere."""
    columns = []
    if current is not site.index:  # the gallery index already links to every page
        for heading, pages in (("Popular meme templates", site.gallery_pages),
                               ("Memes by topic", site.search_pages)):
            links = "\n".join(
                f'                    <li class="list-inline-item mb-2"><a href="{esc(p.file_name)}">{esc(p.label)}</a></li>'
                for p in pages
                if p is not current
            )
            if links:
                columns.append(f"""            <div class="col-md-6">
                <h2 class="h6">{esc(heading)}</h2>
                <ul class="list-inline mb-0">
{links}
                </ul>
            </div>""")
    links_html = ""
    if columns:
        columns_html = "\n".join(columns)
        links_html = f"""
        <div class="row g-4 mb-4">
{columns_html}
        </div>"""
    return f"""<footer>
    <div class="container">{links_html}
        <p class="text-center mb-0">
            <small>{esc(SITE_NAME)} • {esc(SITE_TAGLINE)}</small>
        </p>
    </div>
</footer>"""


def render_install_section(search_term: str, heading: str) -> str:
    term = esc(search_term)
    return f"""<section id="how-to-download">
    <h2 class="mb-4">{esc(heading)}</h2>
    <div class="card">
        <div class="card-body">

            <h3 class="h5">📱 Android</h3>
            <ol>
                <li>Download the <a href="{esc(PLAY_STORE_URL)}" target="_blank" rel="noopener">{esc(SITE_NAME)} app</a> from Google Play.</li>
                <li>Open the app.</li>
                <li>Search for <strong>"{term}"</strong>.</li>
            </ol>

            <h3 class="h5 mt-4">🍎 iPhone &amp; iPad</h3>
            <ol>
                <li>Open <strong>Safari</strong>.</li>
                <li>Visit <a href="{esc(SITE_URL)}" target="_blank" rel="noopener">{esc(urlsplit(SITE_URL).netloc)}</a>.</li>
                <li>Tap <strong>Launch on Web</strong>.</li>
                <li>Search for <strong>"{term}"</strong>.</li>
                <li>Optional: <a href="{esc(IPHONE_INSTALL_VIDEO_URL)}" target="_blank" rel="noopener">see how to install the web app on your iPhone</a>.</li>
            </ol>

        </div>
    </div>
</section>"""


def render_related_links(pages: List[Page]) -> str:
    return "\n".join(
        f'<a href="{esc(p.file_name)}" class="btn btn-sm btn-outline-primary me-2 mb-2">{esc(p.label)}</a>'
        for p in pages
    )


def render_document(site: Site, page: Page, *, title: str, description: str,
                    ld_nodes: List[dict], body: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
{render_head(page, title, description, ld_nodes)}
</head>

<body>

{render_nav()}

<main class="container py-4 py-md-5">
{body}
</main>

{render_footer(site, page)}

</body>
</html>
"""


# -------------------------------------------------------------------------------------
# Page builders
# -------------------------------------------------------------------------------------

def build_gallery_page(site: Site, page: Page) -> str:
    """Page for one meme template: the template, its description, how to edit it, examples."""
    meme = page.meme
    subject = meme_subject(page.name)  # e.g. "Drake Meme"
    description = clean(meme.get("description"))
    keywords = page.keywords

    title = fit_title(
        f"{page.label} – Download & Edit | {SITE_NAME}",
        f"{page.label} – Download & Edit",
        f"{page.label} | {SITE_NAME}",
        page.label,
    )
    meta_description = truncate(
        description or (f"Download the {subject} template and edit it in seconds with "
                        f"{SITE_NAME}, plus 1000+ other meme templates."),
        MAX_META_DESCRIPTION,
        )
    crumbs_html, crumbs_ld = render_breadcrumbs(site, page)

    # Template image: the main image of the page, so it loads first rather than lazily.
    hero_html = ""
    if page.image:
        hero_html = f"""    <div class="col-lg-5">
        <img
            src="{esc(page.image)}"
            class="img-fluid rounded shadow border"
            alt="{esc(page.alt)}"
            fetchpriority="high"
        >
    </div>
"""

    details = []
    if description:
        details.append(f'<p class="lead">{esc(description)}</p>')
    if keywords:
        badges = "\n".join(f'<span class="badge bg-primary me-2 mb-2">{esc(k)}</span>' for k in keywords)
        details.append(f'<h2 class="h5">Keywords</h2>\n<div class="mb-4">\n{badges}\n</div>')
    if page.related:
        details.append(f'<h2 class="h5">Related memes</h2>\n<div class="mb-4">\n'
                       f'{render_related_links(page.related)}\n</div>')
    details_html = "\n".join(details)
    details_class = "col-lg-7" if hero_html else "col-12"

    cards = []
    for case in meme.get("useCases") or []:
        image_url = clean(case.get("url"))
        if not image_url:
            continue
        case_name = clean(case.get("name"))
        case_desc = clean(case.get("description"))
        # The caption already shows the description, so the alt text names the meme instead.
        alt_detail = case_name or truncate(case_desc, 100)
        alt = f"{subject} example: {alt_detail}" if alt_detail else f"{subject} example {len(cards) + 1}"
        caption = ""
        if case_name:
            caption += f'<span class="d-block fw-medium">{esc(case_name)}</span>'
        if case_desc and case_desc != case_name:
            caption += f'<span class="d-block small text-body-secondary mt-1">{esc(case_desc)}</span>'
        figcaption = ""
        if caption:
            figcaption = f'\n                <figcaption class="card-body py-2 text-center">{caption}</figcaption>'
        cards.append(f"""
        <div class="col-xl-3 col-lg-4 col-md-6 col-6 mb-4">
            <figure class="card h-100 shadow-sm mb-0">
                <img
                    src="{esc(image_url)}"
                    class="card-img-top w-100"
                    alt="{esc(alt)}"
                    loading="lazy"
                    decoding="async"
                    style="aspect-ratio: 1 / 1; object-fit: contain;"
                >{figcaption}
            </figure>
        </div>""")

    examples_html = ""
    if cards:
        cards_html = "".join(cards)
        examples_html = f"""
<hr class="my-5">

<section>
    <h2 class="mb-4">{esc(subject)} Examples</h2>
    <div class="row">{cards_html}
    </div>
</section>"""

    install_html = render_install_section(page.name, f"How to Download & Edit the {subject} Template")
    body = f"""
{crumbs_html}

<h1 class="mb-2">{esc(page.label)}</h1>
<p class="text-body-secondary mb-4">Download the "{esc(page.name)}" template (and 1000+ other meme templates) and edit it in seconds.</p>

<div class="row g-4 g-lg-5">
{hero_html}    <div class="{details_class}">
{details_html}
    </div>
</div>

<hr class="my-5">

{install_html}
{examples_html}
"""
    ld_nodes = [
        webpage_node(page, "WebPage", description or meta_description, keywords=", ".join(keywords)),
        crumbs_ld,
    ]
    return render_document(site, page, title=title, description=meta_description,
                           ld_nodes=ld_nodes, body=body)


def build_search_result_page(site: Site, page: Page) -> str:
    """Page listing every template that matches one keyword."""
    keyword = page.name
    count = len(page.rows)
    templates_text = count_label(count, f"{keyword} meme template")  # "25 Fish meme templates"
    title = fit_title(
        f"{page.label}: {count_label(count, f'{keyword} Meme Template')} | {SITE_NAME}",
        f"{page.label}: {count_label(count, f'{keyword} Meme Template')}",
        f"{page.label} | {SITE_NAME}",
        page.label,
    )
    intro = (f"Browse {templates_text}. Pick one, add your text and share your own "
             f"{keyword} meme in seconds with {SITE_NAME}.")
    meta_description = truncate(
        f"Browse {templates_text}. Pick one, add your text and make your own {keyword} meme "
        f"in seconds with {SITE_NAME} on Android, iPhone or the web.",
        MAX_META_DESCRIPTION,
    )
    crumbs_html, crumbs_ld = render_breadcrumbs(site, page)

    related_html = ""
    if page.related:
        related_html = (f'<p class="mb-1 fw-medium">Featured templates:</p>\n<div class="mb-3">\n'
                        f'{render_related_links(page.related)}\n</div>\n')

    cards = []
    for row in page.rows:
        snippet = truncate(row["description"], 100)
        snippet_html = ""
        if snippet:
            snippet_html = f'\n                    <span class="d-block small text-body-secondary mt-1">{esc(snippet)}</span>'
        card_alt = f"{meme_subject(row['title'])} template"
        cards.append(f"""
        <div class="col-6 col-md-4 col-lg-3 col-xl-2">
            <figure class="card h-100 shadow-sm mb-0">
                <img
                    src="{esc(row['image'])}"
                    style="height: 200px; object-fit: cover;"
                    class="card-img-top img-fluid"
                    alt="{esc(card_alt)}"
                    loading="lazy"
                    decoding="async"
                >
                <figcaption class="card-body p-3">
                    <span class="d-block fw-medium">{esc(row['title'])}</span>{snippet_html}
                </figcaption>
            </figure>
        </div>""")
    cards_html = "".join(cards)

    install_html = render_install_section(keyword, f"How to Download & Edit {keyword} Meme Templates")
    body = f"""
{crumbs_html}

<h1 class="display-6 fw-bold mb-2">{esc(page.label)}</h1>
<p class="text-body-secondary mb-4">{esc(intro)}</p>
{related_html}
<hr class="my-2">

{install_html}

<section>
    <h2 class="mb-4 mt-4">{esc(keyword)} Meme Templates</h2>
    <div class="row g-3 g-md-4">{cards_html}
    </div>
</section>
"""
    ld_nodes = [webpage_node(page, "CollectionPage", meta_description), crumbs_ld]
    return render_document(site, page, title=title, description=meta_description,
                           ld_nodes=ld_nodes, body=body)


def render_link_card(page: Page, lazy: bool) -> str:
    image_html = ""
    if page.image:
        loading = '\n                        loading="lazy"\n                        decoding="async"' if lazy else ""
        image_html = f"""
                    <img
                        src="{esc(page.image)}"
                        alt="{esc(page.alt or page.label)}"
                        class="card-img-top img-fluid"
                        style="height: 200px; object-fit: contain;"{loading}
                    >"""
    return f"""
        <div class="col-6 col-md-4 col-lg-3 col-xl-2">
            <a href="{esc(page.file_name)}" class="text-decoration-none text-dark">
                <div class="card h-100 shadow-sm">{image_html}
                    <div class="card-body p-3">
                        <h3 class="h6 card-title mb-0">{esc(page.label)}</h3>
                    </div>
                </div>
            </a>
        </div>"""


def build_gallery(site: Site) -> str:
    """The gallery index, linking to every meme page and search page."""
    page = site.index
    heading = "Popular Meme Templates"
    title = fit_title(f"{heading} Gallery | {SITE_NAME}", f"{heading} | {SITE_NAME}", heading)
    intro = (f"Browse popular meme templates and memes by topic. Pick a template, add your text "
             f"and share your meme in seconds with {SITE_NAME}.")
    topic_names = ", ".join(p.name for p in site.search_pages[:5])
    if topic_names:
        meta_description = truncate(
            f"Browse popular meme templates and memes by topic: {topic_names} and more. "
            f"Pick one and make your meme in seconds with {SITE_NAME}.",
            MAX_META_DESCRIPTION,
        )
    else:
        meta_description = truncate(intro, MAX_META_DESCRIPTION)
    crumbs_html, crumbs_ld = render_breadcrumbs(site, page)

    sections, shown = [], 0
    for section_heading, pages in (("Meme templates", site.gallery_pages),
                                   ("Memes by topic", site.search_pages)):
        if not pages:
            continue
        cards = []
        for linked_page in pages:
            cards.append(render_link_card(linked_page, lazy=shown >= EAGER_IMAGES))
            shown += 1
        cards_html = "".join(cards)
        sections.append(f"""
<section class="mb-5">
    <h2 class="h4 mb-3">{esc(section_heading)}</h2>
    <div class="row g-3 g-md-4">{cards_html}
    </div>
</section>""")
    sections_html = "\n".join(sections)

    body = f"""
{crumbs_html}

<h1 class="mb-2">{esc(heading)}</h1>
<p class="lead mb-4">{esc(intro)}</p>
{sections_html}
"""
    item_list = {
        "@type": "ItemList",
        "itemListElement": [
            {"@type": "ListItem", "position": position, "url": p.url, "name": p.label}
            for position, p in enumerate(site.gallery_pages + site.search_pages, start=1)
        ],
    }
    ld_nodes = [
        webpage_node(page, "CollectionPage", meta_description, mainEntity=item_list),
        crumbs_ld,
    ]
    return render_document(site, page, title=title, description=meta_description,
                           ld_nodes=ld_nodes, body=body)


# -------------------------------------------------------------------------------------
# Sitemap and robots.txt
# -------------------------------------------------------------------------------------

def build_sitemap(site: Site) -> str:
    """sitemap.xml with every page, its last change date and its images."""
    entries = []

    def add(url: str, lastmod: Optional[str], images: List[str]) -> None:
        image_urls = list(dict.fromkeys(absolute_url(u) for u in images if clean(u)))[:1000]
        lines = ["  <url>", f"    <loc>{xml_escape(url)}</loc>"]
        if lastmod:
            lines.append(f"    <lastmod>{lastmod}</lastmod>")
        lines += [f"    <image:image><image:loc>{xml_escape(u)}</image:loc></image:image>"
                  for u in image_urls]
        lines.append("  </url>")
        entries.append("\n".join(lines))

    for path, local_file in OTHER_SITEMAP_PAGES:
        add(urljoin(SITE_URL, path), newest_date(local_file), [])
    add(site.index.url, site.index.lastmod, [p.image for p in site.gallery_pages + site.search_pages])
    for page in site.gallery_pages:
        add(page.url, page.lastmod,
            [page.image] + [case.get("url") for case in page.meme.get("useCases") or []])
    for page in site.search_pages:
        add(page.url, page.lastmod, [row["image"] for row in page.rows])

    entries_xml = "\n".join(entries)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">
{entries_xml}
</urlset>
"""


def build_robots_txt() -> str:
    sitemap_url = urljoin(SITE_URL, Path(SITEMAP_FILE).name)
    return f"User-agent: *\nDisallow:\n\nSitemap: {sitemap_url}\n"


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"Generated {path}")


# -------------------------------------------------------------------------------------
# Pages to build (add new ones here)
# -------------------------------------------------------------------------------------

GALLERY_PAGES = [  # (meme JSON file, output HTML file)
    ("./articles/gallery/distracted_boyfriend_meme.json", "./distracted_boyfriend_meme.html"),
    ("./articles/gallery/drake_meme.json", "./drake_meme.html"),
    ("./articles/gallery/what_meme.json", "./what_meme.html"),
    ("./articles/gallery/speed_dating_meme.json", "./speed_dating_meme.html"),
]

SEARCH_RESULT_PAGES = [  # (search keyword, output HTML file)
    ("Fish", "./fish_memes.html"),
    ("Cat", "./cat_memes.html"),
    ("Dog", "./dog_memes.html"),
    ("Duck", "./duck_memes.html"),
    ("Bird", "./bird_memes.html"),
    ("Wolf", "./wolf_memes.html"),
    ("Laugh", "./laugh_memes.html"),
    ("Cry", "./cry_memes.html"),
    ("Choice", "./choice_memes.html"),
    ("Spiderman", "./spiderman_memes.html"),
    ("Spongebob", "./spongebob_memes.html"),
    ("Scared", "./scared_memes.html"),
    ("Thinking", "./thinking_memes.html"),
    ("Friday", "./friday_memes.html"),
    ("Shocked", "./shocked_memes.html"),
]


def main() -> None:
    gallery_pages = [load_gallery_page(json_file, output) for json_file, output in GALLERY_PAGES]
    search_pages = [page for page in (load_search_page(keyword, output)
                                      for keyword, output in SEARCH_RESULT_PAGES) if page]
    all_pages = gallery_pages + search_pages
    cover = next((p for p in all_pages if p.image), None)  # the index borrows its first image
    index = Page(
        kind="index",
        output_path=Path(GALLERY_INDEX_FILE),
        name="Meme Templates",
        image=cover.image if cover else "",
        alt=cover.alt if cover else "",
        lastmod=max((p.lastmod for p in all_pages if p.lastmod), default=None),
    )
    site = Site(gallery_pages=gallery_pages, search_pages=search_pages, index=index)
    link_related_pages(site)

    for page in gallery_pages:
        write_file(page.output_path, build_gallery_page(site, page))
    for page in search_pages:
        write_file(page.output_path, build_search_result_page(site, page))
    write_file(index.output_path, build_gallery(site))
    write_file(Path(SITEMAP_FILE), build_sitemap(site))
    if not Path(ROBOTS_FILE).exists():
        write_file(Path(ROBOTS_FILE), build_robots_txt())


if __name__ == "__main__":
    main()