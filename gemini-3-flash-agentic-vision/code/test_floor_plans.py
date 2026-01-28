"""
Test floor plan images for trees/doors counting and fittings counting.
Run after saving images to inputs/ folder.
"""

import os
import json
import base64
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

# Load environment
load_dotenv(EXPERIMENT_DIR / ".env")

# Initialize Gemini client
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
MODEL = "gemini-3-flash-preview"

# New test images
FLOOR_PLAN_TESTS = {
    "floor_plan": {
        "file": "floor_plan.jpg",
        "prompt": "Count how many trees are visible in this floor plan. Count how many doors are visible. Give me the exact counts.",
        "description": "Floor plan with pool, garage, multiple rooms"
    },
    "fittings": {
        "file": "fittings.webp",
        "prompt": "This is a lighting plan. Count the new/extra fittings (blue squares and rectangles) and the original fittings (red circles). Give me exact counts for each category.",
        "description": "Lighting plan with blue=new fittings, red=original"
    },
}


def load_image_as_part(image_path: Path) -> types.Part:
    """Load image file as Gemini Part."""
    with open(image_path, "rb") as f:
        image_data = f.read()

    suffix = image_path.suffix.lower()
    mime_types = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}
    mime_type = mime_types.get(suffix, "image/png")

    return types.Part.from_bytes(data=image_data, mime_type=mime_type)


def run_vision_query(image_path: Path, prompt: str, code_execution: bool) -> dict:
    """Run a vision query with optional code execution."""
    image = load_image_as_part(image_path)

    tools = []
    if code_execution:
        tools = [types.Tool(code_execution=types.ToolCodeExecution())]

    config = types.GenerateContentConfig(tools=tools)

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
            "images_generated_count": 0,
            "images_generated": [],  # Will truncate base64 for display
        }

        for candidate in response.candidates:
            for part in candidate.content.parts:
                if hasattr(part, "text") and part.text:
                    result["text"] += part.text
                if hasattr(part, "executable_code") and part.executable_code:
                    result["code_executed"].append(part.executable_code.code)
                if hasattr(part, "code_execution_result") and part.code_execution_result:
                    result["code_results"].append(part.code_execution_result.output)
                if hasattr(part, "inline_data") and part.inline_data:
                    result["images_generated_count"] += 1
                    # Store truncated version for display
                    b64_preview = base64.b64encode(part.inline_data.data).decode()[:100]
                    result["images_generated"].append({
                        "mime_type": part.inline_data.mime_type,
                        "data_preview": f"{b64_preview}... <truncated>"
                    })
                    # Save actual image
                    save_generated_image(part.inline_data, image_path.stem, code_execution, result["images_generated_count"])

        return result

    except Exception as e:
        return {"success": False, "error": str(e)}


def save_generated_image(inline_data, test_name: str, code_execution: bool, index: int):
    """Save generated image to screenshots folder."""
    mode = "code_ON" if code_execution else "code_OFF"
    img_path = SCREENSHOTS_DIR / f"{test_name}_{mode}_{index}.png"
    with open(img_path, "wb") as f:
        f.write(inline_data.data)
    print(f"    Saved: {img_path.name}")


def format_json_for_blog(result: dict, truncate_code: bool = True) -> str:
    """Format result as JSON suitable for blog display."""
    display = {
        "success": result.get("success"),
        "text": result.get("text", "")[:500] + "..." if len(result.get("text", "")) > 500 else result.get("text", ""),
        "code_executed": [c[:200] + "..." if len(c) > 200 else c for c in result.get("code_executed", [])] if truncate_code else result.get("code_executed", []),
        "code_results": result.get("code_results", [])[:2],  # First 2 results
        "images_generated_count": result.get("images_generated_count", 0),
    }
    return json.dumps(display, indent=2)


def main():
    print("=" * 60)
    print("FLOOR PLAN VISION TESTS")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print()

    # Check which images exist
    available_tests = {}
    for name, info in FLOOR_PLAN_TESTS.items():
        path = INPUTS_DIR / info["file"]
        if path.exists():
            available_tests[name] = {"path": path, **info}
            print(f"✓ Found: {info['file']}")
        else:
            print(f"✗ Missing: {info['file']} - please save to inputs/")

    if not available_tests:
        print("\nNo test images found. Please save images to:")
        print(f"  {INPUTS_DIR}/floor_plan.png")
        print(f"  {INPUTS_DIR}/fittings.png")
        return

    print()
    all_results = []

    for name, info in available_tests.items():
        print("=" * 50)
        print(f"Test: {name}")
        print(f"Description: {info['description']}")
        print("=" * 50)

        # Code OFF
        print("\n[Code OFF]")
        result_off = run_vision_query(info["path"], info["prompt"], code_execution=False)
        if result_off.get("success"):
            print(f"Response: {result_off['text'][:200]}...")
        else:
            print(f"Error: {result_off.get('error')}")

        # Code ON
        print("\n[Code ON]")
        result_on = run_vision_query(info["path"], info["prompt"], code_execution=True)
        if result_on.get("success"):
            print(f"Response: {result_on['text'][:200]}...")
            print(f"Code blocks executed: {len(result_on.get('code_executed', []))}")
            print(f"Images generated: {result_on.get('images_generated_count', 0)}")
        else:
            print(f"Error: {result_on.get('error')}")

        all_results.append({
            "test": name,
            "description": info["description"],
            "code_off": result_off,
            "code_on": result_on,
        })

        # Print JSON for blog
        print("\n--- JSON for Blog (Code ON) ---")
        print(format_json_for_blog(result_on))
        print()

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = RAW_DIR / f"floor_plan_tests_{timestamp}.json"
    with open(results_file, "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\nResults saved to: {results_file}")


if __name__ == "__main__":
    main()
