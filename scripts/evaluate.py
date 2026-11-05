"""Local DataMate evaluator (train rulebook). Not the official contest scorer.

Default: development businesses only. Keep holdout sealed until final check.
Usage: python scripts/evaluate.py [--split validation] [--predictions PATH]
"""
import argparse
import csv
import json
import math
import re
import unicodedata
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GOLD_PATH = ROOT / "train" / "train" / "answers.jsonl"
QUESTIONS_PATH = ROOT / "train" / "train" / "questions.jsonl"
PRED_PATH = ROOT / "scripts" / "predictions.jsonl"
MANIFEST_PATH = ROOT / "scripts" / "split_manifest.json"
ERRORS_PATH = ROOT / "errors.csv"

ANSWER_TYPES = {
    "number", "percent", "date", "boolean",
    "string", "list", "table", "unanswerable",
}


def load_jsonl(path):
    """Read indexed JSONL; reject invalid or duplicate IDs."""
    records = {}
    with Path(path).open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: invalid JSON") from exc
            if not isinstance(record, dict) or not isinstance(record.get("id"), str):
                raise ValueError(f"{path}:{line_no}: expected object with string id")
            qid = record["id"]
            if qid in records:
                raise ValueError(f"{path}:{line_no}: duplicate id {qid}")
            records[qid] = record
    return records


def normalize_text(value):
    """Ignore case, punctuation and whitespace; preserve Vietnamese accents."""
    text = unicodedata.normalize("NFC", value).casefold()
    text = "".join(
        " " if unicodedata.category(ch).startswith(("P", "Z")) else ch
        for ch in text
    )
    return " ".join(text.split())


def equal_number(expected, actual):
    # bool is an int subclass; reject it for numeric answers.
    if type(expected) not in (int, float) or type(actual) not in (int, float):
        return False
    if not (math.isfinite(expected) and math.isfinite(actual)):
        return False
    return math.isclose(expected, actual, rel_tol=0, abs_tol=1e-9)


def equal_text(expected, actual, aliases=()):
    if not isinstance(expected, str) or not isinstance(actual, str):
        return False
    choices = [expected] + [x for x in aliases if isinstance(x, str)]
    return normalize_text(actual) in {normalize_text(x) for x in choices}


def valid_date(value):
    if not isinstance(value, str):
        return False
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        try:
            date.fromisoformat(value)
            return True
        except ValueError:
            return False
    if re.fullmatch(r"\d{4}-\d{2}", value):
        try:
            date.fromisoformat(value + "-01")
            return True
        except ValueError:
            return False
    return False


def equal_scalar(expected, actual, aliases=()):
    if isinstance(expected, str):
        return equal_text(expected, actual, aliases)
    if type(expected) is bool:
        return type(actual) is bool and expected == actual
    if type(expected) in (int, float):
        return equal_number(expected, actual)
    return False


def equal_list(gold, actual):
    expected = gold.get("answer")
    if not isinstance(expected, list) or not isinstance(actual, list):
        return False
    if len(expected) != len(actual):
        return False
    aliases = gold.get("alias", [])
    for index, (exp, got) in enumerate(zip(expected, actual)):
        options = (aliases[index] if index < len(aliases) and
                   isinstance(aliases[index], list) else [])
        if not equal_scalar(exp, got, options):
            return False
    return True


def equal_table(gold, actual):
    expected = gold.get("answer")
    if not isinstance(expected, dict) or not isinstance(actual, dict):
        return False
    cols_g, rows_g = expected.get("columns"), expected.get("rows")
    cols_p, rows_p = actual.get("columns"), actual.get("rows")
    if not all(isinstance(x, list) for x in (cols_g, rows_g, cols_p, rows_p)):
        return False
    if not cols_g or len(cols_g) != len(cols_p) or len(rows_g) != len(rows_p):
        return False
    if not all(isinstance(c, str) for c in cols_g + cols_p):
        return False

    # Match columns by name when possible, otherwise by position.
    normalized_g = [normalize_text(c) for c in cols_g]
    normalized_p = [normalize_text(c) for c in cols_p]
    if len(set(normalized_p)) == len(normalized_p) and set(normalized_g) == set(normalized_p):
        col_positions = [normalized_p.index(c) for c in normalized_g]
    else:
        col_positions = list(range(len(cols_g)))

    if not all(isinstance(r, list) and len(r) == len(cols_g) for r in rows_g):
        return False
    if not all(isinstance(r, list) and len(r) == len(cols_p) for r in rows_p):
        return False

    row_aliases = gold.get("alias", [])

    def row_matches(gold_i, predicted_row):
        gold_row = rows_g[gold_i]
        options = (row_aliases[gold_i] if gold_i < len(row_aliases) and
                   isinstance(row_aliases[gold_i], list) else [])
        for col, exp in enumerate(gold_row):
            got = predicted_row[col_positions[col]]
            if not equal_scalar(exp, got, options if col == 0 else ()):
                return False
        return True

    # One-to-one row matching handles arbitrary row order, even duplicate rows.
    assigned = {}

    def match(gold_i, seen):
        for pred_i, pred_row in enumerate(rows_p):
            if pred_i in seen or not row_matches(gold_i, pred_row):
                continue
            seen.add(pred_i)
            if pred_i not in assigned or match(assigned[pred_i], seen):
                assigned[pred_i] = gold_i
                return True
        return False

    return all(match(i, set()) for i in range(len(rows_g)))


