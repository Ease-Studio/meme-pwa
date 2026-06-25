import markdown
from jinja2 import Environment, FileSystemLoader
import os

from bs4 import BeautifulSoup
import shutil

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


