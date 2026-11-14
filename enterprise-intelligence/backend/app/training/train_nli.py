from __future__ import annotations

import argparse
import json
from pathlib import Path

from datasets import Dataset
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    Trainer,
    TrainingArguments,
)


LABELS = ["contradiction", "neutral", "entailment"]
LABEL_TO_ID = {label: index for index, label in enumerate(LABELS)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True)
    parser.add_argument("--base-model", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--epochs", type=int, default=3)
    args = parser.parse_args()

    rows = []
    with Path(args.data).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                item = json.loads(line)
                label = item["label"].lower()

                if label not in LABEL_TO_ID:
                    raise ValueError(f"Invalid NLI label: {label}")

                rows.append({
                    "premise": item["premise"],
                    "hypothesis": item["hypothesis"],
                    "labels": LABEL_TO_ID[label],
                })

    if len(rows) < 10:
        raise ValueError("At least 10 NLI examples are required.")

    dataset = Dataset.from_list(rows)
    split = dataset.train_test_split(test_size=0.2, seed=42)

    tokenizer = AutoTokenizer.from_pretrained(args.base_model)

    def encode(batch):
        return tokenizer(
            batch["premise"],
            batch["hypothesis"],
            truncation=True,
            max_length=512,
        )

    tokenized = split.map(
        encode,
        batched=True,
        remove_columns=["premise", "hypothesis"],
    )

    model = AutoModelForSequenceClassification.from_pretrained(
        args.base_model,
        num_labels=3,
        id2label={i: label for i, label in enumerate(LABELS)},
        label2id=LABEL_TO_ID,
    )

    training_args = TrainingArguments(
        output_dir=args.output,
        learning_rate=2e-5,
        per_device_train_batch_size=8,
        per_device_eval_batch_size=8,
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
        train_dataset=tokenized["train"],
        eval_dataset=tokenized["test"],
        processing_class=tokenizer,
    )

    trainer.train()
    trainer.save_model(args.output)
    tokenizer.save_pretrained(args.output)

    print(f"NLI model saved to {args.output}")


if __name__ == "__main__":
    main()