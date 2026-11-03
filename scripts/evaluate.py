import json
from pathlib import Path
current_path = Path(__file__).resolve().parent
file_ans = current_path.parent/"train"/"train"/"answers.jsonl"
ans_data = []
with open(file_ans,"r",encoding = "utf-8") as f:
    for line in f:
        ans_data.append(json.loads(line))
file_ans = current_path/"predictions.jsonl"
predict_data = []
print(file_ans)
with open(file_ans,"r",encoding="utf-8") as f:
    for line in f:
        predict_data.append(json.loads(line))
predict_data = {pre["id"]:pre["answer"] for pre in predict_data}
correct = 0
wrong = 0
abstain = 0
for ans in ans_data:
    if(ans["id"] in predict_data):
        if(ans["answer"] == predict_data[ans["id"]]):
            correct+=1
        elif(predict_data[ans["id"]]  == "null"):
            abstain+=1
        else:
            wrong+=1
PA = (correct - wrong)/(correct + wrong + abstain)
print(PA)