# daily.factlab 쇼츠 자동화 프로젝트

부동산 경매·정부 세금 정책 주제로 유튜브(@daily.factlab, 채널ID UCtbDzu67QWkpZ-apBla_ynw)·틱톡·인스타그램에 쇼츠를 올리는 1인 크리에이터의 자동화 파이프라인. 목표는 구독자/팔로워 100만 (장기, 천천히 점진적으로 최적화 — 서두르지 말 것, 중간중간 성과 분석 병행).

**중요**: 2026-08-22부로 OneDrive 동기화를 완전히 중단했습니다 (OneDrive 저장용량 부족으로 `media_host/`의 `.git` 객체가 손상되고, 데스크톱에서 변경한 코드가 노트북에 조용히 동기화 안 되는 사고가 있었음). 이제 이 폴더는 **각 컴퓨터의 로컬 디스크**(`C:\shorts_auto`)에 독립적으로 존재합니다. 두 컴퓨터 간 동기화는 (git/클라우드 자동화 대신) **USB로 수동 복사**하는 방식으로 결정함 (2026-08-22) — 코드/스크립트를 수정한 쪽에서 그날그날 USB로 반대쪽 컴퓨터에 옮겨줘야 함. 그러니 **새 세션에서 코드를 수정하기 전엔 "이 컴퓨터가 최신 버전이 맞는지" 사용자에게 먼저 확인할 것** — 자동 동기화가 없어서 두 컴퓨터 버전이 갈릴 위험이 상시 있음.

Claude Code의 대화 세션·auto-memory는 각 컴퓨터의 로컬 사용자 프로필(`~/.claude/`)에 저장되고 컴퓨터 간 동기화되지 않으므로, 새 컴퓨터/새 세션에서는 이 파일(USB로 옮겨진 최신 사본)이 유일한 맥락 소스입니다. 작업하면서 알게 된 중요한 결정/제약은 이 파일에 계속 업데이트하고, **수정할 때마다 USB로 반대쪽 컴퓨터에도 옮겨달라고 사용자에게 안내할 것**.

## 폴더 구조 (2026-08-22 재정리, 위치: `C:\shorts_auto`)
- `scripts/` — 파이프라인 코드(.py)만. 문서/템플릿은 `docs/`로 분리함
- `docs/` — 프로세스 문서 (`script_template.md`, `script_package_template.md`, `platform_checklist.md`, `daily_topic_scan_process.md`, `weekly_review_process.md`, `blog_template.md`)
- `input/queue/NN_이름/` — 대기열 아이템 (script.txt, images/, meta.json)
- `input/backlog/` — 아직 큐에 안 들어간 예전 초안 스크립트/주제 메모 (예전엔 `input/` 루트에 흩어져 있던 것 정리함)
- `input/bgm/`, `input/broll/`, `input/broll_images/`, `input/voice/` — 소스 미디어
- `credentials/` — OAuth 토큰/시크릿 (client_secret.json, token.json, instagram_secret.json, instagram_token.json, github_token.txt) — **로컬 전용**
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
7. (신규, 2026-08-22, 수동 도구) `discover_topics.py`, `new_queue_item.py`, `naver_blog_autofill.py`, `publish_naver_blog.py` — 네이버 블로그에도 콘텐츠를 올리는 반자동 도구 모음. `run_queue.py`가 자동으로 호출하지 않음(별도 실행). `naver_blog_autofill.py`는 `playwright` 패키지 필요(미설치 상태) + 최초 1회 `login` 커맨드로 사람이 직접 로그인해서 세션 저장하는 방식(API 키 없음). 노트북엔 아직 설치/로그인 안 함 — 사용자가 실제로 쓰겠다고 하면 그때 세팅.

### `run_queue.py`의 git 기반 상호배제 락 (2026-08-22, 데스크톱발 설계 — 현재 노트북에선 비활성)
데스크톱 쪽 `run_queue.py`는 `shorts_auto` 자체가 git 저장소로 두 컴퓨터에 동기화된다는 전제로, 처리 시작 전 `input/queue/NN_이름/processing.lock`을 커밋+push해서 "내가 먼저 선점했다"를 표시하고, push가 거부되면(다른 컴퓨터가 먼저 올림) 양보하는 방식으로 동시 처리를 막는다 (git push의 원자성 이용, 락 3시간 지나면 이전 실행이 죽은 것으로 보고 무시). **그런데 사용자가 최종적으로 컴퓨터 간 동기화는 git이 아니라 USB 수동 복사로 결정**했기 때문에, `C:\shorts_auto`가 git 저장소가 아니라서 이 락은 `git pull`/`git push`가 매번 "not a git repository"로 실패 → 코드 설계상 예외를 던지지 않고 그냥 로컬 락으로 진행하도록 우아하게 열화(degrade)됨 — 즉 지금은 있으나 마나 한 상태. 대신 노트북=평일/데스크톱=주말로 스케줄러를 나눠서 동시 실행을 막고 있음(아래). **불일치 상태이니 인지하고 있을 것** — 나중에 이 락을 살리려면 `shorts_auto`를 실제 git 저장소로 만들어야 하는데, 이는 사용자가 명시적으로 거부한 방향이라 함부로 되돌리지 말 것.

