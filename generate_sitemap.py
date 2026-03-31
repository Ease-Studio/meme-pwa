import os
from datetime import datetime

# 🔧 CONFIG
BASE_URL = "https://meme-express.io.vn"
HTML_FOLDER = "articles"
OUTPUT_FILE = "sitemap.xml"

def get_html_files(folder):
    html_files = []
    for file in os.listdir(folder):  # ❗ no recursion
        if file.endswith(".html"):
            full_path = os.path.join(folder, file)
            if os.path.isfile(full_path):
                html_files.append(full_path)
    return html_files

def path_to_url(file_path, folder):
    filename = os.path.basename(file_path)

    # clean index.html → /
    if filename == "index.html":
        return BASE_URL

    return f"{BASE_URL}/{folder}/{filename}"

def get_lastmod(file_path):
    timestamp = os.path.getmtime(file_path)
    return datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d")

def generate_sitemap():
    html_files = get_html_files(HTML_FOLDER)

    urls = []
    for file in html_files:
        url = path_to_url(file, HTML_FOLDER)
        lastmod = get_lastmod(file)

        urls.append(f"""
  <url>
    <loc>{url}</loc>
    <lastmod>{lastmod}</lastmod>
  </url>""")

    sitemap_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{''.join(urls)}
</urlset>
"""

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(sitemap_content)

    print(f"✅ Sitemap generated: {OUTPUT_FILE} ({len(urls)} URLs)")

if __name__ == "__main__":
    generate_sitemap()