def judge(gold, pred):
    """Return correct, wrong, or abstain according to train rulebook."""
    if pred is None:
        return "abstain"
    if not isinstance(pred, dict):
        return "wrong"
    kind = pred.get("type")
    if kind == "abstain":
        return "abstain"
    # Invalid unanswerable reason makes the record unreadable (zero score).
    if kind == "unanswerable" and "reason" in pred and not isinstance(pred["reason"], str):
        return "abstain"
    if kind != gold.get("type"):
        return "wrong"
    if kind not in ANSWER_TYPES:
        return "wrong"
    if kind == "unanswerable":
        # Train gold uses answer=null; prediction may omit answer entirely.
        return "correct" if pred.get("answer") is None else "wrong"
    if "answer" not in pred:
        return "wrong"

    actual = pred["answer"]
    expected = gold.get("answer")
    if kind in ("number", "percent"):
        ok = equal_number(expected, actual)
    elif kind == "date":
        ok = valid_date(actual) and actual == expected
    elif kind == "boolean":
        ok = type(actual) is bool and actual == expected
    elif kind == "string":
        ok = equal_text(expected, actual, gold.get("alias", []))
    elif kind == "list":
        ok = equal_list(gold, actual)
    else:
        ok = equal_table(gold, actual)
    return "correct" if ok else "wrong"


def evaluate(golds, predictions):
    """Evaluate one selected split; missing predictions count as abstain."""
    unknown_ids = set(predictions) - set(golds)
    if unknown_ids:
        raise ValueError(f"Unknown prediction IDs: {sorted(unknown_ids)[:5]}")
    if not golds:
        raise ValueError("Evaluation dataset is empty")
    counts = Counter()
    details = []
    for qid, gold in golds.items():
        pred = predictions.get(qid)
        status = judge(gold, pred)
        counts[status] += 1
        if status != "correct":
            details.append({
                "id": qid,
                "gold_type": gold.get("type"),
                "gold_answer": gold.get("answer"),
                "pred_type": pred.get("type") if pred else None,
                "pred_answer": pred.get("answer") if pred else None,
                "status": status,
            })
    assert sum(counts.values()) == len(golds)
    return {
        "total": len(golds),
        "correct": counts["correct"],
        "wrong": counts["wrong"],
        "abstain": counts["abstain"],
        "PA": (counts["correct"] - counts["wrong"]) / len(golds),
    }, details


def select_split(golds, questions, manifest, split):
    """Keep full golds separate; select business IDs without rewriting inputs."""
    selected = manifest[split]
    if len(set(selected)) != len(selected):
        raise ValueError(f"Duplicate business in {split}")
    selected_set = set(selected)
    missing = set(golds) - set(questions)
    if missing:
        raise ValueError(f"Questions missing for gold IDs: {len(missing)}")
    return {
        qid: gold for qid, gold in golds.items()
        if questions[qid].get("business_id") in selected_set
    }


def write_errors(path, details, questions=None):
    """Write wrong/abstain rows; never include unseen business gold values."""
    columns = ["id", "business_id", "question", "gold_type",
               "gold_answer", "pred_type", "pred_answer", "status"]
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with Path(path).open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for row in details:
            q = (questions or {}).get(row["id"], {})
            writer.writerow({
                **row,
                "business_id": q.get("business_id", ""),
                "question": q.get("question", ""),
                "gold_answer": json.dumps(row["gold_answer"], ensure_ascii=False),
                "pred_answer": json.dumps(row["pred_answer"], ensure_ascii=False),
            })


def main():
    parser = argparse.ArgumentParser(description="DataMate local PA evaluator (train)")
    parser.add_argument("--gold", type=Path, default=GOLD_PATH)
    parser.add_argument("--predictions", type=Path, default=PRED_PATH)
    parser.add_argument("--questions", type=Path, default=QUESTIONS_PATH)
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--split", choices=["development", "validation", "holdout"],
                        default="development")
    parser.add_argument("--allow-holdout", action="store_true")
    parser.add_argument("--errors", type=Path, default=ERRORS_PATH)
    args = parser.parse_args()
    if args.split == "holdout" and not args.allow_holdout:
        parser.error("Holdout is sealed: use --allow-holdout only for the final check")

    golds = load_jsonl(args.gold)
    predictions = load_jsonl(args.predictions)
    questions = load_jsonl(args.questions)
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    allowed_ids = set().union(*map(set, manifest.values()))
    if len(allowed_ids) != 30 or any(len(manifest[s]) != n for s, n in
                                     [("development", 20), ("validation", 5), ("holdout", 5)]):
        raise ValueError("Expected 20/5/5 distinct businesses in split manifest")
    target = select_split(golds, questions, manifest, args.split)

    if set(predictions) - set(golds):
        raise ValueError("Prediction contains ID not present in train answers")
    # Allow a prediction file containing multiple splits; score only selected.
    chosen_predictions = {qid: pred for qid, pred in predictions.items() if qid in target}
    summary, details = evaluate(target, chosen_predictions)
    write_errors(args.errors, details, questions)

    print(f"Split: {args.split}")
    for name, value in summary.items():
        print(f"{name}: {value}")
    print(f"Error report: {args.errors}")


if __name__ == "__main__":
    main()