## 중요 결정/제약
- **틱톡은 API 완전자동 불가** — Content Posting API가 Audit 통과 전엔 비공개로만 업로드됨. 계속 반자동 유지.
- **클라우드 완전 무인화는 보류** — 인증 토큰을 깃허브 등에 올리는 보안 위험 때문에 거부, 로컬 예약작업(Task Scheduler)만 사용.
- **유튜브 토큰은 테스트 앱이라 7일마다 재인증 필요**. 인스타그램 토큰은 60일.
- **인스타그램 파일명은 반드시 ASCII(영문/숫자)만 사용** — 2026-08-17에 한글 파일명 때문에 Meta 서버가 영상 URL을 못 읽어 게시 실패한 적 있음 (`run_queue.py`에서 이미 수정됨, `re.sub(r'[^A-Za-z0-9_-]', '', name)`).
- **인스타그램 게시가 8/17부터 매일 실패 중, 원인 두 가지 발견(2026-08-22)**:
  1. (노트북 한정, 해결됨) OneDrive 저장용량 부족으로 `media_host/.git` 내부 blob 객체 6개가 소실 + git 사용자 정보(`user.name`/`user.email`) 미설정 → 깃허브 push 자체가 실패 → 영상 URL이 실제로 존재하지 않는데 인스타그램 API를 호출해서 400. `media_host`를 fresh clone으로 교체하고 git identity 설정해서 해결.
  2. (원인 특정 안 됨, 재현도 안 됨) 영상 URL이 실제로 공개 접근 가능한 상태에서(직접 200 OK 확인함) `instagram_upload.py`의 미디어 컨테이너 생성 API(`POST /{user_id}/media`)가 400 Bad Request 났던 이력이 6일 연속 있었음. 실패 시 진짜 에러 본문(`response.text`)을 로그에 남기도록 `instagram_upload.py`를 고쳐놓고(라인 127 근처, `create_resp.status_code != 200`이면 출력), 이모지/해시태그 캡션·CDN 전파 지연 등 여러 가설로 재현을 시도했지만 **전부 성공**해버려서(테스트 중 실수로 실제 릴스 1건이 게시됨, 사용자가 직접 삭제 처리) 못 잡음 — 계정 차원의 일시적 제한이었을 가능성. **이 로그 fix는 데스크톱 동기화(2026-08-22 USB 이관) 때 desktop 버전으로 덮어써졌다가 다시 적용함 — USB로 코드 주고받을 때 이 fix가 유실되지 않았는지 확인할 것.** 다음에 실제로 또 실패하면 `queue_log.txt`에 Meta의 진짜 에러 메시지가 남을 것.
- **두 컴퓨터 동시 스케줄러 실행 주의** — 그날 실제로 쓰는 컴퓨터에서만 "ShortsAutoQueue" 작업을 활성화하고 나머지는 꺼둘 것 (중복 처리 방지).
- **요일별 실행 컴퓨터 분리 (2026-08-22 확정)**: 평일(월~금)은 노트북, 주말(토~일)은 데스크톱에서만 "ShortsAutoQueue" 실행. 각 컴퓨터의 Task Scheduler 트리거를 `DaysOfWeek`로 분리해서 등록(둘 다 08:00, 겹치지 않음) — 매번 수동 on/off 안 해도 되게 함. 노트북 트리거 등록 완료(Mon-Fri, action 경로 `C:\shorts_auto\scripts\run_queue.py`). 데스크톱은 기존 daily 트리거를 Sat-Sun으로 교체 + action 경로를 `C:\shorts_auto`로 갱신 필요.
- **OneDrive 사용 중단 (2026-08-22)** — 저장용량 부족으로 `media_host/.git` 객체 손상 + 데스크톱↔노트북 코드 동기화 조용히 실패하는 사고가 있었음. 이제 `shorts_auto`는 `C:\shorts_auto`(순수 로컬, OneDrive 아님)에 있고, 컴퓨터 간 동기화는 **USB 수동 복사**로 함 (git/클라우드 자동화 안 씀 — 아래 참고). OneDrive의 구버전 사본은 삭제 완료(2026-08-22), 더 이상 존재하지 않음.
- **⚠️ `input/queue/`도 매번 USB로 같이 옮겨야 함 — 안 그러면 중복 게시 위험 (2026-08-22 파악)**: 대기열이 컴퓨터별로 로컬 독립이라, 한쪽에서 처리한 항목의 `done.txt`가 반대쪽엔 안 보임. 예: 주말에 데스크톱이 `09_선순위임차인`을 처리해도 그 사실이 노트북엔 반영 안 되므로, 월요일에 노트북이 켜지면 **같은 항목을 또 처리해서 유튜브/인스타에 중복 업로드**할 수 있음. `run_queue.py`의 git 기반 락(위 참고)은 이 문제를 막으려고 설계된 건데 git을 안 쓰기로 해서 무력화된 상태 — 그 빈자리를 사람이 메워야 함. **컴퓨터를 바꿔 쓰기 전엔 반드시 `input/queue/`를 USB로 최신 상태로 맞출 것** (`scripts/`, `docs/`, `CLAUDE.md`와 함께).
- 실제 공개(public/private) 여부는 meta.json의 privacy 필드로 제어, 신규 아이템은 기본 안전하게 확인 후 진행.

