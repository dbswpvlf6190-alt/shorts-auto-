"""주간 스코어카드 (2026-11-20). 쇼츠 주제 그룹별 성과 + 롱폼 지표 + 채널 요약을 docs/scorecard_YYYY-MM-DD.md로 쓴다.
사용: python scripts/analytics/weekly_scorecard.py   (유튜브 토큰 필요, 읽기 전용)
주의: Analytics 날짜는 태평양시 → 영상별 조회는 윈도 시작을 게시일(UTC)-1일로 잡는다. 최근 3일 영상은 지표가 덜 집계돼 표에서 뺀다."""
import datetime
import os
import re
import statistics as st
import sys

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(BASE, "scripts"))
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
from googleapiclient.discovery import build  # noqa: E402
from youtube_upload import get_credentials  # noqa: E402

TAX = re.compile(r"양도|장기보유|중과|종부|재산세|종합부동산|상속|증여|재건축|재개발|조합|분담금|정비")
LOW = re.compile(r"대출|DSR|LTV|연체|전세|월세|임대|보증|임차|취득세|신고|과태료|자금조달")


def group(title):
    if TAX.search(title):
        return "A 세금·재건축"
    if LOW.search(title):
        return "B 대출·전월세·신고"
    return "C 기타(탐색)"


def main():
    creds = get_credentials()
    yt = build("youtube", "v3", credentials=creds)
    an = build("youtubeAnalytics", "v2", credentials=creds)
    today = datetime.date.today()
    since = (today - datetime.timedelta(days=60)).isoformat()
    ch = yt.channels().list(part="statistics,contentDetails", mine=True).execute()["items"][0]
    uploads = ch["contentDetails"]["relatedPlaylists"]["uploads"]
    vids, token = [], None
    while True:
        r = yt.playlistItems().list(part="snippet", playlistId=uploads, maxResults=50, pageToken=token).execute()
        for it in r["items"]:
            if it["snippet"]["publishedAt"][:10] >= since:
                vids.append((it["snippet"]["resourceId"]["videoId"], it["snippet"]["title"], it["snippet"]["publishedAt"]))
        token = r.get("nextPageToken")
        if not token or r["items"][-1]["snippet"]["publishedAt"][:10] < since:
            break
    meta = {}
    for i in range(0, len(vids), 50):
        for v in yt.videos().list(part="contentDetails,status", id=",".join(x[0] for x in vids[i:i + 50])).execute()["items"]:
            d = v["contentDetails"]["duration"]
            m = re.match(r"PT(?:(\d+)M)?(?:(\d+)S)?", d)
            meta[v["id"]] = (9999 if "H" in d else int(m.group(1) or 0) * 60 + int(m.group(2) or 0), v["status"]["privacyStatus"])
    rep = an.reports().query(ids="channel==MINE", startDate=since, endDate=today.isoformat(), dimensions="video",
                             metrics="views,averageViewPercentage,averageViewDuration,subscribersGained,likes,shares",
                             sort="-views", maxResults=200).execute()
    heads = [h["name"] for h in rep["columnHeaders"]]
    stats = {row[0]: dict(zip(heads, row)) for row in rep.get("rows", [])}
    cutoff = (today - datetime.timedelta(days=3)).isoformat()
    shorts, longs = [], []
    for vid, title, pub in vids:
        sec, priv = meta.get(vid, (0, ""))
        s = stats.get(vid)
        if priv != "public" or not s or pub[:10] > cutoff:
            continue
        s = dict(s, title=title, pub=pub[:10])
        (shorts if sec <= 180 else longs).append(s)
    out = [f"# 주간 스코어카드 {today.isoformat()}", "",
           f"채널: 구독 {ch['statistics']['subscriberCount']} · 영상 {ch['statistics']['videoCount']} · 총조회 {ch['statistics']['viewCount']}",
           f"(최근 60일 공개 영상 중 게시 3일 이상 지난 것만 집계: 쇼츠 {len(shorts)}편, 롱폼 {len(longs)}편)", "",
           "## 쇼츠 주제 그룹별", "", "| 그룹 | 편수 | 조회 중앙값 | 평균 유지율% | 구독/1000뷰 |", "|---|---|---|---|---|"]
    by = {}
    for s in shorts:
        by.setdefault(group(s["title"]), []).append(s)
    for g, l in sorted(by.items()):
        v = sum(z["views"] for z in l)
        out.append(f"| {g} | {len(l)} | {st.median(z['views'] for z in l):.0f} | {st.median(z['averageViewPercentage'] for z in l):.0f} | {sum(z['subscribersGained'] for z in l) / max(v, 1) * 1000:.2f} |")
    if shorts:
        tv = sum(z["views"] for z in shorts)
        out += ["", f"쇼츠 전체: 조회 중앙값 {st.median(z['views'] for z in shorts):.0f}, 좋아요/1000뷰 {sum(z['likes'] for z in shorts) / tv * 1000:.1f}, 공유/1000뷰 {sum(z['shares'] for z in shorts) / tv * 1000:.1f}, 구독/1000뷰 {sum(z['subscribersGained'] for z in shorts) / tv * 1000:.2f}"]
        out += ["", "### 쇼츠 상위 5 / 하위 5", ""]
        ranked = sorted(shorts, key=lambda z: -z["views"])
        for z in ranked[:5] + ranked[-5:]:
            out.append(f"- {z['pub']} 조회 {z['views']} 유지 {z['averageViewPercentage']:.0f}% [{group(z['title'])[0]}] {z['title'][:46]}")
    out += ["", "## 롱폼", "", "| 게시일 | 조회 | 평균시청(초) | 유지율% | 구독+ | 제목 |", "|---|---|---|---|---|---|"]
    for z in sorted(longs, key=lambda z: z["pub"]):
        out.append(f"| {z['pub']} | {z['views']} | {z['averageViewDuration']} | {z['averageViewPercentage']:.0f} | {z['subscribersGained']} | {z['title'][:36]} |")
    path = os.path.join(BASE, "docs", f"scorecard_{today.isoformat()}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    print(path)


if __name__ == "__main__":
    main()
