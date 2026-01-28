"""
Compare code execution ON vs OFF results and generate report.
"""

import json
import re
from pathlib import Path
from datetime import datetime

OUTPUTS_DIR = Path(__file__).parent.parent / "outputs"
RAW_DIR = OUTPUTS_DIR / "raw"


def find_latest_results() -> Path:
    """Find the most recent results file."""
    results_files = list(RAW_DIR.glob("experiment_results_*.json"))
    if not results_files:
        raise FileNotFoundError("No results files found in outputs/raw/")
    return max(results_files, key=lambda p: p.stat().st_mtime)


def extract_number(text: str) -> int | None:
    """Try to extract a number from response text."""
    # Look for patterns like "5 fingers", "there are 8", "count: 15"
    patterns = [
        r"(\d+)\s*fingers?",
        r"(\d+)\s*coins?",
        r"(\d+)\s*rebar",
        r"(\d+)\s*pieces?",
        r"(\d+)\s*items?",
        r"count[:\s]+(\d+)",
        r"total[:\s]+(\d+)",
        r"there (?:are|is) (\d+)",
        r"^(\d+)$",  # Just a number
    ]

    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            return int(match.group(1))
    return None


def analyze_results(results: list) -> dict:
    """Analyze results and compute metrics."""
    # Group by test and mode
    by_test = {}
    for result in results:
        test_name = result["test_name"]
        mode = "code_on" if result["code_execution"] else "code_off"

        if test_name not in by_test:
            by_test[test_name] = {"code_on": [], "code_off": []}

        by_test[test_name][mode] = result["results"]

    # Compute comparison metrics
    comparison = {}
    for test_name, modes in by_test.items():
        code_on = modes.get("code_on", [])
        code_off = modes.get("code_off", [])

        # Counting accuracy (for tests with ground truth)
        on_correct = 0
        off_correct = 0
        total_with_gt = 0

        for i, (on_result, off_result) in enumerate(zip(code_on, code_off)):
            gt = on_result.get("ground_truth")
            if gt is not None:
                total_with_gt += 1

                on_extracted = extract_number(on_result.get("response_text", ""))
                off_extracted = extract_number(off_result.get("response_text", ""))

                if on_extracted == gt:
                    on_correct += 1
                if off_extracted == gt:
                    off_correct += 1

        # Code execution stats
        on_used_code = sum(1 for r in code_on if r.get("code_executed"))
        on_generated_images = sum(r.get("images_generated", 0) for r in code_on)

        comparison[test_name] = {
            "total_images": len(code_on),
            "code_on_accuracy": on_correct / total_with_gt if total_with_gt > 0 else None,
            "code_off_accuracy": off_correct / total_with_gt if total_with_gt > 0 else None,
            "code_blocks_executed": on_used_code,
            "images_annotated": on_generated_images,
            "has_ground_truth": total_with_gt > 0,
        }

    return comparison


def generate_report(results: list, comparison: dict) -> str:
    """Generate markdown comparison report."""
    report = []
    report.append("# Experiment Results: Gemini 3 Flash Agentic Vision")
    report.append(f"\n**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    report.append("\n## Summary\n")

    # Summary table
    report.append("| Test | Code OFF Accuracy | Code ON Accuracy | Code Blocks Used | Images Annotated |")
    report.append("|------|-------------------|------------------|------------------|------------------|")

    for test_name, stats in comparison.items():
        off_acc = f"{stats['code_off_accuracy']:.0%}" if stats['code_off_accuracy'] is not None else "N/A"
        on_acc = f"{stats['code_on_accuracy']:.0%}" if stats['code_on_accuracy'] is not None else "N/A"
        report.append(f"| {test_name} | {off_acc} | {on_acc} | {stats['code_blocks_executed']} | {stats['images_annotated']} |")

    # Detailed results
    report.append("\n## Detailed Results\n")

    for result in results:
        mode = "Code Execution ON" if result["code_execution"] else "Code Execution OFF"
        report.append(f"### {result['test_name']} ({mode})\n")

        for r in result["results"]:
            status_icon = "✓" if r["status"] == "success" else "⚠" if r["status"] == "skipped" else "✗"
            report.append(f"**{r['image']}** {status_icon}")

            if r.get("ground_truth"):
                extracted = extract_number(r.get("response_text", ""))
                correct = "✓" if extracted == r["ground_truth"] else "✗"
                report.append(f"  - Ground truth: {r['ground_truth']}, Extracted: {extracted} {correct}")

            if r.get("response_text"):
                preview = r["response_text"][:200].replace("\n", " ")
                report.append(f"  - Response: {preview}...")

            if r.get("code_executed"):
                report.append(f"  - Code executed: {len(r['code_executed'])} blocks")

            if r.get("images_generated"):
                report.append(f"  - Annotated images generated: {r['images_generated']}")

            report.append("")

    # Key findings
    report.append("\n## Key Findings\n")
    report.append("*To be filled in after reviewing results*\n")
    report.append("1. **[Most surprising result]**: ...\n")
    report.append("2. **[Hypothesis confirmed/refuted]**: ...\n")
    report.append("3. **[Unexpected behavior]**: ...\n")

    return "\n".join(report)


def main():
    print("Comparing experiment results...\n")

    # Load latest results
    results_file = find_latest_results()
    print(f"Loading: {results_file.name}")

    with open(results_file) as f:
        results = json.load(f)

    # Analyze
    comparison = analyze_results(results)

    # Generate report
    report = generate_report(results, comparison)

    # Save report
    report_path = OUTPUTS_DIR / "comparison.md"
    with open(report_path, "w") as f:
        f.write(report)

    print(f"\nReport saved to: {report_path}")
    print("\n" + "="*50)
    print("COMPARISON SUMMARY")
    print("="*50)

    for test_name, stats in comparison.items():
        print(f"\n{test_name}:")
        if stats["has_ground_truth"]:
            off_acc = f"{stats['code_off_accuracy']:.0%}" if stats['code_off_accuracy'] is not None else "N/A"
            on_acc = f"{stats['code_on_accuracy']:.0%}" if stats['code_on_accuracy'] is not None else "N/A"
            print(f"  Code OFF: {off_acc} → Code ON: {on_acc}")
        else:
            print(f"  (No ground truth - manual review needed)")
        print(f"  Code blocks executed: {stats['code_blocks_executed']}")
        print(f"  Annotated images: {stats['images_annotated']}")


if __name__ == "__main__":
    main()
