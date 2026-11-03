import json
import random
from pathlib import Path
random.seed(2026)

question_path = Path(__file__).resolve().parent
file_ques = question_path.parent/"train"/"train"/"questions.jsonl"

data_question = []
with open(file_ques, "r", encoding="utf-8") as f:
    for line in f:
        data_question.append(json.loads(line))

business ={bid["business_id"] for bid in data_question}


data_split = {"development":{"biz_129","biz_120","biz_123"},"validation":{"biz_101","biz_112"},"holdout":{"biz_111","biz_113"}}
current_split = {"biz_129","biz_120","biz_123","biz_101","biz_112","biz_111","biz_113"}
need_dev = 20 - len(data_split["development"])
need_val = 5 - len(data_split["validation"])
need_hold = 5 - len(data_split["holdout"])

remain_list = sorted(business - current_split)
combination_dev = random.sample(remain_list,need_dev)
data_split["development"].update(set(combination_dev))
remain_list = list(set(remain_list) - set(combination_dev))
combination_val = random.sample(remain_list,need_val)
data_split["validation"].update(set(combination_val))
remain_list = list(set(remain_list)-set(combination_val))
combination_hold = random.sample(remain_list,need_hold)
data_split["holdout"].update(set(combination_hold))
data_split = {"development":sorted(data_split["development"]), "validation":sorted(data_split["validation"]), "holdout":sorted(data_split["holdout"])}
file_save = Path(__file__).resolve().parent/"split_manifest.json"

with open(file_save,"w",encoding = "utf-8") as f:
    json.dump(data_split,f,indent = 0,ensure_ascii=False)

