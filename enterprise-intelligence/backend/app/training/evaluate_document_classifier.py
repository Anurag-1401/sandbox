from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    f1_score,
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True)
    parser.add_argument("--model", required=True)
    args = parser.parse_args()

    model = joblib.load(args.model)

    texts, labels = [], []
    with Path(args.data).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            item = json.loads(line)
            texts.append(item["text"])
            labels.append(item["label"])

    predictions = model.predict(texts)

    output = {
        "macro_f1": f1_score(
            labels,
            predictions,
            average="macro",
            zero_division=0,
        ),
        "weighted_f1": f1_score(
            labels,
            predictions,
            average="weighted",
            zero_division=0,
        ),
        "classification_report": classification_report(
            labels,
            predictions,
            output_dict=True,
            zero_division=0,
        ),
        "confusion_matrix": confusion_matrix(
            labels,
            predictions,
            labels=sorted(set(labels)),
        ).tolist(),
        "labels": sorted(set(labels)),
    }

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()