## 동기화 이관 진행 상황 (2026-08-22)
- [x] `shorts_auto`, `업로드영상`을 OneDrive에서 `C:\shorts_auto`로 복사 완료 + 무결성 확인(파일 수 일치)
- [x] `input/`, `scripts/` 폴더 정리 (위 폴더 구조 참고)
- [x] Task Scheduler "ShortsAutoQueue"(노트북) action 경로를 `C:\shorts_auto`로 갱신
- [x] ~~GitHub 비공개 저장소로 동기화~~ → **USB 수동 복사로 최종 결정**. git+GitHub 안 씀 (단, `run_queue.py`의 락 기능이 git 저장소를 가정하고 설계되어 있음 — 위 "git 기반 상호배제 락" 참고, 알고 있는 불일치이니 재작업하지 말 것).
- [x] **데스크톱→노트북 USB 동기화 1차 완료**: USB(`D:\shorts_auto`)가 NTFS 권한 문제로 처음엔 안 읽혔음(desktop 계정 소유로 복사되어 노트북 계정이 배제됨) → 사용자가 관리자 PowerShell에서 `takeown`+`icacls` 실행해서 해결. 이후 `scripts/`, `docs/`, `input/queue/09,10`을 전량 동기화함. 데스크톱에서 오늘(2026-08-22) 만든 변경사항: 오프닝 훅 TTS화, 엔딩 CTA 개편, RENDER_ROOT 분리, git 기반 락, 네이버 블로그 도구 4종, 자막 wrap 수정, 통계 숫자 폰트 오버플로 수정 — 전부 반영됨.
- [x] `media_host/`, `업로드영상/`을 새 구조(`~\ShortsAutoRender\`)로 이동
- [ ] 데스크톱도 `C:\shorts_auto`(OneDrive 밖) + `~\ShortsAutoRender\` 구조로 정리되어 있는지 재확인 필요 (desktop 코드는 이미 이 구조를 가정하고 있었음 — desktop 쪽 실제 폴더도 이 경로인지는 노트북에서 확인 불가, 다음 데스크톱 세션에서 점검)
- [ ] `naver_blog_autofill.py` 쓰려면 노트북에 `pip install playwright` + `playwright install` + 최초 로그인 필요 (아직 안 함, 사용자가 원할 때 진행)

### USB 동기화 워크플로우 — 더블클릭 스크립트로 자동화 (2026-08-22)
매번 폴더 여러 개를 손으로 복사하는 게 번거롭다는 사용자 피드백으로, USB 루트에 배치 스크립트 두 개를 만들어둠 (원본은 `scripts/sync_to_usb.bat`, `scripts/sync_from_usb.bat`에도 있음, USB 쪽이 마스터):
- **`sync_to_usb.bat`** (지금 쓰던 컴퓨터에서 실행): `C:\shorts_auto`의 `scripts/`, `docs/`, `input/queue/`, `CLAUDE.md`를 USB로 복사 (robocopy `/MIR`, `done.txt` 포함)
- **`sync_from_usb.bat`** (USB를 옮겨간 반대쪽 컴퓨터에서 실행): USB의 내용을 그 컴퓨터의 `C:\shorts_auto`에 덮어씀
- 배치파일은 한글 텍스트를 쓰면 cmd.exe가 UTF-8/코드페이지 문제로 깨지는 걸 실제로 겪어서(chcp 65001로도 해결 안 됨) **영어 메시지로만 작성함** — 앞으로 이 파일들 수정할 때도 한글 절대 넣지 말 것.
- 사용법: 컴퓨터 바꾸기 전에 USB 꽂고 `sync_to_usb.bat` 더블클릭 → 반대쪽 컴퓨터에서 같은 USB로 `sync_from_usb.bat` 더블클릭. 끝.
- **`input/queue/`를 빼먹으면 중복 게시 위험** — 위 "중요 결정/제약"의 ⚠️ 항목 참고 (이 스크립트들은 이미 포함하고 있어서 신경 안 써도 됨)
- `credentials/`, `output/`, `input/`의 미디어 파일(bgm/broll/voice), `~\ShortsAutoRender\`(렌더링 결과물+media_host)는 컴퓨터별로 로컬에만 두고 USB로 안 옮김 (민감하거나 용량 큼, 굳이 동기화 불필요)
- **USB 폴더가 다른 컴퓨터 계정 소유로 복사되면 NTFS 권한 때문에 못 읽을 수 있음** (2026-08-22 실제로 겪음) — 그럴 땐 관리자 권한 PowerShell에서 `takeown /F "D:\경로" /R /D Y` 후 `icacls "D:\경로" /grant "사용자명:(OI)(CI)F" /T` 실행
- 새 세션 시작 시 CLAUDE.md 맨 위 "최근 변경 이력"을 보고 이 컴퓨터가 최신인지 사용자에게 확인할 것

## 콘텐츠 인사이트 (실제 채널 데이터 기반)
- 잘 되는 영상: 궁금증 유발("~이유/순간/기준"), 반전/역설, 실시간 정책뉴스 반응, 구체적 숫자
- 안 되는 영상: 특정 단지 초협소 주제, 궁금증 없는 통계 나열, 뻔한 자기계발 조언
- 대본/카드 작성 시 `scripts/script_template.md`(훅 패턴), `scripts/script_package_template.md`(실전 포맷) 항상 참고

## 작업 스타일 (사용자 선호)
- 보안 위험 있으면 편의보다 안전, 대신 구체적 대안 여러 개 제시하고 사용자가 고르게 할 것
- 반복 작업은 처음 1~2개만 확인받고 이후 기본값으로 진행
- 설명보다 실제 샘플(영상/이미지) 만들어서 보여주는 걸 선호
- 반자동 워크플로우는 파일명 등에 필요 정보 직접 내장해서 마찰 최소화
- 막히면 얕은 우회 대신 근본 원인까지 검증 (예: API 에러 메시지가 실제 원인을 잘못 표시하는 경우 있음 — 값을 소스와 직접 대조)
- 최적화는 천천히, 주기적 성과 분석 병행 (`scripts/weekly_review_process.md`)

## 최근 변경 이력
- 2026-08-15: 파이프라인 최초 구축, 유튜브 완전자동, 인스타그램 완전자동, 대기열 방식 확정
- 2026-08-17: 그래픽/오프닝훅/엔딩CTA/로고 오버레이 전면 개선(어지러운 줌 전환 → 크로스페이드, 무음 훅 → 임팩트 사운드, 팔로우/댓글 유도 CTA 추가), 인스타그램 한글 파일명 버그 수정
- 2026-08-21: 데스크톱-노트북 OneDrive 동기화 체계 구축 (`shorts_auto`, `업로드영상` 폴더를 `Desktop\클로드코드1`에서 `OneDrive\` 로 이동), 작업 스케줄러 경로 갱신
- 2026-08-22: 노트북 최초 세팅(Python/ffmpeg/패키지 설치), 요일별 컴퓨터 분리(평일 노트북/주말 데스크톱) 확정 및 노트북 스케줄러 등록, 노트북에서 유튜브 업로드 실사용 테스트 성공(08_명도소송, public). 인스타그램 6일 연속 실패 원인 조사 — OneDrive 용량 부족이 근본 원인으로 드러나 **OneDrive 동기화 전면 중단**, `C:\shorts_auto`로 이전 + 컴퓨터 간 동기화는 **USB 수동 복사**로 전환 확정. USB로 데스크톱의 대규모 변경사항(오프닝 훅 TTS화, CTA 개편, RENDER_ROOT 분리로 렌더링 결과물/media_host를 `~\ShortsAutoRender\`로 이전, git 기반 상호배제 락 설계, 네이버 블로그 도구 4종 추가, 자막/폰트 버그 수정 2건)을 노트북에 반영 완료. 폴더 구조 정리(`docs/`, `input/backlog/` 신설).
