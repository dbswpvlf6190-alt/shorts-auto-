# Korean YouTube search optimization and title/thumbnail packaging for tax and personal-finance videos (2025–2026)

Research date: 2026-11-28. Method: web search and fetch, plus three first-hand datasets collected on 2026-11-28:
- **(A) YouTube Data API v3.** `search.list` was run with regionCode=KR, relevanceLanguage=ko and publishedAfter=2024-01-01, then joined with `videos.list` and `channels.list` for views, length and subscriber counts. Two passes:
  - A1 used order=relevance with all lengths.
  - A2 used order=viewCount with videoDuration=medium (4–20 min).
  - The account's existing read-only token was loaded in memory only; the token file was not rewritten.
  - API search is not personalized, but it is not identical to what a logged-in user sees in the app.
- **(B) YouTube autocomplete** (`suggestqueries.google.com/complete/search?client=firefox&ds=yt&hl=ko&gl=kr`). This is the same suggestion source as the YouTube search box.
- **(C) Google Trends KR, "today 5-y", weekly points**, from the unofficial explore/widget endpoint. It was run for both Web search and YouTube search (gprop=youtube). Monthly indices are averages for each calendar month divided by that keyword's own 12-month mean, so 1.0 means an average month.

Scripts are in the session scratchpad (`yt_top.py`, `ac.py`, `tr.py`, `tr2.py`). Every video cited below links to `https://www.youtube.com/watch?v=<id>`.

---

## Q1. What official YouTube guidance (2024–2026) says affects search ranking: title, description, captions/transcripts, tags, chapters, engagement

### Takeaway
YouTube officially names three search factors: relevance, engagement and quality.
- **Relevance:** title, tags, description and the video content are matched to the query.
- **Engagement:** watch time for that specific query.
- **Quality:** expertise, authoritativeness and trustworthiness (E-A-T).

YouTube says tags play only a minimal role. Title, thumbnail and description matter more. Chapters mainly add value through Google "Key Moments" and in-video navigation. No official source says captions are a direct ranking factor.

