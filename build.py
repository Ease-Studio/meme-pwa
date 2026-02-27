import markdown
from jinja2 import Environment, FileSystemLoader
import os

# Folder that contains partial HTML files
PARTS_DIR = "articles/parts"


# Create output folder if missing
# os.makedirs("output", exist_ok=True)

# Setup Jinja environment
env = Environment(loader=FileSystemLoader(PARTS_DIR))

# Load each HTML part as template
nav_template = env.get_template("nav.html")
header_template = env.get_template("header.html")
footer_template = env.get_template("footer.html")

# Render each part (you can pass variables here later)
nav_html = nav_template.render()
header_html = header_template.render()
footer_html = footer_template.render()

content_dir = 'articles/content'

files = os.listdir(content_dir)
for file in files:
    if not file.endswith('.md'):
        continue
    with open(os.path.join(content_dir, file), "r", encoding="utf-8") as f:
        md_text = f.read()
        body = markdown.markdown(md_text, extensions=[
            "tables",
            "fenced_code",
            "codehilite",
            "toc",
            "nl2br"
        ])

        final_html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
        {header_html}
        </head>
        <body>
        {nav_html}
        <div class="article_wrapper">
        {body}
        </div>
        {footer_html}
        </body>
        </html>
        """

        out = os.path.join('articles', file.replace('.md', '.html'))
        # Write output
        with open(out, "w", encoding="utf-8") as f:
            f.write(final_html)

        print("✅ HTML generated:", out)

from bs4 import BeautifulSoup
import shutil

def copy_index_file(
        src="/Users/nguyenduyy/AndroidStudioProjects/meme/build/web/index.html",
        dst="index_tmp.html"
):
    shutil.copyfile(src, dst)
    print(f"✅ Copied {src} → {dst}")


copy_index_file()


def inject_html_bs(
        index_path="index_tmp.html",
        header_path="./articles/parts/header.html",
        nav_path="./articles/parts/nav.html",
        body_path="./articles/parts/home_content.html",
        footer_path="./articles/parts/footer.html",
        output_path="index_1.html"
):
    # Read base index.html
    with open(index_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    # ---- Inject HEADER into <head> ----
    if soup.head and header_path:
        with open(header_path, "r", encoding="utf-8") as f:
            header_soup = BeautifulSoup(f.read(), "html.parser")

        for tag in header_soup.contents:
            soup.head.append(tag)

    # ---- Inject NAV + BODY + FOOTER into <body> ----
    if soup.body:

        # NAV (top of body)
        if nav_path:
            with open(nav_path, "r", encoding="utf-8") as f:
                nav_soup = BeautifulSoup(f.read(), "html.parser")

            for tag in reversed(nav_soup.contents):
                soup.body.insert(0, tag)

        # BODY content (after nav)
        if body_path:
            with open(body_path, "r", encoding="utf-8") as f:
                body_soup = BeautifulSoup(f.read(), "html.parser")

            for tag in body_soup.contents:
                soup.body.append(tag)

        # FOOTER (last)
        if footer_path:
            with open(footer_path, "r", encoding="utf-8") as f:
                footer_soup = BeautifulSoup(f.read(), "html.parser")

            for tag in footer_soup.contents:
                soup.body.append(tag)

    # ---- Save pretty HTML ----
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(soup.prettify())

    print(f"✅ Generated: {output_path}")


inject_html_bs()


def replace_flutter_loader_script(
        input_path="index_1.html",
        output_path="index.html"
):
    with open(input_path, "r", encoding="utf-8") as f:
        html = f.read()

    soup = BeautifulSoup(html, "html.parser")

    # New script content
    new_script_js = """
function launchMemeExpress() {
    // Show overlay
  const overlay = document.getElementById("memeOverlay");
  if (overlay) overlay.style.display = "flex";
  // Download main.dart.js
  _flutter.loader.loadEntrypoint({
    serviceWorker: {
      serviceWorkerVersion: serviceWorkerVersion,
    },
    onEntrypointLoaded: function(engineInitializer) {
      engineInitializer.initializeEngine().then(function(appRunner) {
        // Hide overlay when app starts
        if (overlay) overlay.style.display = "none";
        document.body.innerHTML = "";
        // (Optional) Remove body styles if landing page had layout CSS
        document.body.removeAttribute("class");
        document.body.removeAttribute("style");
        appRunner.runApp();
      });
    }
  });
}
"""

    # Find script containing flutter load event
    for script in soup.find_all("script"):
        if script.string and "window.addEventListener('load'" in script.string:
            new_script_tag = soup.new_tag("script")
            new_script_tag.string = new_script_js.strip()

            script.replace_with(new_script_tag)
            break

    # Save pretty HTML
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(soup.prettify())

    print(f"✅ Script block replaced via BS4 → {output_path}")


replace_flutter_loader_script()


import os
import re
from bs4 import BeautifulSoup


MD_FOLDER = "./articles/content"


def extract_md_info(md_text):
    # Extract first H1 title
    title_match = re.search(r"^#\s+(.+)", md_text, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else "Untitled"

    # Extract first image URL
    img_match = re.search(r"!\[.*?\]\((.*?)\)", md_text)
    img_url = img_match.group(1).strip() if img_match else ""

    return title, img_url


def slugify(filename):
    return os.path.splitext(filename)[0]


def build_article_card(slug, title, img_url):
    return f"""
<div class="article-card" onclick="openArticle('{slug}')">
    <img src="{img_url}" />
    <div>{title}</div>
</div>
""".strip()


def generate_articles():
    cards_html = []

    # Read all MD files
    for filename in os.listdir(MD_FOLDER):
        if filename.endswith(".md"):
            path = os.path.join(MD_FOLDER, filename)

            with open(path, "r", encoding="utf-8") as f:
                md_text = f.read()

            title, img_url = extract_md_info(md_text)
            slug = slugify(filename)

            card_html = build_article_card(slug, title, img_url)
            cards_html.append(card_html)

    return "\n".join(cards_html)



def inject_into_template(cards_html, target='index.html'):
    # Read existing index.html
    with open(target, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    # ----------------------------
    # 1️⃣ Ensure JS function exists
    # ----------------------------
    js_code = """
    function openArticle(id) {
        window.location.href = `/articles/${id}.html`;
    }
    """

    # Check if function already exists
    if "function openArticle" not in str(soup):
        script_tag = soup.new_tag("script")
        script_tag.string = js_code
        soup.body.append(script_tag)

    # ----------------------------
    # 2️⃣ Append cards to grid
    # ----------------------------
    grid = soup.find("div", class_="article-grid")

    if not grid:
        print(f"❌ .article-grid not found in {target}")
        return

    fragment = BeautifulSoup(cards_html, "html.parser")

    # Append without clearing existing content
    grid.append(fragment)

    # ----------------------------
    # 3️⃣ Save back to file
    # ----------------------------
    with open(target, "w", encoding="utf-8") as f:
        f.write(str(soup))   # use str() to avoid heavy reformatting

    print("✅ Cards appended and JS preserved in:", target)


cards = generate_articles()
inject_into_template(cards, 'index.html')

