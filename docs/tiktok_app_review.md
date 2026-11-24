# 틱톡 임시 저장함 자동 전송: 정식 심사 준비 (주말에 진행)

작성 2026-11-24 (노트북). 데스크톱에서 이어서 하면 된다.

## 지금 상태
| 항목 | 상태 |
|---|---|
| 코드 | `scripts/tiktok_upload.py` + `run_queue.py`의 `send_tiktok_inbox()` (main에 반영됨) |
| 키·토큰 | `%OneDrive%\shorts_auto_secrets\` (tiktok_app.json, tiktok_token.json). OneDrive라 두 컴퓨터 공용, 1년 유효 |
| 안내 사이트 | https://dbswpvlf6190-alt.github.io/shorts-auto-/ (gh-pages 브랜치, URL prefix 인증 완료) |
| 틱톡 앱 | "도장찍기전에 업로더" (개인 소유), Sandbox "daily-upload", target user daily.factlab |
| 시험 결과 | 공개 계정: API는 SEND_TO_USER_INBOX인데 알림 안 옴. 비공개 계정: 도착 확인 |
| 결론 | Production 앱 심사를 통과해야 공개 계정에 매일 도착 |

심사 전에도 매일 아침 전송은 시도되고(실패해도 파이프라인 무영향), 바탕 화면 `틱톡_*.mp4`는 계속 생긴다.

## 주말 할 일 (순서)
1. **Production 칸 다시 채우기**: 11/24에는 심사 칸(설명·시연 영상)이 비어서 저장이 안 됐다. 아래 값들을 Production에 다시 넣는다.
   - 아이콘: `assets/branding/pro_B_레드앱아이콘.png`를 1024px로 (11/24 만든 파일: 노트북 `OneDrive\바탕 화면\클로드코드1\틱톡앱_아이콘_1024.png`)
   - 이름 `도장찍기전에 업로더` · 분류 `Education`
   - 설명 `Sends my own short videos about Korean real estate and tax to my TikTok inbox as drafts.`
   - 약관 `https://dbswpvlf6190-alt.github.io/shorts-auto-/terms/`
   - 개인정보 `https://dbswpvlf6190-alt.github.io/shorts-auto-/privacy/`
   - 플랫폼 Web, 주소 `https://dbswpvlf6190-alt.github.io/shorts-auto-/`
   - 제품 Login Kit(Redirect URI `https://dbswpvlf6190-alt.github.io/shorts-auto-/tiktok/callback/`) + Content Posting API (**Direct Post 끔**)
   - 권한 user.info.basic, video.upload
2. **시연 영상 녹화** (계정을 잠깐 비공개로 바꾼 상태에서, 끝나면 바로 공개로 되돌리기)
   - **사용자 요청(11/24): 데스크톱 컴퓨터로 진행.** 녹화는 Windows 캡처 도구(Win+Shift+R) 또는 Xbox Game Bar(Win+Alt+R). 마지막 '도착' 장면은 PC 브라우저 tiktok.com 알림에 보이면 그걸로 찍고, 안 보이면 폰 화면 녹화 한 컷만 추가.
   1. 브라우저로 안내 사이트 첫 화면을 보여 준다 (주소창 도메인이 보이게).
   2. 터미널에서 `python scripts/tiktok_upload.py auth` → 틱톡 허용 화면 → 허용 → "연결됐어요" 화면.
   3. `python scripts/tiktok_upload.py upload --video <영상>` → `TIKTOK_OK ... SEND_TO_USER_INBOX` 출력.
   4. 폰 틱톡 받은 편지함 알림 → 편집 화면 열기 (폰 화면 녹화를 이어 붙임).
   - mp4, 50MB 이하.
3. **설명 글 붙여 넣고 Submit for review.**

## 심사 설명 글 (복사용, 1000자 이내)
```
This is a private, single-user tool for my own TikTok account (daily.factlab), which posts short educational videos about Korean real estate, tax and public policy.

Login Kit (user.info.basic): I authorize the app once with my own TikTok account through the web authorization page. The redirect page on my website passes the authorization code to the uploader running on my computer, which exchanges it for an access token. user.info.basic is used only to identify the authorized account (open_id).

Content Posting API (video.upload): Every morning my video pipeline renders one vertical short video. The uploader sends the finished file with FILE_UPLOAD to my TikTok inbox as a draft. I then open the inbox notification in the TikTok app, add the caption, choose the privacy setting and post it myself. The app never posts directly, and Direct Post is not enabled.

No data from other users is collected. Tokens are stored only on my own computer.
```

## 참고
- 공식 문서: Content Posting API Upload, Get Post Status, Login Kit Web
- 시험판 제한 관련: https://github.com/GraphiteTuff/sitguru-app/pull/235
