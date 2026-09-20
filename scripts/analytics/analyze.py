import json
import random
import re
import statistics as st
import sys
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")
random.seed(7)

vids = {v["id"]: v for v in json.load(open("videos_full.json", encoding="utf-8"))}
pv = json.load(open("per_video.json", encoding="utf-8"))
heads = pv["heads"]
rows = []
for r in pv["rows"]:
    d = dict(zip(heads, r))
    v = vids.get(d["video"])
    if not v:
        continue
    d.update(title=v["title"], published=v["published"][:10], duration=v["duration"], tags=v["tags"], vid=v["id"])
    d["era"] = "AUTO" if v["published"] >= "2026-08-15" else "OLD"
    rows.append(d)


def topic(t):
    t = re.sub(r"#\S+", "", t)
    rules = [
        ("전세사기/전세", r"전세"),
        ("경매", r"경매|낙찰|유찰|명도|입찰|권리|말소|지분"),
        ("세금(종부/양도/재산/취득)", r"종부세|양도세|재산세|취득세|세금|공제|과세|증세|감세|세율"),
        ("대출/금융", r"대출|DSR|LTV|금리|이자|은행"),
        ("청약/특공", r"청약|특공|특별공급|분양"),
        ("재건축/재개발", r"재건축|재개발|이주비|부담금|조합"),
        ("정책/공급/규제", r"그린벨트|공급|토허|토지거래|규제|감독원|정책|착공|다주택"),
        ("마인드셋/재테크일반", r"돈|부자|월급|마인드|재테크|투자|고수|삶|시도|습관|행동|이유"),
    ]
    for name, pat in rules:
        if re.search(pat, t):
            return name
    return "기타"


def title_feats(t):
    core = re.sub(r"#\S+", "", t).strip()
    return {
        "has_number": bool(re.search(r"\d", core)),
        "has_인데": "인데" in core or "는데" in core,
        "has_question": "?" in core or bool(re.search(r"(까|나요|이유|왜)\s*$", core)),
        "quote_style": core.startswith(("“", '"', "‘")),
        "len_gt30": len(core) > 30,
    }


for d in rows:
    d["topic"] = topic(d["title"])
    d.update(title_feats(d["title"]))
    d["conv"] = d["subscribersGained"] / d["views"] * 1000 if d["views"] else 0
    d["dow"] = datetime.fromisoformat(d["published"]).weekday()


def med(xs):
    return st.median(xs) if xs else float("nan")


def boot_ci(xs, n=2000):
    if len(xs) < 4:
        return (float("nan"), float("nan"))
    meds = sorted(med([random.choice(xs) for _ in xs]) for _ in range(n))
    return meds[int(n * 0.05)], meds[int(n * 0.95)]


def spearman(x, y):
    def rank(a):
        s = sorted(range(len(a)), key=lambda i: a[i])
        r = [0] * len(a)
        i = 0
        while i < len(s):
            j = i
            while j + 1 < len(s) and a[s[j + 1]] == a[s[i]]:
                j += 1
            for k in range(i, j + 1):
                r[s[k]] = (i + j) / 2 + 1
            i = j + 1
        return r
    rx, ry = rank(x), rank(y)
    mx, my = st.mean(rx), st.mean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = (sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry)) ** 0.5
    return num / den if den else float("nan")


def perm_p(a, b, n=5000):
    """두 그룹 중앙값 차이의 순열검정(양측) p값."""
    if len(a) < 3 or len(b) < 3:
        return float("nan")
    obs = abs(med(a) - med(b))
    pool = a + b
    cnt = 0
    for _ in range(n):
        random.shuffle(pool)
        if abs(med(pool[:len(a)]) - med(pool[len(a):])) >= obs:
            cnt += 1
    return cnt / n


def line(label, xs, extra=""):
    lo, hi = boot_ci(xs)
    print(f"  {label:<26} n={len(xs):>3}  중앙값={med(xs):>7.0f}  90%CI[{lo:.0f}~{hi:.0f}] {extra}")


json.dump(rows, open("joined.json", "w", encoding="utf-8"), ensure_ascii=False)

