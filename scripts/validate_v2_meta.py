"""v2 meta.json 검사기 (표준 라이브러리만 사용 — 클라우드 루틴 샌드박스에서도 돈다).
사용: python scripts/validate_v2_meta.py input/queue/NN_이름/meta.json
오류(ERROR)가 하나라도 있으면 종료코드 1. 경고(WARN)는 참고만.
규칙 근거는 docs/script_template_v2.md."""
import json
import re
import sys

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

KINDS = ("photo", "big", "money", "timeline")
COLORS = ("green", "gold", "red", "white")
BANNED_IMG = ("person", "people", "man", "woman", "face", "hand", "hands", "finger", "fingers", "crowd", "child",
              "sign", "signs", "signboard", "poster", "banner", "document", "documents", "contract", "calendar",
              "banknote", "banknotes", "currency", "cash", "dollar", "receipt", "newspaper", "screen", "logo",
              "letter", "letters", "words")
SUB_SENTENCE = "구독하고 놓치지 마세요."


def check(meta):
    errs, warns = [], []
    E, W = errs.append, warns.append

    if meta.get("format") != "v2":
        E('format이 "v2"가 아님')
    scenes = meta.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        E("scenes 누락")
        return errs, warns

    for key in ("youtube_title", "youtube_description", "tags", "tiktok_caption", "instagram_caption", "source_label"):
        if not str(meta.get(key, "")).strip():
            E(f"{key} 누락")
    if meta.get("privacy") != "public":
        E('privacy는 "public"이어야 함')
    desc = str(meta.get("youtube_description", ""))
    if SUB_SENTENCE not in desc:
        E("youtube_description에 '구독하고 놓치지 마세요.' 마무리 문장 없음")
    if "팔로우" in desc:
        E("youtube_description에 '팔로우' 금지(유튜브는 '구독')")
    for key in ("tiktok_caption", "instagram_caption"):
        if "팔로우" not in str(meta.get(key, "")):
            E(f"{key}에 '팔로우' 유도 문장 없음")
    if not str(meta.get("source_label", "")).startswith("출처"):
        W("source_label이 '출처:'로 시작하지 않음")

    n = len(scenes)
    if not 10 <= n <= 15:
        E(f"장면 수 {n}: 10~15개여야 함")
    total = 0
    photo = 0
    prompts = []
    has_money = False
    for i, sc in enumerate(scenes):
        p = f"scene {i}"
        kind = sc.get("kind")
        if kind not in KINDS:
            E(f"{p}: kind {kind!r}는 {KINDS} 중 하나")
            continue
        voice = str(sc.get("voice", ""))
        cap = str(sc.get("caption", ""))
        if not voice.strip():
            E(f"{p}: voice 누락")
        if not cap.strip():
            E(f"{p}: caption 누락")
        # 빌더가 공백 한 칸 기준 단어 수로 음성 타이밍을 장면에 나누므로 공백 형식이 어긋나면 렌더가 실패한다
        if voice != voice.strip() or "  " in voice or "\n" in voice or "\t" in voice:
            E(f"{p}: voice에 앞뒤 공백/연속 공백/줄바꿈 금지(단어는 공백 한 칸으로만 구분)")
        if re.search(r"[A-Za-z]{2,}", voice):
            W(f"{p}: voice에 영문 약어 있음 — 목소리가 잘못 읽을 수 있으니 한글 발음으로 쓸 것(자막 caption은 영문 가능)")
        if re.search(r"[0-9]{1,3}(,[0-9]{3})+|%|~|→|·", voice):
            W(f"{p}: voice에 쉼표숫자/%/~/→/·가 있음 — 읽기 표기를 풀어 쓸 것(예: 3% → 3퍼센트)")
        total += len(voice)
        if kind == "photo":
            photo += 1
            ip = str(sc.get("image_prompt", ""))
            prompts.append(ip)
            if not ip:
                E(f"{p}: image_prompt 누락")
            else:
                low = ip.lower()
                if not low.startswith("photorealistic"):
                    E(f"{p}: image_prompt는 'photorealistic'으로 시작")
                if not low.rstrip().endswith("no text"):
                    W(f"{p}: image_prompt는 ', no text'로 끝내는 것을 권장(빌더가 자동으로 붙임)")
                if re.search(r"[가-힣]", ip):
                    E(f"{p}: image_prompt는 영어여야 함")
                scrub = re.sub(r"no (text|signs?|logos?|people|words)", "", low)
                for bad in BANNED_IMG:
                    if re.search(rf"{bad}", scrub):
                        E(f"{p}: image_prompt에 금지 소재 '{bad}' (얼굴·손·간판·문서·지폐·달력 등은 가짜 글자/기형 발생)")
        if kind == "big" and not sc.get("big"):
            E(f"{p}: big 누락")
        if kind == "money":
            has_money = True
            if not isinstance(sc.get("amount"), (int, float)) or isinstance(sc.get("amount"), bool):
                E(f"{p}: amount(숫자) 누락")
            if "예시" not in str(sc.get("note", "")):
                E(f"{p}: money 장면 note에 '(예시 금액)' 표기 필요(금액은 가정임을 명시)")
        if kind == "timeline":
            cards = sc.get("cards")
            if not cards:
                E(f"{p}: cards 누락")
            else:
                for c in cards:
                    if c.get("color") not in COLORS:
                        E(f"{p}: card color는 {COLORS} 중 하나")
                    if not c.get("date") or not c.get("who"):
                        E(f"{p}: card에 date/who 필요")
                act = sc.get("active", "all")
                if act != "all" and (not isinstance(act, list) or any(not isinstance(a, int) or a >= len(cards) for a in act)):
                    E(f"{p}: active는 'all' 또는 카드 인덱스 배열")
        if sc.get("sfx") not in (None, "ding"):
            E(f"{p}: sfx는 'ding'만 가능")

    first = str(scenes[0].get("voice", ""))
    if len(first) > 20:
        E(f"훅(첫 장면 voice) {len(first)}자: 20자 이내(권장 15자)")
    elif len(first) > 15:
        W(f"훅 {len(first)}자: 15자 이내 권장")
    if not 250 <= total <= 380:
        E(f"voice 총 {total}자: 250~380자여야 함(약 30~40초)")
    if photo > n / 2 + 0.5:
        E(f"photo 장면 {photo}/{n}: 절반 이하여야 함")
    if len(set(prompts)) != len(prompts):
        E("image_prompt가 중복됨(같은 그림 반복 금지)")
    if not has_money:
        W("money 장면(금액 예시)이 없음 — 금액이 관련된 주제라면 넣을 것")
    last = str(scenes[-1].get("voice", ""))
    if "?" not in last:
        E("마지막 장면은 댓글을 부르는 질문(?)이어야 함")
    if not any("?" in str(s.get("voice", "")) for s in scenes[1:-1]):
        E("중간 반전 질문(?)이 없음")
    if not any(k in "".join(str(s.get("voice", "")) for s in scenes[-3:]) for k in ("보내", "공유", "알려")):
        W("공유 유도 문장이 마지막 3장면 안에 없음")
    return errs, warns


def main():
    if len(sys.argv) != 2:
        raise SystemExit("사용: python scripts/validate_v2_meta.py <meta.json>")
    with open(sys.argv[1], "r", encoding="utf-8") as f:
        meta = json.load(f)
    errs, warns = check(meta)
    for w in warns:
        print("WARN ", w)
    for e in errs:
        print("ERROR", e)
    print(f"결과: 오류 {len(errs)}, 경고 {len(warns)}")
    sys.exit(1 if errs else 0)


if __name__ == "__main__":
    main()
