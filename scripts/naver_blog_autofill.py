"""네이버 블로그 글쓰기 로컬 브라우저 자동화 (2026-08-22, 위험 감수하고 진행하기로 사용자와 합의).

**반드시 읽을 것**:
- 네이버 블로그 API(blog/writePost.json)는 신규 앱에 더 이상 열리지 않아 사용 불가 확인됨(publish_naver_blog.py 참고).
- 커뮤니티 보고에 따르면(2025-07 기준) 네이버는 매크로성 자동 행위(공감/댓글/서로이웃 등)를 탐지해서
  계정을 제재하는 경우가 있음. 글쓰기 자동화도 같은 탐지에 걸릴 위험이 있다는 걸 사용자에게 미리 알렸고,
  위험을 감수하고 진행하기로 합의함(2026-08-22).
- 이 위험을 조금이라도 줄이기 위한 설계 원칙:
  1) **발행 버튼은 절대 자동으로 누르지 않는다** — 제목/본문만 채워두고 브라우저 창을 열어둔 채로 끝냄.
     최종 검토와 발행 클릭은 항상 사람이 직접 한다.
  2) 타이핑은 사람처럼 글자 단위 딜레이를 준다 (즉시 붙여넣기 아님).
  3) 로그인은 이 스크립트가 절대 대신 하지 않는다 — 최초 1회 `login` 커맨드로 사람이 직접 로그인하면
     그 세션이 로컬 프로필 폴더에 저장되고, 이후 `fill` 커맨드가 그 세션을 재사용한다.
- **셀렉터는 SmartEditor ONE의 알려진 구조 기준 최선의 추정이다.** 네이버가 에디터 마크업을 바꾸면
  안 맞을 수 있다 — 실패하면 `output/naver_autofill_debug.png` 스크린샷을 확인해서 이 파일의
  TITLE_SELECTORS/BODY_SELECTORS를 조정할 것.

사용법:
  python scripts/naver_blog_autofill.py login   # 최초 1회, 브라우저 뜨면 직접 로그인 후 터미널에서 Enter
  python scripts/naver_blog_autofill.py fill --draft "input/queue/09_.../blog_draft.md"
"""
import argparse
import os
import re
import sys

from playwright.sync_api import sync_playwright

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RENDER_ROOT = os.environ.get("SHORTS_RENDER_DIR", os.path.join(os.path.expanduser("~"), "ShortsAutoRender"))
PROFILE_DIR = os.path.join(RENDER_ROOT, "naver_browser_profile")  # 로그인 세션 저장 위치 — git 밖, 이 컴퓨터 로컬 전용
DEBUG_SCREENSHOT = os.path.join(BASE_DIR, "output", "naver_autofill_debug.png")

WRITE_URL = "https://blog.naver.com/GoBlogWrite.naver"

# 알려진 SmartEditor ONE 구조 기준 후보 셀렉터 (우선순위 순으로 시도)
TITLE_SELECTORS = [
    ".se-title-text .se-text-paragraph",
    ".se-documentTitle .se-text-paragraph",
    ".se-title-text [contenteditable='true']",
]
BODY_SELECTORS = [
    ".se-main-container .se-component-content .se-text-paragraph",
    ".se-main-container [contenteditable='true']",
]


def parse_draft(path):
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    m = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    title = m.group(1).strip() if m else os.path.splitext(os.path.basename(path))[0]
    # 본문은 제목 줄 제외, 마크다운 기호(#, **, -, 숫자.)를 걷어낸 평문 문단들로 변환
    # (SmartEditor는 문단 단위 타이핑이 안전 — 복잡한 서식 자동화는 하지 않음, 서식은 발행 전 사람이 다듬음)
    body_lines = [l for l in text.split("\n") if not l.startswith("# ")]
    paragraphs = []
    cur = []
    for line in body_lines:
        line = line.strip()
        if line.startswith("---"):
            continue
        if not line:
            if cur:
                paragraphs.append(" ".join(cur))
                cur = []
            continue
        line = re.sub(r"^#+\s*", "", line)
        line = re.sub(r"^\d+\.\s*", "", line)
        line = line.replace("**", "")
        cur.append(line)
    if cur:
        paragraphs.append(" ".join(cur))
    return title, paragraphs


