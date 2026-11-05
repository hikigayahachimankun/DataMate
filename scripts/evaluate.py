import json
import math
from pathlib import Path
from collections import Counter
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]

GOLD_PATH = ROOT / "train/train/answers.jsonl"
PRED_PATH = ROOT / "scripts/predictions.jsonl"


def load_jsonl(path):
    records = {}

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue

            record = json.loads(line)
            qid = record["id"]

            if qid in records:
                raise ValueError(f"Duplicate ID: {qid}")

            records[qid] = record

    return records


def compare_number(gold, pred):
    actual = pred.get("answer")
    expected = gold.get("answer")

    if type(actual) not in (int, float):
        return False

    if type(expected) not in (int, float):
        return False

    return math.isclose(
        actual,
        expected,
        rel_tol=0,
        abs_tol=1e-9
    )

def compare_percent(gold, pred):
    actual = pred.get("answer")
    expected = gold["answer"]

    if type(actual) not in (int, float):
        return False
    return math.isclose(actual, expected, rel_tol = 0, abs_tol = 1e-9)


def compare_date(gold, pred):
    actual = pred.get("answer")
    expected = gold["answer"]
    d = ""
    if type(actual) != str:
        return False
    try:
        if len(actual) == 10:
            d = datetime.strptime(actual, "%Y-%m-%d")
            return d.strftime("%Y-%m-%d") == expected
        elif len(actual) == 7:
            d = datetime.strptime(actual, "%Y-%m")
            return d.strftime("%Y-%m") == expected
    except ValueError:
        return False 

def judge(gold, pred):

    if pred is None or pred.get("type") == "abstain":
        return "abstain"


    if pred.get("type") != gold["type"]:
        return "wrong"

    answer_type = gold["type"]


    if answer_type == "unanswerable":
        if "reason" in pred and not isinstance(pred["reason"], str):
            return "abstain"
        return "correct"


    if answer_type == "number":
        return "correct" if compare_number(gold, pred) else "wrong"

    if answer_type == "percent":
        return "correct" if compare_percent(gold, pred) else "wrong"

    if answer_type == "date":
        return "correct" if compare_date(gold,pred) else "wrong"


    raise NotImplementedError(
        f"Unsupported answer type: {answer_type}"
    )


def evaluate(golds, predictions):
    unknown_ids = predictions.keys() - golds.keys()

    if unknown_ids:
        raise ValueError(f"Unknown IDs: {sorted(unknown_ids)}")

    results = Counter()

    for qid, gold in golds.items():
        pred = predictions.get(qid)
        status = judge(gold, pred)
        results[status] += 1

    total = len(golds)
    pa = (results["correct"] - results["wrong"]) / total if total else 0

    return {
        "total": total,
        "correct": results["correct"],
        "wrong": results["wrong"],
        "abstain": results["abstain"],
        "PA": pa
    }


def main():
    golds = load_jsonl(GOLD_PATH)
    predictions = load_jsonl(PRED_PATH)

    results = evaluate(golds, predictions)

    for key, value in results.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
