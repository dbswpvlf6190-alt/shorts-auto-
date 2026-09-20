import json
import random
import statistics as st
import sys
from datetime import datetime, timedelta, timezone

sys.stdout.reconfigure(encoding="utf-8")
random.seed(42)
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

an = build("youtubeAnalytics", "v2", credentials=Credentials.from_authorized_user_file("../../credentials/token.json"))
videos = json.load(open("videos_full.json", encoding="utf-8"))
KST = timezone(timedelta(hours=9))
DAYS = 15  # 업로드 전날부터 15일 (분석 일자는 태평양시 기준이라 하루 앞에서 시작해야 당일이 안 빠짐)
TOT = "views,engagedViews,averageViewPercentage,subscribersGained,likes,shares,comments"

sel = [v for v in videos if "2026-06-15" <= v["published"][:10] <= "2026-09-05" and v["privacy"] != "x"]
out = []
for v in sel:
    pub = datetime.fromisoformat(v["published"].replace("Z", "+00:00"))
    start = (pub - timedelta(days=1)).date()
    end = start + timedelta(days=DAYS)
    if end > datetime(2026, 9, 19).date():
        continue
    f = dict(ids="channel==MINE", startDate=start.isoformat(), endDate=end.isoformat(), filters=f"video=={v['id']}")
    try:
        t = an.reports().query(metrics=TOT, **f).execute().get("rows")
        d = an.reports().query(metrics="views", dimensions="day", sort="day", **f).execute().get("rows", [])
    except Exception as e:
        print("ERR", v["id"], str(e)[:60])
        continue
    if not t:
        continue
    views, eng, avp, subs, likes, shares, comments = t[0]
    daily = [r[1] for r in d]
    first2 = sum(daily[:3])  # 전날(0) + 당일 + 다음날
    out.append(dict(id=v["id"], era="AUTO" if v["published"] >= "2026-08-15" else "OLD", title=v["title"], pub=v["published"],
                    hourKST=pub.astimezone(KST).hour, dur=v["duration"], views=views, eng=eng, avp=avp, subs=subs,
                    likes=likes, shares=shares, comments=comments, first2share=(first2 / views if views else None)))
json.dump(out, open("redo14.json", "w", encoding="utf-8"), ensure_ascii=False)
print("영상 수:", len(out), "OLD", sum(x["era"] == "OLD" for x in out), "AUTO", sum(x["era"] == "AUTO" for x in out))

med = st.median


def perm(a, b, n=10000):
    obs = abs(med(a) - med(b))
    pool = a + b
    c = 0
    for _ in range(n):
        random.shuffle(pool)
        if abs(med(pool[:len(a)]) - med(pool[len(a):])) >= obs:
            c += 1
    return c / n


G = {e: [x for x in out if x["era"] == e] for e in ("OLD", "AUTO")}
print("\n=== 올바른 창(업로드 전날부터 15일) 비교 ===")
for e, R in G.items():
    tv = sum(x["views"] for x in R)
    print(f"[{e}] n={len(R)} | 조회 중앙값 {med(x['views'] for x in R):.0f} | 시청비율 중앙값 {med(x['avp'] for x in R):.0f}% | 스와이프안함 {sum(x['eng'] for x in R)/tv*100:.1f}% | "
          f"구독 {sum(x['subs'] for x in R)} ({sum(x['subs'] for x in R)/tv*1000:.2f}/1000뷰) | 좋아요 {sum(x['likes'] for x in R)/tv*1000:.1f}/1000 | 공유 {sum(x['shares'] for x in R)/tv*1000:.2f}/1000 | 길이 {med(x['dur'] for x in R):.0f}s")
    print(f"      조회의 첫 2~3일 집중도(중앙값) {med(x['first2share'] for x in R if x['first2share'] is not None)*100:.0f}%")
for k in ("views", "avp"):
    print(f"  {k}: OLD vs AUTO 순열검정 p={perm([x[k] for x in G['OLD']], [x[k] for x in G['AUTO']]):.4f}")

print("\n=== 업로드 시각(KST) × 시대별 15일 조회 중앙값 ===")


def bk(h):
    return "저녁(18-23)" if 18 <= h <= 23 else ("아침(6-10)" if 6 <= h <= 10 else "기타")


for e, R in G.items():
    b = {}
    for x in R:
        b.setdefault(bk(x["hourKST"]), []).append(x["views"])
    print(" ", e, {k: (len(v), int(med(v))) for k, v in b.items()})
A = G["AUTO"]
ev = [x["views"] for x in A if bk(x["hourKST"]) == "저녁(18-23)"]
ot = [x["views"] for x in A if bk(x["hourKST"]) != "저녁(18-23)"]
if len(ev) >= 3 and len(ot) >= 3:
    print(f"  AUTO 저녁 vs 그 외: 중앙값 {med(ev):.0f} vs {med(ot):.0f}, p={perm(ev, ot):.4f}")
