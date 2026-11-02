import json
from pathlib import Path
current_path = Path(__file__).resolve().parent
file_path = current_path.parent/"train"/"train"/"questions.jsonl"

data = []
with open(file_path, "r", encoding="utf-8") as f:
    for line in f:
        data.append(json.loads(line))

print(f"total number of questions: {len(data)}")
print(data[0])