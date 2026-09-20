"""이 컴퓨터에서 v2 영상을 만들 준비가 됐는지 점검 (비밀값은 출력하지 않음).
사용: python scripts/check_v2_env.py [--no-image]   (--no-image: Cloudflare 이미지 1장 테스트 생략)"""
import json
import os
import shutil
import sys
import tempfile

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "scripts"))
results = []


def report(ok, label, hint=""):
    results.append(ok)
    print(("OK   " if ok else "FAIL ") + label + ("" if ok or not hint else f"\n       → {hint}"))


def has(mod):
    try:
        __import__(mod)
        return True
    except Exception:
        return False


for mod, pkg in (("numpy", "numpy"), ("soundfile", "soundfile"), ("PIL", "pillow")):
    report(has(mod), f"파이썬 패키지 {pkg}", f"pip install {pkg}")
report(bool(shutil.which("ffmpeg")), "ffmpeg (PATH)", "ffmpeg 설치 후 PATH 등록")

try:
    import make_short as base
    report(os.path.exists(base.SUPERTONIC_PYTHON), "목소리(Supertonic) 파이썬 환경", f"없음: {base.SUPERTONIC_PYTHON} — CLAUDE.md '목소리 교체 M3' 절차로 설치")
    report(os.path.exists(base.CLONED_VOICE_STYLE), "목소리 스타일 파일(M3)", f"없음: {base.CLONED_VOICE_STYLE} — git pull 필요")
except Exception as e:
    report(False, "make_short 불러오기", str(e))

cred = os.path.join(BASE, "credentials", "cloudflare.json")
ok_cred = False
if os.path.exists(cred):
    try:
        d = json.load(open(cred, encoding="utf-8"))
        ok_cred = bool(d.get("account_id")) and bool(d.get("api_token"))
    except Exception:
        pass
report(ok_cred, "credentials/cloudflare.json (account_id, api_token)", "데스크톱의 같은 파일을 이 경로로 복사(깃에 올리지 말 것)")
report(os.path.exists(os.path.join(BASE, "credentials", "token.json")), "유튜브 token.json")
report(os.path.exists(os.path.join(BASE, "credentials", "github_token.txt")), "github_token.txt (인스타 게시용)")

if ok_cred and "--no-image" not in sys.argv:
    try:
        import imagegen_cloudflare as cf
        out = os.path.join(tempfile.mkdtemp(), "t.png")
        cf.generate("photorealistic small wooden model house on a table, soft light, no text", out)
        size = os.path.getsize(out)
        report(size > 20000, f"Cloudflare 이미지 생성 테스트 ({size // 1024}KB)")
    except Exception as e:
        report(False, "Cloudflare 이미지 생성 테스트", str(e)[:200])

print("\n" + ("모두 통과 — 이 컴퓨터에서 v2 렌더 가능" if all(results) else f"실패 {results.count(False)}건 — 위 FAIL 항목 해결 필요"))
sys.exit(0 if all(results) else 1)
