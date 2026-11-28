# YouTube Shorts feed distribution (2025–2026) and converting Shorts viewers to long-form

Scope: how new Shorts are distributed (test pools, "viewed vs swiped away" / Korean Studio label 계속 시청함 / "Stayed to watch", plateaus), benchmarks, hook techniques, near-zero-impression Shorts, and Shorts→long-form conversion. Our case is a Korean finance/real-estate channel. It posts one 35–45s Short a day, and most of its audience is 65+. Each Short gets about 200 views at first. At about 40% or more viewed it reaches about 1,000 views and stops. Below about 35% it stops at about 200. Shorts send 0–2 views to each long-form video.

Source labels: **[OFFICIAL]** = YouTube help centre, YouTube blog or a named YouTube employee. **[3P-DATA]** = third-party dataset with a stated sample. **[ANECDOTE/VENDOR]** = creator claims or tool-vendor blogs with no method given.

---

## 1. Official YouTube statements on Shorts ranking, the separate Shorts feed, and the 2025 view-count change

### Takeaway
YouTube has confirmed the basic mechanism and nothing more. Each Short goes to a "seed audience." Depending on how that audience responds, the Short "may get a lot more traffic or it may taper off." The Shorts feed is ranked differently from long-form, and Shorts watch history is kept apart from long-form recommendations. YouTube publishes no thresholds, batch sizes or stage definitions. Since 31 Mar 2025 a public "view" counts every start or replay. The older, stricter count lives on as "engaged views."

