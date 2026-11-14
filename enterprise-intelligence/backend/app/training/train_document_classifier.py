from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline


def load_dataset(path: Path):
    texts, labels = [], []

    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue

            item = json.loads(line)
            text = str(item["text"]).strip()
            label = str(item["label"]).strip()

            if not text or not label:
                raise ValueError(
                    f"Empty text or label on line {line_number}"
                )

            texts.append(text)
            labels.append(label)

    if len(texts) < 10:
        raise ValueError("At least 10 labelled examples are required.")

    return texts, labels


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True)
    parser.add_argument(
        "--output",
        default="./artifacts/models/document-classifier/latest.joblib",
    )
    args = parser.parse_args()

    texts, labels = load_dataset(Path(args.data))

    train_x, test_x, train_y, test_y = train_test_split(
        texts,
        labels,
        test_size=0.2,
        random_state=42,
        stratify=labels,
    )

    model = Pipeline([
        (
            "tfidf",
            TfidfVectorizer(
                ngram_range=(1, 2),
                max_features=100000,
                min_df=1,
                sublinear_tf=True,
            ),
        ),
        (
            "classifier",
            LogisticRegression(
                max_iter=2000,
                class_weight="balanced",
            ),
        ),
    ])

    model.fit(train_x, train_y)
    predictions = model.predict(test_x)

    report = classification_report(
        test_y,
        predictions,
        output_dict=True,
        zero_division=0,
    )

    print(json.dumps(report, indent=2))

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, output)

    metrics = {
        "macro_f1": f1_score(
            test_y,
            predictions,
            average="macro",
            zero_division=0,
        ),
        "weighted_f1": f1_score(
            test_y,
            predictions,
            average="weighted",
            zero_division=0,
        ),
        "test_examples": len(test_y),
        "labels": sorted(set(labels)),
        "classification_report": report,
    }

    metrics_path = output.with_suffix(".metrics.json")
    metrics_path.write_text(
        json.dumps(metrics, indent=2),
        encoding="utf-8",
    )

    print(f"Model saved: {output}")
    print(f"Metrics saved: {metrics_path}")


if __name__ == "__main__":
    main()