### Cited Findings
- YouTube's "How YouTube search works" page names three ranking elements and says their importance "may vary by search type":
  - Relevance looks at "how well the title, tags, description, and video content match your search query."
  - Engagement uses "the watch time of a particular video for a particular query."
  - Quality looks for channels that show "expertise, authoritativeness, and trustworthiness on a given topic."
  - Search and watch history may also personalize results.
  — [YouTube Help: How YouTube search works](https://support.google.com/youtube/answer/16090438?hl=en)
- The same page does not mention view counts, captions, chapters or freshness as ranking factors. — [YouTube Help](https://support.google.com/youtube/answer/16090438?hl=en)
- YouTube's performance FAQ says Search ranks by "how well the title, description and video content match the viewer's search" and "what videos drive the most engagement for a search." It also says: "Search results are not a list of the most-viewed videos for a given search." — [YouTube Help: Performance FAQ](https://support.google.com/youtube/answer/141805?hl=en-GB)
- The same FAQ advises:
  - Titles and thumbnails should accurately reflect the content.
  - Avoid misleading or shocking packaging, ALL CAPS and excessive punctuation.
  - "Changing your video title and thumbnail can be an effective way to get more views, but don't change what's working."
  - It also lists "video topic is declining in popularity" as a common cause of traffic drops.
  — [YouTube Help: Performance FAQ](https://support.google.com/youtube/answer/141805?hl=en-GB)
- Users can pause or clear search and watch history, and those signals are then excluded from their results. — [How YouTube Works: Search](https://www.youtube.com/howyoutubeworks/product-features/search)
- **Tags:** "Tags can be useful if the content of your video is commonly misspelled. Otherwise, tags play a minimal role in your video's discovery." The same page says the title, thumbnail and description are the more important metadata. — [YouTube Help: Add tags](https://support.google.com/youtube/answer/146402)
- vidIQ's own test found that tags did not affect search results, while a keyword in the title made a test video searchable within minutes. This is old (2019/2020) and vendor-run. — [vidIQ tag case study](https://vidiq.com/vi/blog/post/youtube-keyword-tags-2019-case-study)
- **Descriptions:** "Writing descriptions with keywords can help viewers find your videos more easily through search. Search terms are matched with the video and the text in the description."
  - The limit is 5,000 characters, and each video should have a unique description.
  - Creators should check how the description appears in search and on mobile.
  - Advice to put the most important keywords near the beginning circulates in guides citing YouTube. Third-party guides say the first ~100–200 characters are what show above "Show more."
  — [YouTube Help: Tips for video descriptions](https://support.google.com/youtube/answer/12948449?hl=en); [Search Engine Land description guide](https://searchengineland.com/guide/youtube-video-descriptions)
- **Chapters:** A video needs at least 3 timestamps in ascending order, starting at 0:00, and each chapter must be at least 10 seconds. Automatic chapters can be switched off. — [YouTube Help: Video chapters](https://support.google.com/youtube/answer/9884579?hl=en)
- **Google Search Key Moments:** Google Search shows links to points in a video using timestamps from the description, and Google can also detect key moments automatically. The 2021 rollout note says this is "in English" for timestamped YouTube videos; I found no confirmation of current Korean coverage. — [Google blog: Key moments](https://www.blog.google/products/search/key-moments-video-search/); [Google Search Central 2021](https://developers.google.com/search/blog/2021/07/new-way-key-moments?authuser=0)
- **Captions:** No official YouTube page found states that captions are a ranking factor.
  - Semrush quotes YouTube's Todd Beaupré (Creator Insider) saying there's "no single answer" to what ranks a video. It lists spoken content and captions among relevance signals, but that list is Semrush's interpretation. — [Semrush YouTube SEO](https://www.semrush.com/blog/youtube-seo/)
  - One vendor says uploaded closed captions are indexed but burned-in text is not. — [3Play Media](https://www.3playmedia.com/blog/9-quick-tips-for-youtube-seo-strategy/)
  - A DreamHost summary of an Adilo study says 94% of top-ranking videos had transcripts. That is correlation only. — [DreamHost](https://www.dreamhost.com/blog/youtube-seo-strategy/)
  - A Nov 2025 piece cautions that transcripts are not guaranteed ranking boosters. — [Contently 2025](https://contently.com/2025/11/25/do-youtube-transcripts-influence-ai-search-summaries/)
- Korean SEO guides make similar recommendations, but these are not official:
  - Put the main keyword in the title, using a structure like "[키워드] + [구체적 결과] + [대상/조건]".
  - A year or "TOP 10" stands out.
  - Keyword stuffing alone fails; YouTube also judges whether the video actually covers the topic and whether viewers stay.
  - The search snippet did not show which guide made which point. — [Carat 유튜브 SEO 가이드](https://carat.im/blog/youtube-seo-optimization-guide); [i-boss 클릭을 부르는 제목](https://www.i-boss.co.kr/ab-6141-56699); [Openads](https://www.openads.co.kr/content/contentDetail?contsId=16588)

### Inferences
- For our channel, the two most useful levers YouTube itself names are:
  - Put the exact query phrase in the title and in the first line of the description.
  - Earn watch time *for that query*, meaning the opening must answer the search intent quickly.
- Adding more tags (we already have 18–20) is unlikely to change anything.
- The "quality/E-A-T" factor matters for tax topics. Several top results carry credentials in the title (국세청 출신 세무사, 세무사 names; see Q3). An AI-narrated channel without credentials should borrow authority in other ways:
  - Cite 국세청/법령 on screen.
  - Put source links in the description.
  - Use a "팩트체크" framing, which fits the "팩트는 먼저" brand.
- Uploaded captions (we already upload `captions.srt` for long-form) are good practice for accessibility and matching. Their direct ranking effect is unproven, so don't expect a jump from them.
- Chapters with keyword-phrased titles (for example "증여세 면제한도 표", "10년 합산 계산 예시") cost nothing. They may also help Google Search key moments, though Korean support is unconfirmed.

### Gaps
- No official 2024–2026 statement found on how much captions or transcripts count in ranking.
- No official numeric weights for any factor.
- Whether Google Key Moments currently supports Korean videos is unconfirmed.

---

## Q2. Do curiosity titles and keyword titles perform differently for small channels? Evidence

### Takeaway
No controlled study isolates small channels or search traffic. The best available evidence:
- **Vendor guidance (vidIQ):** use curiosity titles for Browse/Suggested and keyword titles for Search.
- **Large observational studies:** question-ending and generic curiosity titles do *not* reliably outperform. Concrete, specific promises do.
- **Our own API sample:** small Korean tax channels (1–12K subs) rank at the top of exact-intent searches such as "증여세 면제한도" when the title contains the exact phrase and the year. The large-view long-form hits pair a keyword with a quoted dramatic statement and a concrete amount.

### Cited Findings
- **vidIQ "Title Flip" framework:**
  - Launch with an honest curiosity title for Browse/Suggested, wait at least 48 hours, then switch to a keyword title around 48–72 hours, once impressions plateau or CTR falls below the channel average, to collect long-term Search traffic.
  - Keep the title if traffic holds.
  - Low impressions mean the title may need stronger keywords. High impressions with low CTR mean it needs more clarity.
  - It cites ~70% of views coming from Browse/Suggested (Quartz), with no small-channel breakdown.
  — [vidIQ Title Flip](https://vidiq.com/blog/post/YouTube-Title-Flip-SEO-Framework/)
- **vidIQ 4M+ title study (2026):**
  - Specific story frames beat generic formulas:
    - "Do not/stop/never": ~2×
    - "Nobody knows": >2.5×
    - "Specific superlative": >1.5×
    - "X days/years": ~1.5×
  - Question-ending titles averaged 0.82×, and "why/how" phrasing was worse than direct titles. A plain how-to was ~1.07×.
  - It is observational, not broken out by channel size or traffic source, and the page shows two different dates.
  — [vidIQ Research: title formulas](https://vidiq.com/research/youtube-title-formulas-study/)
- An independent analysis of 3,357 mature videos found curiosity-gap titles had a median of 0.92× baseline versus 1.00× for controls. — [OverseerOS](https://www.overseeros.com/blog/curiosity-gap-youtube-titles)
- The vidIQ algorithm guide says small channels can outrank big ones in search if they satisfy the query better. A separate vidIQ small-channel video argues for designing videos for Browse rather than relying on search. — [vidIQ algorithm guide](https://www.vidiq.com/blog/post/youtube-algorithm); [vidIQ small channel guide](https://rosetta.to/u/vidiq/the-ultimate-small-channel-guide-to-more-views-on-youtube)
- **Our API sample A1 (relevance order, query "증여세 면제한도"):** small channels win positions 1, 5 and 12–13 with exact-phrase titles.
  - #1: 「2026년 증여세 면제 한도, 자녀에게 얼마까지 줘도 될까요? …」 — 11.1K subs, 30.8K views, 5:34. [Zn6C1t14yHc](https://www.youtube.com/watch?v=Zn6C1t14yHc)
  - #5: 「2025년 증여세 면제 한도? I 효과적인 자녀증여방법 feat 증여재산공제…」 — **1,320 subs, 82K views**, 9:53. [FNZ-GsmmA8Y](https://www.youtube.com/watch?v=FNZ-GsmmA8Y)
  - #12: 「2025년 증여세 면제 한도 증여 공제 한도, 계산하는 방법은?」 — **199 subs, 49.5K views**, 0:35. [BzMUdNjbx1c](https://www.youtube.com/watch?v=BzMUdNjbx1c)
  - #13: 「"부모님이 도와주신 결혼 자금" 세금 내야 하나요?｜신혼부부 증여세 공제 기준 총정리」 — 367 subs, 22.7K views. [063kAFbtPqQ](https://www.youtube.com/watch?v=063kAFbtPqQ)
- In the same sample, curiosity/hybrid titles from big channels collect the largest view totals but rank lower for the exact query:
  - #7: 「"국세청 출신인 저도 하고 있습니다" 자녀에게 합법적으로 3억 주는 방법 [세금학교 2강]」 — 329K subs, 3.62M views, 20:36. [M2c2RN42Luk](https://www.youtube.com/watch?v=M2c2RN42Luk)
  - #8: 「현금증여 '이렇게' 하세요 "평생 세금 없어요…"」 — 312K subs, 982K views. [EgXqSrqo9GI](https://www.youtube.com/watch?v=EgXqSrqo9GI)
- **Query "DSR 대출 규제" (A1):** a 38-sub channel's keyword-dense title 「주택담보대출 한도 5천만 원 줄어드는 이유 (스트레스 DSR 3단계 총정리)」 has 17.8K views, 7:00. [zkMwKtItFqY](https://www.youtube.com/watch?v=zkMwKtItFqY)
- **Query "양도세" (A1):** a 2,140-sub channel's 「1가구 1주택 양도세, 이렇게 계산하면 됩니다」 has 94K views. [zSGTFTGbthM](https://www.youtube.com/watch?v=zSGTFTGbthM)
- **Query "상속세" (A1):** a 10.9K-sub channel's 「1분만에 이해되는, 상속세 계산 방법」 has 21.9K views. [ys85czRNU7I](https://www.youtube.com/watch?v=ys85czRNU7I)

### Inferences
- For a 253-sub channel whose long-form gets only 300–1,000 impressions, the realistic route is **intent-matching hybrid titles**. Pure curiosity titles like 「올해 안 하면 무조건 후회하는 것」 contain no query phrase, so they cannot rank for any search. Pure keyword strings get few Browse clicks.
  - Recommended pattern: **[exact search phrase] + [concrete number/year] + [loss/benefit hook]**.
  - Examples: 「2026 증여세 면제한도 총정리: 자녀 5천만 원, 모르면 세금 폭탄」, 「연금저축 세액공제 한도 900만 원, 12월 31일 전에 넣어야 하는 이유」.
  - Put the search phrase in the first ~15 characters, because mobile truncates long titles. This truncation figure is my inference; I found no official character limit.
- Avoid ending titles in a question; vidIQ's 4M study puts them at 0.82×. Use declarative "~하는 법 / ~원까지 / ~총정리".
- Evidence shows small channels *do* rank for exact-intent tax queries in Korea (positions 1–13 with 199–11K subs). Search is a realistic growth channel here, unlike broad entertainment topics.
- The Title Flip idea suits our case: launch long-form with the hybrid title, and after 48–72 h switch the keyword-weaker versions to keyword-first titles. Also retrofit old long-form (02–12) with keyword-first titles, since they no longer get Browse impressions anyway.

### Gaps
- No published controlled test of keyword vs curiosity titles specifically for small channels or for Korean.
- API ranks are not the same as personalized in-app ranks. CTR and impressions for competitor videos are not observable.

---

## Q3. How to find what Korean users actually search: autocomplete, Trends, Naver DataLab, and high-demand query phrasing

### Takeaway
YouTube autocomplete shows that Korean viewers search with **[세목] + 면제한도/한도/계산(법/기)/신고방법/비과세 요건 + 연도(2026)**. The legal term ("증여재산공제") is not what people type; they use the colloquial "면제한도."

On YouTube, "종부세" is searched far more than "종합부동산세," and "연금저축" is the largest of the tested head terms.

### Cited Findings
YouTube autocomplete (dataset B, KR/ko, collected 2026-11-28; source: [YouTube suggest endpoint](https://suggestqueries.google.com/complete/search?client=firefox&ds=yt&hl=ko&gl=kr&q=%EC%A6%9D%EC%97%AC%EC%84%B8)):

| Seed | Suggestions (YouTube) |
|---|---|
| 증여세 | 신고방법 · 개편 · 신고 · 계산 · **면제한도 2026** · 상속세 · 기한후신고 방법 · 계산법 · 2026 |
| 증여세 면제한도 | **2026** · 2025 · 신고 · 2025 결혼 · 2024 · 상향 · 미신고 · 손자 증여세 면제한도 · 며느리 증여세 면제한도 |
| 자녀 증여 | 자녀 증여세 신고 방법 · 자녀 증여 주식 · 자녀 증여세 홈택스 신고 방법 · 자녀 증여세 기한후 신고 |
| 증여세 계산 | 계산법 · 계산기 · 가산세 계산 · 아파트 증여세 계산 · 토지 증여세 계산 |
| 연금저축 세액공제 | **안받으면** · **한도** · 받는법 · 미적용 · 이월 · 안받는법 · 계산 · 단점 · 환급 |
| IRP 세액공제 | 한도 · 방법 · 이월 · 안받으면 · **900만원** · 연금저축 irp 세액공제 · 개인사업자 · isa irp |
| 연금저축 | 연금저축펀드 · 계좌 · etf 추천 · irp · 계좌 개설 · 펀드 추천 · 가입방법 |
| 종부세 | **계산방법** · 폭탄 · 기준 · 개편안 · **고지서** · 종부세란 · 폭등 · 다주택자 |
| 종부세 계산 | 계산방법 · 계산기 · 계산법 · 세율 계산 · 다주택자/2주택/3주택 · 공동명의 종부세 계산 |
| 양도세 | 개편 · 중과 유예 · 중과 · 10억 · 셀프신고 · 신고방법 · **비과세 요건** · 절세 |
| 1주택 양도세 | **비과세 요건** · 계산법 · 비거주 1주택 · 1세대 1주택 비과세 · 부부공동명의 · 9억이하 |
| 양도세 계산 | 계산기 · 2주택자/다주택자/공동명의/1주택 양도세 계산법 · 재건축 아파트 양도세 계산 |
| 상속세 | 증여세 · 계산 · 신고방법 · 개정 · 개편 · 폐지 · **신고 안해도 되는 경우** · 상속세율 · 개편안 |
| 상속세 면제 | 면제한도 2025 · 면제 한도 · 면제한도 2026 · 자녀 상속세 면제한도 |
| LTV | ltv dsr · ltv dti · ltv dti dsr · ltv 대출 · ltv 40 · ltv 한도 규제 · ltv 70 |
| DSR | dsr 계산 · dsr 대출 (the rest is noise: "ds경제" etc.) |
| 연말정산 | 미리보기 · 하는법 · 신용카드 체크카드 · 세액공제 · 소득공제 · 환급 |
| 기초연금 | 개편 · 계산방법 · 신청방법 · 수급자격 재산 · 자격조건 · 소득인정금액 계산 · 개혁안 · 자동차기준 |
| 건강보험료 | 인상 · 산정기준 · 계산 · 피부양자 등록 · 금융소득 · 줄이는 방법 · 조정신청 · 개편 · 피부양자 자격요건 |
| 재산세 | 계산 · 카드납부 · 과세표준 · 납부방법 · 조회 |

- **Relative YouTube search volume** (Google Trends YouTube property, KR, 5-year mean, one comparison set): 연금저축 33.9 · 증여세 13.9 · 양도세 13.6 · 종부세 3.4 · 종합부동산세 0.4. On YouTube, "종부세" is about 8× "종합부동산세," and 연금저축 is about 2.5× 증여세/양도세. — [Google Trends KR](https://trends.google.com/trends/explore?geo=KR&gprop=youtube&date=today%205-y&q=%EC%97%B0%EA%B8%88%EC%A0%80%EC%B6%95,%EC%A6%9D%EC%97%AC%EC%84%B8,%EC%96%91%EB%8F%84%EC%84%B8,%EC%A2%85%EB%B6%80%EC%84%B8)
- **Relative Web (Google) long-tail volume**, 5-year mean, one set: 연금저축 세액공제 16.4 · 양도세 계산 5.6 · 증여세 계산 4.8 · 종부세 계산 1.0 · "증여세 면제한도" 0.2. Caveat: Trends matches exact strings, and Korean spacing varies (면제한도 vs 면제 한도). The autocomplete above shows "증여세 면제한도 2026" is a top YouTube suggestion, so the low Web number likely reflects spacing variants, low Google-web use for this topic, or both. — [Google Trends KR](https://trends.google.com/trends/explore?geo=KR&date=today%205-y)
- The colloquial "면제한도" is legally imprecise; the correct term is "증여재산공제." — [로앤톡](https://www.lawtalk.co.kr/posts/48232)
- Current deduction amounts (spouse 6억, adult child 5천만/minor 2천만, other relatives 1천만, 10-year aggregation) were reported in 2023 coverage. Verify against current 국세청 guidance before use. — [택스워치 2023](https://www.taxwatch.co.kr/article/tax/2023/06/30/0001)
- Korean press has flagged YouTube tax misinformation:
  - The claim "무이자 차용증 2억1700만원까지 세금 없음" — the press says the interest exemption is separate from principal gift tax. [머니투데이 2026-07](https://www.mt.co.kr/article/2026071016541328103)
  - The claim "990만원씩 쪼개서 입금" — called a myth. [다음/파이낸셜뉴스](https://v.daum.net/v/p45gQzEogw)
- Naver DataLab: I found no published article giving DataLab numbers for these tax keywords. It requires direct querying at datalab.naver.com; search returned only unrelated items. — [search result example](https://news.tf.co.kr/read/economy/1902074.htm)

### Inferences
- Title vocabulary to use, chosen to match autocomplete:
  - 「면제한도」 not 「공제」 in the title; put 「증여재산공제」 in the description.
  - 「계산법/계산방법」, 「신고방법」, 「비과세 요건」, 「한도」, 「안받으면」.
  - Always add the year 「2026」. Switch to 「2027」 in late December for evergreen pieces, since autocomplete already shows a year-suffix habit (2024/2025/2026).
- Use 「종부세」 rather than 「종합부동산세」 in YouTube titles.
- Relationship long-tails are distinct demand pockets: 「손자 증여세 면제한도」, 「며느리 증여세 면제한도」, 「결혼」. These are plausible for a 65+ audience giving to grandchildren.
- Negative-intent queries ("연금저축 세액공제 안받으면", "상속세 신고 안해도 되는 경우", "증여세 미신고/기한후신고") are a hook style that is both searchable and loss-framed. They match our channel's "손실 표현" finding.
- A "유튜브에 도는 증여세 말 팩트체크" angle is backed by real press coverage of misinformation and fits the brand. It is a differentiator against big 세무사 channels.

### Gaps
- No Naver DataLab figures were retrieved; that needs an API key or manual query. It matters because 65+ Koreans still use Naver heavily.
- The autocomplete order is not a volume measure. Trends gives relative, not absolute, volumes.

---

## Q4. Most-viewed Korean YouTube videos on 증여세, 연금저축 세액공제, 종부세, 양도세 (2024–2026): titles, lengths, channel sizes, thumbnail style, and recurring title formulas

### Takeaway
High-view long-form (0.3–7M views) comes mostly from 150K–4M-sub channels, often with a guest 세무사 (이장원 세무사 appears across at least 5 channels). Titles stack:
- a **quoted dramatic line** ("…"),
- a **specific amount** (3억, 5억, 10억, 0원),
- a **method promise** (방법 / 이렇게 하세요),
- a **loss word** (세금 폭탄, 피눈물, 손해),
- an **authority marker** (국세청 출신, 국세청이 허락한, 세무사 name).

Typical length is 7–20 minutes. Small channels mostly win with exact-keyword "연도 + 면제한도/계산법 + 총정리" titles, often as Shorts.

### Cited Findings
**증여세, most-viewed 4–20 min since 2024 (A2):**
- 「"생활비"라고 썼는데 세금 폭탄?" 가족 간 송금할 때 대다수가 하는 치명적인 실수」 — 지식인사이드 4.22M subs, 2.68M views, 19:52. [LDXSSyJKfb0](https://www.youtube.com/watch?v=LDXSSyJKfb0)
- 「가족끼리는 10억을 계좌이체해도 절대 세무조사 안나옵니다, 제발 속지 마세요.」 — 신사임당 2.84M subs, 1.98M views, 15:35. [EtqNlF8bro4](https://www.youtube.com/watch?v=EtqNlF8bro4)
- 「장관님은 알고 우리만 몰랐던 '증여세 0원'의 비밀 (상속전문변호사)」 — **74.5K subs, 2.25M views, 5:30**. [KI_xYcOgn5g](https://www.youtube.com/watch?v=KI_xYcOgn5g)
- 「"자칫하면 세금 폭탄 맞아요" 증여, 상속 받기 전 꼭 알아두세요. (이장원 세무사)」 — 월급쟁이부자들TV 2.12M subs, 1.64M views, 14:19. [ILq1_9q-SU4](https://www.youtube.com/watch?v=ILq1_9q-SU4)
- 「증여공제 범위 내 금액이라도 상속재산에 합산될 수 있다는 사실을 국세청출신세무사가 설명드립니다.」 — 세금 아는형 329K subs, 1.42M views, 15:29. [jA8ExBgsVsw](https://www.youtube.com/watch?v=jA8ExBgsVsw)
- 「요즘 강남 부자들이 증여 안하는 이유를 아시나요?」 — 김택스 63K subs, 995K views, 6:57. [s432B8MyQbs](https://www.youtube.com/watch?v=s432B8MyQbs)
- 「증여세 면제한도? 자녀에게 이체하고 신고어떻게 하지? (셀프 신고방법?!)」 — 52K subs, 786K views, 7:42. [UatFUqX9IYo](https://www.youtube.com/watch?v=UatFUqX9IYo)
- Lottery-tax videos dominate raw views. Example: 「"로또 1등 당첨 후 세금 폭탄!" 당첨시 반드시 이렇게 수령하세요!」 — 52.9K subs, 7.16M views, 13:09. [9qXt26kzygM](https://www.youtube.com/watch?v=9qXt26kzygM)

**증여세 면제한도, relevance order (A1):** besides the small-channel items in Q2, many 5–9-second slideshow Shorts with "총정리" titles get 0.2–1.1M views:
- 「증여세 없는 가족간 증여한도 총정리, 최대 1억 5천만원까지」 — 9.2K subs, 1.11M views. [ROjGkdAzvBY](https://www.youtube.com/watch?v=ROjGkdAzvBY)
- 「가족간 증여시 증여세 면제 한도 완벽 정리(2025년)」 — 2.8K subs, 206K views. [MpwL-Cr-VEY](https://www.youtube.com/watch?v=MpwL-Cr-VEY)
- 「[2026 최신] 가족 간 돈 주고받을 때 '이것' 모르면 세금 폭탄! 증여세 면제 한도 총정리」 — 8.2K subs, 84K views. [Wa_wEVJUXPE](https://www.youtube.com/watch?v=Wa_wEVJUXPE)
- The 9-second item uses hashtags #시니어재테크 #노후준비 #손자녀용돈, which explicitly targets seniors.

**연금저축 / IRP / 연말정산:**
- 「연금저축, IRP 세액공제 받지 않은 재원이 효자 입니다」 — 연금이야기 167K subs, 208K views, 17:35. [WBvn0rAqJ3o](https://www.youtube.com/watch?v=WBvn0rAqJ3o)
- 「연금저축 사용설명서 | 연말정산 세액공제 가능한 연금저축펀드 | ver.2026」 — 박곰희TV 1.28M subs, 266K views, 25:00. [a-890uldXeo](https://www.youtube.com/watch?v=a-890uldXeo)
- 「연금저축펀드 이건 꼭 알고 가입하세요‼️ (세액공제, 장단점, 연말정산)」 — **11.6K subs, 221K views, 6:18**. [HilW1DovD6o](https://www.youtube.com/watch?v=HilW1DovD6o)
- 「연말정산 148만원 돌려받는 통장? 제발 주의하세요. (연금저축펀드, IRP 장단점 총정리)」 — 뿅글이 479K subs, 366K views, 13:03. [VWupRkq5gmc](https://www.youtube.com/watch?v=VWupRkq5gmc)
- 「"마지막 기회입니다" 2025 연말정산 환급 많이 받는 방법 총정리! (바뀐내용 100% 반영, 연금저축, 기부금, 청약통장)」 — 479K subs, 311K views, 13:08, uploaded **2025-11-23**. [PzHYQMYUfRM](https://www.youtube.com/watch?v=PzHYQMYUfRM)
- 「연금저축 매달 50만원? 자동이체 당장 멈추세요. 1월에 600만원 일시납이 무조건 이득인 이유」 — 178K subs, 341K views, uploaded 2026-01-13. [IWHIdSgmd6A](https://www.youtube.com/watch?v=IWHIdSgmd6A)
- 「세금 가장 덜 내는 황금배분 (연금저축, IRP, ISA)」 — 한경 코리아마켓 767K subs, 466K views, 8:19. [Cdgqgr2RevA](https://www.youtube.com/watch?v=Cdgqgr2RevA)
- 「연금계좌 세액공제 환급액 554만원」 — 244K subs, 50K views, Shorts 0:21. [IDdqfpUynR8](https://www.youtube.com/watch?v=IDdqfpUynR8)
- 「[연말정산 방법] 로그인부터 자료 제출까지 "연말정산 무작정 따라하기"」 — **2.4K subs, 135K views, 5:14**. [UgZsmLNOLQ4](https://www.youtube.com/watch?v=UgZsmLNOLQ4)

**종부세:**
- Relevance results this week (A1, notice season) are dominated by news channels uploaded 2026-11-26/27. Examples:
  - KBS 「2.3조 종부세 '융단폭격'…」 — 286K views. [l9lI6qyUyg0](https://www.youtube.com/watch?v=l9lI6qyUyg0)
  - JTBC 「…올해 종부세 고지 대상 72만명, 1년 새 35% 증가…1세대 1주택자 고지세액도 두 배 넘게…」 [r3--2Hj91Qo](https://www.youtube.com/watch?v=r3--2Hj91Qo)
  - 꽉TV 「"내가 집값 올렸냐" 1주택자 종부세 역대 최대, 50초 안에 설명하기」 — 445K views. [4aaSNX6qcXc](https://www.youtube.com/watch?v=4aaSNX6qcXc)
- One creator video this week: 「'세금 폭탄된다' 종부세 고지서 그대로 내면 손해, 최대 80% 공제 빠졌는지 지금 확인해야 할 3가지」 — 연금박사 454K subs, 29K views in 1 day, 20:34. [Vajo5iX8WVE](https://www.youtube.com/watch?v=Vajo5iX8WVE)
- Most-viewed 4–20 min (A2):
  - 「세제개편안 결국 확정됐다, 앞으로 집값 이렇게 됩니다」 — 부읽남TV 1.86M subs, 1.89M views, 18:44. [hV9NbpY5L7A](https://www.youtube.com/watch?v=hV9NbpY5L7A)
  - 「집값 O억 넘으면 단독명의 하세요」 — 집코노미 672K subs, 674K views. [YqDbszXbdQ0](https://www.youtube.com/watch?v=YqDbszXbdQ0)
  - 「"비거주 1주택자도 세금 부과 한다는데..." 6억 이하 집은 앞으로 이렇게 하세요. 세금 90% → 0원 됩니다. 나중엔 절대 바꿀 수 없어요」 — 312K subs, 237K views. [vHVe8Vrjbio](https://www.youtube.com/watch?v=vHVe8Vrjbio)
- 「1분만에 끝내는 종부세 핵심정리」 — **213 subs, 39K views**, Shorts 0:53. [BCxnIJeTbt0](https://www.youtube.com/watch?v=BCxnIJeTbt0)

**양도세:**
- 「집 한 채인데 세금이 이렇게? 양도세·종부세 개정안 핵심 정리」 — 싹풀TV 156K subs, 577K views, 9:38. [dvC8Ll7Y8CI](https://www.youtube.com/watch?v=dvC8Ll7Y8CI)
- 「내년 우리집 재산세, 종부세, 양도세 크게 오르는 거 알고 계시나요?」 — 단희TV 959K subs, 346K views. [rpcs5twRBAo](https://www.youtube.com/watch?v=rpcs5twRBAo)
- 「"1주택 양도세 비과세였는데 3억 세금폭탄 나온 이유" 1세대 1주택을 확실하게 구분하는 방법을 국세청 출신 세무사가 알려드립니다.」 — 329K subs, 186K views. [w14Ixw7Pr9E](https://www.youtube.com/watch?v=w14Ixw7Pr9E)
- 「1주택자인데 양도세 폭탄? 90%가 놓치는 비과세 요건」 — **6.8K subs, 43K views**. [6qw4mgg46Kk](https://www.youtube.com/watch?v=6qw4mgg46Kk)
- 「"비거주자도 2027년까지 팔아야 하나요?" 양도세 신고 절차부터 해외송금 방법까지 5분 정리!」 — **5.1K subs, 63K views**. [TtVY5fZgPFc](https://www.youtube.com/watch?v=TtVY5fZgPFc)
- 「5월 10일 이후에도 중과 안됩니다! 다주택자 양도세 중과를 피하는 '4가지' 방법」 — **8.3K subs, 59K views**, 10:59. [4jVFU2pfAm8](https://www.youtube.com/watch?v=4jVFU2pfAm8)
- A government channel uses a keyword plus a calculation promise: 「내 집 양도세 얼마? 10년 보유했다면 이렇게 계산됩니다」 — 재정경제부, 48.5K views. [71qjMwfrvjw](https://www.youtube.com/watch?v=71qjMwfrvjw)

**상속세:**
- 「"국세청 공식 발표 떴다" 부모님 재산 10억 미만은 상속세 안 내도 된다? …억대 세금 → 0원 된다」 — 312K subs, **1.28M views, 35:29**. [pBZHsAAv7mQ](https://www.youtube.com/watch?v=pBZHsAAv7mQ)
- 「재산 10억까지는 상속세 내지 마라? 피눈물 흘리실 겁니다 "집 한 채만 있어도 세무조사 나옵니다…"」 — 312K subs, 475K views, 19:30. [OcRyWgfrg9k](https://www.youtube.com/watch?v=OcRyWgfrg9k)
- 「"상속세 세금폭탄 피하려면 이때 팔아야 합니다" 2025년 상속세 안 내는 방법을 국세청 출신 세무사가 알려드립니다.」 — 329K subs, 258K views. [9gRlHYKQ3EQ](https://www.youtube.com/watch?v=9gRlHYKQ3EQ)
- 「상속세 세무조사, 국세청은 실제로 무엇을 물어볼까?」 — **10.9K subs, 99K views**, 12:56. [NoYmzRupKPQ](https://www.youtube.com/watch?v=NoYmzRupKPQ)

**DSR/LTV:** demand on YouTube is much smaller. The top relevance results are 0.7K–165K views, mostly Shorts; for example, 「LTVㆍDTIㆍDSR 뭐가 다른 건데?」 has 16.9K views. [ser1E341-QA](https://www.youtube.com/watch?v=ser1E341-QA)

**Thumbnail style:**
- I did not download or inspect competitor thumbnails in this pass; WebFetch cannot render YouTube result pages. This is a gap.
- Korean thumbnail guides for senior-targeted channels recommend:
  - outlined text for legibility,
  - yellow/white for benefit phrases and red for emphasis,
  - large faces and big 2-line titles.
  — [lilys.ai 시니어 롱폼 가이드](https://lilys.ai/ko/notes/senior-ai-youtube-20251128/ai-senior-longform-no-edit-3m-passive-income)
- YouTube's performance FAQ warns against misleading or shocking thumbnails and excessive caps or punctuation. — [YouTube Help](https://support.google.com/youtube/answer/141805?hl=en-GB)
- The project's own 2026-10-29 benchmark (CLAUDE.md, `docs/script_template_longform.md` v6) found the same pattern among Korean finance channels: two big lines of yellow, white and red text plus a number. This is internal, not a web source.

### Recurring title formulas (synthesized from the titles above)
1. **"[인용 충격 문장]" + [구체 금액/결과] + [방법]** — 「"국세청 출신인 저도 하고 있습니다" 자녀에게 합법적으로 3억 주는 방법」
2. **[세목/상황] + [금액] + 해도/줘도 + [의외 결과]** — 「가족끼리는 10억을 계좌이체해도 절대 세무조사 안나옵니다」
3. **[연도] + [정확 검색어] + 총정리/완벽 정리** (small channels, Shorts) — 「2026년 증여세 면제 한도 …」, 「가족간 증여시 증여세 면제 한도 완벽 정리(2025년)」
4. **[대상 상황]인데 + 세금 폭탄? + [N%가 놓치는] + [요건]** — 「1주택자인데 양도세 폭탄? 90%가 놓치는 비과세 요건」
5. **[금액 → 0원] / [세금 N% → 0원]** — 「세금 90% → 0원 됩니다」, 「억대 세금 → 0원 된다」
6. **[행동 금지/멈춤 명령]** — 「자동이체 당장 멈추세요」, 「증여세 절대 내지 마세요!」, 「제발 속지 마세요」 (this matches vidIQ's "do not/stop" ~2× frame)
7. **[기한/마지막 기회] + [연도] + 방법 총정리 + (괄호 키워드 나열)** — 「"마지막 기회입니다" 2025 연말정산 환급 많이 받는 방법 총정리! (…연금저축, 기부금, 청약통장)」
8. **Authority tag** — 「국세청 출신 세무사가 알려드립니다」, 「(이장원 세무사)」, 「(상속전문변호사)」, 「국세청이 허락한 유일한 방법」
9. **Bracketed keyword list at the end** — 「(세액공제, 장단점, 연말정산)」, 「[재개발, 재건축 양도소득세 장기보유특별공제 적용 완벽 정리]」. This puts the search terms in the title without hurting the hook.

### Inferences
- Our titles (「올해 안 하면 무조건 후회하는 것」, 「자녀에게 돈 주기 전에 모르면 세금 폭탄 맞는 것」) already use formula-style loss hooks. They are missing three things the winners have: **(a) the exact search phrase, (b) a concrete number, (c) a bracketed keyword tail.**
  - A minimal fix: 「자녀에게 돈 주기 전에 모르면 세금 폭탄 (2026 증여세 면제한도·10년 합산·신고방법 총정리)」.
- Big-view packaging leans on authority: credentialed 세무사 faces and "국세청 출신." We have no credential, so substitute verifiable authority: 「국세청 안내 기준」 or 「법조문으로 확인」, plus the official source on screen. This is an inference; it is untested.
- Tax long-form winners cluster at 7–20 min. A few hits run 25–35 min, but those come from big channels with guest experts.
- Avoid exaggerated promises like "국세청도 못 말리는," "절대 모른다." Press has flagged these as misinformation (see Q3), and YouTube's FAQ warns against misleading packaging.

### Gaps
- Thumbnails of the listed videos were not visually inspected. A follow-up should open the `i.ytimg.com/vi/<id>/hqdefault.jpg` images for ~15 of the IDs above (with permission if downloading).
- No CTR, impression or traffic-source data for competitor videos, so we cannot tell which of these views came from search versus browse.
- I found no data on how 65+ viewers specifically respond to thumbnail font size, contrast or faces. The only Korean sources are vendor courses.

---

## Q5. Seasonal demand: when Korean search interest peaks for 연말정산/연금저축 (Nov–Dec), 종부세 notices (late Nov), 증여 (year-end), 양도세 (Jan–May), 상속세

### Takeaway
Google Trends KR (5 years, monthly index where 1.0 is an average month) shows:
- **연금저축/IRP peak in December (1.5–1.7×) and January (1.3–1.5×).**
- **연말정산 explodes in January (YouTube 4.8×, Web 7.3×)** and starts rising in December (1.3×).
- **종부세 peaks in Nov–Dec (YouTube 1.8×/1.7×, Web 2.0×/1.5×).** In 2026 there was also a large summer spike from the August tax-reform announcement.
- **증여세 and 상속세 are flat all year (0.9–1.3×)**, so they behave as evergreen search terms and spike only on policy news.
- **양도세 rises mildly in Dec (1.3–1.4×) and Feb (1.3×).**
- **재산세 peaks in July (3.2–3.8×) and September (2.2×).** 기초연금 (Web) peaks in August (2.7×) with government-plan news.

### Cited Findings
Dataset C, Google Trends KR "today 5-y" (weekly), monthly index. Source: [Google Trends KR](https://trends.google.com/trends/explore?geo=KR&date=today%205-y). YouTube rows use gprop=youtube.

| Keyword | Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 연말정산 (YT) | **4.8** | 1.8 | 0.7 | 0.5 | 0.8 | 0.3 | 0.3 | 0.3 | 0.3 | 0.4 | 0.6 | 1.3 |
| 연말정산 (Web) | **7.3** | 1.9 | 0.4 | 0.3 | 0.4 | 0.2 | 0.1 | 0.1 | 0.2 | 0.2 | 0.3 | 0.7 |
| 연금저축 (YT) | 1.3 | 1.3 | 1.1 | 0.8 | 1.0 | 0.9 | 0.7 | 0.8 | 0.8 | 0.8 | 1.0 | **1.5** |
| 연금저축 (Web) | 1.5 | 1.3 | 0.9 | 0.7 | 1.1 | 0.8 | 0.7 | 0.7 | 0.7 | 0.8 | 1.1 | **1.7** |
| IRP (YT) | 1.2 | 1.3 | 1.0 | 0.8 | 0.9 | 0.9 | 0.7 | 0.8 | 0.8 | 0.9 | 1.1 | **1.6** |
| 종부세 (YT) | 0.6 | 0.3 | 0.5 | 0.1 | 1.1 | 1.4 | 1.3 | 1.4 | 1.2 | 0.5 | **1.8** | 1.7 |
| 종부세 (Web) | 0.8 | 0.8 | 1.0 | 0.6 | 0.9 | 0.8 | 0.9 | 1.2 | 0.9 | 0.6 | **2.0** | 1.5 |
| 종합부동산세 (YT) | 0.0 | 0.3 | 0.0 | 0.2 | 0.3 | 0.6 | 0.4 | 1.1 | 3.0 | 0.7 | **3.2** | 2.1 |
| 양도세 (YT) | 1.1 | 1.3 | 0.9 | 1.0 | 1.2 | 0.8 | 0.8 | 1.1 | 0.8 | 0.7 | 0.9 | **1.4** |
| 증여세 (YT) | 1.0 | 1.1 | 1.1 | 0.9 | 1.1 | 1.0 | 1.1 | 0.9 | 0.9 | 0.9 | 0.9 | 1.1 |
| 증여세 (Web) | 0.9 | 1.0 | 0.9 | 1.1 | **1.3** | 1.0 | 0.9 | 0.9 | 0.8 | 1.2 | 1.1 | 0.9 |
| 상속세 (YT) | 0.9 | 1.1 | 1.1 | 0.9 | 0.9 | 1.2 | 1.1 | 0.9 | 1.0 | 0.9 | 1.0 | 0.9 |
| 재산세 (YT) | 0.2 | 0.4 | 0.7 | 0.4 | 0.7 | 1.0 | **3.8** | 1.0 | 2.2 | 1.0 | 0.4 | 0.1 |
| 기초연금 (Web) | 0.7 | 0.4 | 0.4 | 0.8 | 1.3 | 1.3 | 0.8 | **2.7** | 1.4 | 0.8 | 0.8 | 0.6 |
| DSR (YT) | 0.9 | 1.0 | 0.9 | 0.7 | 1.1 | **1.5** | 1.1 | 1.0 | 0.9 | 1.0 | 1.0 | 0.9 |
| 건강보험료 (YT) | 1.2 | 1.0 | 0.9 | 0.8 | 1.1 | 1.0 | 0.8 | 0.9 | 0.8 | 0.8 | 1.2 | **1.4** |

- **Peak weeks (Web, 5y):**
  - 연말정산: the third week of January every year (e.g., 2026-01-18~24).
  - 연금저축/IRP: 2025-12-21~2026-01-03.
  - 종부세: 2026-08-02~08 (reform), 2021-11-28~12-04, 2022-11-20~26, **2026-11-22~28 (this week)**.
  - 증여세: 2026-10-25~31 and 2026-04-26~05-09.
  - 상속세: 2026-07-05~11 and 2026-11-01~07.
  - 양도세: 2026-02-01~07, 2021-12-05~11, 2022-05-08~14, 2025-12-21~27.
  — [Google Trends KR](https://trends.google.com/trends/explore?geo=KR&date=today%205-y)
- **Payment calendar:** 종부세 is paid 12/1–12/15 each year. A deferral request is due by 12/12. If the bill exceeds 250만원, part can be paid in installments by about June 15 of the next year. Notices are usually sent in late November; one article reports 63만 people notified "from the 24th," but the year of that article is unclear. — [wikidocs TaxSave 2026](https://wikidocs.net/blog/@TaxSave/32508/); [SBS Biz](https://biz.sbs.co.kr/amp/article/20000274619); [택스워치 2025-11-26](https://www.taxwatch.co.kr/article/tax/2025/11/26/0002); [토스뱅크 2026 종부세](https://www.tossbank.com/articles/real-estate-tax)
- **2026 notice coverage:** JTBC (2026-11-26) titled its video "올해 종부세 고지 대상 72만명, 1년 새 35% 증가." — [JTBC r3--2Hj91Qo](https://www.youtube.com/watch?v=r3--2Hj91Qo). Sources conflict on the 2026 1-house basic deduction (12억 vs proposed 14억, pending the National Assembly). — [택스타임즈](https://www.taxtimes.co.kr/news/article.html?no=272564); [경향신문 2026-08-03](https://www.khan.co.kr/article/202608031800051)
- **Competitor timing:** 뿅글이's 연말정산 video was published **2025-11-23**, and 광화문금융러's "1월 일시납" 연금저축 video was published 2026-01-13. Both sit just before the demand peaks. — [PzHYQMYUfRM](https://www.youtube.com/watch?v=PzHYQMYUfRM); [IWHIdSgmd6A](https://www.youtube.com/watch?v=IWHIdSgmd6A)

### Inferences
- **Immediate calendar for this channel (as of 2026-11-28):**
  - **종부세 (now, through about 12/15):** a keyword title such as 「종부세 고지서 받았다면: 계산방법·분납·납부기한 12월 15일」. Interest is at its 5-year seasonal high this week.
  - **연금저축/IRP 세액공제 (Dec 1–31):** 「연금저축 세액공제 한도 900만 원, 12월 31일 전에 넣어야」. This targets the December 1.5–1.7× peak and the "안받으면/한도/이월" long-tails.
  - **연말정산 (publish late Dec to early Jan):** catch the 4.8× January spike, publishing before the third week of January.
  - **증여세/상속세:** evergreen. Publish any time, but refresh the year in titles ("2027") right after New Year, because autocomplete is year-suffixed.
  - **양도세:** mild Dec and Feb bumps; the May 확정신고 effect is weak in the data. Policy news (중과 유예, 장특공 개편) drives the real spikes.
  - **재산세:** July and September (1기/2기 notices).
- Seasonal peaks (×1.5–7) are larger than any title-formula effect in the vidIQ study (×1.5–2). Matching topic and timing to these peaks is probably the single biggest search lever available to a small channel. This is an inference from combining two different datasets.

### Gaps
- Naver DataLab (likely more representative for 65+ users) was not queried.
- Google Trends is relative and exact-string; the 5-year average mixes in policy shocks (2021–22 종부세, 2026 세제개편).
- The 2026 notice count and the final 2026 1-house deduction amount are unconfirmed.

---

## Q6. Test & Compare (title/thumbnail A/B) availability and best practices

### Takeaway
Test & Compare is available in YouTube Studio on desktop for channels with advanced features. It tests up to 3 titles, 3 thumbnails, or 3 combinations, and picks the winner by **watch time share, not CTR**. Shorts cannot be tested. Low-impression videos rarely produce a winner, which is a real constraint for our long-form at 300–1,000 impressions per video.

### Cited Findings
- **Eligibility and setup:** desktop YouTube Studio only, and advanced features must be enabled. Up to 3 titles and/or thumbnails can be tested.
  - Tests usually finish within 2 weeks, but can end in a few days.
  - The winner is chosen by watch time share and then shown to everyone.
  - Result labels are Winner / Performed Same / Inconclusive. If Inconclusive, the first-uploaded version stays.
  — [YouTube Help: A/B test titles & thumbnails](https://support.google.com/youtube/answer/16391400?hl=en)
- **Limitations:**
  - No Shorts, scheduled lives, unconverted premieres, made-for-kids, mature or private videos.
  - Editing the title or thumbnail mid-test stops the test.
  - A small control group is excluded.
  - "Videos with low impressions are less likely to produce a winner."
  - If any thumbnail is below 720p, all are downscaled to 480p.
  — [YouTube Help](https://support.google.com/youtube/answer/16391400?hl=en)
- **Best practices from YouTube:** test older videos first, use meaningfully different variants, allow time, and upload at 1280×720 or higher. — [YouTube Help](https://support.google.com/youtube/answer/16391400?hl=en)
- **Timeline:**
  - Thumbnail testing was announced at VidCon 2023 and rolled out in 2024. — [TechCrunch 2024-06-12](https://techcrunch.com/2024/06/12/youtube-creators-can-test-multiple-video-thumbnails); [SEJ: thumbnail A/B to all channels](https://www.searchenginejournal.com/youtube-rolls-out-thumbnail-a-b-testing-to-all-channels/519281/)
  - Title testing was added in 2025. Tubefilter dates the expansion to 2025-07-16, while Toptal says late 2025; the sources conflict on exact timing. — [Tubefilter 2025-07-16](https://www.tubefilter.com/2025/07/16/youtube-feature-test-and-compare-titles-thumbnails/); [SEJ: title A/B global](https://www.searchenginejournal.com/youtube-title-a-b-testing-rolls-out-globally-to-creators/562571/); [Toptal](https://www.toptal.com/creator/post/youtube-thumbnail-ab-testing)
- YouTube's rationale for watch time share: it captures both CTR and retention. — [YouTube Help: Test & compare thumbnails](https://support.google.com/youtube/answer/13861714)
- The vidIQ guidance notes that a manual title edit ends a running Test & Compare experiment, so a "flip" should be a separate, deliberate edit after the test. — [vidIQ Title Flip](https://vidiq.com/blog/post/YouTube-Title-Flip-SEO-Framework/)

### Inferences
- At 300–1,000 impressions per long-form, most tests will likely come back "Inconclusive" or "Performed Same." Test & Compare is more useful once a video gets search impressions over weeks; evergreen 증여세/연금저축 videos are candidates.
- Make variants differ meaningfully:
  - **title A** = keyword-first ("2026 증여세 면제한도 총정리…"), **title B** = loss-hook ("모르면 세금 폭탄…"), **title C** = hybrid.
  - Pair them with genuinely different thumbnails (number-board vs face vs quiz).
- Because the metric is watch time share, a keyword title that attracts searchers who stay could beat a curiosity title even with lower CTR. This is what we want to learn.
- Retrofit tests on older long-form (02–12) are low-risk, which matches YouTube's own advice to test older videos first.

### Gaps
- No public data on the minimum impressions needed for a conclusive result.
- No Korean-language case studies of Test & Compare results found.

---

## Supplementary: older (65+) Korean audience context, relevant to packaging

### Cited Findings
- **YouTube news use in Korea (Digital News Report 2025):** 50s 61% and 60+ 53%, about double the 48-country averages of 31% and 26%. A 2026 follow-up puts 60+ weekly YouTube news use at 59%. — [뉴시스 2026-06-16](https://www.newsis.com/view/NISX20260616_0003671612); [Korea Times 2025-06-18](https://www.koreatimes.co.kr/southkorea/society/20250618/youtube-dominates-news-consumption-among-older-conservative-koreans-study); [기자협회보](https://www.journalist.or.kr/m/m_article.html?no=58780); [Reuters Institute DNR 2025](https://reutersinstitute.politics.ox.ac.uk/digital-news-report/2025/dnr-executive-summary)
- **App time by age:**
  - In Aug 2024, YouTube was the longest-used app among 50s (173.9억분) and 60+ (138.4억분). The underlying data source (Wiseapp or another) is unclear.
  - A 2025 Wiseapp report said 60+ spent the most time on TikTok Lite.
  — [디지털데일리 2024-09-19](https://www.ddaily.co.kr/page/view/2024091909340549146); [다음 팩트체크 2025-09-22](https://v.daum.net/v/20250922063158978)
- **Senior-targeted Shorts in our sample:** they use hashtags such as #시니어재테크 #노후준비 #손자녀용돈 and channel names like 백세인생창고, 시니어건강이최고, 장례지도사. These get 0.2–1.1M views on 증여/상속 한도 "총정리" slides. — [MpwL-Cr-VEY](https://www.youtube.com/watch?v=MpwL-Cr-VEY); [xG9wCv3XAZ4](https://www.youtube.com/watch?v=xG9wCv3XAZ4); [t_cgK82-gVs](https://www.youtube.com/watch?v=t_cgK82-gVs)

### Inferences
- A 65+ audience that uses YouTube as a news source may respond better to news-like, notice-driven packaging than to abstract curiosity hooks: 「고지서」, 「납부기한 12월 15일」, 「올해부터 바뀐」.
- Relationship-specific queries are plausible senior intents: 「손자 증여세 면제한도」, 「며느리」, 「자녀 결혼 자금」.
- Thumbnail legibility rules for older viewers (font size, contrast) are not backed by any rigorous Korean source found. Keep the project's current "2 big lines, yellow/white/red, number" rule, which matches competitors.