for era in ("OLD", "AUTO"):
    R = [d for d in rows if d["era"] == era]
    tv = sum(d["views"] for d in R)
    ts = sum(d["subscribersGained"] for d in R)
    tw = sum(d["shares"] for d in R)
    tl = sum(d["likes"] for d in R)
    print(f"\n===== {era} 영상 {len(R)}편 (2026-01-01 이후 집계) =====")
    print(f"  총조회 {tv:,} | 구독증가 {ts} ({ts / tv * 1000:.2f}/1000뷰) | 좋아요 {tl / tv * 1000:.1f}/1000뷰 | 공유 {tw / tv * 1000:.2f}/1000뷰")
    print(f"  평균시청비율 중앙값 {med([d['averageViewPercentage'] for d in R]):.1f}% | 평균시청시간 중앙값 {med([d['averageViewDuration'] for d in R]):.0f}초 | 길이 중앙값 {med([d['duration'] for d in R]):.0f}초")

print("\n===== 구독을 실제로 데려온 영상 TOP 12 (구독증가 순) =====")
for d in sorted(rows, key=lambda d: -d["subscribersGained"])[:12]:
    print(f"  구독+{d['subscribersGained']:>2} 조회{d['views']:>5} 전환{d['conv']:.1f}/1000 {d['era']} {d['published']} {d['duration']:>3}s 시청{d['averageViewPercentage']:.0f}% | {d['title'][:34]}")
zero = [d for d in rows if d["subscribersGained"] == 0]
print(f"  구독 0명 영상: {len(zero)}/{len(rows)}편, 그 조회수 합 {sum(d['views'] for d in zero):,}")

print("\n===== 조회수 상위 12 =====")
for d in sorted(rows, key=lambda d: -d["views"])[:12]:
    print(f"  조회{d['views']:>5} {d['era']} {d['published']} {d['duration']:>3}s 시청{d['averageViewPercentage']:.0f}% 구독+{d['subscribersGained']} | {d['title'][:36]}")

print("\n===== 주제별 (조회수 중앙값, 구독증가 합) =====")
for era in ("OLD", "AUTO"):
    print(f" [{era}]")
    R = [d for d in rows if d["era"] == era]
    for tp in sorted({d["topic"] for d in R}, key=lambda t: -med([d["views"] for d in R if d["topic"] == t])):
        xs = [d["views"] for d in R if d["topic"] == tp]
        subs = sum(d["subscribersGained"] for d in R if d["topic"] == tp)
        line(tp, xs, f"구독+{subs}")

print("\n===== 길이 vs 성과 (스피어만 상관) =====")
for era in ("OLD", "AUTO"):
    R = [d for d in rows if d["era"] == era]
    du = [d["duration"] for d in R]
    print(f"  [{era}] n={len(R)} 길이범위 {min(du)}~{max(du)}초")
    print(f"    길이 vs 조회수 {spearman(du, [d['views'] for d in R]):+.2f} | 길이 vs 평균시청비율 {spearman(du, [d['averageViewPercentage'] for d in R]):+.2f} | 길이 vs 구독전환 {spearman(du, [d['conv'] for d in R]):+.2f}")

print("\n===== 제목 특성별 조회수 (순열검정 p, 작을수록 우연이 아님) =====")
for feat in ("has_number", "has_인데", "has_question", "quote_style", "len_gt30"):
    for era in ("OLD", "AUTO"):
        R = [d for d in rows if d["era"] == era]
        a = [d["views"] for d in R if d[feat]]
        b = [d["views"] for d in R if not d[feat]]
        if len(a) >= 3 and len(b) >= 3:
            print(f"  {feat:<13} {era:<4} 있음 n={len(a):>3} 중앙값 {med(a):>6.0f} | 없음 n={len(b):>3} 중앙값 {med(b):>6.0f} | p={perm_p(a, b):.3f}")

print("\n===== 업로드 요일별 조회수 중앙값 =====")
names = "월화수목금토일"
for era in ("OLD", "AUTO"):
    R = [d for d in rows if d["era"] == era]
    print(f"  [{era}] " + " ".join(f"{names[k]}:{med([d['views'] for d in R if d['dow']==k]):.0f}(n{len([d for d in R if d['dow']==k])})" for k in range(7)))

