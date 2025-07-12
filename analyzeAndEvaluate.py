from google import genai
from pydantic import BaseModel
import datetime
import json

from systemInstruction import SYSTEM_INSTRUCTION
from evalSystemInstruction import EVAL_SYSTEM_INSTRUCTION
from systemInstructionFixer import SYSTEM_INSTRUCTION_FIXER_INSTRUCTION

class Item(BaseModel):
  userID: str
  contents: str
  reason: str
class Case(BaseModel):
  category: str  
  items: list[Item]

def read_json_content(json_file_path):
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = str(json.load(f))
                    
    except FileNotFoundError:
        print(f"JSON 파일을 찾을 수 없습니다: {json_file_path}")
        return ""
    except Exception as e:
        print(f"JSON 파일 읽기 오류: {e}")
        return ""
    
    return data

#########################################################
# 분석할 파일명
json_data = read_json_content("20250714-121748-parsed-list.json")
#########################################################

client = genai.Client(api_key="")
response = client.models.generate_content(
    model="gemini-2.5-pro",
    contents=f"""
    <DataForAnalyze>
    {json_data}
    </DataForAnalyze>
    """,
    config={
        "system_instruction": SYSTEM_INSTRUCTION,
        "response_mime_type": "application/json",
        "response_schema": list[Case],
        "temperature": 0.1,
    },
)

now = datetime.datetime.now()
FILE_NAME = f"result-{now.strftime('%y%m%d-%H%M%S')}.json"

# Use the response as a JSON string.
with open(FILE_NAME, "w", encoding="utf-8") as f:
    f.write(response.text or "")

eval_response = client.models.generate_content(
    model="gemini-2.5-pro",
    contents=response.text,
    config={
        "system_instruction": EVAL_SYSTEM_INSTRUCTION,
        "response_mime_type": "application/json",
    },
)

with open(f"{FILE_NAME}_eval.json", "w", encoding="utf-8") as f:
    f.write(eval_response.text or "")

# import json
# try:
#     eval_data = json.loads(eval_response.text or "{}")
#     issues = eval_data.get("issues", [])
# except Exception as e:
#     print("검수 결과 파싱 실패:", e)
#     issues = []
