import json
from pathlib import Path
question_path = Path(__file__).resolve().parent
file_ques = question_path.parent/"train"/"train"/"questions.jsonl"

data_question = []
with open(file_ques, "r", encoding="utf-8") as f:
    for line in f:
        data_question.append(json.loads(line))

business ={bid["business_id"]:0 for bid in data_question}
print(f"Number of unique business IDs: {len(business)}")

for b_id in data_question:
    if(b_id["business_id"] in business):
        business[b_id["business_id"]] +=1
print(business)

data_answer = Path(__file__).resolve().parent
file_ans = data_answer.parent/"train"/"train"/"answers.jsonl"

data_ans = []

with open(file_ans,"r",encoding="utf-8") as f:
    for line in f:
        data_ans.append(json.loads(line))

type_count = {type_q["type"]:0 for type_q in data_ans}
for type_q in data_ans:
    if(type_q["type"] in type_count): type_count[type_q["type"]] +=1
print(type_count)