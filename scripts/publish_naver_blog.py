"""네이버 블로그 (2026-08-22, PROJECT_CHARTER.md 5번 항목 확장).

**중요 (2026-08-22 확인)**: writePost.json/listCategory.json은 accessToken 자체는 정상 발급되는데도
404 "API does not exist"를 반환함 — 네이버 개발자센터의 "사용 API 추가" 목록에 "블로그"가 더 이상
없는 것으로 확인됨(검색/카페/캘린더는 있음). 즉 이 문서화된 API를 신규 앱이 더 이상 못 쓰는 것으로 보임.
브라우저 자동화(Selenium 등)로 우회하는 방법도 검토했으나 유지보수 부담이 커서(에디터 구조 변경 시
자주 깨짐) 사용자와 상의 후 보류 — 대신 **글 초안을 사람이 복붙하기 쉬운 HTML로 만들어주는 것까지만
자동화**하기로 확정(2026-08-22).

따라서 실제로 쓰는 건 `render` 커맨드뿐이다. `auth`/`categories`/`publish`는 네이버가 API를 다시 열어주면
쓸 수 있게 남겨둔 코드이며, 공식 스펙(https://github.com/naver/naver-openapi-guide) 기준으로는 맞지만
지금은 호출하면 404가 난다.

credentials/naver_secret.json / naver_token.json: 인스타그램/유튜브와 동일 원칙으로 git에 안 올라감.
"""
import argparse
import json
import os
import re
import sys
import urllib.parse
from datetime import datetime, timedelta

import requests

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CRED_DIR = os.path.join(BASE_DIR, "credentials")
SECRET_PATH = os.path.join(CRED_DIR, "naver_secret.json")
TOKEN_PATH = os.path.join(CRED_DIR, "naver_token.json")

AUTHORIZE_URL = "https://nid.naver.com/oauth2.0/authorize"
TOKEN_URL = "https://nid.naver.com/oauth2.0/token"
WRITE_POST_URL = "https://openapi.naver.com/blog/writePost.json"
LIST_CATEGORY_URL = "https://openapi.naver.com/blog/listCategory.json"


