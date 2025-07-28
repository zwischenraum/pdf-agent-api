#!/usr/bin/env python3
"""
Simple script to run visual QA evaluations.

Usage:
    python run_eval.py                              # Use default files
    python run_eval.py --eval-set my_questions.jsonl  # Custom eval set
    python run_eval.py --image my_image.png         # Custom image
    python run_eval.py --output results.json        # Custom output file
"""

import argparse
from pathlib import Path

from evaluate import run_evaluation


def main():
    parser = argparse.ArgumentParser(
        description="Run Visual QA evaluation on question set",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--eval-set", default="eval/eval_set.jsonl", help="Path to evaluation set (JSONL format)"
    )

    parser.add_argument("--image", default="tests/test.png", help="Path to image file to analyze")

    parser.add_argument(
        "--output", help="Output file for results (default: auto-generated timestamp)"
    )

    parser.add_argument("--verbose", "-v", action="store_true", help="Show verbose output")

    args = parser.parse_args()

    # Validate input files exist
    if not Path(args.eval_set).exists():
        print(f"Error: Evaluation set '{args.eval_set}' not found.")
        return 1

    if not Path(args.image).exists():
        print(f"Error: Image file '{args.image}' not found.")
        return 1

    # Run evaluation
    try:
        results = run_evaluation(
            eval_set_path=args.eval_set, image_path=args.image, output_file=args.output
        )

        if results:
            print(f"\n🎉 Evaluation complete! Accuracy: {results.get_accuracy():.1f}%")
            return 0
        else:
            print("\n❌ Evaluation failed.")
            return 1

    except KeyboardInterrupt:
        print("\n\n⚠️  Evaluation interrupted by user.")
        return 1
    except Exception as e:
        print(f"\n❌ Error during evaluation: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
