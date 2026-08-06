import json
import html
from pathlib import Path


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

        gallery_html += f"""
        <div class="col-xl-3 col-lg-4 col-md-6 col-6 mb-4">
            <img
                src="{html.escape(img)}"
                class="img-fluid rounded shadow-sm border"
                loading="lazy"
                alt="{name}"
            >
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

    page = f"""<!doctype html>
<html lang="en">
<head>

<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">

<title>{name} Meme Template</title>

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
        <a class="navbar-brand fw-bold" href="/">
            Meme Gallery
        </a>
    </div>
</nav>

<div class="container py-5">

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

    <h2 class="mb-4">Examples</h2>

    <div class="row gallery">

        {gallery_html}

    </div>

</div>

<footer>
    <div class="container text-center">
        <small>
            Generated automatically by Meme Gallery
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


build_gallery_page(json_file='./articles/gallery/distracted_boyfriend_meme.json', output_path='./distracted_boyfriend_meme.html')