def load_secret():
    if not os.path.exists(SECRET_PATH):
        raise SystemExit(f"{SECRET_PATH} 없음 — client_id/client_secret/redirect_uri를 먼저 저장할 것")
    with open(SECRET_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_token():
    if not os.path.exists(TOKEN_PATH):
        return None
    with open(TOKEN_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_token(token):
    os.makedirs(CRED_DIR, exist_ok=True)
    with open(TOKEN_PATH, "w", encoding="utf-8") as f:
        json.dump(token, f, ensure_ascii=False, indent=2)


def build_authorize_url():
    secret = load_secret()
    params = {
        "response_type": "code",
        "client_id": secret["client_id"],
        "redirect_uri": secret["redirect_uri"],
        "state": "shortsauto",
    }
    return AUTHORIZE_URL + "?" + urllib.parse.urlencode(params)


def exchange_code_for_token(code):
    secret = load_secret()
    resp = requests.get(TOKEN_URL, params={
        "grant_type": "authorization_code",
        "client_id": secret["client_id"],
        "client_secret": secret["client_secret"],
        "code": code,
        "state": "shortsauto",
    }, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    if "access_token" not in data:
        raise SystemExit(f"토큰 발급 실패: {data}")
    _persist(data)
    return data


def refresh_access_token(refresh_token):
    secret = load_secret()
    resp = requests.get(TOKEN_URL, params={
        "grant_type": "refresh_token",
        "client_id": secret["client_id"],
        "client_secret": secret["client_secret"],
        "refresh_token": refresh_token,
    }, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    if "access_token" not in data:
        raise SystemExit(f"토큰 갱신 실패: {data}")
    if "refresh_token" not in data:
        data["refresh_token"] = refresh_token
    _persist(data)
    return data


def _persist(data):
    expires_in = int(data.get("expires_in", 3600))
    token = {
        "access_token": data["access_token"],
        "refresh_token": data.get("refresh_token"),
        "expires_at": (datetime.now() + timedelta(seconds=expires_in - 60)).isoformat(),
    }
    save_token(token)


def get_valid_access_token():
    token = load_token()
    if not token:
        raise SystemExit(
            "naver_token.json 없음 — 최초 1회는 수동 인증 필요.\n"
            f"1) 아래 URL을 사용자 브라우저에서 열어 로그인/동의:\n{build_authorize_url()}\n"
            "2) 리다이렉트된 콜백 페이지의 code 값을 복사\n"
            "3) python scripts/publish_naver_blog.py auth --code <복사한 code> 실행"
        )
    if datetime.now() >= datetime.fromisoformat(token["expires_at"]):
        token = refresh_access_token(token["refresh_token"])
    return token["access_token"]


def list_categories():
    access_token = get_valid_access_token()
    resp = requests.get(LIST_CATEGORY_URL, headers={"Authorization": f"Bearer {access_token}"}, timeout=15)
    resp.raise_for_status()
    return resp.json()


def markdown_to_naver_html(md_text):
    """blog_template.md 규칙(# 제목, ## 소제목, 리스트, **굵게**)만 다루는 최소 변환기.
    복잡한 마크다운 전체를 지원하려 하지 않음 — 이 프로젝트가 생성하는 blog_draft.md 형식에만 맞춤."""
    lines = md_text.strip().split("\n")
    html_lines = []
    in_list = False
    for line in lines:
        line = line.rstrip()
        if line.startswith("# "):
            continue  # 제목은 title 파라미터로 따로 전송하므로 본문에서 제외
        if line.startswith("## "):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<h3>{line[3:].strip()}</h3>")
        elif re.match(r"^\d+\.\s", line):
            if not in_list:
                html_lines.append("<ul>")
                in_list = True
            html_lines.append(f"<li>{re.sub(r'^\\d+\\.\\s', '', line)}</li>")
        elif line.startswith("---"):
            continue
        elif line.strip() == "":
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append("<br>")
        else:
            text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", line)
            html_lines.append(f"<p>{text}</p>")
    if in_list:
        html_lines.append("</ul>")
    return "\n".join(html_lines)


def parse_blog_draft(path):
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    m = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    title = m.group(1).strip() if m else os.path.splitext(os.path.basename(path))[0]
    contents = markdown_to_naver_html(text)
    return title, contents


def render_to_html(draft_path, out_path=None):
    """blog_draft.md를 브라우저에서 열어 그대로 Ctrl+A/Ctrl+C 한 뒤 네이버 블로그 에디터에
    붙여넣기 좋은 HTML로 만든다. 서식(소제목/리스트/굵게)이 클립보드를 통해 그대로 옮겨감."""
    title, contents = parse_blog_draft(draft_path)
    out_path = out_path or os.path.splitext(draft_path)[0] + ".html"
    html = (
        "<!doctype html><html><head><meta charset='utf-8'>"
        f"<title>{title}</title></head><body>"
        f"<h1>{title}</h1>\n{contents}\n</body></html>"
    )
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    return out_path


def publish_post(title, contents, category_no=None):
    access_token = get_valid_access_token()
    data = {"title": title, "contents": contents}
    if category_no is not None:
        data["categoryNo"] = category_no
    resp = requests.post(WRITE_POST_URL, headers={"Authorization": f"Bearer {access_token}"}, data=data, timeout=20)
    resp.raise_for_status()
    result = resp.json()
    if result.get("message", {}).get("result", {}).get("status") != "SUCCESS":
        raise SystemExit(f"게시 실패: {result}")
    return result


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("auth-url", help="최초 인증용 authorize URL 출력")

    p_auth = sub.add_parser("auth", help="authorize 콜백에서 받은 code로 토큰 발급")
    p_auth.add_argument("--code", required=True)

    sub.add_parser("categories", help="블로그 카테고리 목록 조회")

    p_pub = sub.add_parser("publish", help="[현재 404] blog_draft.md 파일을 게시")
    p_pub.add_argument("--draft", required=True)
    p_pub.add_argument("--category", type=int, default=None)

    p_render = sub.add_parser("render", help="blog_draft.md -> 복붙용 HTML로 변환 (현재 실제로 쓰는 커맨드)")
    p_render.add_argument("--draft", required=True)
    p_render.add_argument("--out", default=None)

    args = ap.parse_args()
    if args.cmd == "auth-url":
        print(build_authorize_url())
    elif args.cmd == "auth":
        token = exchange_code_for_token(args.code)
        print(f"토큰 발급 완료 (만료까지 {token.get('expires_in')}초). {TOKEN_PATH}에 저장됨.")
    elif args.cmd == "categories":
        print(json.dumps(list_categories(), ensure_ascii=False, indent=2))
    elif args.cmd == "publish":
        title, contents = parse_blog_draft(args.draft)
        result = publish_post(title, contents, args.category)
        print(f"게시 완료: {title}")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif args.cmd == "render":
        out_path = render_to_html(args.draft, args.out)
        print(f"완료: {out_path} — 브라우저로 열어서 전체 선택(Ctrl+A) 후 복사, 네이버 블로그 글쓰기 화면에 붙여넣기")


if __name__ == "__main__":
    main()
