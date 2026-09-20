# v2 영상 포맷 — 대본/메타 작성 규칙 (2026-09-20 도입)

`meta.json`에 `"format": "v2"`와 `"scenes"`가 있으면 `run_queue.py`가 v2 빌더(`scripts/make_video_v2.py`)로 렌더한다.
없으면 기존 방식(script.txt + images/)으로 렌더한다 — 롤백은 대기열 항목에서 `format`을 빼면 끝.
대기열 폴더에는 `meta.json` 하나만 있으면 된다(script.txt, images/ 불필요). 이미지는 렌더 시점에 Cloudflare로 생성한다.

## 대본 규칙
- 해요체, **30~40초(공백 포함 약 290~340자)**, 한 장면 = 한 문장(짧게).
- **첫 장면(훅) 15자 이내**, 손실·기한·금액 중 하나를 건다. 예: "판 집인데 재산세 200만 원?"
- **결론을 먼저** 말한다(2번째 장면). 뒤에서 근거·사례.
- 중간(60~70% 지점)에 **반전 질문** 하나: "근데 딱 6월 1일에 넘기면 누가 낼까요?" → 다음 장면에서 답.
- 금액 예시는 반드시 **가정**임을 표시: money 장면의 `"note": "(예시 금액)"`.
- 엔딩 = 공유 유도("~께 꼭 보내주세요") + 댓글 질문("여러분은 ~?").
- `source_label`에 근거 법령·기관 명시. 출처 확인 안 된 실무 관행·통계는 쓰지 않는다.
- 숫자·날짜는 자막/카드로 우리가 직접 그린다(이미지에 글자를 기대하지 않는다).

## meta.json 스키마
```
{ "format": "v2", "rate": "+15%", "source_label": "출처: ...",
  "youtube_title", "youtube_description", "tags", "privacy", "tiktok_caption", "instagram_caption" (기존과 동일),
  "scenes": [ ... ] }
```
공통 필드: `voice`(읽을 문장, **공백으로 나눈 단어 수가 곧 타이밍 기준**이라 문장 그대로), `caption`(화면 자막).
자막 마크업: `{금색 강조}`, `[빨강 강조]`, `\n` 줄바꿈. 장면 선택 필드: `"sfx":"ding"`(정답 공개 등 1~2회만).

| kind | 필수 필드 | 용도 |
|---|---|---|
| photo | `image_prompt` | 분위기 이미지 배경 + 자막 |
| big | `big`, 선택 `badge` | 큰 글자(기간·숫자) + 빨간 배지 |
| money | `amount`(숫자), `unit`, `note` | 금액 카운트업 |
| timeline | `cards:[{date, who, color: green/gold/red/white}]`, `active`(인덱스 배열 또는 "all") | 날짜 비교 카드 |

## image_prompt 규칙
- **영어**, `photorealistic ...`로 시작, 피사체 1개 + 조명 + `shallow depth of field`.
- **사람 얼굴·손·간판·문서 클로즈업·지폐·달력·라벨 금지**(가짜 글자/기형 발생). 건물·사물·야경·책상 위 소품 위주.
- 끝에 `, no text`. 프롬프트는 장면마다 달라야 함(같은 그림 반복 금지). photo 장면은 전체의 절반 이하.
- Cloudflare 실패 시 그라데이션 배경으로 자동 대체되므로 영상 자체는 나온다(품질만 하락 → v2_report.json 확인).

## 렌더 결과
`platform/youtube.mp4`, `tiktok.mp4`(복사본), `thumb.png`(첫 장면 최종 프레임 → 유튜브 썸네일), `v2_report.json`.
유튜브 업로드 시 `--synthetic`으로 "AI 생성 콘텐츠" 표시를 요청한다(반영 여부는 업로드 로그의 "AI 콘텐츠 표시" 줄로 확인, 미확인이면 스튜디오에서 수동 설정).
