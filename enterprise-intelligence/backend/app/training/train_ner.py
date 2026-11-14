from __future__ import annotations

import argparse
import json
from pathlib import Path

from datasets import Dataset
from transformers import (
    AutoModelForTokenClassification,
    AutoTokenizer,
    DataCollatorForTokenClassification,
    Trainer,
    TrainingArguments,
)


LABELS = [
    "O",
    "B-ORG", "I-ORG",
    "B-PRODUCT", "I-PRODUCT",
    "B-REGULATION", "I-REGULATION",
    "B-STANDARD", "I-STANDARD",
    "B-CLAUSE", "I-CLAUSE",
    "B-DATE", "I-DATE",
    "B-JURISDICTION", "I-JURISDICTION",
    "B-PENALTY", "I-PENALTY",
    "B-AUTHORITY", "I-AUTHORITY",
    "B-INDUSTRY", "I-INDUSTRY",
]

LABEL_TO_ID = {label: index for index, label in enumerate(LABELS)}


def load_rows(path: Path):
    rows = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    if not rows:
        raise ValueError("NER dataset is empty.")
    return rows


def build_token_labels(text, entities, offsets):
    labels = [LABEL_TO_ID["O"]] * len(offsets)

    for entity in entities:
        start = int(entity["start"])
        end = int(entity["end"])
        entity_type = str(entity["label"]).upper()

        if entity_type not in {
            "ORG", "PRODUCT", "REGULATION", "STANDARD",
            "CLAUSE", "DATE", "JURISDICTION", "PENALTY",
            "AUTHORITY", "INDUSTRY",
        }:
            raise ValueError(f"Unsupported NER label: {entity_type}")

        first = True

        for index, (token_start, token_end) in enumerate(offsets):
            if token_start == token_end:
                continue

            overlaps = token_start < end and token_end > start
            if not overlaps:
                continue

            prefix = "B-" if first else "I-"
            labels[index] = LABEL_TO_ID[prefix + entity_type]
            first = False

    return labels


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True)
    parser.add_argument("--base-model", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=8)
    args = parser.parse_args()

    rows = load_rows(Path(args.data))
    tokenizer = AutoTokenizer.from_pretrained(args.base_model)

    def encode(row):
        text = row["text"]
        encoded = tokenizer(
            text,
            truncation=True,
            max_length=512,
            return_offsets_mapping=True,
        )

        offsets = encoded.pop("offset_mapping")
        encoded["labels"] = build_token_labels(
            text,
            row.get("entities", []),
            offsets,
        )
        return encoded

    dataset = Dataset.from_list(rows)
    tokenized = dataset.map(
        encode,
        remove_columns=dataset.column_names,
    )

    split = tokenized.train_test_split(
        test_size=0.2,
        seed=42,
    )

    model = AutoModelForTokenClassification.from_pretrained(
        args.base_model,
        num_labels=len(LABELS),
        id2label={i: label for i, label in enumerate(LABELS)},
        label2id=LABEL_TO_ID,
    )

    training_args = TrainingArguments(
        output_dir=args.output,
        learning_rate=2e-5,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        num_train_epochs=args.epochs,
        weight_decay=0.01,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        report_to="none",
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=split["train"],
        eval_dataset=split["test"],
        processing_class=tokenizer,
        data_collator=DataCollatorForTokenClassification(tokenizer),
    )

    trainer.train()
    trainer.save_model(args.output)
    tokenizer.save_pretrained(args.output)

    print(f"NER model saved to {args.output}")


if __name__ == "__main__":
    main()