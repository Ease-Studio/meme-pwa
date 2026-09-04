import json
import html
from pathlib import Path
from typing import List, Dict
from html import escape
from search import search

pages = []

def get_install_instructions_div(name: str):
    return f"""
<section>
    <h2 class="mb-4">
        How to Download & Edit This Template ?
    </h2>
    <div class="card">
        <div class="card-body">

            <h5>📱 Android</h5>

            <ul>
                <li>
                    Download app from PlayStore:
                    <a href="https://play.google.com/store/apps/details?id=com.ease_studio.meme" target="_blank">
                        Meme Express
                    </a>.
                </li>
                <li>
                    Open the app.
                </li>
                <li>
                    Search for <strong>"{name}"</strong>.
                </li>
            </ul>

            <h5 class="mt-4">🍎 iPhone & iPad</h5>

            <ul>
                <li>
                    Open <strong>Safari</strong>.
                </li>
                <li>
                    Visit
                    <a href="https://meme-express.io.vn" target="_blank">
                        https://meme-express.io.vn
                    </a>.
                </li>
                <li>
                    Tap <strong>Launch on Web</strong>.
                </li>
                <li>
                    Search for <strong>"{name}"</strong>.
                </li>
                <li>
                    (Optionally) You can install this web as an application on iPhone: <a href="https://youtube.com/shorts/jJvhzI0J0w4?feature=share" target="_blank">see how !</a>
                </li>
            </ul>

        </div>
    </div>
    </section>
    """

def get_nav():
    return """
    <nav class="navbar navbar-dark bg-dark">
    <div class="container">

        <a class="navbar-brand d-flex align-items-center" href="/">

            <img
                src="/assets/icon.png"
                alt="Meme Express Logo"
                width="40"
                height="40"
                class="me-3"
            >

            <div>
                <div class="fw-bold">
                    Meme Express
                    <small class="text-light opacity-75">
                     • A Good Meme Maker • Go Fun The World!
                </small>
                </div>
                
            </div>

        </a>

    </div>
</nav>
"""

def build_gallery_page(json_file, output_path):
    """Generate a self-contained HTML gallery page for a meme."""

    with open(json_file, "r", encoding="utf-8") as f:
        meme = json.load(f)

    name = html.escape(meme.get("name", "Unknown Meme"))
    description = html.escape(meme.get("description", ""))
    keywords = meme.get("keywords", [])
    template_url = meme.get("template_url", "")

    keyword_html = "".join(
        f'<span class="badge bg-primary me-2 mb-2">{html.escape(k)}</span>'
        for k in keywords
    )

    gallery_html = ""

    for case in meme.get("useCases", []):
        img = case.get("url", "").strip()
        if not img:
            continue
        case_desc = case.get("description", "")
        case_name = case.get("name", "")

        gallery_html += f"""
<div class="col-xl-3 col-lg-4 col-md-6 col-6 mb-4">

    <div class="card h-100 shadow-sm">

        <img
            src="{html.escape(img)}"
            class="card-img-top w-100"
            loading="lazy"
            alt="{case_desc}"
            style="aspect-ratio: 1 / 1; object-fit: contain;"
        >

        <div class="card-body py-2">
            <h6 class="card-title text-center mb-0">
                {html.escape(case_name)}
            </h6>
        </div>

    </div>

</div>
        """

    template_html = ""
    if template_url:
        template_html = f"""
        <img
            src="{html.escape(template_url)}"
            class="img-fluid rounded shadow border"
            alt="{name} template"
        >
        """

    download_section = f"""
    {get_install_instructions_div(name=name)}
"""

    page = f"""<!doctype html>
<html lang="en">
<head>

<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">

<title>Download template {name} and other 1000+ templates in seconds | Meme Express</title>

<meta name="description" content="{description}">
<meta name="keywords" content="{html.escape(', '.join(keywords))}">

<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/css/bootstrap.min.css" rel="stylesheet">

<style>

body {{
    background:#f8f9fa;
}}

.keyword {{
    margin-right:6px;
    margin-bottom:6px;
}}

.gallery img {{
    width:100%;
    aspect-ratio:1;
    object-fit:cover;
}}

footer {{
    margin-top:80px;
    padding:30px 0;
    color:#666;
    border-top:1px solid #ddd;
}}

</style>

</head>

<body>

{get_nav()}

<div class="container py-5">
    <h3 class="mb-4"> Download template "{name}" (and other 1000+ templates) in seconds</h1>
    <div class="row g-5">

        <div class="col-lg-5">
            {template_html}
        </div>

        <div class="col-lg-7">

            <h1>{name}</h1>

            <p class="lead">
                {description}
            </p>

            <h5>Keywords</h5>

            <div class="mb-4">
                {keyword_html}
            </div>
        
        </div>

    </div>
    
    <hr class="my-5">
    
    {download_section}
    
    <hr class="my-5">

    <h2 class="mb-4">Examples</h2>

    <div class="row gallery">

        {gallery_html}

    </div>

</div>

<footer>
    <div class="container text-center">
        <small>
            Meme Express  • A Good Meme Maker • Go Fun The World!
        </small>
    </div>
</footer>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/js/bootstrap.bundle.min.js"></script>

</body>
</html>
"""

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_path.write_text(page, encoding="utf-8")

    print(f"Generated {output_path}")
    pages.append({
        'title': name,
        'href': output_path.name,
        'image': template_url
    })


