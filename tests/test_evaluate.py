import csv
import importlib.util
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "evaluate.py"
spec = importlib.util.spec_from_file_location("datamate_evaluate", MODULE_PATH)
ev = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ev)


def gold(kind, value, aliases=None):
    return {"type": kind, "answer": value, "alias": aliases or []}


def pred(kind, value):
    return {"type": kind, "answer": value}


@pytest.mark.parametrize("g,p,result", [
    (gold("number", 0), pred("number", 0), "correct"),
    (gold("number", 12), pred("number", 12.0), "correct"),
    (gold("number", 12), pred("number", True), "wrong"),
    (gold("number", 12), pred("number", "12"), "wrong"),
    (gold("number", 12), pred("percent", 12), "wrong"),
    (gold("percent", 12.4), pred("percent", 12.4), "correct"),
    (gold("percent", 12.4), pred("percent", 0.124), "wrong"),
    (gold("date", "2026-02-03"), pred("date", "2026-02-03"), "correct"),
    (gold("date", "2026-02-03"), pred("date", "2026-02-30"), "wrong"),
    (gold("date", "2026-02"), pred("date", "2026-02"), "correct"),
    (gold("date", "2026-02"), pred("date", "2026-2"), "wrong"),
    (gold("boolean", True), pred("boolean", True), "correct"),
    (gold("boolean", True), pred("boolean", 1), "wrong"),
    (gold("string", "Cà phê sữa (M)", ["SP0003"]), pred("string", "sp0003"), "correct"),
    (gold("string", "Cà phê sữa (M)"), pred("string", "CÀ PHÊ SỮA M"), "correct"),
    (gold("string", "Cà phê sữa (M)"), pred("string", "Ca phe sua M"), "wrong"),
    (gold("list", [3, 10]), pred("list", [3, 10]), "correct"),
    (gold("list", [3, 10]), pred("list", [10, 3]), "wrong"),
    (gold("list", ["Tên 1", "Tên 2"], [["SP01"], ["SP02"]]),
     pred("list", ["sp01", "Tên 2"]), "correct"),
    (gold("list", ["Tên 1"]), pred("list", "Tên 1"), "wrong"),
    (gold("unanswerable", None), {"type": "unanswerable"}, "correct"),
    (gold("unanswerable", None),
     {"type": "unanswerable", "reason": "Không đủ dữ liệu"}, "correct"),
    (gold("unanswerable", None),
     {"type": "unanswerable", "reason": None}, "abstain"),
    (gold("number", 1), {"type": "unanswerable"}, "wrong"),
    (gold("number", 1), {"type": "abstain"}, "abstain"),
    (gold("number", 1), None, "abstain"),
])
def test_judge(g, p, result):
    assert ev.judge(g, p) == result


def test_table_alias_columns_and_row_order():
    value = {"columns": ["khach_hang", "so_tien_no"],
             "rows": [["Chị Lan", 3200000], ["Anh Nam", 250000]]}
    g = gold("table", value, [["KH1"], ["KH2"]])
    p = {"type": "table", "answer": {
        "columns": ["so_tien_no", "khach_hang"],
        "rows": [[250000, "kh2"], [3200000, "Chị Lan"]]}}
    assert ev.judge(g, p) == "correct"
    p["answer"]["rows"][0][0] = 240000
    assert ev.judge(g, p) == "wrong"


def test_evaluate_pa_missing_and_wrong():
    golds = {"q1": gold("number", 1), "q2": gold("number", 2),
             "q3": gold("number", 3)}
    predictions = {"q1": pred("number", 1), "q2": pred("number", 99)}
    summary, details = ev.evaluate(golds, predictions)
    assert summary == {"total": 3, "correct": 1, "wrong": 1,
                       "abstain": 1, "PA": 0}
    assert {d["id"] for d in details} == {"q2", "q3"}


def test_empty_and_unknown_ids():
    with pytest.raises(ValueError, match="empty"):
        ev.evaluate({}, {})
    with pytest.raises(ValueError, match="Unknown"):
        ev.evaluate({"q1": gold("number", 1)}, {"q2": pred("number", 2)})


def test_load_jsonl_duplicates(tmp_path):
    path = tmp_path / "duplicate.jsonl"
    path.write_text('{"id":"q1"}\n{"id":"q1"}\n', encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate"):
        ev.load_jsonl(path)


def test_error_report(tmp_path):
    output = tmp_path / "errors.csv"
    details = [{"id": "q1", "gold_type": "number", "gold_answer": 2,
                "pred_type": "number", "pred_answer": 3, "status": "wrong"}]
    ev.write_errors(output, details,
                    {"q1": {"business_id": "biz_101", "question": "Bao nhiêu?"}})
    with output.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 1
    assert rows[0]["business_id"] == "biz_101"
    assert rows[0]["gold_answer"] == "2"
