from google import genai
from pydantic import BaseModel
import datetime
import json
import os
import re
import sys

# from sample import SAMPLE
from systemInstruction import SYSTEM_INSTRUCTION
from evalSystemInstruction import EVAL_SYSTEM_INSTRUCTION
from systemInstructionFixer import SYSTEM_INSTRUCTION_FIXER_INSTRUCTION

class Item(BaseModel):
  userID: str
  contents: str
  
class Case(BaseModel):
  category: str  
  items: list[Item]

def generate_classification_result(client, system_instruction, sample_data):
    """분류 결과를 생성하는 함수"""
    response = client.models.generate_content(
        model="gemini-2.5-pro",
        contents=str(sample_data),
        config={
            "system_instruction": system_instruction,
            "response_mime_type": "application/json",
            "response_schema": list[Case],
        },
    )
    return response

def save_result_file(response_text, filename):
    """결과를 파일에 저장하는 함수"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(response_text or "")

def evaluate_result(client, response_text, filename):
    """결과를 평가하는 함수"""
    eval_response = client.models.generate_content(
        model="gemini-2.5-pro",
        contents=response_text,
        config={
            "system_instruction": EVAL_SYSTEM_INSTRUCTION,
            "response_mime_type": "application/json",
        },
    )
    
    save_result_file(eval_response.text, f"{filename}_eval.json")
    
    try:
        eval_data = json.loads(eval_response.text or "{}")
        issues = eval_data.get("issues", [])
        return issues, eval_response.text
    except Exception as e:
        print(f"검수 결과 파싱 실패: {e}")
        return [], ""

def update_system_instruction(new_instruction):
    """systemInstruction.py 파일을 업데이트하는 함수"""
    try:
        # 기존 파일 읽기
        with open("systemInstruction.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        # SYSTEM_INSTRUCTION 변수 내용 교체
        # 삼중 따옴표로 둘러싸인 내용을 찾아서 교체
        pattern = r'SYSTEM_INSTRUCTION = """.*?"""'
        new_content = f'SYSTEM_INSTRUCTION = """{new_instruction}"""'
        
        updated_content = re.sub(pattern, new_content, content, flags=re.DOTALL)
        
        # 파일에 다시 쓰기
        with open("systemInstruction.py", "w", encoding="utf-8") as f:
            f.write(updated_content)
        
        print("✅ systemInstruction.py 파일이 성공적으로 업데이트되었습니다.")
        return True
    except Exception as e:
        print(f"❌ systemInstruction.py 파일 업데이트 실패: {e}")
        return False

def generate_improved_instruction(client, current_instruction, eval_result):
    """개선된 시스템 프롬프트를 생성하는 함수"""
    fixer_response = client.models.generate_content(
        model="gemini-2.5-pro",
        contents=f"""
        <DraftPrompt>
        {current_instruction}
        </DraftPrompt>
        <InspectionResult>
        {eval_result}
        </InspectionResult>
        """,
        config={
            "system_instruction": SYSTEM_INSTRUCTION_FIXER_INSTRUCTION,
            "response_mime_type": "text/plain",
        },
    )
    return fixer_response.text

def main_process(max_iterations=3):
    """메인 프로세스 함수"""
    client = genai.Client(api_key="")
    
    # 반복 횟수 제한을 위한 카운터
    iteration = 0
    
    while iteration < max_iterations:
        iteration += 1
        print(f"\n🔄 반복 {iteration}/{max_iterations} 시작...")
        
        # 현재 시스템 프롬프트 가져오기 (매번 새로 import)
        if iteration > 1:
            # 두 번째 반복부터는 모듈을 다시 로드
            import importlib
            import systemInstruction
            importlib.reload(systemInstruction)
            current_instruction = systemInstruction.SYSTEM_INSTRUCTION
        else:
            current_instruction = SYSTEM_INSTRUCTION
        
        # 1. 분류 결과 생성
        print("📊 분류 결과 생성 중...")
        #########################################################
        # '' 대신 분석할 데이터를 넣어줘야 함
        response = generate_classification_result(client, current_instruction, '')
        #########################################################
        
        # 2. 파일 저장
        now = datetime.datetime.now()
        filename = f"result-{now.strftime('%m%d-%H%M%S')}.json"
        save_result_file(response.text, filename)
        print(f"💾 결과 파일 저장: {filename}")
        
        # 3. 결과 평가
        print("🔍 결과 평가 중...")
        issues, eval_result = evaluate_result(client, response.text, filename)
        
        print(f"📋 발견된 이슈 수: {len(issues)}")
        
        # 4. 이슈가 3개 미만이면 성공적으로 종료
        if len(issues) < 3:
            print("✅ 품질 기준을 만족하는 결과가 생성되었습니다!")
            print(f"📄 최종 결과: {filename}")
            break
        
        # 5. 이슈가 3개 이상이면 시스템 프롬프트 개선
        print("⚠️  이슈가 3개 이상 발견되어 시스템 프롬프트를 개선합니다...")
        
        # 개선된 프롬프트 생성
        improved_instruction = generate_improved_instruction(client, current_instruction, eval_result)
        
        # fixer 결과 저장 (기존 동작 유지)
        with open(f"{filename}_fixer.txt", "w", encoding="utf-8") as f:
            f.write(improved_instruction or "")
        
        # systemInstruction.py 업데이트
        if update_system_instruction(improved_instruction):
            print("🔄 시스템 프롬프트가 업데이트되었습니다. 다시 실행합니다...")
        else:
            print("❌ 시스템 프롬프트 업데이트 실패. 프로세스를 중단합니다.")
            break
    
    if iteration >= max_iterations:
        print(f"⏰ 최대 반복 횟수({max_iterations})에 도달했습니다. 프로세스를 종료합니다.")

if __name__ == "__main__":
    main_process()

    