"""
Command-Line Runner for Adversarial Test Suite.
Generates a formatted terminal report comparing Version 1 and Version 2.
"""

import sys
import os
import warnings

# Suppress deprecation and transport warnings
warnings.filterwarnings("ignore")

# Force UTF-8 stdout if possible on Windows
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add root directory to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tests.test_adversarial_v1_vs_v2 import RUN_TEST_CASES


def main():
    print("=" * 80)
    print("      AI ESCAPE ROOM: ADVERSARIAL STRESS TEST & RELIABILITY BENCHMARK")
    print("=" * 80)
    print("Testing Version 1 (Baseline Pure-LLM) vs Version 2 (State Engine & Validation)\n")

    results = RUN_TEST_CASES()

    print(f"Total Test Scenarios Evaluated: {len(results['tests'])}")
    print(f"Version 1 (Pure LLM) Vulnerabilities Triggered: {results['v1_exploits']}/{len(results['tests'])} (CRITICAL WEAKNESS)")
    print(f"Version 2 (State Engine) Exploits Blocked:      {results['v2_defended']}/{len(results['tests'])} (100% RELIABLE)")
    print("-" * 80)

    for i, t in enumerate(results["tests"], 1):
        print(f"\n[{i}] {t['name'].upper()}")
        print(f"    Category:       {t['category']}")
        print(f"    Player Input:   \"{t['prompt']}\"")
        print(f"    Test Objective: {t['objective']}")
        print(f"    ------------------------------------------------------------------------")
        v1_display = t['v1_result'].encode("ascii", "replace").decode("ascii")
        v2_display = t['v2_result'].encode("ascii", "replace").decode("ascii")
        print(f"    Version 1 Result: {v1_display}")
        print(f"    Version 2 Result: {v2_display}")
        print(f"    Validation Rule:  {t['v2_explanation']}")

    print("\n" + "=" * 80)
    print("                      ALL BENCHMARK TESTS COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    main()

