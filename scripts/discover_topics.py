"""주제 자동 발굴 파일럿 (2026-08-22, PROJECT_CHARTER.md 4번 항목의 첫 단계).

Google News RSS(무료, API 키 불필요)에서 브랜드 관심 키워드로 최근 뉴스를 모아
이미 대기열/완료된 주제와 겹치지 않는 후보만 추려 마크다운으로 저장한다.

의도적으로 하지 않는 것:
- 대본/영상 자동 생성 (사람이 후보를 보고 고른 뒤 직접 대본 작성 요청)
- 점수 산출에 외부 LLM 호출 사용 (비용/키 관리 부담 — 현재는 최신순 + 교차 언급 빈도만 사용)
- 큐에 자동으로 추가 (검토 없이 대기열에 들어가는 걸 방지)
"""
import argparse
import html
import os
import re
import sys
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

import requests

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUEUE_DIR = os.path.join(BASE_DIR, "input", "queue")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

# 브랜드 관심 범위 (PROJECT_CHARTER.md 2번: 「돈이 되는 부동산 지식」 전체)
QUERIES = [
    "부동산 정책", "종합부동산세", "청약 제도", "대출 규제", "DSR 규제",
    "전세사기", "부동산 경매", "재건축 재개발", "임대차보호법", "보유세",
    "취득세", "부동산 대책", "LTV 규제", "전세보증금", "다주택자 세금",
]

RSS_URL = "https://news.google.com/rss/search?q={query}&hl=ko&gl=KR&ceid=KR:ko"


def already_covered_keywords():
    """대기열 폴더 이름(번호 제외)에서 키워드를 뽑아 중복 소재를 거른다."""
    keywords = []
    if not os.path.isdir(QUEUE_DIR):
        return keywords
    for name in os.listdir(QUEUE_DIR):
        stripped = re.sub(r"^\d+_", "", name)
        if stripped:
            keywords.append(stripped)
    return keywords


def fetch_query(query, timeout=10):
    url = RSS_URL.format(query=urllib.parse.quote(query))
    resp = requests.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    root = ET.fromstring(resp.content)
    items = []
    for item in root.findall(".//item"):
        title = html.unescape((item.findtext("title") or "").strip())
        link = (item.findtext("link") or "").strip()
        pub_date_raw = (item.findtext("pubDate") or "").strip()
        try:
            pub_date = datetime.strptime(pub_date_raw, "%a, %d %b %Y %H:%M:%S %Z").replace(tzinfo=timezone.utc)
        except ValueError:
            pub_date = None
        source = (item.findtext("source") or "").strip()
        items.append({"title": title, "link": link, "pub_date": pub_date, "source": source, "query": query})
    return items


def normalize_title(title):
    # 언론사마다 붙는 꼬리표(" - 조선일보" 등)를 떼고 비교
    return re.sub(r"\s*-\s*[^-]+$", "", title).strip()


def discover(days=5, top=15):
    covered = already_covered_keywords()
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    by_norm_title = {}
    for query in QUERIES:
        try:
            items = fetch_query(query)
        except requests.RequestException as e:
            print(f"  [경고] '{query}' 조회 실패(건너뜀): {e}")
            continue
        for it in items:
            if it["pub_date"] and it["pub_date"] < cutoff:
                continue
            norm = normalize_title(it["title"])
            if not norm:
                continue
            if any(kw in norm for kw in covered):
                continue
            entry = by_norm_title.setdefault(norm, {**it, "title": norm, "queries": set()})
            entry["queries"].add(query)
            if it["pub_date"] and (entry["pub_date"] is None or it["pub_date"] > entry["pub_date"]):
                entry["pub_date"] = it["pub_date"]
                entry["link"] = it["link"]
                entry["source"] = it["source"]

    candidates = list(by_norm_title.values())
    candidates.sort(key=lambda e: (len(e["queries"]), e["pub_date"] or cutoff), reverse=True)
    return candidates[:top]


def write_report(candidates, out_path):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"# 콘텐츠 주제 후보 ({datetime.now().strftime('%Y-%m-%d')})\n\n")
        f.write("자동 수집된 뉴스 기반 후보. 대본/영상은 자동 생성되지 않음 — 검토 후 채택할 것만 골라서 대기열에 추가할 것.\n\n")
        if not candidates:
            f.write("이번엔 새로운 후보가 없음(전부 기존 대기열과 겹치거나 최근 기사가 없음).\n")
        for i, c in enumerate(candidates, 1):
            date_str = c["pub_date"].strftime("%Y-%m-%d") if c["pub_date"] else "날짜미상"
            f.write(f"## {i}. {c['title']}\n")
            f.write(f"- 출처: {c['source'] or '미상'} ({date_str})\n")
            f.write(f"- 링크: {c['link']}\n")
            f.write(f"- 매칭 키워드: {', '.join(sorted(c['queries']))}\n\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=5, help="최근 며칠치 뉴스만 볼지")
    ap.add_argument("--top", type=int, default=15, help="후보 몇 개까지 뽑을지")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    out_path = args.out or os.path.join(OUTPUT_DIR, f"topic_candidates_{datetime.now().strftime('%Y-%m-%d')}.md")
    print(f"뉴스 수집 중 ({len(QUERIES)}개 키워드, 최근 {args.days}일)...")
    candidates = discover(days=args.days, top=args.top)
    write_report(candidates, out_path)
    print(f"후보 {len(candidates)}개 -> {out_path}")


if __name__ == "__main__":
    main()
