"""주제 발굴 -> 대기열 등록 사이의 빈틈을 이어주는 스캐폴딩 (2026-08-22, PROJECT_CHARTER.md 6번 항목).

discover_topics.py가 뽑은 후보 목록(output/topic_candidates_*.md)에서 하나를 골라
input/queue/NN_이름/ 폴더를 미리 만들고 원본 기사 정보를 notes.md에 남겨둔다.

**의도적으로 script.txt/meta.json/images/는 만들지 않는다** — run_queue.py는 이 세 가지가
전부 있어야 처리 대상으로 보기 때문에(process_item 참고), 내용이 채워지기 전까지는 이 폴더가
"invalid"로 안전하게 건너뛰어진다. 즉 이 스크립트는 순서 정하기/폴더 만들기 같은 기계적인 일만
자동화하고, 실제 대본 작성(사람 판단이 필요한 부분)은 여전히 별도 단계로 남겨둔다.
"""
import argparse
import os
import re
import sys
from datetime import datetime

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUEUE_DIR = os.path.join(BASE_DIR, "input", "queue")


def parse_candidates(path):
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    items = []
    blocks = re.split(r"^## (\d+)\.\s+(.+)$", text, flags=re.MULTILINE)[1:]
    for i in range(0, len(blocks), 3):
        num, title, body = int(blocks[i]), blocks[i + 1].strip(), blocks[i + 2]
        source = re.search(r"^- 출처:\s*(.+)$", body, re.MULTILINE)
        link = re.search(r"^- 링크:\s*(.+)$", body, re.MULTILINE)
        keywords = re.search(r"^- 매칭 키워드:\s*(.+)$", body, re.MULTILINE)
        items.append({
            "num": num,
            "title": title,
            "source": source.group(1).strip() if source else "",
            "link": link.group(1).strip() if link else "",
            "keywords": keywords.group(1).strip() if keywords else "",
        })
    return items


def next_queue_number():
    if not os.path.isdir(QUEUE_DIR):
        return 1
    nums = []
    for name in os.listdir(QUEUE_DIR):
        m = re.match(r"^(\d+)_", name)
        if m:
            nums.append(int(m.group(1)))
    return (max(nums) + 1) if nums else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidates", required=True, help="output/topic_candidates_YYYY-MM-DD.md 경로")
    ap.add_argument("--pick", type=int, required=True, help="후보 번호 (파일 안의 N번)")
    ap.add_argument("--name", required=True, help="폴더 이름에 쓸 짧은 한글 슬러그 (예: 전월세안심신탁)")
    args = ap.parse_args()

    items = parse_candidates(args.candidates)
    chosen = next((it for it in items if it["num"] == args.pick), None)
    if chosen is None:
        raise SystemExit(f"{args.pick}번 후보를 찾을 수 없음 (파일에 {len(items)}개 후보 있음)")

    safe_name = re.sub(r"[^\w가-힣]", "", args.name)
    n = next_queue_number()
    item_dir = os.path.join(QUEUE_DIR, f"{n:02d}_{safe_name}")
    os.makedirs(item_dir, exist_ok=False)

    with open(os.path.join(item_dir, "notes.md"), "w", encoding="utf-8") as f:
        f.write(f"# 원본 기사 정보 (발견일: {datetime.now().strftime('%Y-%m-%d')})\n\n")
        f.write(f"**제목:** {chosen['title']}\n\n")
        f.write(f"**출처:** {chosen['source']}\n\n")
        f.write(f"**링크:** {chosen['link']}\n\n")
        f.write(f"**매칭 키워드:** {chosen['keywords']}\n\n")
        f.write("---\n이 폴더는 아직 대기열 처리 대상이 아닙니다 (script.txt/meta.json/images/가 없어서 "
                 "run_queue.py가 자동으로 건너뜁니다). script_package_template.md 형식으로 대본을 "
                 "작성하고 script.txt/meta.json/images/를 채우면 정식 대기열 항목이 됩니다.\n")

    print(f"생성 완료: {item_dir}")
    print("다음: script.txt / meta.json / images/ 채우면 대기열에 정식 등록됨 (notes.md의 원본 기사 참고)")


if __name__ == "__main__":
    main()