print("\n===== 자동화 영상 시간순 (조회·시청비율·구독) =====")
for d in sorted([d for d in rows if d["era"] == "AUTO"], key=lambda d: d["published"]):
    print(f"  {d['published']} {d['duration']:>3}s 조회{d['views']:>5} 시청{d['averageViewPercentage']:>5.0f}% 시청시간{d['averageViewDuration']:>3.0f}s 구독+{d['subscribersGained']} 좋아요{d['likes']:>2} 공유{d['shares']:>2} | {d['title'][:28]}")


print("\n\n########## 추가: 같은 조건 비교 (자동화 직전 2개월 OLD vs AUTO) ##########")
late_old = [d for d in rows if d["era"] == "OLD" and "2026-06-15" <= d["published"] <= "2026-08-14"]
auto = [d for d in rows if d["era"] == "AUTO"]
def summ(R, label):
    tv = sum(d["views"] for d in R)
    print(f"[{label}] {len(R)}편 | 조회수 중앙값 {med([d['views'] for d in R]):.0f} | 평균시청비율 중앙값 {med([d['averageViewPercentage'] for d in R]):.0f}% | 길이 중앙값 {med([d['duration'] for d in R]):.0f}초 | "
          f"구독 {sum(d['subscribersGained'] for d in R)} ({sum(d['subscribersGained'] for d in R)/tv*1000:.2f}/1000뷰) | 좋아요 {sum(d['likes'] for d in R)/tv*1000:.1f}/1000뷰 | 댓글 {sum(d['comments'] for d in R)/tv*1000:.2f}/1000뷰 | 공유 {sum(d['shares'] for d in R)/tv*1000:.2f}/1000뷰")
summ(late_old, "OLD 6/15~8/14")
summ(auto, "AUTO 8/15~")
for key, lab in (("views", "조회수"), ("averageViewPercentage", "평균시청비율"), ("duration", "길이")):
    a = [d[key] for d in late_old]; b = [d[key] for d in auto]
    print(f"  {lab}: OLD중앙 {med(a):.0f} vs AUTO중앙 {med(b):.0f}  순열검정 p={perm_p(a, b):.4f}")
# 구독전환: 영상 단위 (구독>=1 비율)
print(f"  구독 1명 이상 얻은 영상 비율: OLD {sum(d['subscribersGained']>0 for d in late_old)/len(late_old)*100:.0f}% vs AUTO {sum(d['subscribersGained']>0 for d in auto)/len(auto)*100:.0f}%")

print("\n########## 평균시청비율 구간별 (AUTO 39편) ##########")
for lo, hi in ((0, 35), (35, 60), (60, 100), (100, 999)):
    R = [d for d in auto if lo <= d["averageViewPercentage"] < hi]
    print(f"  {lo}~{hi}% : {len(R)}편, 조회수 중앙값 {med([d['views'] for d in R]):.0f}, 구독 {sum(d['subscribersGained'] for d in R)}, 공유합 {sum(d['shares'] for d in R)}")

print("\n########## 길이 구간별 (AUTO) ##########")
for lo, hi in ((0, 45), (45, 55), (55, 100)):
    R = [d for d in auto if lo <= d["duration"] < hi]
    print(f"  {lo}~{hi}초: {len(R)}편, 평균시청비율 중앙값 {med([d['averageViewPercentage'] for d in R]):.0f}%, 조회수 중앙값 {med([d['views'] for d in R]):.0f}")

print("\n########## engagedViews / views (스와이프 안 하고 본 비율, 훅 성능 대용) ##########")
for era in ("OLD", "AUTO"):
    R = [d for d in rows if d["era"] == era and d["views"] > 0 and "engagedViews" in d]
    ratios = [d["engagedViews"] / d["views"] for d in R]
    tv = sum(d["views"] for d in R); te = sum(d["engagedViews"] for d in R)
    print(f"  {era}: 전체합 {te/tv*100:.1f}% | 영상별 중앙값 {med(ratios)*100:.1f}%")
