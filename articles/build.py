from jinja2 import Environment, FileSystemLoader
import os

# Folder that contains partial HTML files
PARTS_DIR = "parts"

# Output file
OUTPUT_FILE = "final.html"

# Create output folder if missing
# os.makedirs("output", exist_ok=True)

# Setup Jinja environment
env = Environment(loader=FileSystemLoader(PARTS_DIR))

# Load each HTML part as template
nav_template = env.get_template("nav.html")
header_template = env.get_template("header.html")
footer_template = env.get_template("footer.html")
body_templates = {
    'index.html': env.get_template("home_content.html"),
}

# Render each part (you can pass variables here later)
nav_html = nav_template.render()
header_html = header_template.render()
footer_html = footer_template.render()

for name, template in body_templates.items():
    body_html = template.render()

    # Combine into final HTML
    final_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    {header_html}
    {nav_html}
    <body>
    {body_html}
    </body>
    {footer_html}
    </html>
    """

    # Write output
    with open(name, "w", encoding="utf-8") as f:
        f.write(final_html)

    print("✅ HTML generated:", OUTPUT_FILE)
