import json
import html
from pathlib import Path
from typing import List, Dict

pages = []

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
<hr class="my-5">

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
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Meme Templates Gallery</title>
    <meta name="description" content="Browse our collection of popular meme templates and find the perfect meme for your next post.">

    <style>
        body {
            margin: 0;
            font-family: Arial, sans-serif;
            background: #f5f5f5;
            color: #222;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 30px 20px;
        }

        h1 {
            text-align: center;
            margin-bottom: 30px;
        }

        .gallery {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
            gap: 20px;
        }

        .gallery-item {
            display: block;
            background: #fff;
            border-radius: 10px;
            overflow: hidden;
            text-decoration: none;
            color: inherit;
            box-shadow: 0 2px 8px rgba(0,0,0,.08);
            transition: transform .2s, box-shadow .2s;
        }

        .gallery-item:hover {
            transform: translateY(-3px);
            box-shadow: 0 5px 15px rgba(0,0,0,.15);
        }

        .gallery-item img {
            width: 100%;
            aspect-ratio: 1 / 1;
            object-fit: cover;
            display: block;
        }

        .gallery-content {
            padding: 15px;
        }

        .gallery-title {
            font-size: 18px;
            font-weight: bold;
            margin: 0 0 8px;
        }

        .gallery-description {
            font-size: 14px;
            color: #666;
            line-height: 1.5;
            margin: 0;
        }
    </style>
</head>

<body>
    <main class="container">
        <h1>Meme Templates</h1>

        <div class="gallery">
"""

    for page in subpages:
        title = page.get("title", "")
        url = page.get("href", "#")
        image = page.get("image", "")

        html += f"""
            <a class="gallery-item" href="{url}">
                <img src="{image}" alt="{title}" loading="lazy">
                <div class="gallery-content">
                    <h2 class="gallery-title">{title}</h2>
                </div>
            </a>
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


build_gallery_page(json_file='./articles/gallery/distracted_boyfriend_meme.json', output_path='./distracted_boyfriend_meme.html')
build_gallery_page(json_file='./articles/gallery/drake_meme.json', output_path='./drake_meme.html')
build_gallery(subpages=pages, output_path='./gallery.html')
