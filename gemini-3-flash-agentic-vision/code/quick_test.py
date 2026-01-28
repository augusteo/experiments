"""
Quick experiment runner - downloads images and runs focused tests.
Tests the core claim: does code execution improve counting accuracy?
"""

import os
import json
import base64
import requests
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Setup paths
EXPERIMENT_DIR = Path(__file__).parent.parent
INPUTS_DIR = EXPERIMENT_DIR / "inputs"
OUTPUTS_DIR = EXPERIMENT_DIR / "outputs"
RAW_DIR = OUTPUTS_DIR / "raw"
SCREENSHOTS_DIR = OUTPUTS_DIR / "screenshots"

# Create directories
INPUTS_DIR.mkdir(exist_ok=True)
RAW_DIR.mkdir(parents=True, exist_ok=True)
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

# Load environment
load_dotenv(EXPERIMENT_DIR / ".env")

# Initialize Gemini client
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
MODEL = "gemini-3-flash-preview"

# Test images - using Unsplash direct URLs (publicly available)
TEST_IMAGES = {
    # Counting tests - construction/industrial
    "rebar_1": {
        "url": "https://images.unsplash.com/photo-1589939705384-5185137a7f0f?w=800",
        "prompt": "Count the exact number of rebar (metal reinforcement bars) visible in this image. Be precise and count each bar.",
        "category": "counting",
        "description": "Rebar grid construction"
    },
    "bolts": {
        "url": "https://images.unsplash.com/photo-1572981779307-38b8cabb2407?w=800",
        "prompt": "Count the exact number of bolts or screws visible in this image.",
        "category": "counting",
        "description": "Industrial bolts/hardware"
    },
    "pipes": {
        "url": "https://images.unsplash.com/photo-1504328345606-18bbc8c9d7d1?w=800",
        "prompt": "Count the exact number of pipes visible in this image.",
        "category": "counting",
        "description": "Industrial pipes"
    },
    # PPE detection
    "construction_worker": {
        "url": "https://images.unsplash.com/photo-1504307651254-35680f356dfd?w=800",
        "prompt": "List all Personal Protective Equipment (PPE) items visible on workers in this image. Be specific about each item.",
        "category": "ppe",
        "description": "Construction workers with PPE"
    },
    # Dense information extraction
    "chart": {
        "url": "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=800",
        "prompt": "Extract all the data values and labels visible in this chart or dashboard.",
        "category": "extraction",
        "description": "Data dashboard/chart"
    },
}


def download_image(name: str, url: str) -> Path:
    """Download image if not already present."""
    filepath = INPUTS_DIR / f"{name}.jpg"

    if filepath.exists():
        print(f"  ✓ {name}.jpg already exists")
        return filepath

    try:
        print(f"  Downloading {name}...")
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        with open(filepath, "wb") as f:
            f.write(response.content)

        print(f"  ✓ Saved {name}.jpg ({len(response.content) / 1024:.1f} KB)")
        return filepath

    except Exception as e:
        print(f"  ✗ Failed: {e}")
        return None


def load_image_as_part(image_path: Path) -> types.Part:
    """Load image file as Gemini Part."""
    with open(image_path, "rb") as f:
        image_data = f.read()
    return types.Part.from_bytes(data=image_data, mime_type="image/jpeg")


def run_vision_query(image_path: Path, prompt: str, code_execution: bool) -> dict:
    """Run a vision query with optional code execution."""
    image = load_image_as_part(image_path)

    # Configure tools
    tools = []
    if code_execution:
        tools = [types.Tool(code_execution=types.ToolCodeExecution())]

    config = types.GenerateContentConfig(
        tools=tools,
    )

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=[image, prompt],
            config=config,
        )

        result = {
            "success": True,
            "text": "",
            "code_executed": [],
            "code_results": [],
            "images_generated": [],
        }

        # Parse response parts
        for candidate in response.candidates:
            for part in candidate.content.parts:
                if hasattr(part, "text") and part.text:
                    result["text"] += part.text
                if hasattr(part, "executable_code") and part.executable_code:
                    result["code_executed"].append(part.executable_code.code)
                if hasattr(part, "code_execution_result") and part.code_execution_result:
                    result["code_results"].append(part.code_execution_result.output)
                if hasattr(part, "inline_data") and part.inline_data:
                    result["images_generated"].append({
                        "mime_type": part.inline_data.mime_type,
                        "data": base64.b64encode(part.inline_data.data).decode()
                    })

        return result

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "text": "",
            "code_executed": [],
            "code_results": [],
            "images_generated": [],
        }


