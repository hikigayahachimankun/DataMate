import json
from pathlib import Path
question_path = Path(__file__).resolve().parent
file_ques = question_path.parent/"train"/"train"/"questions.jsonl"

data_question = []
with open(file_ques, "r", encoding="utf-8") as f:
    for line in f:
        data_question.append(json.loads(line))

business ={bid["business_id"]:0 for bid in data_question}

for b_id in data_question:
        business[b_id["business_id"]] +=1
print(business)
check_only = {"1":set() , "2": set(), "3" : set(), "4":set()}
id_business = {}
for key in data_question:
    id_business[key["id"]] = id_business.get(key["id"],0) + 1
    if(id_business[key["id"]]> 1): 
         check_only["1"].add(key["id"])

data_answer = Path(__file__).resolve().parent
file_ans = data_answer.parent/"train"/"train"/"answers.jsonl"

data_ans = []

with open(file_ans,"r",encoding="utf-8") as f:
    for line in f:
        data_ans.append(json.loads(line))

type_count = {type_q["type"]:0 for type_q in data_ans}
for type_q in data_ans:
    type_count[type_q["type"]] +=1

id_answer = {}
for key in data_ans:
    id_answer[key["id"]] = id_answer.get(key["id"],0) + 1
    if(id_answer[key["id"]] > 1): 
        check_only["2"].add(key["id"])
