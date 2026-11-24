# Free sources of platform-wide Trends on Instagram, TikTok and Facebook

Research for [issue #10](https://github.com/sami3ullah/Farsight/issues/10) (map: [#1](https://github.com/sami3ullah/Farsight/issues/1)). Feeds the should-have **Trend (platform-wide)** Insight from [#5](https://github.com/sami3ullah/Farsight/issues/5). Researched 2026-11-24.

Constraints applied: $0, numbers only from deterministic collectors (never typed by an AI), Research Runs execute on the user's home machine (Cloudflare Workers cannot run Python), Competitor collection routes from [#3](https://github.com/sami3ullah/Farsight/issues/3) already exist.

Legend: **[C]** confirmed against a primary source (official docs, project source code, or a live request made for this research, with the method stated). **[U]** uncertain: inferred, vendor claim, or not stated by the owner of the fact.

## Answer in one paragraph

Only TikTok has a free, logged-out, structured source of platform-wide Trends, and it is thin: **TikTok Creative Center** (now part of "TikTok One Creative Suite") returns the **top 3 trending hashtags** per country x industry x period (7/30/90 days) to an anonymous caller, with exact post counts, view counts, a daily 0-100 popularity curve and top creators, from one plain JSON POST that needs no browser. Its trending **songs** list is gone and its **creators** list says "Coming soon"; the full rankings sit behind a login, which would mean automating a logged-in TikTok For Business account against TikTok's "no automated scripts" term. **Instagram** exposes trending audio (up to 50 tracks, US only) and trending reels only inside the mobile app; the only programmatic route is instagrapi's private-API `music_trending`, which needs a logged-in account and carries the highest ban risk, so it is not recommended. The official **Instagram Hashtag Search API** can measure a hashtag Farsight already knows about (top/recent media with likes and comments, 30 hashtags per 7 days) but cannot discover what is trending, and it needs App Review for Instagram Public Content Access. **Facebook** has no platform-wide trend source at all: Trending was removed in 2018, the Inspiration Hub is an in-app creator dashboard, and Meta Content Library is for non-profit researchers only. **Recommendation:** build the Trend (platform-wide) Insight for **TikTok only**, from the anonymous Creative Center hashtag endpoint, fanned out over the Brand's country and industry and all three periods, and enrich candidate sounds and hashtags (found in Competitor Posts) with platform-wide usage counts from TikTok-Api `sound.info()` / `hashtag.info()`. For Instagram and Facebook, rely on the cross-Brand **Trend (tracked Brands)** Insight computed from Posts Farsight already collects, and say plainly in the UI that platform-wide trends are TikTok-only.

## TikTok

### TikTok Creative Center trends (anonymous)

Checked by loading `https://ads.tiktok.com/creative/creativeCenter/trends/hashtag` in headless Chromium with a desktop user agent and recording its network traffic, then replaying the call with `curl` (2026-11-24). [C]

- **URL change:** the old `https://ads.tiktok.com/business/creativecenter/inspiration/popular/hashtag/pc/en` now 301-redirects to `https://ads.tiktok.com/creative/creativeCenter/trends`, titled "TikTok One Creative Suite". The old internal `creative_radar_api/v1/popular_trend/{hashtag,sound,creator}/list` endpoints that older scrapers used now return `{"code":40101,"msg":"no permission"}` (hashtag, creator) or 404 (sound). [C] Any scraper written before this redesign is dead.
- **Endpoint:** `POST https://ads.tiktok.com/CreativeOne/KnowledgeAPI/GetHashtagList`, headers `content-type: application/json` and `agw-js-conv: str`, body `{"timeRange":7,"countryCode":"US","page":1,"limit":20}`. Optional `"industryID":"14000000000"` filters by industry. No cookies, signature or login needed; works from plain `curl`. [C]
- **Anonymous cap:** the server ignores `limit` and returns `pagination: {"hasMore":false,"limit":3,"totalCount":3}`; page 2 is empty. The page shows the same 3 rows and then "View more top hashtags on TikTok - Log in or sign up". [C]
- **Fields per hashtag:** `rankIndex`, `hashtagID`, `hashtagName`, `industryIDs`, `publishCnt` (posts, exact integer), `vv` (video views, exact integer), `popularityCurve` (one point per day, normalised 0-100), `topCreators` (rank, handle, nickname, `followedCnt`, country, TikTok user ID, avatar URL). All numbers are typed JSON, so they fit the "deterministic collector" rule. [C]
- **Periods:** `timeRange` 7, 30 and 90 work; 1, 120 and 180 return nothing. [C]
- **Countries:** US, GB and DE returned data; PK, IN and NL returned nothing. [C] An Apify vendor lists 27 supported hashtag markets (US, GB, FR, DE, IT, ES, AR, AU, BR, CA, CO, EG, ID, IL, JP, KR, MY, MX, PH, SA, SG, ZA, TW, TH, TR, AE, VN) and 15 industries. [U, vendor claim: [data_xplorer/tiktok-trends](https://apify.com/data_xplorer/tiktok-trends)]
- **Industry fan-out:** since the cap is 3 per query, querying each industry separately yields up to 3 x 15 industries x 3 periods = about 135 hashtag rows per country per Run, the Brand's own industry being the most relevant. Example: `industryID 14000000000` gave `#smilecheck`, `#bracescheck`, `#hygienetok`. [C for the filter working; U for the exact industry ID list]
- **Freshness:** a fetch at 2026-11-24 20:00 UTC returned a daily curve ending 2026-11-22 00:00 UTC, so data lags about 2 days. [C]
- **Other tabs:** "Video" shows 4 top videos anonymously (views, creator follower count) with "Go to TikTok One to view more rankings and data". "Creator" shows "Coming soon". The `/trends/song` URL renders the hashtag tab: the trending songs list is gone. [C] An Apify vendor says the same: "TikTok Creative Center no longer shows its Songs and Creators trend lists". [U, vendor] I did not isolate the Video tab's endpoint.
- **Hashtag analytics** (`/trends/hashtag/{name}`) shows only a login dialog when anonymous. [C]
- **Login:** TikTok's guidelines say "a login is not required to access Creative Center" but recommend logging in "to see all features, data, and insights"; Creative Center is described as a free, public resource. [C] [Creative Center Guidelines](https://ads.tiktok.com/help/article?aid=14099). How many rows a logged-in free account sees after the redesign was not verified. [U]
- **Bot detection:** plain headless Chromium with its default user agent got HTTP 403 on the page; a desktop user agent passed. The JSON endpoint itself answered plain `curl`. [C] Rate limits are undocumented; a Run needs at most a few dozen calls, so pace them (1-2 s apart). [U]
- **Terms:** TikTok Terms of Service, section 5: you may not "use automated scripts to collect information from or otherwise interact with the Services" nor "bypass any measures we may use to prevent or restrict access to the Services". [C] [TikTok ToS](https://www.tiktok.com/legal/page/row/terms-of-service/en). Anonymous calls are still automated collection under that wording, but there is no account to lose, and they stay within what TikTok serves publicly. Logging in to get past the 3-row cap would also count as getting around an access restriction and would put a TikTok For Business account at risk. Not recommended.
- **Runs from a home machine:** yes, from any language. The endpoint is plain HTTPS + JSON, so it could even run from a Cloudflare Worker, but Runs execute locally anyway (see [#4](https://github.com/sami3ullah/Farsight/issues/4)), and residential IPs are the safer default. [C for the protocol; U for how TikTok treats Cloudflare IPs]
- **Hosted scrapers:** several Apify actors cover the redesigned Creative Center (for example [automation-lab/tiktok-creative-center-scraper](https://apify.com/automation-lab/tiktok-creative-center-scraper), which uses Playwright and notes "a small public sample per market before login"). They fit inside the $5/month free credit, but they reach the same anonymous data as a direct call, so they add nothing. No maintained open-source scraper for the redesigned pages was found. [U for the search being exhaustive]

### Platform-wide usage counts for a known sound or hashtag

- **TikTok-Api** (davidteather, v7.3.5, 2026-11-14) has `Sound.info()` (calls `https://www.tiktok.com/api/music/detail/`, returns `stats` including the number of videos using the sound), `Sound.videos()` (`/api/music/item_list/`), `Hashtag.info()` (`/api/challenge/detail/`, `stats` with video and view counts) and `Hashtag.videos()` (`/api/challenge/item_list/`). `Trending.videos()` calls `/api/recommend/item_list/`, which is a For You feed for the session, not a platform-wide ranking. [C] [source](https://github.com/davidteather/TikTok-Api/tree/main/TikTokApi/api). Needs an `ms_token` from a browser session and Playwright, as found in #3; no TikTok account login.
- **yt-dlp** returns `track`, `artists` and `album` for every TikTok video it collects (from the video's `music` object), so sounds used by tracked Brands come for free with Post collection. [C] [tiktok.py](https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/extractor/tiktok.py). Its sound and tag extractors are marked not working (see #3).
- **Use:** take sounds and hashtags found in Competitor Posts (or Creative Center), then attach a deterministic platform-wide figure such as "this sound is used in N videos". This is a single snapshot per Run. Measuring growth needs snapshots over time, which the map puts out of scope.

### TikTok official APIs

- **Research API**: academic and not-for-profit only, must be independent of commercial interests (see #3). Not eligible. [C] [Research API](https://developers.tiktok.com/products/research-api/)
- No official public API for Creative Center trends was found. The Creative Center "API" page (`/creative/creativeCenter/tools/api`) is the Symphony generative-video API, not trend data. [C]

## Instagram

| Source | What it gives | Login / account | Ban risk | ToS | Freshness | Filters | Verdict |
|---|---|---|---|---|---|---|---|
| **In-app Trending audio** (Professional dashboard / Your dashboard; arrow icon in Reels) | Up to 50 trending audio tracks; audio page shows reel count | Public IG account, mobile app only | n/a (manual) | Fine for humans | Current | **US only** | Not programmatic. [C] [Help Center](https://help.instagram.com/637936641677566) |
| **Edits app trending reels** | Trending public reels with views, likes, shares; "Use audio" | Edits app (logged in) | n/a (manual) | Fine for humans | Current | None stated | Not programmatic. [C] [Help Center](https://help.instagram.com/2166086880451823) |
| **instagrapi** `music_trending()` / `music_top_trends()` | Raw private-API response from `music/trending/` (trending music candidates) | **Logged-in account always**, emulates the Android app | **Highest**: checkpoints and bans, as found in #3 | Breaks Meta's automated-collection term while logged in | Current | Probably the account's market [U] | Not recommended. [C] [track.py](https://github.com/subzeroid/instagrapi/blob/master/instagrapi/mixins/track.py) |
| **Hashtag Search API** (official) | For a named hashtag: `top_media` and `recent_media` with `caption`, `like_count` (omitted if hidden), `comments_count`, `media_type`, `permalink`, `timestamp`; no `username` | IG Business/Creator account + Meta app; **App Review for Instagram Public Content Access** | None | Sanctioned | From 2027-02-16 `top_media` refreshes about hourly, max 200 results, includes Reels | 30 unique hashtags per rolling 7 days per account | Measures a known hashtag; cannot discover trends. [C] [Hashtag Search](https://developers.facebook.com/docs/instagram-platform/instagram-api-with-facebook-login/hashtag-search), [top_media](https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/ig-hashtag/top-media) |
| **instaloader** hashtag targets | Top posts and post count for a named hashtag | `#hashtag` targets "Require login" | Logged-in account risk | As above | Current | None | Not recommended. [C] [basic-usage.rst](https://github.com/instaloader/instaloader/blob/master/docs/basic-usage.rst) |

Notes:

- The Hashtag Search docs list App Review for Instagram Public Content Access as a requirement. Whether Standard Access (app-role users only, no review) is enough for a single-user app was not confirmed; Meta's access-level page does not mention this feature. [U] Even if it works, it answers "how big is #blackfriday right now", not "what is trending".
- Meta announced a Reels "trends" destination in 2023 showing "top trending songs on Reels and how many times each audio has been used" plus trending topics and hashtags. It lives in the app; no API. [C] [Meta, April 2023](https://about.fb.com/news/2023/04/instagram-reels-trending-audio-and-gifts-updates/)

## Facebook

- **Trending** was removed in June 2018 ("only available in five countries and accounted for less than 1.5% of clicks to news publishers"). [C] [Meta, June 2018](https://about.fb.com/news/2018/06/removing-trending/)
- **Inspiration Hub** (2023) collects "popular reels, hashtags, topics and music" for creators inside the Professional Dashboard. In-app only, logged in, no API; current availability not confirmed. [U for 2026 status] [Meta, June 2023](https://about.fb.com/news/2023/06/helping-creators-get-discovered-and-earn-money-on-facebook/)
- **Graph API** has no hashtag search or trend endpoint for Facebook. Page Public Content Access needs App Review and business verification (see #3). [C via #3]
- **Meta Content Library and API**: free, covers public Facebook and Instagram content, but only accredited not-for-profit academic institutions or not-for-profit research organisations may apply; businesses run for profit do not qualify. [C] [Get access](https://developers.facebook.com/docs/content-library-and-api/get-access)
- **Terms:** Meta Terms 3.2.3 bar accessing or collecting data from Meta Products "using automated means (without our prior permission)". [C] [Meta Terms](https://www.facebook.com/terms.php). *Meta v. Bright Data* (2024) held that logged-out scraping of public data does not breach these terms (see #3); every trend surface above is logged-in only, so that ruling does not help.

**Result:** there is no $0 deterministic source of platform-wide Facebook trends.

## What Farsight can build at $0

1. **TikTok platform-wide hashtags (recommended).** One collector calls `GetHashtagList` anonymously for the Brand's country (if supported), for the Brand's industry and "all industries", for periods 7, 30 and 90 days. Store rank, name, posts, views, curve and fetch time with the Run. About 6 calls per Brand country; up to about 135 rows if fanned over all industries. Label it "TikTok top hashtags (Creative Center, top 3 per category)" so the user knows the sample is small.
2. **Usage counts for sounds and hashtags (recommended, TikTok).** For sounds and hashtags found in tracked Posts (yt-dlp `track`/`artists`, caption hashtags) and Creative Center rows, fetch `music/detail` / `challenge/detail` stats via TikTok-Api and show "used in N videos platform-wide". Deterministic, logged out.
3. **Trend (tracked Brands) on all three platforms.** Already possible from #3 data: hashtags, sounds (TikTok), themes and timestamps shared by several tracked Brands within the Lookback window. This is Farsight's only trend signal on Instagram and Facebook.
4. **Themes and moments.** No platform publishes a free theme feed. Themes come from the AI interpreting collected Posts (the AI labels, deterministic code counts), and calendar moments (Black Friday and so on) can be a static list. Never let the AI produce trend numbers.

Not recommended: logged-in automation of Creative Center, instagrapi trending music, instaloader hashtag targets, any Facebook in-app surface. All need a logged-in account, break the platform's terms and risk the account, for data the user can see by hand in a minute.

## Risks

- **Small sample:** 3 hashtags per category is a hint, not a ranking. The UI must show it as "top 3", never as a full list.
- **Fragility:** the Creative Center was rebuilt in 2026 and every older scraper broke; `GetHashtagList` is undocumented and can change or be locked without notice. Keep it behind its own swappable collector, record the source and fetch time on every figure, and let the Insight disappear cleanly when the call fails.
- **Country gaps:** many markets (for example PK, IN, NL in this test) return nothing. Fall back to US or show "not available for this country".
- **Terms:** anonymous calls are still automated collection under TikTok's terms. Low practical risk (public data, no account, a few calls per Run), but not zero. Revisit before a multi-tenant SaaS.
- **Instagram and Facebook stay blind** to platform-wide trends at $0. That limits the should-have Insight, not any must-have.

## Sources

- TikTok Creative Center trends page and `CreativeOne/KnowledgeAPI/GetHashtagList`: live requests on 2026-11-24 (headless Chromium network capture plus `curl` replay).
- [Creative Center Guidelines](https://ads.tiktok.com/help/article?aid=14099)
- [TikTok Terms of Service (ROW)](https://www.tiktok.com/legal/page/row/terms-of-service/en), section 5
- [TikTok Research API](https://developers.tiktok.com/products/research-api/)
- [TikTok-Api source](https://github.com/davidteather/TikTok-Api/tree/main/TikTokApi/api), v7.3.5
- [yt-dlp tiktok.py](https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/extractor/tiktok.py)
- [Apify: data_xplorer/tiktok-trends](https://apify.com/data_xplorer/tiktok-trends), [automation-lab/tiktok-creative-center-scraper](https://apify.com/automation-lab/tiktok-creative-center-scraper) (vendor claims)
- [Instagram Help: trending audio](https://help.instagram.com/637936641677566), [Edits trending reels](https://help.instagram.com/2166086880451823)
- [Instagram Hashtag Search](https://developers.facebook.com/docs/instagram-platform/instagram-api-with-facebook-login/hashtag-search), [IG Hashtag top_media](https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/ig-hashtag/top-media), [Graph API access levels](https://developers.facebook.com/docs/graph-api/overview/access-levels)
- [instagrapi track.py](https://github.com/subzeroid/instagrapi/blob/master/instagrapi/mixins/track.py), [instaloader basic-usage.rst](https://github.com/instaloader/instaloader/blob/master/docs/basic-usage.rst)
- [Meta: removing Trending (2018)](https://about.fb.com/news/2018/06/removing-trending/), [Meta: Reels trends (2023)](https://about.fb.com/news/2023/04/instagram-reels-trending-audio-and-gifts-updates/), [Meta: Facebook Inspiration Hub (2023)](https://about.fb.com/news/2023/06/helping-creators-get-discovered-and-earn-money-on-facebook/)
- [Meta Content Library: get access](https://developers.facebook.com/docs/content-library-and-api/get-access)
- [Meta Terms](https://www.facebook.com/terms.php), section 3.2.3