def run_test(name: str, image_path: Path, prompt: str, code_execution: bool) -> dict:
    """Run a single test and return results."""
    mode = "code_ON" if code_execution else "code_OFF"
    print(f"\n  [{mode}] Testing {name}...")

    result = run_vision_query(image_path, prompt, code_execution)

    if result["success"]:
        # Show preview
        text_preview = result["text"][:150].replace("\n", " ")
        print(f"    Response: {text_preview}...")

        if result["code_executed"]:
            print(f"    ✓ Code executed: {len(result['code_executed'])} block(s)")

        if result["images_generated"]:
            print(f"    ✓ Annotated image generated")
            # Save the image
            for i, img in enumerate(result["images_generated"]):
                img_bytes = base64.b64decode(img["data"])
                img_path = SCREENSHOTS_DIR / f"{name}_{mode}_{i}.png"
                with open(img_path, "wb") as f:
                    f.write(img_bytes)
                print(f"    ✓ Saved: {img_path.name}")
    else:
        print(f"    ✗ Error: {result.get('error', 'Unknown')}")

    return result


def main():
    print("=" * 60)
    print("GEMINI 3 FLASH AGENTIC VISION EXPERIMENT")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"Model: {MODEL}")
    print()

    # Step 1: Download images
    print("STEP 1: Downloading test images")
    print("-" * 40)

    image_paths = {}
    for name, info in TEST_IMAGES.items():
        path = download_image(name, info["url"])
        if path:
            image_paths[name] = path

    print(f"\nDownloaded {len(image_paths)}/{len(TEST_IMAGES)} images")

    if not image_paths:
        print("No images available. Exiting.")
        return

    # Step 2: Run experiments
    print("\n" + "=" * 60)
    print("STEP 2: Running experiments")
    print("=" * 60)

    all_results = []

    for name, path in image_paths.items():
        info = TEST_IMAGES[name]
        print(f"\n{'='*40}")
        print(f"Test: {name} ({info['category']})")
        print(f"Description: {info['description']}")
        print(f"{'='*40}")

        # Run with code execution OFF
        result_off = run_test(name, path, info["prompt"], code_execution=False)

        # Run with code execution ON
        result_on = run_test(name, path, info["prompt"], code_execution=True)

        all_results.append({
            "name": name,
            "category": info["category"],
            "description": info["description"],
            "prompt": info["prompt"],
            "code_off": result_off,
            "code_on": result_on,
        })

    # Step 3: Save results
    print("\n" + "=" * 60)
    print("STEP 3: Saving results")
    print("=" * 60)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = RAW_DIR / f"quick_test_{timestamp}.json"

    with open(results_file, "w") as f:
        json.dump(all_results, f, indent=2)

    print(f"Results saved to: {results_file}")

    # Step 4: Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    for r in all_results:
        print(f"\n{r['name']} ({r['category']}):")

        # Code OFF
        off_text = r["code_off"].get("text", "")[:100]
        print(f"  Code OFF: {off_text}...")

        # Code ON
        on_text = r["code_on"].get("text", "")[:100]
        on_code = len(r["code_on"].get("code_executed", []))
        on_images = len(r["code_on"].get("images_generated", []))
        print(f"  Code ON:  {on_text}...")
        print(f"            (code blocks: {on_code}, annotated images: {on_images})")

    print("\n" + "=" * 60)
    print("EXPERIMENT COMPLETE")
    print("=" * 60)
    print(f"Results: {results_file}")
    print(f"Screenshots: {SCREENSHOTS_DIR}")
    print("\nNext: Review results and create results.md")


if __name__ == "__main__":
    main()