### Cited Findings
- **[OFFICIAL] Seed audience.** Todd Sherman (then Shorts product lead), on YouTube's Creator Insider channel with Liaison Rene Ritchie: "Sometimes those algorithms will go and effectively find a seed audience, find a set of people that may enjoy your video… And depending on how that goes, it may get a lot more traffic, or it may kind of taper off." OnlineMarketing.de reported this as YouTube's explanation for Shorts that stall at roughly 1,000 views, and it says YouTube treats those seed views "more like impressions." — [OnlineMarketing.de](https://onlinemarketing.de/social-media-marketing/erklaerung-shorts-1000-views-stagnation); [Search Engine Journal](https://www.searchenginejournal.com/youtube-explains-how-shorts-algorithm-works/494953/)
- **[OFFICIAL] Swipe feed vs chosen click.** Sherman (TechCrunch, 25 Aug 2023): long-form viewers pick a video on purpose, while Shorts viewers are "swiping through content not knowing what comes next." A swipe-past is therefore not a view unless it passes a "meaningful threshold." YouTube does not publish that threshold because it changes over time and YouTube does not want people "to try to game the system." The feed is deliberately kept varied because people scroll through so many Shorts. — [TechCrunch](https://techcrunch.com/2023/08/25/youtube-demystifies-the-shorts-algorithm-views-and-answers-other-creator-questions/)
- **[OFFICIAL] Timing and volume.** Sherman said time of day is not worth optimising except for news, where freshness matters, and that upload volume does not drive reach: "it's more about quality over quantity." He also advised against deleting and re-uploading Shorts because this can look like spam. — [TechCrunch](https://techcrunch.com/2023/08/25/youtube-demystifies-the-shorts-algorithm-views-and-answers-other-creator-questions/)
- **[OFFICIAL] Separate watch history.** Todd Beaupré (YouTube discovery director, VidCon 2022): YouTube separated Shorts watch history from long-form. Before that, the system read heavy Shorts viewers as wanting only short content and "basically stopped recommending those viewers long-form content." YouTube does not use Shorts viewing on the main (long-form) side so the algorithm does not "get the wrong idea." — [vidIQ](https://vidiq.com/blog/post/youtube-shorts-long-form-viewers-algorithm/)
- **[OFFICIAL] Metric definitions (current Help Center, fetched 2026-11-28).**
  - "Stayed to watch": "The percentage of times viewers stayed to watch past the initial seconds of a Short."
  - Engaged views: "How many times viewers stayed to watch past the initial seconds, not including any loops."
  - The Shorts report also has a "How viewers engaged" breakdown.
  - Sources: [YouTube Help 12220281](https://support.google.com/youtube/answer/12220281). The reach page describes it as the percentage of times viewers viewed a Short versus swiped away: [YouTube Help 9314355](https://support.google.com/youtube/answer/9314355?hl=en). "Viewed vs swiped away", "Stayed to watch" and 계속 시청함 are therefore the same gate metric under different Studio labels.
- **[OFFICIAL] 31 Mar 2025 view-count change.**
  - A Shorts view now counts when a Short starts or replays, with no minimum watch time.
  - The old metric was renamed "engaged views" (Advanced Mode). Monetisation and YPP eligibility still use engaged views.
  - YouTube advised comparing content from before and after the change using engaged views.
  - Sources: [TechCrunch](https://techcrunch.com/2025/03/26/youtube-is-changing-how-youtube-shorts-views-are-counted); [Search Engine Journal](https://www.searchenginejournal.com/youtube-changes-shorts-view-counts-no-change-to-monetization/543005/); [Digital Music News](https://www.digitalmusicnews.com/2025/03/27/how-does-youtube-shorts-count-views-2025/); [Digiday](https://digiday.com/media/youtube-shorts-view-count-update-wins-over-brands-but-creators-arent-sold/)
- **[3P-DATA] Size of the view/engaged-view gap.** Agentio measured public Shorts views about 65% above engaged views across 550 organic Shorts. That implies roughly 39% of counted views are not engaged views (arithmetic from Agentio's figure). — [Agentio](https://www.agentio.com/blog/youtube-view-vs-engaged-view)
- **[OFFICIAL] Shorts length.** Since 15 Oct 2024, square or vertical uploads up to 3 minutes are classified as Shorts. YouTube said its recommendation systems would take "a few weeks" to adapt to longer Shorts. A 16:9 video is classified as long-form and does not compete in the Shorts feed. — [YouTube Help 15424877](https://support.google.com/youtube/answer/15424877?hl=en); [YouTube blog](https://blog.youtube/news-and-events/tall-updates-coming-to-shorts/); [TechCrunch](https://techcrunch.com/2024/10/03/youtube-takes-on-tiktok-with-longer-shorts-templates-trends-and-more)
- **[OFFICIAL, secondhand] Videos judged one by one.** YouTube's growth team reportedly said the system judges each video, not the channel average, and that there is "no penalty box." This comes via cut.pro, which gives no primary link. — [cut.pro](https://cut.pro/en/blog/youtube-shorts-stuck-low-views-2026)
- **[3P-DATA / unconfirmed] "Flattening" of older Shorts.** Mario Joos (retention strategist) posted on 30 Nov 2025, using data from seven large Shorts channels. He said that from mid-Sep 2025, Shorts older than about 28–30 days get far fewer impressions. He calls this "a carefully constructed working theory and not a confirmed fact," and YouTube has not confirmed any change. — [Search Engine Journal](https://www.searchenginejournal.com/youtube-shorts-algorithm-may-now-favor-fresh-over-evergreen/562661/)
- **[3P-DATA] Shorts feed share of views.** Metricool studied 799,718 videos from 71,177 accounts (mostly US). It found 61% of measured views came from the Shorts feed. Shorts traffic more than doubled year over year, while long-form engagement fell 45%. — [Tubefilter](https://www.tubefilter.com/2026/08/03/youtube-shorts-long-form-study-metricool/)

### Inferences
- Our pattern fits Sherman's description: a seed batch of about 200 viewers, expansion only when the response is good enough, then a taper. There is no official evidence for fixed "walls" at 200 or 1,000. Those numbers are probably just where our channel's response lands.
- Our 계속 시청함 figures (35–45%) are in the Studio metric that YouTube itself defines as the gate ("stayed to watch past the initial seconds"). It is the right KPI for the first stage.
- Since 31 Mar 2025, our public view counts include swipe-past starts. When diagnosing reach, use engaged views and "shown in feed" impressions, not public views.

### Gaps
- YouTube has never published the stages, batch sizes, the "meaningful threshold" in seconds, or the relative weight of stayed-to-watch, average percentage viewed, likes and shares. Every staged model below is third-party.
- I could not verify the original Creator Insider video's date, and could not retrieve its transcript.
- I found no official 2025–2026 statement confirming or denying Joos's recency change.

---

## 2. Benchmarks for "viewed (vs swiped away)" / stayed-to-watch, and its effect on reach

### Takeaway
YouTube publishes no benchmark. Third-party "targets" cluster around 50–60% as average and 70% or more as good. None of them gives a method, and they mix up different metrics (stayed-to-watch vs average percentage viewed). Our 35–45% is below every published target. The best evidence is the channel's own relationship between stayed-to-watch and 7-day views, and we have that already: correlation 0.62 in our data.

### Cited Findings
- **[3P, no method]** YouTube publishes no official benchmark. The most common creator target is 70–80% viewed. One guide calls about 50/50 "average" and 70%+ "viral territory." Another says 50–60% is average and 70–80% is good. — [1of10](https://1of10.com/blog/youtube-shorts-analytics/); [ContentMatch](https://contentmatch.io/youtube-shorts-algorithm-viewed-vs-swiped-ratio-2026/); [falconvid](https://falconvid.ai/blog/youtube-shorts-viewed-vs-swiped-away); [vidpal](https://www.vidpal.ai/blog/good-retention-rate-for-youtube-shorts-benchmarks-2026)
- **[3P, unverified]** Some guides claim YouTube stops serving a Short whose viewed share is under 70%. No YouTube document supports this, and our own Shorts expand at about 40%, which contradicts it. — [ContentMatch](https://contentmatch.io/youtube-shorts-algorithm-viewed-vs-swiped-ratio-2026/)
- **[3P, method caveat]** One guide says to read viewed-vs-swiped only after about 48 hours and at least 1,000 feed impressions, because early readings are noisy. — [falconvid](https://falconvid.ai/blog/youtube-shorts-viewed-vs-swiped-away)
- **[3P, KR blog]** Korean blogs cite targets of "80%+ for Shorts over 31 seconds, close to 100% under 30 seconds" (apparently 2024 data). This most likely refers to average percentage viewed, not stayed-to-watch, and has no clear source. Treat it as unreliable. — [tilnote](https://tilnote.io/pages/6a2edb80da0e1b7feb5fea78); [maily.so desireanalyst](https://maily.so/desireanalyst/posts/3jrk9g56z51)
- **[ANECDOTE]** Jenny Hoyos (Shorts specialist) is summarised as citing about 90% retention for viral reach. The same interview also has her saying retention matters less than people think, so the figure is contested. — [Creator Science podcast](https://podcast.creatorscience.com/jenny-hoyos/); [marketing-examined summary](https://marketing-examined.beehiiv.com/p/jenny-hoyos-shortform-video-playbook)
- **[3P-DATA]** vidIQ cites Nate Black's analysis of 35 billion Shorts views: channels with at least 200 Shorts see consistent view growth over time. — [vidIQ](https://vidiq.com/blog/post/youtube-shorts-algorithm/)
- **[3P, KR]** The YouTube test watches two signals: the share who watched instead of swiping, and how long they stayed. — [vidIQ (small channels)](https://vidiq.com/blog/post/more-views-small-youtube-channel/)

### Inferences
- The external "70%" figure may be inflated by English-language entertainment niches and young audiences, and it may confuse the metric with average percentage viewed. For a Korean finance channel watched mostly by people over 65, the useful targets are relative ones from our own data. Our split already shows 35% → stays near 200 and 40%+ → about 1,000.
- To break the about-1,000 ceiling, stayed-to-watch is probably necessary but not sufficient. The second-stage signals (average percentage viewed, likes, shares) also need to improve. Our data shows likes correlate 0.68 with views, which is consistent with this.

### Gaps
- No published dataset links stayed-to-watch levels to reach tiers. No benchmark exists for older audiences, for Korea, or for finance/informational content.

---

## 3. Hook techniques that raise viewed % (first frame, text, motion, no intro, question hooks, loops, length)

### Takeaway
The evidence is almost all practitioner consensus, not controlled studies. The common points: decide the first 1–2 seconds before anything else. Open on the payoff or a high-stakes claim, never on a logo, greeting or setup. Put bold on-screen text that works with the sound off. End immediately after the payoff. Avoid dead seconds. Shorter is better unless the content earns the length. YouTube's own long-form advice repeats the "no logo or slow intro" rule.

### Cited Findings
- **[OFFICIAL, long-form side]** YouTube's blog (Julia Lee Harter, 14 Jul 2026) says a long video reached from a Short should address the promised topic within the first 5–10 seconds, "not channel logos, slow intros, or unrelated updates." Viewers who have to hunt for the promised content leave quickly. — [YouTube Blog](https://blog.youtube/creator-and-artist-stories/youtube-related-videos-traffic-guide/)
- **[3P]** vidIQ's fix for stalled Shorts: strengthen the hook in the first 1–3 seconds and match what the seed audience expects from the channel. — [vidIQ](https://vidiq.com/blog/post/youtube-shorts-algorithm/)
- **[3P]** Viewers decide to keep watching or swipe in the first 1–2 seconds. Hooks built on curiosity, urgency or a broken pattern hold attention. — [vidIQ hooks](https://vidiq.com/blog/post/viral-video-hooks-youtube-shorts/)
- **[ANECDOTE, Jenny Hoyos]** "Every 2nd counts on a short. Whatever you say you're gonna do, you end it right after you do it." Keep hooks under 3 seconds and visual. Hoyos also stresses the last second because the payoff sits there. One write-up says removing a single dead second raised retention from 83% to 88%. — [Creator Science podcast](https://podcast.creatorscience.com/jenny-hoyos/); [marketing-examined](https://marketing-examined.beehiiv.com/p/jenny-hoyos-shortform-video-playbook); [leaderonomics](https://leaderonomics.com/videos/box-of-chocolates/how-to-make-great-youtube-shorts-lessons-from-jenny-hoyos)
- **[ANECDOTE]** Stating the payoff inside the hook, rather than delaying it, fixed a Short that "fell off a cliff." Flipping the hook from "how to" to "stop doing" helped. Closing a loop in the final line raised rewatches from 4% to 21%. All three are single creator self-reports. — [HookConfessions (Telegram)](https://t.me/s/HookConfessions/11)
- **[3P, unsourced]** A visually distinct opening frame with bold on-screen text carries the hook during silent autoplay. Burned-in captions are claimed to bring 15–25% higher retention (no source). — [dev.to hook engineering](https://dev.to/bulkdl/hook-engineering-the-science-of-the-first-3-seconds-in-short-form-video-2026-2jp9); [Opus](https://www.opus.pro/blog/ideal-youtube-shorts-length-format-retention)
- **[3P]** A final frame that matches the first makes the replay seamless. Forced loops work poorly for straightforward announcements, which may include policy news. — [dev.to experimentation playbook](https://dev.to/mamadou_hurbourg_797b27d3/youtube-shorts-as-an-experimentation-system-a-2026-playbook-for-consistent-reach-26el)
- **[KR blogs]** Korean blogs recommend putting the result or key sentence first instead of a greeting, keeping captions and key visuals clear of the Shorts UI buttons (right rail and bottom caption area), and loop endings. — [miso.kr (captions/UI)](https://miso.kr/blog/thread/%EC%87%BC%EC%B8%A0-%EC%95%8C%EA%B3%A0%EB%A6%AC%EC%A6%98-%EA%BF%80%ED%8C%81); [miso.kr (views)](https://miso.kr/blog/thread/%EC%87%BC%EC%B8%A0-%EC%A1%B0%ED%9A%8C%EC%88%98-%EB%8A%98%EB%A6%AC%EA%B8%B0-%EA%BF%80%ED%8C%81)
- **[KR, opinion]** One Korean newsletter argues the first 1–3 seconds act as the "thumbnail" in the feed. It claims 60–70% or more of Shorts traffic now comes from browse surfaces where titles and thumbnails matter (citing Mario Joos via ppc.land). This conflicts with our channel's data, where the Shorts feed is about 96% of Shorts traffic. Treat it as niche-dependent. — [maily.so desireanalyst](https://maily.so/desireanalyst/posts/3jrk9g56z51)
- **[3P-DATA]** Metricool: average view duration on Shorts has fallen "dramatically" year over year (no figure given), and 83% of interactions happen in the first 10 days. — [Tubefilter](https://www.tubefilter.com/2026/08/03/youtube-shorts-long-form-study-metricool/); [cut.pro citing Metricool](https://cut.pro/en/blog/youtube-shorts-stuck-low-views-2026)

### Inferences
- For a finance/policy Short aimed at viewers over 65, these points suggest:
  - The first frame should be a large-type loss or number statement ("이것 모르면 세금 ○○만 원 더") over a relevant, full-frame photo, not a small object or a branded title card.
  - The narration should start at frame 0 with no lead-in.
  - Captions should be large and placed above the bottom UI band.
  - Cut 35–45s toward about 25–35s where the content allows, so the payoff lands sooner.
  - These match the channel's own 11/22 first-scene rules.
- Older viewers may swipe for different reasons than younger ones (readability, speech speed, voice naturalness). No source covers this, so A/B test it on our own Shorts.

### Gaps
- I found no controlled study on hooks, loops or length for finance or informational Shorts, and nothing specific to Korean or older audiences. Every percentage uplift above is a self-report.

---

## 4. Why Shorts plateau around 1K on small channels, and why some get near-zero impressions

### Takeaway
The plateau is best explained by YouTube's officially described seed-then-expand-or-taper behaviour. A Short that does well enough with the first pool gets a second, larger pool, but not a third. That points to second-stage signals (retention depth, likes, shares) or a small pool of interested viewers, not a hard cap. Officially confirmed causes of near-zero distribution are narrow: misclassification (non-vertical or over 3 min), Content ID blocks, policy restrictions (spam, reused content) and, possibly, Made for Kids. "300-view jail" and shadowbans are folklore. Same-day multiple uploads have no official support as a cause, but splitting the signal is a plausible theory.

### Cited Findings
- **[OFFICIAL]** YouTube's Creator Insider explanation for Shorts stalling near 1,000 views is the seed-audience test: weak signals mean the Short is no longer pushed wider. The article reads this as either the video not being among the creator's best, or not enough interest in interactions and watch time. — [OnlineMarketing.de](https://onlinemarketing.de/social-media-marketing/erklaerung-shorts-1000-views-stagnation)
- **[3P]** vidIQ calls a stall hitting the "exploit" ceiling after the seed audience shows low retention or high swipe-away. — [vidIQ](https://vidiq.com/blog/post/youtube-shorts-algorithm/)
- **[3P, estimate]** One blog estimates the first test batch at about 100–500 non-subscribers within the first hour or two. It is not a published number. Another claims that posting too many Shorts in one day gives the algorithm a weaker signal on each (unverified). — [ytstudiodesktop](https://www.ytstudiodesktop.com/blog/shorts-getting-less-than-1000-views); [subscribr](https://subscribr.ai/youtube-strategy/youtube-shorts-no-views-fix)
- **[3P case study]** Halving uploads (99 → 50) cut total views about 10.5%, kept watch time flat, and raised views per video by 77%. The authors attribute this to weaker videos no longer competing with strong ones for the same audience. Vendor case study. — [AIR Media-Tech](https://air.io/en/creators-spotlight/half-the-uploads-77-more-views-per-video-entertainment-channel-case)
- **[OFFICIAL] Causes of near-zero reach that YouTube confirms:**
  - Non-vertical (for example 16:9) uploads are classed as long-form and do not compete in the Shorts feed.
  - Shorts of 1–3 minutes with an active Content ID claim, uploaded 15 Oct 2024–24 Sep 2026, were blocked. Newer ones are not automatically blocked.
  - The reused-content policy applies even with the original creator's permission.
  - Deleting and re-uploading may be treated as spam (Sherman 2023, Ritchie reportedly).
  - Sources: [YouTube Help 15424877](https://support.google.com/youtube/answer/15424877?hl=en); [YouTube Help 1311392](https://support.google.com/youtube/answer/1311392?hl=en); [TechCrunch](https://techcrunch.com/2023/08/25/youtube-demystifies-the-shorts-algorithm-views-and-answers-other-creator-questions/); [cut.pro summary](https://cut.pro/en/blog/youtube-shorts-stuck-low-views-2026)
- **[3P, labelled not official by the source]** Videos still processing, private, scheduled or age-restricted; forum advice to wait 72 hours; fixed view walls at 100, 300 or 2,000; "300-view jail" or shadowbans; dead Shorts reviving weeks later; loops being rewarded. cut.pro's audit finds no official basis for any of these, and says the per-video judgment contradicts the jail and shadowban idea. — [cut.pro](https://cut.pro/en/blog/youtube-shorts-stuck-low-views-2026)
- **[3P] Diagnosing zero.** Zero usually means the Short never entered the feed. Check that it appears under the Shorts tab in Studio, check Reach impressions or "shown in feed," and check for claims, restrictions and Made for Kids. — [lilachbullock](https://www.lilachbullock.com/youtube-shorts-view-count-stuck-at-zero/); [sprizzy](https://sprizzy.com/blog/youtube-shorts-0-views/)
- **[OFFICIAL] Diversity.** Sherman said the feed is deliberately kept varied. cut.pro infers that a "topic ceiling" can follow when similar clips compete for the same slots (inference, not official). — [TechCrunch](https://techcrunch.com/2023/08/25/youtube-demystifies-the-shorts-algorithm-views-and-answers-other-creator-questions/); [cut.pro](https://cut.pro/en/blog/youtube-shorts-stuck-low-views-2026)
- **[3P, unconfirmed]** Joos's recency theory (§1) implies the reach window is about 30 days, so Shorts are unlikely to keep climbing late. — [Search Engine Journal](https://www.searchenginejournal.com/youtube-shorts-algorithm-may-now-favor-fresh-over-evergreen/562661/)

### Inferences
- About 200 → about 1,000 → stop looks like two test stages. The ~40% stayed-to-watch is enough to pass the first gate. Average percentage viewed, likes and shares are probably what hold back stage 3. Small seed-pool affinity (an older, niche Korean finance audience) may also cap how far it can spread.
- Possible causes of the rare "3 viewers" Short, roughly in order of plausibility:
  1. Classification or processing: confirm it shows under the Shorts tab, is 9:16 and under 3 minutes.
  2. A policy, label or claim problem (AI-labelled synthetic media is unverified as a factor).
  3. A second upload landing close to another one (for example the "extra" slot at 11:00 after the 08:00 Short), which may split the seed audience. Unverified, but cheap to test by spacing uploads further apart or comparing days with one versus two uploads.
  4. Content the system classifies as too similar to the previous day's Short.
- Do not delete and re-upload stalled Shorts. YouTube staff explicitly warn this can look like spam.

### Gaps
- There is no official statement on same-day multiple uploads, minimum spacing, or whether AI-synthetic labels or "inauthentic/mass-produced" content signals reduce Shorts distribution (as opposed to monetisation). I found no reliable data on how often near-zero Shorts happen for healthy channels.

---

## 5. Moving Shorts viewers to long-form: related video link, pinned comments, clips, trailers, separate channels

### Takeaway
Every source, official or not, says Shorts→long-form conversion is structurally weak. Shorts history is kept out of long-form recommendations, and YouTube's own guide says many Shorts-only viewers "may never click a long video." The related-video link is worth keeping but typically sends well under 1% of Shorts viewers. The methods with the most support are:
- Make the Short a genuine teaser of one specific long video, with a verbal and visual CTA in the last 5 seconds.
- Make sure the long video delivers the promised topic within 5–10 seconds.
- Use "Edit into a Short" or Clips cut from the long-form, which link back automatically.
- Use the same topic, packaging and audience on both sides.
- Treat Shorts mainly as a topic-testing and discovery tool, not a traffic pipe.

Subscribers gained from long-form are worth more than those from Shorts.

### Cited Findings
- **[OFFICIAL] YouTube's playbook** (blog, 14 Jul 2026, "How to convert YouTube Shorts views into long-form channel growth"):
  - Audience segments: Shorts-only viewers "may never click a long video." Context-dependent viewers want clips of specific moments. Exploratory viewers use Shorts to find new channels.
  - Step 1: add a Related video link matched to the viewer's intent (quick tip → full tutorial).
  - Step 2: put a verbal CTA plus visual cues (point at the link, or briefly show the long video's thumbnail) in the final 5 seconds. Clips should still stand alone.
  - Step 3: the long video must deliver the promised topic in its first 5–10 seconds.
  - Optional: vertical or dual-format live streams that appear in the Shorts feed.
  - The post contains no conversion statistics or case studies.
  - Source: [YouTube Blog](https://blog.youtube/creator-and-artist-stories/youtube-related-videos-traffic-guide/)
- **[OFFICIAL] Separate history.** Beaupré: Shorts viewing is not used on the long-form side. YouTube's reason was to stop Shorts-heavy viewers being shown only Shorts, but it also means a Shorts view does not, by itself, warm a viewer up for long-form recommendations. — [vidIQ](https://vidiq.com/blog/post/youtube-shorts-long-form-viewers-algorithm/)
- **[OFFICIAL] Clips and "Edit into a Short."** From a long video's watch page: Remix → Edit into a Short, selecting up to 60 seconds. Shorts made this way link back to the original video. The separate "Video clips" Studio tool adds a "Watch full video" button that continues playing the long-form. — [YouTube Help 15824265](https://support.google.com/youtube/answer/15824265); [vidIQ](https://vidiq.com/blog/post/Clip-youtube-videos-long-to-short/)
- **[3P, secondhand]** Social Media Examiner reports that YouTube said it now recommends a channel's relevant long-form to viewers who have only watched its Shorts. This is not a direct YouTube quote, and it partly conflicts with Beaupré's history separation. — [Social Media Examiner](https://www.socialmediaexaminer.com/how-to-easily-make-youtube-shorts-with-your-longer-videos/)
- **[3P/VENDOR] Related-link click-through.**
  - YouTube does not report related-link clicks as their own traffic source.
  - Creator-tool analyses put the related-link click rate "under 1%", and pinned comments at about 1–3% (unverified).
  - OutlierKit estimates a 100K-view Short sends "only a few hundred" visits, roughly 0.3% (author estimate).
  - Other blogs cite 0.05% at the low end, and some vendors claim 4.5% (method unverifiable).
  - Sources: [ytgrowth](https://ytgrowth.io/blog/shorts-vs-long-form); [OutlierKit](https://outlierkit.com/resources/youtube-shorts-to-long-form/); [subscribr](https://subscribr.ai/youtube-strategy/drive-traffic-shorts-to-long-videos); [klipa](https://klipa.ai/en/blog/convert-shorts-views-long-form-growth_997)
- **[VENDOR] TubeBuddy strategies.** A "flood" approach points many top Shorts at one long video, switching to time-sensitive videos then back to evergreen ones, and A/B tests which long video is "stickiest." No supporting data is given. — [TubeBuddy](https://www.tubebuddy.com/blog/youtube-shorts-related-video-manager-strategy/)
- **[3P] OutlierKit tactics.** Say the long video's exact title aloud in the Short. Pin a comment with the link. Put the Short and the long video in one playlist and add a community post on release day. Use three Shorts on three topics in a week as a topic poll, then make the long video on the winner. — [OutlierKit](https://outlierkit.com/resources/youtube-shorts-to-long-form/)
- **[3P-DATA] Paddy Galloway (2023, 33 channels, 5,400 Shorts).** Long-form converted 22.7 subscribers per 10,000 views and Shorts 16.9. The ranking flips for channels over 1M subscribers, which Galloway attributes to better Shorts and better CTAs. Sourced from his thread, not a published method. — [Threadreader](https://threadreaderapp.com/thread/1646898356419981315.html); [Digital Information World](https://www.digitalinformationworld.com/2023/04/paddy-galloway-decoded-youtube-shorts.html)
- **[3P-DATA, academic] arXiv 2402.18208.** 250 creators with 100K+ subscribers, at least 8 Shorts and 8 long videos each, videos before 31 Dec 2023:
  - Long-form views fell after the first Short overall (mean −743,589, p=0.011).
  - Long-form-focused creators: −920,189, p=0.005.
  - Short-form-focused creators: no significant drop.
  - Only channels over 5M subscribers showed a significant drop.
  - Information/educational channels were least affected.
  - Likes and comments changes were not significant.
  - Source: [arXiv](https://arxiv.org/html/2402.18208v2)
- **[KR, anecdote]** A Korean streamer blog reports that adding replay links and timestamps under Shorts led to 30% of click-through viewers watching 10+ minutes. Single channel, no control group. Korean marketing blogs agree that Shorts views and long-form viewing "move separately," so the Short must create its own reason to keep watching. Some advise not putting the full conclusion in the Short. — [streamhub](https://streamhub.world/ko/streamer-blog/youtube/4367-how-to-use-youtube-shorts-to-drive-traffic-to-your-live-stream-archives-2/); [i-boss](https://www.i-boss.co.kr/ab-6141-69320); [ampm insight](https://inside.ampm.co.kr/insight/59637)
- **[3P-DATA, KR audience]** A Consumer Insight survey, reported in the press, found people in their 60s and older most often watch short-form in sessions under 5 minutes (27%). Those aged 40–60+ relatively prefer 1–2 hour videos. The survey year is unclear. Korean 50s and 60+ use YouTube for news at about twice the 48-country average (Korea Press Foundation, Digital News Report 2025). — [Daum/News](https://v.daum.net/v/20250817073212400); [Wikitree](https://www.wikitree.co.kr/articles/1073271); search summary of KPF report via [segye](https://www.segye.com/newsView/20260622512685?OutUrl=Zum)
- **[3P-DATA, KR blog]** About 74% of Shorts views come from non-subscribers, unsourced. — [tilnote](https://tilnote.io/pages/6a2edb15da0e1b7feb5fe7bd)

### Inferences
- Our 0–2 long-form views per Short matches the official and vendor picture. At about 1,000 views per Short and 0.05–1% click-through, we should expect 0.5–10 clicks, so the link is performing as designed. Our Short volume is simply too small for a link to matter. The bottleneck is long-form's own browse and suggested exposure (thumbnail and title CTR), not the Shorts link.
- Higher-leverage options, in order:
  1. **Clips from long-form** ("Edit into a Short" or Clips, which auto-link). Make them on the day the long video goes live, with a spoken CTA naming the long video's title in the last 5 seconds and the long video's thumbnail shown briefly.
  2. **Withhold the answer.** The Short poses the question or the first of N items and the long video answers it. This fits the channel's 11/6 decision to stop revealing answers early.
  3. **One target long video.** Point all recent Shorts at a single "stickiest" long video instead of many.
  4. **Treat Shorts as topic tests.** Pick long-form topics from Shorts that win on stayed-to-watch (for example tax and reconstruction topics), since those predict long-form CTR.
  5. **Pin a comment** with the long link. Possibly higher click-through than the related link, but unverified.
- An older Korean audience that watches short-form in sub-5-minute sessions yet prefers long videos may be better reached through long-form browse and search than through the Shorts feed. That reinforces long-form packaging (CTR) as the main lever.
- A separate Shorts channel: I found no evidence it helps conversion. Since Shorts history is already kept apart from long-form recommendations, a separate channel would mainly protect long-form audience signals. That matches the arXiv finding of long-form harm mostly in large long-form-focused channels, which does not describe our channel today.

### Gaps
- There is no official YouTube statistic on related-video link CTR or Shorts→long-form conversion rates.
- I found no rigorous case study (with numbers) of a small channel that grew long-form mainly through Shorts.
- There is no data comparing clip-from-long-form Shorts with original Shorts for click-through.
- I found no source on separate Shorts channels and conversion.
- I could not verify the Social Media Examiner claim that YouTube now recommends long-form to Shorts-only viewers against a primary source.
