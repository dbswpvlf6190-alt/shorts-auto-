# daily.factlab 쇼츠 자동화 프로젝트

부동산 경매·정부 세금 정책 주제로 유튜브(@daily.factlab, 채널ID UCtbDzu67QWkpZ-apBla_ynw)·틱톡·인스타그램에 쇼츠를 올리는 1인 크리에이터의 자동화 파이프라인. 목표는 구독자/팔로워 100만 (장기, 천천히 점진적으로 최적화 — 서두르지 말 것, 중간중간 성과 분석 병행).

**중요**: 2026-08-22부로 OneDrive 동기화를 완전히 중단했습니다 (OneDrive 저장용량 부족으로 `media_host/`의 `.git` 객체가 손상되고, 데스크톱에서 변경한 코드가 노트북에 조용히 동기화 안 되는 사고가 있었음). 이 폴더는 **각 컴퓨터의 로컬 디스크**(`C:\shorts_auto`)에 있고, 컴퓨터 간 동기화는 **git + GitHub 비공개 저장소**(`dbswpvlf6190-alt/shorts-auto-` — 이름 끝에 하이픈이 하나 더 있음, 실수로 그렇게 생성됨, 그대로 씀)로 합니다. (중간에 USB 수동 복사도 시도했었지만 번거로워서 최종적으로 git으로 전환함, 2026-08-22.) `scripts/`, `docs/`, `input/queue/`, `CLAUDE.md`가 이 저장소에 들어있고, `credentials/`, `output/`, `temp/`, `input/`의 미디어 파일(bgm/broll/broll_images/voice/backlog)은 `.gitignore`로 제외되어 컴퓨터마다 로컬로만 존재. **작업 시작 전 `git pull`, 작업 끝나면 `git push`를 습관처럼 할 것.**

Claude Code의 대화 세션·auto-memory는 각 컴퓨터의 로컬 사용자 프로필(`~/.claude/`)에 저장되고 컴퓨터 간 동기화되지 않으므로, 새 컴퓨터/새 세션에서는 이 파일(git으로 pull된 최신 사본)이 유일한 맥락 소스입니다. 작업하면서 알게 된 중요한 결정/제약은 이 파일에 계속 업데이트하고 **push까지 할 것**.

## 프로젝트 헌장 — `PROJECT_CHARTER.md` (2026-08-22, 필독)
장기 비전/브랜드 방향/Claude Code 역할 원칙을 담은 문서. 신규 기능 제안 시 이 헌장과의 정합성을 먼저 확인할 것. 이 CLAUDE.md는 현재 구현 상태 요약이고, 전문은 그 파일이 원본.

## 중요 — 오늘(2026-08-22) 저녁, 서로 다른 두 세션이 같은 마이그레이션을 독립적으로 진행했던 일
낮부터 저녁까지 **완전히 다른 Claude Code 세션 두 개**가, 서로의 존재를 모른 채 거의 같은 문제(OneDrive 사고 이후 git으로 전환)를 각자 풀고 있었음:
- 세션 A: `C:\Users\dbswp\Desktop\클로드코드1\shorts_auto` (저장소 `shorts-auto-pipeline`) — 텍스트 오버플로 버그 2건, CTA 개편, discover_topics.py/new_queue_item.py/네이버 블로그 도구 4종을 이쪽에서 먼저 만듦
- 세션 B(=지금 이 폴더): `C:\shorts_auto` (저장소 `shorts-auto-`) — 노트북 세팅 과정에서 별도로 git 전환을 진행, 요일별 컴퓨터 분리(평일 노트북/주말 데스크톱) 확정, 인스타그램 실패 원인 조사를 더 깊이 함

저녁에 사용자가 이 상황을 발견하고 **`C:\shorts_auto`를 최종 채택**하기로 결정함. 세션 A에서 만든 산출물(위 도구들, 텍스트 오버플로 수정, PROJECT_CHARTER.md)은 이 폴더로 옮겨 반영 완료. 세션 A의 `Desktop\클로드코드1\shorts_auto` 폴더/`shorts-auto-pipeline` 저장소는 이제 안 씀(삭제는 안 했음, 필요하면 나중에 사용자가 정리).
**교훈**: 새 세션을 열 때 이 프로젝트 관련이면 항상 `C:\shorts_auto`인지 먼저 확인하고, 다른 경로면 그 세션에서 이 사실을 사용자에게 알릴 것.

