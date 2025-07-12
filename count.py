import json
import argparse

# 1. 의도 및 계획 설명
# - 명령줄 파라미터로 JSON 파일 경로를 받아서, 각 category(카테고리)별로 items(아이템)가 몇 개씩 있는지 세어볼 거야.
# - 개수와 함께 전체 대비 백분율도 표시해서 비율을 한눈에 파악할 수 있게 해줄 거야.
# - argparse를 사용해서 사용자 친화적인 명령줄 인터페이스를 제공할 거야.
# - 출력은 "카테고리명: 개수 (백분율)" 형태로 보여줄 거고, 혹시 파일이 없거나 JSON 구조가 다르면 예외 처리를 해줄 거야.

def count_items_by_category(json_path):
    """JSON 파일에서 카테고리별 아이템 개수와 백분율을 세는 함수"""
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"❌ 파일을 찾을 수 없습니다: {json_path}")
        return
    except json.JSONDecodeError:
        print(f"❌ JSON 파일 형식이 올바르지 않습니다: {json_path}")
        return

    total_items = 0
    category_counts = []
    
    # 먼저 전체 아이템 수 계산
    for category_block in data:
        category = category_block.get("category", "알 수 없음")
        items = category_block.get("items", [])
        item_count = len(items)
        total_items += item_count
        category_counts.append((category, item_count))
    
    # 전체 아이템이 0개인 경우 처리
    if total_items == 0:
        print("📊 분석 결과: 아이템이 없습니다.")
        return
    
    print(f"📊 파일 분석 결과: {json_path}")
    print("=" * 70)
    
    # 카테고리별 개수와 백분율 출력
    for category, item_count in category_counts:
        percentage = (item_count / total_items) * 100
        print(f"{category}: {item_count}개 ({percentage:.1f}%)")
    
    print("=" * 70)
    print(f"🔢 전체 아이템 수: {total_items}개 (100.0%)")

def main():
    # ArgumentParser 생성
    parser = argparse.ArgumentParser(
        description="JSON 파일의 카테고리별 아이템 개수와 백분율을 분석하는 프로그램",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  python count.py result.json
  python count.py results/result-0714-000721.json
  python count.py results/20250714-030156-classified.json
        """
    )
    
    # 필수 인수: JSON 파일 경로
    parser.add_argument(
        "json_file", 
        help="분석할 JSON 파일의 경로"
    )
    
    # 인수 파싱
    args = parser.parse_args()
    
    # 카테고리별 개수와 백분율 분석 실행
    count_items_by_category(args.json_file)

if __name__ == "__main__":
    main()