from pathlib import Path
from typing import List, Dict



def build_gallery(subpages: List[Dict], output_path):
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <title>Meme Templates Gallery</title>

    <meta
        name="description"
        content="Browse our collection of popular meme templates and find the perfect meme for your next post."
    >

    <link
        href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/css/bootstrap.min.css"
        rel="stylesheet"
    >
</head>

<body>
{get_nav()}

<main class="container py-4">

    <h1 class="mb-4">Meme Templates</h1>

    <div class="row g-3 g-md-4">
"""

    for page in subpages:
        title = escape(str(page.get("title", "")))
        url = escape(str(page.get("href", "#")))
        image = escape(str(page.get("image", "")))

        if not title:
            continue

        html += f"""
        <div class="col-6 col-md-4 col-lg-3 col-xl-2">
            <a
                href="{url}"
                class="text-decoration-none text-dark"
            >
                <div class="card h-100 shadow-sm">
                    <img
                        src="{image}"
                        alt="{title}"
                        class="card-img-top img-fluid"
                        style="height: 200px; object-fit: contain;"
                        loading="lazy"
                    >

                    <div class="card-body p-3">
                        <h2 class="h6 card-title mb-0">
                            {title}
                        </h2>
                    </div>
                </div>
            </a>
        </div>
"""

    html += """
    </div>

</main>

</body>
</html>
"""

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_path.write_text(html, encoding="utf-8")

    print(f"Generated {output_path}")


def build_search_result_page(keyword: str, output_path):
    csv_file = "/Users/nguyenduyy/AndroidStudioProjects/meme/scripts/python/memes_output.csv"
    rows = search(csv_file=csv_file, keywords=[keyword])

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    cards = []
    banner = None

    for row in rows:
        meme_id = str(row.get("id", "")).strip()
        title = str(row.get("title", "")).strip()
        description = str(row.get("description", "")).strip()

        if not meme_id or not title:
            continue

        image_url = f"https://storage.googleapis.com/y_meme_templates/{meme_id}.jpg"

        if not banner:
            banner = image_url

        cards.append(f"""
        <div class="col-6 col-md-4 col-lg-3 col-xl-2">
            <div class="card h-100 shadow-sm">
                <img
                    src="{escape(image_url)}"
                    style="height: 200px; object-fit: cover;"
                    class="card-img-top img-fluid"
                    alt="{escape(title)}"
                    loading="lazy"
                >
                <div class="card-body p-3">
                    <h2 class="h6 card-title mb-0">
                        {escape(title)}
                    </h2>
                </div>
            </div>
        </div>
        """)

    gallery = "\n".join(cards)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <title>{escape(keyword)} Memes - Meme Express</title>

    <meta
        name="description"
        content="Find the best {escape(keyword)} memes and meme templates. Browse, create, and download memes on Meme Express."
    >

    <link
        href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/css/bootstrap.min.css"
        rel="stylesheet"
    >
</head>

<body class="bg-light">

{get_nav()}

<div class="container py-4 py-md-5">

    <h1 class="display-6 fw-bold mb-2">
        "{escape(keyword)}" Memes
    </h1>

    <p class="text-secondary mb-4">
        Browse best templates for {escape(keyword)} memes.
        Make memes with Meme Express.
    </p>
    
    <hr class="my-2">

    {get_install_instructions_div(name=keyword)}    
    <h2 class="mb-4 mt-4">Templates</h2>

    <section class="row g-3 g-md-4">
        {gallery}
    </section>

</div>

</body>
</html>
"""

    output_path.write_text(html, encoding="utf-8")

    pages.append({
        "title": keyword,
        "href": output_path.name,
        "image": banner
    })

    print(f"Generated {output_path}")



build_gallery_page(json_file='./articles/gallery/distracted_boyfriend_meme.json', output_path='./distracted_boyfriend_meme.html')
build_gallery_page(json_file='./articles/gallery/drake_meme.json', output_path='./drake_meme.html')
build_gallery_page(json_file='./articles/gallery/what_meme.json', output_path='./what_meme.html')
build_gallery_page(json_file='./articles/gallery/speed_dating_meme.json', output_path='./speed_dating_meme.html')
build_search_result_page(keyword='Fish', output_path='./fish_memes.html')
build_search_result_page(keyword='Cat', output_path='./cat_memes.html')
build_search_result_page(keyword='Dog', output_path='./dog_memes.html')
build_search_result_page(keyword='Duck', output_path='./duck_memes.html')
build_search_result_page(keyword='Bird', output_path='./bird_memes.html')
build_search_result_page(keyword='Wolf', output_path='./wolf_memes.html')
build_search_result_page(keyword='Laugh', output_path='./laugh_memes.html')
build_search_result_page(keyword='Cry', output_path='./cry_memes.html')
build_search_result_page(keyword='Choice', output_path='./choice_memes.html')
build_search_result_page(keyword='Spiderman', output_path='./spiderman_memes.html')
build_search_result_page(keyword='Spongebob', output_path='./spongebob_memes.html')
build_search_result_page(keyword='Scared', output_path='./scared_memes.html')
build_search_result_page(keyword='Thinking', output_path='./thinking_memes.html')
build_search_result_page(keyword='Friday', output_path='./friday_memes.html')
build_search_result_page(keyword='Shocked', output_path='./shocked_memes.html')
build_gallery(subpages=pages, output_path='./gallery.html')
