# Free ways to collect Posts from Instagram, TikTok and Facebook

Research for [issue #3](https://github.com/sami3ullah/Farsight/issues/3) (map: [#1](https://github.com/sami3ullah/Farsight/issues/1)). Researched 2026-11-22.

Constraints applied: $0 for V1, numbers only from deterministic collectors (never an AI reading a page), core metrics (likes, comments) required, Lookback window up to three months.

Legend: **[C]** confirmed against a primary source (official docs, project source code, project issue tracker, provider pricing page). **[U]** uncertain: inferred, single-user report, or not stated by the owner of the fact.

## Answer in one paragraph

There is a $0, deterministic route per platform, but no single tool covers all three and every unofficial route breaks every few weeks. **Instagram:** use Meta's official **Business Discovery API** (free, no App Review for an app you own, returns likes, comments, views, caption, timestamp, media URL and follower count for any public Business/Creator account) and keep **instaloader** as the fallback for comment text and fields the API lacks. **TikTok:** there is no usable official API for a commercial app, so use **yt-dlp** (`tiktok:user` playlist; gives views, likes, comments, shares and saves) with **TikTok-Api** as the fallback and for comment text. **Facebook:** the official route (Page Public Content Access) needs App Review plus business verification, so V1 must scrape: Facebook is the weakest platform, with no well-maintained open-source Page-post collector; plan on a Playwright collector that captures Facebook's own GraphQL JSON responses (deterministic, no AI), with yt-dlp for per-video metrics. Run all unofficial collectors from a residential IP (the user's machine), not Cloudflare, and logged out where possible. Apify's free $5/month credit is a legitimate $0 backstop for small volumes on all three platforms.

## Instagram

### Options

| Option | Fields reliably yielded | Login needed | Ban / block risk | Free limits | Status Nov 2026 |
|---|---|---|---|---|---|
| **Business Discovery API** (official Graph API) | caption, media_type, media_product_type (FEED/REELS), timestamp, permalink, like_count, comments_count, view_count, media_url, thumbnail_url; account followers_count, media_count. Hashtags/mentions: parse from caption. | Your own IG professional account linked to a Facebook Page, plus a Meta app (Facebook Login). Targets: any public **Business or Creator** account, by username. | None to the account (sanctioned API). | Free. Platform rate limit (per app user per hour) [U for exact number]. No App Review for an app used only by people with a role on it. | Working [C] |
| **instaloader** 4.16 (open source, Python) | caption, hashtags, mentions, tagged users, typename/format, video_duration, date_utc, likes, comments count, video_view_count, video_play_count, owner followers, media download. Comment text needs login. | Works logged out for profiles and posts, but logged-out is rate-limited hard; comments need a session. | Logged out: IP 429/302 blocks. Logged in: checkpoint / "feedback_required" challenges, account risk. | Free; self-throttled. | Working again since 4.16 (2026-10-26) after a breaking period; new anonymous-failure report 2026-11-21 [C] |
| **yt-dlp** Instagram | Per-post only: description, timestamp, duration, likes, comments, views, media. | Often needs cookies. | As above. | Free. | `instagram:user` (profile listing) is marked `_WORKING = False` in source [C]. Not usable for profile collection. |
| **instagrapi** (private mobile API) | Very rich incl. comments. | Logged in always. | Highest account-ban risk (emulates mobile app). | Free. | Active (3.2.19, 2026-11-19) [C] |
| **Apify** `instagram-post-scraper` | caption, hashtags, mentions, type, timestamp, likesCount (-1 if hidden), commentsCount, videoViewCount, videoPlayCount, videoDuration, latestComments, media URLs, ownerUsername. | No (provider handles it). | None to you. | $5 free credit / month, no card; $2.70 per 1,000 results on Free plan => roughly 1,800 posts / month. | Working [C] |

### Key facts

- Business Discovery requires both querying and target accounts to be Business or Creator accounts; age-gated accounts return nothing; `media_url` is omitted for video with copyrighted/licensed audio and for reels whose owner disabled downloads. [C] [business_discovery reference](https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/ig-user/business_discovery)
- Token needs `instagram_basic`, `instagram_manage_insights`, `pages_read_engagement`. [C] same page.
- `view_count` is "Available for Business Discovery API only"; `like_count` is omitted when the owner has hidden like counts; owners can hide likes, comments, views, reposts and shares. [C] [IG Media reference](https://developers.facebook.com/docs/instagram-platform/reference/instagram-media)
- Standard Access is automatically granted and needs no App Review, but only works for users with a role on the app. [C] [Access levels](https://developers.facebook.com/docs/graph-api/overview/access-levels). For single-user V1 this is enough; a multi-tenant SaaS later needs Advanced Access + App Review + business verification.
- Business Discovery calls fall under Platform rate limits, not the Business Use Case formula. [C] [Rate limiting](https://developers.facebook.com/docs/graph-api/overview/rate-limiting)
- Not available from Business Discovery: comment text, shares, saves, duration [U: not listed]. Saves are never public on Instagram. Duration can be read deterministically from the downloaded media (ffprobe) when `media_url` is present.
- instaloader docs: cloud, VPN and proxy IPs "might be subject to significantly stricter limits for anonymous access"; logged-in access "do not seem to be affected". [C] [troubleshooting.rst](https://github.com/instaloader/instaloader/blob/master/docs/troubleshooting.rst)
- instaloader 4.16 (2026-10-26) "Fix Profile.get_posts() when logged in / when not logged in". [C] [release](https://github.com/instaloader/instaloader/releases/tag/v4.16). Users confirm 4.16 fixed it ([#2794](https://github.com/instaloader/instaloader/issues/2794)); one user reports anonymous 429 errors "every 6 posts" and 302s across several profiles. [U, single report]. Open: anonymous post-metadata failure ([#2806](https://github.com/instaloader/instaloader/issues/2806), 2026-11-21), reels listing broken ([#2797](https://github.com/instaloader/instaloader/issues/2797)), login/cookies broken ([#2792](https://github.com/instaloader/instaloader/issues/2792)), "Is Instaloader still working reliably in 2026? Persistent 429" ([#2786](https://github.com/instaloader/instaloader/issues/2786)).
- `Post.get_comments()` raises `LoginRequiredException` without login. [C] instaloader `structures.py`.

### Lookback (3 months)

Business Discovery: page through the `media` edge with `after` cursors (no `next` link is returned; build it from cursors) until `timestamp` is older than the window. [C] for cursor behaviour. instaloader: `get_posts()` is newest-first, stop at the window edge; pinned posts (`is_pinned`) can be out of order. Feasible for both; for very active accounts (100+ posts / 3 months) anonymous instaloader will hit 429s.

## TikTok

### Options

| Option | Fields reliably yielded | Login needed | Ban / block risk | Free limits | Status Nov 2026 |
|---|---|---|---|---|---|
| **yt-dlp** `tiktok:user` + `TikTokIE` | description (caption; hashtags/mentions parsed from it), timestamp, duration, view_count (play_count), like_count (digg), comment_count, repost_count (share), **save_count (collect)**, uploader, media download. No comment text. | No. Cookies optional (must match browser user-agent, [#18045](https://github.com/yt-dlp/yt-dlp/issues/18045)). | IP-level blocks ("Unexpected response from webpage request"); no account at risk when logged out. | Free. | Working, with intermittent failures (see below) [C] |
| **TikTok-Api** (davidteather, v7.3.5 2026-11-14) | User videos with full stats, comments text, follower count. | Needs an `ms_token` cookie from a browser session; runs Playwright. | `EmptyResponseException` = TikTok detected a bot; README suggests proxies. | Free (proxies cost money). | Active [C] |
| **Official Research API** | Rich. | n/a | n/a | Free | **Not eligible**: academic / not-for-profit only, must be "independent of commercial interests". [C] |
| **Official Display API** | A creator's own videos via their OAuth consent. | The creator's own login. | None. | Free | Only useful for the Brand's own account, not Competitors [U on exact scope]. |
| **Apify** `clockworks/tiktok-scraper` | text, diggCount, shareCount, playCount, collectCount, commentCount, authorMeta.fans (followers), media. | No. | None to you. | $5/month credit; "from $1.70 / 1,000 results" (free-plan rate likely higher [U]). | Working [C] |
| `drawrowfly/tiktok-scraper` | - | - | - | - | Dead (last push 2023) [C] |

### Key facts

- yt-dlp source maps TikTok `stats` to `view_count`, `like_count`, `repost_count`, `comment_count`, `save_count`. [C] [tiktok.py](https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/extractor/tiktok.py). Sound, effect and tag extractors are `_WORKING = False`; user extractor is working.
- Open reliability issues: user extractor sometimes "unable to extract the secondary user ID" ([#17500](https://github.com/yt-dlp/yt-dlp/issues/17500)); a commenter scraping ~23 accounts hourly sees roughly one failure every 3 runs [U, single report]. Several "Unexpected response from webpage request" breakages in Aug-Sep 2026 were fixed in releases ([#17403](https://github.com/yt-dlp/yt-dlp/issues/17403) etc., closed). Latest release 2026.10.26. [C]
- TikTok Research API eligibility: academic institutions (US, EEA, UK, CA, CH), EU not-for-profits, Brazil youth-safety research; applicants must be non-commercial. [C] [Research API](https://developers.tiktok.com/products/research-api/)
- Follower count: available from TikTok-Api or the profile page JSON; yt-dlp exposes `channel_follower_count` only in some paths [U].

### Lookback (3 months)

`yt-dlp --flat-playlist` on `https://www.tiktok.com/@handle` lists the full video history; `--dateafter` or stopping on `timestamp` bounds it. Achievable [C for capability; volume limits U].

## Facebook

### Options

| Option | Fields reliably yielded | Login needed | Ban / block risk | Free limits | Status Nov 2026 |
|---|---|---|---|---|---|
| **Graph API Pages** (own Page) | Full post data and insights for Pages you manage. | Page admin token. | None. | Free. | Working, but only the Brand's own Page [C] |
| **Page Public Content Access** (official, competitor Pages) | Page feed, posts, public comments. | Meta app. | None. | Free | Requires **App Review and business verification**, "may also need to sign additional contracts". Realistic for a company later, not for V1. [C] |
| **Meta Content Library** | Rich | - | - | - | Researchers only [U, not re-verified this session] |
| **yt-dlp** Facebook | Per video/reel URL: description, timestamp, duration, like_count, view_count, sometimes comment_count. No Page post listing. | Usually no for public video. | Low (per URL). | Free | Working with open breakages: [#17906](https://github.com/yt-dlp/yt-dlp/issues/17906) "Breaking change with videos" (2026-10-24), [#18003](https://github.com/yt-dlp/yt-dlp/issues/18003) (2026-11-06) [C] |
| `kevinzg/facebook-scraper` | - | - | - | - | Effectively dead: last push 2024-06; "Example Scrape does not return any posts" ([#1130](https://github.com/kevinzg/facebook-scraper/issues/1130)) [C] |
| `facebook-gql-scraper` (XD-MHLOO, 67 stars, pushed 2026-11-19) | Profiles, posts, comments, reactions via Facebook's internal GraphQL; auto-rediscovers doc IDs. | Anonymous mode ("strict rate limits; results may be incomplete") or cookie session. | Logged-in: account risk. | Free | Active but young, small, unproven [U] |
| **Playwright collector** (own code) capturing Facebook's GraphQL JSON responses while a headless browser scrolls a Page | Whatever the Page UI loads: text, time, reaction counts, comment count, share count, video views. | Logged out hits a login wall after some scrolling [U]; logged in is more complete. | Logged-in account at risk; IP blocks. | Free | Feasible; must be built and maintained by us [U] |
| **Apify** `facebook-posts-scraper` | text, time, likes, reaction breakdown, comments, shares, viewsCount, top comments. | No. | None to you. | Free plan covers "up to 1,000 posts (700 with the date filter)" per month at $5/1,000. [C] | Working [C] |

### Key facts

- PPCA: "requires successful completion of the App Review process", "only available with business verification", readable data includes "business metadata, public comments and posts". [C] [PPCA](https://developers.facebook.com/docs/features-reference/page-public-content-access)
- Facebook has no healthy community collector comparable to instaloader or yt-dlp. Any V1 Facebook collector is either our own Playwright + JSON-capture code or a young third-party library. Treat Facebook as the highest-maintenance platform.

### Lookback (3 months)

Depends on scrolling the Page timeline; three months is feasible for normal Pages if logged in, uncertain logged out because of the login wall [U]. Apify's date filter handles it directly.

## Cross-cutting findings

### Residential vs data-centre (Cloudflare) IPs

- Instagram explicitly treats cloud/VPN/proxy IPs more strictly for anonymous access (instaloader docs) [C]. yt-dlp issues show Instagram IP bans and sandbox environments failing where home machines work ([#17070](https://github.com/yt-dlp/yt-dlp/issues/17070), [#17156](https://github.com/yt-dlp/yt-dlp/issues/17156)) [C]. TikTok-Api's README recommends residential proxies against bot detection [C].
- Cloudflare Workers also cannot run Python tools like instaloader or yt-dlp natively. Implication: **unofficial collectors should run on the user's own machine (residential IP)**, and the official Instagram API can run anywhere including Cloudflare. This feeds the Collection architecture and hosting tickets.

### Terms of service and legal exposure

- All three platforms' terms prohibit automated collection without permission (Meta: no automated collection; TikTok: similar) [U: terms text not re-fetched this session].
- *Meta v. Bright Data* (N.D. Cal., 23 Jan 2024, Judge Chen): Meta's terms bind logged-in **users**, so logged-off scraping of public data did not breach Facebook or Instagram terms; the court did not rule on logged-in scraping. Meta later dropped the claim [U on dismissal details]. Persuasive in the US only, specific to Meta's terms. [C for holding via multiple law-firm write-ups, e.g. [Farella Braun + Martel](https://www.fbm.com/business-litigation/publications/major-decision-affects-law-of-scraping-and-online-data-collection-meta-platforms-v-bright-data/), [TechCrunch](https://techcrunch.com/2024/01/24/court-rules-in-favor-of-a-web-scraper-bright-data-which-meta-had-used-and-then-sued)]
- Practical rule: prefer official API, then logged-out scraping of public data, and treat logged-in scraping as a last resort with a throwaway account (account loss is the main risk, plus contract exposure). Collect public business-account data only; avoid storing personal data of commenters beyond what an Insight needs (GDPR exposure if EU users) [U, not legal advice].

### Deterministic numbers

Every option above yields metrics as typed JSON fields (official API JSON, yt-dlp info dict, instaloader properties, GraphQL responses captured by Playwright, Apify datasets). None requires an AI to read numbers. The one pattern to avoid is "AI agent browsing" that reads counts off rendered pages: it violates the reliability principle and gains nothing, because the same page already loads the numbers as JSON. Hidden metrics come back as absent (Business Discovery omits `like_count`) or `-1` (Apify): store them as unknown, never estimate.

### Free data-provider tiers

- **Apify**: $5 usage per month, no card, unused credit expires monthly. [C] [pricing](https://apify.com/pricing). Enough for a pilot (~1,800 IG posts, or ~1,000 FB posts, or a mix) per month. Recurring, so it fits the $0 rule.
- **ScrapeCreators**: 100 free credits plus up to 1,200 claimable; credits do not expire; not monthly. Trial-sized only. [C] [scrapecreators.com](https://scrapecreators.com/)
- Others (RapidAPI wrappers, EnsembleData trials) not evaluated in depth [U].

## Recommendation per platform (V1, $0)

| Platform | Primary | Fallback | Main risk |
|---|---|---|---|
| Instagram | Business Discovery API (official, free, Standard Access) | instaloader 4.16+ logged out on residential IP (and logged-in throwaway for comment text); Apify free credit | Target must be Business/Creator; no comment text, shares or saves from the API |
| TikTok | yt-dlp `tiktok:user` on residential IP, logged out | TikTok-Api (comments, followers); Apify free credit | Breakages every few weeks; pin and auto-update yt-dlp |
| Facebook | Own Playwright collector capturing GraphQL JSON (or facebook-gql-scraper after a spike) + yt-dlp for video metrics | Apify free credit (~1,000 posts/month) | No maintained OSS; login wall; highest maintenance |

Design implications: put every collector behind one interface per platform with swappable implementations, record which collector produced each figure, and surface collector failures as partial Run failures rather than estimated values.

## Open questions (need a spike)

1. Business Discovery exact Platform rate limit per hour, and whether Reels `view_count` is populated for all Competitor accounts.
2. How far logged-out Facebook Page scrolling gets before the login wall, and whether facebook-gql-scraper returns reaction/comment/share counts reliably.
3. Whether Instagram now exposes public share counts on Reels in its web JSON.
4. Sustained throughput of yt-dlp TikTok and anonymous instaloader for ~10 Profiles x 3 months from one home IP.
