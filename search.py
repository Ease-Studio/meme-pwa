import argparse
import csv

def search(csv_file, keywords):
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
        description = row.get("description", "")

        if not meme_id or not title:
            continue

        image_url = f"https://storage.googleapis.com/y_meme_templates/{meme_id}.jpg"

        print(f"{meme_id} | {title} | {image_url} | {description}")

    return matched_rows


if __name__ == '__main__':
    # Example usage
    csv_file = "/Users/nguyenduyy/AndroidStudioProjects/meme/scripts/python/memes_output.csv"

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-k",
        type=str,
        required=True,
    )
    args = parser.parse_args()
    keyword = args.k
    search(csv_file, [keyword])