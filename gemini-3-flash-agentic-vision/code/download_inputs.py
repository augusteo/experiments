"""
Download sample images for construction domain tests.
Uses Unsplash API for free stock photos.
"""

import os
import requests
from pathlib import Path

INPUTS_DIR = Path(__file__).parent.parent / "inputs"
INPUTS_DIR.mkdir(exist_ok=True)

# Unsplash direct URLs (no API key needed for direct links)
# These are sample images - replace with specific ones as needed
SAMPLE_IMAGES = {
    # Rebar images
    "rebar_grid_1.jpg": "https://images.unsplash.com/photo-1504307651254-35680f356dfd?w=1200",
    "rebar_grid_2.jpg": "https://images.unsplash.com/photo-1541888946425-d81bb19240f5?w=1200",

    # Construction workers with PPE
    "construction_ppe_1.jpg": "https://images.unsplash.com/photo-1504307651254-35680f356dfd?w=1200",
    "construction_ppe_2.jpg": "https://images.unsplash.com/photo-1581094794329-c8112a89af12?w=1200",

    # Blueprint/floor plan - placeholder
    # Note: Good blueprint images are hard to find on Unsplash
    # Consider using public domain architectural drawings
}


def download_image(url: str, filename: str) -> bool:
    """Download an image from URL and save to inputs folder."""
    filepath = INPUTS_DIR / filename

    if filepath.exists():
        print(f"  ⚠ {filename} already exists, skipping")
        return True

    try:
        print(f"  Downloading {filename}...")
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        with open(filepath, "wb") as f:
            f.write(response.content)

        print(f"  ✓ Saved {filename} ({len(response.content) / 1024:.1f} KB)")
        return True

    except Exception as e:
        print(f"  ✗ Failed to download {filename}: {e}")
        return False


def create_placeholder_list():
    """Create a list of images that need to be provided manually."""
    manual_images = [
        "fingers_1.jpg - Photo of hand showing 1 finger",
        "fingers_3.jpg - Photo of hand showing 3 fingers",
        "fingers_5.jpg - Photo of hand showing 5 fingers",
        "fingers_7.jpg - Photo of hand showing 7 fingers",
        "fingers_10.jpg - Photo of two hands showing 10 fingers",
        "coins_8.jpg - Photo of 8 coins on a surface",
        "coins_15.jpg - Photo of 15 coins on a surface",
        "coins_23.jpg - Photo of 23 coins on a surface",
        "receipt_1.jpg - Photo of a receipt with known total",
        "receipt_2.jpg - Photo of another receipt with known total",
        "table_financial.png - Screenshot of a financial table",
        "table_materials.jpg - Photo of a construction materials list",
        "blueprint_1.png - Floor plan with measurements",
        "blueprint_2.png - Another floor plan with measurements",
        "rebar_stack.jpg - Photo of stacked rebar with countable pieces",
        "construction_ppe_3.jpg - Photo of worker with various PPE items",
    ]

    readme_path = INPUTS_DIR / "README.md"
    with open(readme_path, "w") as f:
        f.write("# Input Images Needed\n\n")
        f.write("## Images to provide manually:\n\n")
        for img in manual_images:
            f.write(f"- [ ] `{img}`\n")
        f.write("\n## Downloaded automatically:\n\n")
        for img in SAMPLE_IMAGES.keys():
            f.write(f"- [x] `{img}`\n")

    print(f"\nCreated {readme_path} with checklist of needed images")


def main():
    print("Downloading sample images for experiment...\n")

    success_count = 0
    for filename, url in SAMPLE_IMAGES.items():
        if download_image(url, filename):
            success_count += 1

    print(f"\nDownloaded {success_count}/{len(SAMPLE_IMAGES)} images")

    create_placeholder_list()

    print("\n" + "="*50)
    print("NEXT STEPS:")
    print("="*50)
    print("1. Check inputs/README.md for list of images needed")
    print("2. Take photos or find images for the manual items")
    print("3. Place all images in the inputs/ folder")
    print("4. Run: python run_experiment.py")


if __name__ == "__main__":
    main()
