"""렌더된 롱폼 올리기(2026-10-30): long.mp4를 예약 공개로 올리고, 썸네일·자막(captions.srt)까지 붙인다.
업로드 정보는 make_longform이 만든 upload.json을 그대로 쓴다. 사용자 확인 후에만 실행할 것.

  python scripts/upload_longform.py --out-dir <렌더 폴더> --publish-at "2026-11-01 18:00"   (KST)

자막은 youtube.force-ssl 권한이 있는 토큰에서만 올라간다(데스크톱은 10/30 재인증 완료). 실패해도 영상은 그대로 두고 경고만 낸다."""
import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import youtube_upload as yu  # noqa: E402

KST = timezone(timedelta(hours=9))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--publish-at", required=True, help='KST "YYYY-MM-DD HH:MM"')
    args = ap.parse_args()

    done_p = os.path.join(args.out_dir, "youtube_uploaded.json")
    if os.path.exists(done_p):
        raise SystemExit(f"이미 올린 영상입니다: {open(done_p, encoding='utf-8').read()}")
    when = datetime.strptime(args.publish_at, "%Y-%m-%d %H:%M").replace(tzinfo=KST)
    if when <= datetime.now(KST):
        raise SystemExit("공개 시각이 이미 지났습니다")
    print(f"공개 예정: {when:%Y-%m-%d (%a) %H:%M} KST")  # 요일 확인용(10/30 요일 착각 사고)

    info = json.load(open(os.path.join(args.out_dir, "upload.json"), encoding="utf-8"))
    vid = yu.upload(os.path.join(args.out_dir, "long.mp4"), info["title"], info["description"], info["privacy"],
                    tags=info["tags"], thumbnail=info["thumbnail"], synthetic=info.get("synthetic", False),
                    category=info.get("category", "27"), language=info.get("language", "ko"),
                    publish_at=when.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    with open(done_p, "w", encoding="utf-8") as f:
        json.dump({"video_id": vid, "publish_at_kst": args.publish_at}, f, ensure_ascii=False)

    srt = os.path.join(args.out_dir, "captions.srt")
    if os.path.exists(srt):
        try:
            yu.upload_captions(vid, srt)
        except Exception as e:
            print(f"  [경고] 자막 업로드 실패(영상은 정상): {str(e)[:200]}\n"
                  "  → 이 컴퓨터 토큰에 youtube.force-ssl 권한이 없으면 scripts/_reauth_youtube.py로 재인증 후 upload_captions만 다시 실행")
    print(f"완료: https://youtu.be/{vid}")


if __name__ == "__main__":
    main()