## 폴더 구조 (2026-08-22 재정리, 위치: `C:\shorts_auto`)
- `scripts/` — 파이프라인 코드(.py)만. 문서/템플릿은 `docs/`로 분리함
- `docs/` — 프로세스 문서 (`script_template.md`, `script_package_template.md`, `platform_checklist.md`, `daily_topic_scan_process.md`, `weekly_review_process.md`, `blog_template.md`)
- `input/queue/NN_이름/` — 대기열 아이템 (script.txt, images/, meta.json)
- `input/backlog/` — 아직 큐에 안 들어간 예전 초안 스크립트/주제 메모 (예전엔 `input/` 루트에 흩어져 있던 것 정리함)
- `input/bgm/`, `input/broll/`, `input/broll_images/`, `input/voice/` — 소스 미디어
- `credentials/` — OAuth 토큰/시크릿 (client_secret.json, token.json, instagram_secret.json, instagram_token.json, github_token.txt, github_shorts_auto_token.txt) — **로컬 전용, git에 안 올라감**
- `output/` — 큐 실행 로그(`queue_log.txt`), 주제 후보 목록, 채널 스냅샷 (렌더링 결과물은 아래 RENDER_ROOT로 분리됨)

### 렌더링 결과물은 `shorts_auto` 밖, `~\ShortsAutoRender\`에 저장 (2026-08-22, 데스크톱발 변경)
용량 크고 자주 바뀌는 것과 코드/설정을 분리하려고 데스크톱에서 도입한 구조. `run_queue.py`/`publish_instagram.py`의 `RENDER_ROOT`(환경변수 `SHORTS_RENDER_DIR`로 override 가능, 기본값 `~\ShortsAutoRender`)가 기준:
- `~\ShortsAutoRender\queue_render\NN_이름\` — 큐 아이템별 렌더링 작업 파일(base.mp4, platform/ 등). 예전엔 `input/queue/NN_이름/` 안에 있었음.
- `~\ShortsAutoRender\업로드영상\YYYY-MM-DD-요일\` — 최종 배송 폴더 (요일 접미사 추가됨, 예전엔 `YYYY-MM-DD`만). 노트북/데스크톱 둘 다 각자 로컬로 독립.
- `~\ShortsAutoRender\media_host\` — 인스타그램 릴스 호스팅용 git 저장소(GitHub Pages, `dbswpvlf6190-alt/shorts-media-host`, 별도 저장소·별도 토큰). **더 이상 `shorts_auto` 안에 없음** — git 저장소를 코드 폴더 안에 두면 안 된다는 교훈(OneDrive가 `.git` 손상시킨 사고) 반영.

## 파이프라인 (scripts/run_queue.py가 매일 08:00 자동 실행, Windows 작업 스케줄러 "ShortsAutoQueue")
1. `make_short.py` — 대본 → edge-tts 음성(ko-KR-InJoonNeural, 1.3배속 `+30%`) → 브롤 이미지(완만한 줌인+크로스페이드 전환) → 카라오케 자막 → base.mp4
2. `make_graphic.py` — PIL 카드 생성 (그라디언트+글로우+키커+워터마크 디자인). 서브커맨드: title/stat/compare/checklist/cta/logo. 큰 숫자가 카드 폭을 넘으면 폰트 자동 축소(2026-08-22).
3. `make_platform_variants.py` — **오프닝 훅을 이제 TTS로 실제로 읽음**(2026-08-22 개편, 예전엔 무음+임팩트 사운드만). 훅 문구를 음성 합성 후 발화 타이밍에 맞춰 단어별 팝인/줌펀치를 동기화, 임팩트 사운드는 배경으로 믹스. 엔딩 CTA도 "다음편 예고형"으로 개편(뭉뚱그린 "팔로우하세요"보다 다음 소재를 구체적으로 예고하는 게 재방문 동기 부여에 낫다는 근거, `--next-teaser` 인자로 문구 지정) + 우측 상단 `daily.factlab` 로고 고정 오버레이 → youtube.mp4/tiktok.mp4
4. `youtube_upload.py` — YouTube Data API v3 자동 업로드
5. `instagram_upload.py` + `publish_instagram.py` — Instagram Graph API 자동 릴스 게시 (영상은 media_host 통해 GitHub raw URL로 호스팅)
6. `run_queue.py` — 위 전체를 매일 대기열에서 1개씩 처리, 유튜브+인스타그램 자동 게시, 틱톡은 파일명에 캡션 박아서 반자동(사용자가 직접 업로드). **두 컴퓨터 동시 처리 방지용 git 기반 락 내장**(아래 참고).
7. (신규, 2026-08-22, 수동 도구) `discover_topics.py`, `new_queue_item.py`, `naver_blog_autofill.py`, `publish_naver_blog.py` — 네이버 블로그에도 콘텐츠를 올리는 반자동 도구 모음. `run_queue.py`가 자동으로 호출하지 않음(별도 실행). `naver_blog_autofill.py`는 `playwright` 패키지 필요(미설치 상태) + 최초 1회 `login` 커맨드로 사람이 직접 로그인해서 세션 저장하는 방식(API 키 없음). 아직 설치/로그인 안 함 — 사용자가 실제로 쓰겠다고 하면 그때 세팅.

### `run_queue.py`의 git 기반 상호배제 락 (2026-08-22, 데스크톱발 설계 — 지금은 양쪽 다 활성)
`shorts_auto`가 실제 git 저장소가 되면서(위 참고), 이 락 기능이 노트북·데스크톱 둘 다에서 정상 작동함. 처리 시작 전 `input/queue/NN_이름/processing.lock`을 커밋+push해서 "내가 먼저 선점했다"를 표시하고, push가 거부되면(다른 컴퓨터가 먼저 올림) 양보하는 방식으로 동시 처리를 막는다 (git push의 원자성 이용, 락 3시간 지나면 이전 실행이 죽은 것으로 보고 무시). 요일별 스케줄러 분리(아래)와 이중으로 중복 처리를 막아줌.

## 중요 결정/제약
- **틱톡은 API 완전자동 불가** — Content Posting API가 Audit 통과 전엔 비공개로만 업로드됨. 계속 반자동 유지.
- **클라우드 완전 무인화는 보류** — 인증 토큰을 깃허브 등에 올리는 보안 위험 때문에 거부, 로컬 예약작업(Task Scheduler)만 사용.
- **유튜브 토큰은 테스트 앱이라 7일마다 재인증 필요**. 인스타그램 토큰은 60일.
- **인스타그램 파일명은 반드시 ASCII(영문/숫자)만 사용** — 2026-08-17에 한글 파일명 때문에 Meta 서버가 영상 URL을 못 읽어 게시 실패한 적 있음 (`run_queue.py`에서 이미 수정됨, `re.sub(r'[^A-Za-z0-9_-]', '', name)`).
- **인스타그램 게시가 8/17부터 매일 실패했던 적 있음, 원인 두 가지 발견(2026-08-22)**:
  1. (해결됨) OneDrive 저장용량 부족으로 `media_host/.git` 내부 blob 객체 6개가 소실 + git 사용자 정보(`user.name`/`user.email`) 미설정 → 깃허브 push 자체가 실패 → 영상 URL이 실제로 존재하지 않는데 인스타그램 API를 호출해서 400. `media_host`를 fresh clone으로 교체하고 git identity 설정해서 해결.
  2. (원인 특정 안 됨, 재현도 안 됨) 영상 URL이 실제로 공개 접근 가능한 상태에서(직접 200 OK 확인함) `instagram_upload.py`의 미디어 컨테이너 생성 API(`POST /{user_id}/media`)가 400 Bad Request 났던 이력이 6일 연속 있었음. 실패 시 진짜 에러 본문(`response.text`)을 로그에 남기도록 `instagram_upload.py`를 고쳐놓음(라인 127 근처, `create_resp.status_code != 200`이면 출력) — 이 fix가 코드에 계속 남아있는지 가끔 확인할 것 (한 번 다른 버전에 덮어써졌다가 재적용한 적 있음). 이모지/해시태그 캡션·CDN 전파 지연 등 여러 가설로 재현을 시도했지만 **전부 성공**해버려서(테스트 중 실수로 실제 릴스 1건이 게시됨, 사용자가 직접 삭제 처리) 못 잡음 — 계정 차원의 일시적 제한이었을 가능성. 다음에 실제로 또 실패하면 `queue_log.txt`에 Meta의 진짜 에러 메시지가 남을 것.
- **두 컴퓨터 동시 스케줄러 실행 주의** — 그날 실제로 쓰는 컴퓨터에서만 "ShortsAutoQueue" 작업을 활성화하고 나머지는 꺼둘 것 (중복 처리 방지). git 기반 락(위 참고)도 이중 안전장치로 있음.
- **요일별 실행 컴퓨터 분리 (2026-08-22 확정)**: 평일(월~금)은 노트북, 주말(토~일)은 데스크톱에서만 "ShortsAutoQueue" 실행. 각 컴퓨터의 Task Scheduler 트리거를 `DaysOfWeek`로 분리해서 등록(둘 다 08:00, 겹치지 않음) — 매번 수동 on/off 안 해도 되게 함. 노트북(Mon-Fri)·데스크톱(Sat-Sun) 둘 다 등록 완료 및 확인됨, action 경로 둘 다 `C:\shorts_auto\scripts\run_queue.py`.
- **OneDrive 사용 중단 (2026-08-22)** — 저장용량 부족으로 `media_host/.git` 객체 손상 + 데스크톱↔노트북 코드 동기화 조용히 실패하는 사고가 있었음. OneDrive의 구버전 사본은 삭제 완료, 더 이상 존재하지 않음. 이제 `C:\shorts_auto` + git/GitHub로 완전히 대체됨.
- 실제 공개(public/private) 여부는 meta.json의 privacy 필드로 제어, 신규 아이템은 기본 안전하게 확인 후 진행.

## 동기화: git + GitHub (2026-08-22, 완료)
- 저장소: `dbswpvlf6190-alt/shorts-auto-` (private, 이름 끝 하이픈 오타 그대로 사용 중)
- 토큰: fine-grained PAT, `shorts-auto-` repo 한정, Contents: Read/write. `credentials/github_shorts_auto_token.txt`에 저장 (노트북·데스크톱 각자, git에는 안 올라감 — `.gitignore`로 제외)
- **워크플로우**: 작업 시작 전 `cd C:\shorts_auto && git pull` → 코드/큐 수정 → `git add -A && git commit -m "..."` → `git push`
- **`git push`가 이 환경의 Bash 도구 자동승인 정책(classifier)에 막힐 수 있음** (2026-08-22 실제로 겪음, 재시도해도 계속 막힘 — `git commit`/`git remote`/`git branch` 등 다른 명령은 대체로 문제없었음). 이럴 땐 우회 시도하지 말고 **사용자에게 직접 터미널(제가 실행하는 Bash 도구 말고, 사용자가 직접 여는 PowerShell)에서 `git push` 실행해달라고 요청할 것.**
- fine-grained 토큰 만들 때 **"Repository permissions → Contents"를 반드시 "Read and write"로 바꿔야 함** — 기본값(No access/Read-only)으로 두면 push가 403/401로 거부됨 (2026-08-22 실제로 이 실수로 한 번 헤맸음).
- `.gitignore`로 제외되는 것(git에 안 올라감, 컴퓨터마다 로컬로만 존재): `credentials/`, `output/`, `temp/`, `input/backlog/`, `input/bgm/`, `input/broll/`, `input/broll_images/`, `input/voice/`
- `sync_to_usb.bat`/`sync_from_usb.bat`, `D:\sync_*.bat`는 USB 방식 쓰던 시절 잔재 — 이제 git으로 대체되어 **더 이상 안 씀** (지워도 무방하지만 급하지 않아서 안 지움).
- 새 세션 시작 시 CLAUDE.md 맨 위 "최근 변경 이력"을 보고 이 컴퓨터가 최신인지 확인 — 애매하면 그냥 `git pull`부터 할 것 (충돌 안 나면 안전).
- 남은 TODO: `naver_blog_autofill.py` 쓰려면 `pip install playwright` + `playwright install` + 최초 로그인 필요 (아직 안 함, 사용자가 원할 때 진행).

## 콘텐츠 인사이트 (실제 채널 데이터 기반)
- 잘 되는 영상: 궁금증 유발("~이유/순간/기준"), 반전/역설, 실시간 정책뉴스 반응, 구체적 숫자
- 안 되는 영상: 특정 단지 초협소 주제, 궁금증 없는 통계 나열, 뻔한 자기계발 조언
- 대본/카드 작성 시 `docs/script_template.md`(훅 패턴), `docs/script_package_template.md`(실전 포맷) 항상 참고

## 작업 스타일 (사용자 선호)
- 보안 위험 있으면 편의보다 안전, 대신 구체적 대안 여러 개 제시하고 사용자가 고르게 할 것
- 반복 작업은 처음 1~2개만 확인받고 이후 기본값으로 진행
- 설명보다 실제 샘플(영상/이미지) 만들어서 보여주는 걸 선호
- 반자동 워크플로우는 파일명 등에 필요 정보 직접 내장해서 마찰 최소화
- 막히면 얕은 우회 대신 근본 원인까지 검증 (예: API 에러 메시지가 실제 원인을 잘못 표시하는 경우 있음 — 값을 소스와 직접 대조)
- 최적화는 천천히, 주기적 성과 분석 병행 (`docs/weekly_review_process.md`)
- 번거로운 반복 작업(예: 컴퓨터 간 파일 동기화)은 계속 불평 없이 시키지 말고, 더 편한 대안을 먼저 제안할 것 (USB 수동 복사 → 귀찮다는 피드백 받고 git으로 전환한 사례 있음)

## 최근 변경 이력
- 2026-08-15: 파이프라인 최초 구축, 유튜브 완전자동, 인스타그램 완전자동, 대기열 방식 확정
- 2026-08-17: 그래픽/오프닝훅/엔딩CTA/로고 오버레이 전면 개선(어지러운 줌 전환 → 크로스페이드, 무음 훅 → 임팩트 사운드, 팔로우/댓글 유도 CTA 추가), 인스타그램 한글 파일명 버그 수정
- 2026-08-21: 데스크톱-노트북 OneDrive 동기화 체계 구축 (`shorts_auto`, `업로드영상` 폴더를 `Desktop\클로드코드1`에서 `OneDrive\` 로 이동), 작업 스케줄러 경로 갱신
- 2026-08-22: 노트북 최초 세팅(Python/ffmpeg/패키지 설치), 요일별 컴퓨터 분리(평일 노트북/주말 데스크톱) 확정 및 양쪽 스케줄러 등록, 노트북에서 유튜브 업로드 실사용 테스트 성공(08_명도소송, public). 인스타그램 6일 연속 실패 원인 조사 — OneDrive 용량 부족이 근본 원인으로 드러나 **OneDrive 동기화 전면 중단** → `C:\shorts_auto`로 이전, 렌더링 결과물/media_host를 `~\ShortsAutoRender\`로 분리. 컴퓨터 간 동기화는 USB 수동 복사를 거쳐 최종적으로 **git + GitHub 비공개 저장소**로 전환 (노트북·데스크톱 둘 다 clone/설정 완료, `run_queue.py`의 git 기반 상호배제 락도 이제 실제로 작동). 데스크톱의 대규모 변경사항(오프닝 훅 TTS화, CTA 개편, 네이버 블로그 도구 4종, 자막/폰트 버그 수정 2건)도 반영 완료. 폴더 구조 정리(`docs/`, `input/backlog/` 신설).