def cmd_login(args):
    os.makedirs(PROFILE_DIR, exist_ok=True)
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(PROFILE_DIR, headless=False)
        page = context.new_page()
        page.goto("https://nid.naver.com/nidlogin.login")
        print(f"브라우저 창에서 네이버 로그인을 직접 완료하세요 (비밀번호는 이 스크립트가 절대 입력하지 않습니다). {args.wait}초 기다립니다...")
        page.wait_for_timeout(args.wait * 1000)
        context.close()
    print(f"로그인 세션 저장 완료: {PROFILE_DIR}")


def _find_first(frame, selectors):
    for sel in selectors:
        loc = frame.locator(sel).first
        try:
            if loc.count() > 0:
                return loc
        except Exception:
            continue
    return None


def cmd_fill(args):
    if not os.path.isdir(PROFILE_DIR):
        raise SystemExit("로그인 세션이 없습니다 — 먼저 'login' 커맨드를 실행하세요.")
    title, paragraphs = parse_draft(args.draft)

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(PROFILE_DIR, headless=False)
        page = context.new_page()
        page.on("dialog", lambda d: (print(f"[대화상자] {d.message}"), d.accept()))
        page.goto(WRITE_URL)
        page.wait_for_timeout(3000)

        frame = page.frame_locator("iframe#mainFrame")

        title_el = _find_first(frame, TITLE_SELECTORS)
        if title_el is None:
            os.makedirs(os.path.dirname(DEBUG_SCREENSHOT), exist_ok=True)
            page.screenshot(path=DEBUG_SCREENSHOT)
            raise SystemExit(
                f"제목 입력란을 못 찾았습니다. {DEBUG_SCREENSHOT} 스크린샷을 확인하고 "
                "TITLE_SELECTORS를 조정하세요. 브라우저 창은 열어뒀으니 직접 눌러서 계속 진행해도 됩니다."
            )
        title_el.click()
        page.keyboard.type(title, delay=35)

        body_el = _find_first(frame, BODY_SELECTORS)
        if body_el is None:
            os.makedirs(os.path.dirname(DEBUG_SCREENSHOT), exist_ok=True)
            page.screenshot(path=DEBUG_SCREENSHOT)
            print(f"본문 입력란을 못 찾았습니다. {DEBUG_SCREENSHOT} 확인 후 직접 본문만 입력해주세요.")
        else:
            body_el.click()
            for para in paragraphs:
                page.keyboard.type(para, delay=15)
                page.keyboard.press("Enter")
                page.keyboard.press("Enter")

        os.makedirs(os.path.dirname(DEBUG_SCREENSHOT), exist_ok=True)
        page.screenshot(path=DEBUG_SCREENSHOT)
        print(f"제목/본문 입력 완료 (스크린샷: {DEBUG_SCREENSHOT}).")
        print("*** 발행 버튼은 자동으로 누르지 않습니다 — 서식/오탈자 확인 후 직접 발행해주세요. ***")
        input("확인 다 하셨으면 이 터미널에서 Enter를 누르세요 (창은 그대로 열려 있습니다)...")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_login = sub.add_parser("login", help="최초 1회 수동 로그인 (세션 저장)")
    p_login.add_argument("--wait", type=int, default=90, help="로그인할 시간(초), 기본 90초")
    p_fill = sub.add_parser("fill", help="blog_draft.md 내용을 글쓰기 화면에 채워넣기 (발행은 안 함)")
    p_fill.add_argument("--draft", required=True)
    args = ap.parse_args()
    if args.cmd == "login":
        cmd_login(args)
    elif args.cmd == "fill":
        cmd_fill(args)


if __name__ == "__main__":
    main()
