"""이 컴퓨터의 credentials/cloudflare.json을 직접 입력으로 만든다(파일을 옮길 필요 없음).
사용: python scripts/setup_cloudflare_key.py
토큰은 입력해도 화면에 보이지 않고(getpass), 어디에도 출력·기록되지 않는다."""
import getpass
import json
import os
import re
import subprocess
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(BASE, "credentials", "cloudflare.json")

if os.path.exists(PATH):
    if input("이미 cloudflare.json이 있습니다. 덮어쓸까요? (y/N) ").strip().lower() != "y":
        raise SystemExit("중단")
acc = input("Cloudflare Account ID (32자 영숫자, 대시보드 주소창 dash.cloudflare.com/ 뒤): ").strip()
if not re.fullmatch(r"[0-9a-fA-F]{32}", acc):
    raise SystemExit("Account ID 형식이 아님(32자리 16진수)")
tok = getpass.getpass("API Token (입력해도 안 보임, 붙여넣고 Enter): ").strip()
if len(tok) < 30 or " " in tok:
    raise SystemExit("토큰 형식이 이상함(너무 짧거나 공백 포함)")
os.makedirs(os.path.dirname(PATH), exist_ok=True)
with open(PATH, "w", encoding="utf-8") as f:
    json.dump({"account_id": acc, "api_token": tok}, f)
print("저장 완료 → 점검 실행")
sys.exit(subprocess.call([sys.executable, os.path.join(BASE, "scripts", "check_v2_env.py")]))
