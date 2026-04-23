from __future__ import annotations

import argparse
from pathlib import Path

from advanced_metrics import calculate_metrics
from analyze_delays import analyze
from clean_data import clean_and_merge
from interactive_charts import main as build_charts


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the TTC Analyst pipeline end to end or by step."
    )
    parser.add_argument(
        "--step",
        choices=("all", "clean", "analysis", "metrics", "charts"),
        default="all",
        help="Choose a single step or run the full pipeline.",
    )
    return parser


def run_pipeline(step: str) -> list[Path]:
    outputs: list[Path] = []

    if step in {"all", "clean"}:
        outputs.append(clean_and_merge())
    if step in {"all", "analysis"}:
        outputs.append(analyze())
    if step in {"all", "metrics"}:
        outputs.append(calculate_metrics())
    if step in {"all", "charts"}:
        outputs.append(build_charts())

    return outputs


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    outputs = run_pipeline(args.step)
    print("\nPipeline outputs:")
    for output_path in outputs:
        print(f"- {output_path}")


if __name__ == "__main__":
    main()
