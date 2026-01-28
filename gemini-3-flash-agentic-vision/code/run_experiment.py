"""
Main experiment runner for Gemini 3 Flash Agentic Vision tests.

Usage:
    python run_experiment.py              # Run all tests
    python run_experiment.py --test 1     # Run specific test
    python run_experiment.py --baseline   # Run baseline only (code exec OFF)
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

from gemini_client import run_vision_query, test_connection

# Paths
EXPERIMENT_DIR = Path(__file__).parent.parent
INPUTS_DIR = EXPERIMENT_DIR / "inputs"
OUTPUTS_DIR = EXPERIMENT_DIR / "outputs"
RAW_DIR = OUTPUTS_DIR / "raw"
SCREENSHOTS_DIR = OUTPUTS_DIR / "screenshots"

# Ensure output dirs exist
RAW_DIR.mkdir(parents=True, exist_ok=True)
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)


# Test definitions
TESTS = {
    1: {
        "name": "finger_counting",
        "description": "Count fingers in hand images",
        "prompt": "Count the exact number of fingers shown in this image. Be precise.",
        "images": ["fingers_1.jpg", "fingers_3.jpg", "fingers_5.jpg", "fingers_7.jpg", "fingers_10.jpg"],
        "ground_truth": [1, 3, 5, 7, 10],
    },
    2: {
        "name": "coin_counting",
        "description": "Count coins on surface",
        "prompt": "Count the exact number of coins in this image. Give me a precise count, not an estimate.",
        "images": ["coins_8.jpg", "coins_15.jpg", "coins_23.jpg"],
        "ground_truth": [8, 15, 23],
    },
    3: {
        "name": "rebar_counting",
        "description": "Count rebar pieces (construction domain)",
        "prompt": "Count the exact number of rebar pieces (metal reinforcement bars) visible in this image. Mark each one you count.",
        "images": ["rebar_grid_1.jpg", "rebar_grid_2.jpg", "rebar_stack.jpg"],
        "ground_truth": None,  # TBD after getting images
    },
    4: {
        "name": "table_extraction",
        "description": "Extract values from dense tables",
        "prompt": "Extract all values from this table as a JSON object. Include every cell value exactly as shown.",
        "images": ["table_financial.png", "table_materials.jpg"],
        "ground_truth": None,  # Manual verification
    },
    5: {
        "name": "ppe_detection",
        "description": "Detect PPE on construction workers",
        "prompt": "Identify all Personal Protective Equipment (PPE) items worn by workers in this image. List each item and mark its location if possible.",
        "images": ["construction_ppe_1.jpg", "construction_ppe_2.jpg", "construction_ppe_3.jpg"],
        "ground_truth": None,  # Manual verification
    },
    6: {
        "name": "blueprint_reading",
        "description": "Read measurements from blueprints",
        "prompt": "Read all the measurements and dimensions shown on this blueprint/floor plan. List each measurement with its location.",
        "images": ["blueprint_1.png", "blueprint_2.png"],
        "ground_truth": None,  # Manual verification
    },
    7: {
        "name": "receipt_math",
        "description": "Calculate total from receipt",
        "prompt": "Read all the line items on this receipt and calculate the total. Show your work.",
        "images": ["receipt_1.jpg", "receipt_2.jpg"],
        "ground_truth": None,  # Known totals to be added
    },
}


def run_single_test(test_id: int, code_execution: bool) -> dict:
    """Run a single test with specified code execution setting."""
    test = TESTS[test_id]
    mode = "code_on" if code_execution else "code_off"

    print(f"\n{'='*60}")
    print(f"Test {test_id}: {test['name']} (code_execution={code_execution})")
    print(f"{'='*60}")

    results = []

    for i, image_file in enumerate(test["images"]):
        image_path = INPUTS_DIR / image_file

        if not image_path.exists():
            print(f"  ⚠ Skipping {image_file} - file not found")
            results.append({
                "image": image_file,
                "status": "skipped",
                "reason": "file not found"
            })
            continue

        print(f"  Running: {image_file}...")

        response = run_vision_query(
            image_path=str(image_path),
            prompt=test["prompt"],
            code_execution=code_execution,
        )

        # Check ground truth if available
        ground_truth = None
        if test["ground_truth"] and i < len(test["ground_truth"]):
            ground_truth = test["ground_truth"][i]

        result = {
            "image": image_file,
            "status": "success" if response["success"] else "error",
            "response_text": response.get("text", ""),
            "code_executed": response.get("code_executed", []),
            "code_results": response.get("code_results", []),
            "images_generated": len(response.get("images_generated", [])),
            "ground_truth": ground_truth,
            "error": response.get("error"),
        }

        results.append(result)

        # Save any generated images
        for j, img_data in enumerate(response.get("images_generated", [])):
            import base64
            img_bytes = base64.b64decode(img_data["data"])
            img_path = SCREENSHOTS_DIR / f"{test['name']}_{image_file}_{mode}_{j}.png"
            with open(img_path, "wb") as f:
                f.write(img_bytes)
            print(f"    Saved annotated image: {img_path.name}")

        # Print summary
        if response["success"]:
            text_preview = response["text"][:100].replace("\n", " ")
            print(f"    ✓ Response: {text_preview}...")
            if response["code_executed"]:
                print(f"    ✓ Code executed: {len(response['code_executed'])} blocks")
        else:
            print(f"    ✗ Error: {response.get('error', 'Unknown')}")

    return {
        "test_id": test_id,
        "test_name": test["name"],
        "code_execution": code_execution,
        "results": results,
    }


def save_results(all_results: list, filename: str):
    """Save results to JSON file."""
    output_path = RAW_DIR / filename
    with open(output_path, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nResults saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Run Gemini 3 Flash Agentic Vision experiments")
    parser.add_argument("--test", type=int, help="Run specific test (1-7)")
    parser.add_argument("--baseline", action="store_true", help="Run baseline only (code exec OFF)")
    parser.add_argument("--treatment", action="store_true", help="Run treatment only (code exec ON)")
    args = parser.parse_args()

    # Test API connection first
    print("Testing API connection...")
    if not test_connection():
        print("\n✗ API connection failed. Check your GOOGLE_API_KEY in .env")
        sys.exit(1)
    print("✓ API connection successful\n")

    # Determine which tests to run
    test_ids = [args.test] if args.test else list(TESTS.keys())

    # Determine which modes to run
    modes = []
    if args.baseline:
        modes = [False]  # code exec OFF only
    elif args.treatment:
        modes = [True]   # code exec ON only
    else:
        modes = [False, True]  # both

    all_results = []
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    for code_exec in modes:
        mode_name = "code_on" if code_exec else "code_off"
        print(f"\n{'#'*60}")
        print(f"# Running: {mode_name.upper()}")
        print(f"{'#'*60}")

        for test_id in test_ids:
            if test_id not in TESTS:
                print(f"Unknown test ID: {test_id}")
                continue

            result = run_single_test(test_id, code_exec)
            all_results.append(result)

    # Save all results
    save_results(all_results, f"experiment_results_{timestamp}.json")

    # Print summary
    print("\n" + "="*60)
    print("EXPERIMENT COMPLETE")
    print("="*60)
    print(f"Tests run: {len(test_ids)}")
    print(f"Modes: {['code_off', 'code_on'] if len(modes) == 2 else modes}")
    print(f"Results saved to: outputs/raw/experiment_results_{timestamp}.json")
    print("\nNext: Run compare_results.py to generate comparison report")


if __name__ == "__main__":
    main()
