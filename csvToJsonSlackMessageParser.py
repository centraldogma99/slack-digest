import json
import re
from datetime import datetime
import argparse
import sys

def remove_channel_status_messages(messages):
    """
    채널 출입 메시지를 제거합니다.
    '~에서 나갔습니다', '님이 채널을 떠남' 등의 메시지를 필터링합니다.
    """
    # 채널 출입 관련 키워드 패턴
    status_patterns = [
        r'.*에서 나갔습니다.*',
        r'.*님이 채널을 떠남.*',
        r'.*님이 채널에 참여.*',
        r'.*님이 들어왔습니다.*',
        r'.*님이 채널을 나갔습니다.*',
        r'.*님이 채널에서 나갔습니다.*',
        r'.*joined the channel.*',
        r'.*left the channel.*',
        r'.*has joined.*',
        r'.*has left.*'
    ]
    
    filtered_messages = []
    for message in messages:
        is_status_message = False
        for pattern in status_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                is_status_message = True
                break
        if not is_status_message:
            filtered_messages.append(message)
    
    return filtered_messages

def extract_user_id_and_contents(message):
    """
    메시지에서 User ID와 제보 내용을 추출합니다.
    """
    # User ID 추출 (숫자로 된 ID만)
    user_id_match = re.search(r'User ID:\s*(\d+)', message)
    if not user_id_match:
        return None, None
    
    user_id = user_id_match.group(1)
    
    # 제보 내용 추출 (제보 내용: ~ 첨부 파일: 전까지)
    contents_match = re.search(r'제보 내용:\s*(.*?)\s*첨부 파일:', message, re.DOTALL)
    if not contents_match:
        return None, None
    
    contents = contents_match.group(1).strip()
    
    return user_id, contents

def parse_slack_messages(raw_messages):
    """
    슬랙 메시지 목록을 파싱하여 JSON 형태로 변환합니다.
    """
    # 빈 줄 제거
    messages = [msg.strip() for msg in raw_messages if msg.strip()]
    
    if not messages:
        return []
    
    # 채널 출입 메시지 제거
    messages = remove_channel_status_messages(messages)
    
    # User ID와 제보 내용 추출
    parsed_messages = []
    for message in messages:
        user_id, contents = extract_user_id_and_contents(message)
        if user_id and contents:
            parsed_messages.append({
                "userId": user_id,
                "contents": contents
            })
    
    return parsed_messages

def generate_filename(output_path=None):
    """
    현재 시간을 기반으로 파일명을 생성합니다.
    """
    if output_path:
        return output_path
    
    current_time = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"{current_time}-parsed-list.json"

def save_to_json(data, filename):
    """
    데이터를 JSON 파일로 저장합니다.
    """
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def main():
    parser = argparse.ArgumentParser(description='슬랙 메시지를 파싱하여 JSON으로 변환')
    parser.add_argument('--input', '-i', help='입력 파일 경로 (없으면 stdin에서 읽음)')
    parser.add_argument('--output', '-o', help='출력 파일 경로 (없으면 현재 시간 기반으로 생성)')
    
    args = parser.parse_args()
    
    # 입력 데이터 읽기
    if args.input:
        try:
            with open(args.input, 'r', encoding='utf-8') as f:
                raw_data = f.read()
        except FileNotFoundError:
            print(f"파일을 찾을 수 없습니다: {args.input}")
            sys.exit(1)
    else:
        print("슬랙 메시지를 입력하세요 (완료 후 Ctrl+D 또는 Ctrl+Z):")
        raw_data = sys.stdin.read()
    
    # 메시지 목록으로 분할
    raw_messages = raw_data.split('\n')
    
    # 메시지 파싱
    parsed_messages = parse_slack_messages(raw_messages)
    
    # 파일명 생성
    filename = generate_filename(args.output)
    
    # JSON 파일로 저장
    save_to_json(parsed_messages, filename)
    
    print(f"파싱 완료: {len(parsed_messages)}개의 메시지가 '{filename}'에 저장되었습니다.")

if __name__ == "__main__":
    main() 