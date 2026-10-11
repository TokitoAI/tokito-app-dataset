"""Record confidence-threshold sensitivity for a partial-label model diagnostic."""
import argparse
import json
from pathlib import Path

from train_partial_component_diagnostic import OUT, audited_metrics, prepare


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WEIGHTS = ROOT / "models/partial-component-diagnostic/best.pt"
DEFAULT_REPORT = ROOT / "models/partial-component-diagnostic/threshold-sweep.json"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--weights", type=Path, default=DEFAULT_WEIGHTS)
    parser.add_argument("--output", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--thresholds", type=float, nargs="+", default=[0.01, 0.03, 0.05, 0.1, 0.25])
    args = parser.parse_args()
    if not args.weights.is_file():
        raise FileNotFoundError(args.weights)

    from ultralytics import YOLO

    samples, manifest = prepare(640)
    validation = [sample for sample in samples if sample["entry"]["split"] == "val"]
    model = YOLO(str(args.weights))
    report = {
        "evaluation_valid": False,
        "production_eligible": False,
        "scope": (
            "Partial reviewed regions on the existing known-specimen validation images. "
            "Unknown pixels remain ignored; this is threshold sensitivity, not independent evaluation."
        ),
        "checkpoint": str(args.weights),
        "validation_images": [sample["entry"]["path"] for sample in validation],
        "thresholds": [
            audited_metrics(model, validation, manifest["class_names"], confidence=threshold)
            for threshold in args.thresholds
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
