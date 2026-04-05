import csv

def generate_md_from_keywords(csv_file, keywords, output_md):
    keywords = [k.lower() for k in keywords]
    matched_rows = []

    # Read CSV
    with open(csv_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            title = (row.get("title") or "").lower()
            description = (row.get("description") or "").lower()

            # Check if any keyword appears
            if any(k in title or k in description for k in keywords):
                matched_rows.append(row)

    print(f"Found {len(matched_rows)} matching rows")

    # Generate Markdown
    md_sections = []

    for row in matched_rows:
        meme_id = row.get("id", "").strip()
        title = row.get("title", "").strip()

        if not meme_id or not title:
            continue

        image_url = f"https://storage.googleapis.com/y_meme_templates/{meme_id}.jpg"

        section = f"""## {title}
![{title}]({image_url})
"""
        md_sections.append(section)

    # Write to MD file
    with open(output_md, "w", encoding="utf-8") as f:
        f.write("# Filtered Memes\n\n")
        f.write("\n".join(md_sections))

    print(f"✅ Markdown file generated: {output_md}")


# Example usage
csv_file = "/Users/nguyenduyy/AndroidStudioProjects/meme/scripts/python/memes_output.csv"
keywords = ["cat"]
output_md = "./articles/content/cat_memes.md"

generate_md_from_keywords(csv_file, keywords, output_md)