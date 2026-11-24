# Do the free collectors hold up against real Profiles?

Spikes for [Do the free collectors hold up against real Profiles?](https://github.com/sami3ullah/Farsight/issues/9), run 2026-11-24 from a residential connection in Germany (EU cookie consent applies), logged out everywhere, Lookback window three months.

Spike scripts are in `spikes/` on this branch; raw outputs are in `spikes/out/*.json`. This is throwaway code, not product code.

**Profiles tested (10 Brands x 3 platforms):** Nike, Gymshark, Duolingo, Glossier, Red Bull, Starbucks, Ryanair, Liquid Death, Fenty Beauty, Netflix.

**Tool versions:** instaloader 4.16, yt-dlp 2026.11.23, facebook-gql-scraper 0.11.1, Playwright 1.65.2 (Chromium headless shell).

## Results table

| # | Collector | Profiles OK | Reaches 3 months? | Fields that came back | Blocking seen | Verdict |
|---|---|---|---|---|---|---|
| 1 | **Instagram Business Discovery API** | _pending: needs the user's Meta app (checklist below)_ | - | - | - | **Open** |
| 2 | **instaloader 4.16, logged out** | 0 / 10 | No | Profile only (followers). The Post list returns shortcodes only; every Post metadata call failed | `Rate limit exceeded` (code 1675004) on the **first** Post call, still in force 20+ min later | **Fails.** Not a usable fallback |
| 2b | Instagram web, logged-out browser (extra) | 10 / 10, but shallow | No | Profile grid: 12 Posts, then a sign-up wall. Reels tab: exactly 12 Reels with exact `like_count`, `comment_count`, `play_count`, but **no post date** | No 429s; hard sign-up wall after 12 items | **Fails** for a Lookback window; could only check "latest 12" |
| 3 | **yt-dlp `tiktok:user`, logged out** | 9 / 10 full, 1 aborted after 190 Posts | **Yes** (all 10) | views, likes, comments, shares (`repost_count`), saves, caption, timestamp, track: 100%. Duration 99.4% (missing on photo Posts). No follower count, no parsed tags | None across 963 Posts in about 17 min. One unavailable video (status 10101) aborted the Netflix playlist | **Holds up.** See the rounding caveat |
| 4a | **facebook-gql-scraper, anonymous** | 8 / 10 (Red Bull, Liquid Death: "No profile found") | Yes (pages deep: up to 300 items) | comment count: 100%. Reactions and date: about 70% (missing on all Reels). **Share count: 0%.** Text: mostly empty | None, but slow (up to 6 min per Page) | **Partial.** Good lister, bad metrics source |
| 4b | **Own Playwright collector, logged out (Page feed)** | 8 / 10 had Posts (Nike's Page dormant since 2025-09; Liquid Death unavailable logged out) | **No**: login wall after 2 scrolls, 12-21 Posts per Page, about 1-9 weeks back | Exact reactions, comments, shares, video views per Post, from Facebook's own JSON | Login wall, no IP block | **Partial.** Exact metrics, shallow |
| 4c | Own Playwright, one Post URL at a time (extra) | 3 / 3 tried | n/a (per Post) | Normal Post: exact reactions 3,509, shares 322, comments 277. Reel page: exact reactions (`unified_reactors` 24,118) and publish time, **no share or comment count** | None in a handful of loads | **Promising**, needs a volume test |
| 5 | **Instagram Reel share counts in web data** | 10 / 10 checked | n/a | No share, reshare, repost or send count key anywhere in logged-out page JSON or GraphQL responses | - | **No.** Not exposed |

## Findings per question

### 1. Business Discovery API: pending

This part needs your own Meta app, Instagram Business account and Facebook Page, so it is still open. `spikes/business_discovery_spike.py` is ready. It pages each Profile's `media` edge back three months and records field coverage, including whether Reels carry `view_count`. Then it burns 40 cheap calls and logs the `x-app-usage` header, so the real hourly ceiling can be extrapolated. See the checklist at the end.

### 2. instaloader 4.16 logged out: fails

- `Profile.from_username` works and returns followers.
- `get_posts()` gets a list of nodes that hold only shortcode, caption and type. There are no timestamps or metrics. instaloader then fetches each Post's metadata (doc_id `27128499623469141`, web API). From this IP, every one of those calls returned `{"errors":[{"message":"Rate limit exceeded","code":1675004}]}`. That includes the very first call of the run, and the limit still held 20+ minutes later. It matches the open instaloader issue #2806 (anonymous Post-metadata failure).
- A real logged-out browser fares no better on depth: Instagram shows 12 grid items and then a "See photos, videos and more" sign-up dialog.
- **Implication:** Instagram has no logged-out $0 route to a three-month Lookback window. Unless Business Discovery holds up, the only remaining options are logged-in scraping (against Meta's terms, and the account is at risk) or Apify's free credit.

### 3. yt-dlp on TikTok: holds up, with caveats

- **963 Posts across 10 Profiles** in about 17 minutes, with no blocking. Red Bull hit the spike's 200-Post cap inside the window.
- **Rounding:** TikTok's public stats are **rounded to the nearest 100 at or above 10,000**. All 40 sampled view counts at or above 10K end in 00, and so do all likes, shares and saves at or above 10K (for example 7,100,000 views). Below 10K the counts are exact. A single-video fetch gives the same rounded numbers, so this is TikTok's own value, not a yt-dlp artefact. The values are still deterministic, so they work for Baseline comparisons, but the UI must not imply exactness above 10K.
- **Follower count** is not in yt-dlp's entries. The Profile page HTML has `followerCount` (one plain HTTP GET), also rounded (18,600,000).
- **Fragility:** one unavailable video (status 10101) raised an error and aborted Netflix's whole playlist. A collector must skip bad entries per Post, not fail the Profile.
- yt-dlp warns that it wants an impersonation target (`curl_cffi`). Installing it should make the collector more robust against TikTok's bot checks.
- Hashtags are not returned as a field. Parse them from the caption, as the Notes already plan.

### 4. Facebook: no single route is enough; a hybrid may be

- **Logged-out Page feed (browser):** the EU cookie dialog must be dismissed first. Without that, nothing loads. After about 2 scrolls a "See more on Facebook" login wall appears and loading stops, at **12-21 Posts per Page**. For active Pages (Red Bull, Ryanair) that is only 2-3 days. For quieter Pages (Starbucks, Fenty Beauty) it is up to about 9 weeks. The Posts that do load come with exact reactions, comments, shares and video views in Facebook's GraphQL/JSON.
- **facebook-gql-scraper, anonymous:** pages far back without hitting a wall (up to 300 items), but:
  - it yields **media items, not Posts**: each photo of an album is a separate item with its own reactions, so item counts overstate Posts by roughly 3-5x;
  - Reels come back with comment count only, no date and no reactions (the date is reachable via the parent Post);
  - **share count is never returned anonymously**, and the parent Post's reaction count is also null;
  - username lookup failed outright for 2 of 10 Pages.
- **Per-Post URL (browser):** a logged-out load of a single Post URL returns exact reactions, shares and comments. A Reel URL returns exact reactions and the publish time, but no shares or comments. yt-dlp adds Reel `view_count` and duration. Comments are available from the gql lister.
- **Pages unavailable logged out:** Liquid Death's Page shows "This content isn't available right now" logged out (probably age-gated or a different slug). Some Competitors may not be collectable logged out at all.
- **Implication:** a hybrid is plausible. The gql scraper (or our own GraphQL calls) lists Post ids and dates for the full window. A browser then loads each Post URL for exact metrics. Reel shares stay unknown. The cost is one page load per Post (about 5-10 s), so 10-30 min per active Page for three months. The block risk at that volume is **untested**.

### 5. Reel share counts on Instagram web: not exposed

Across 10 Profiles' Reels tabs and an individual Reel page (logged out), the JSON carries `like_count`, `comment_count` and `play_count`, plus a `like_and_view_counts_disabled` flag. It has no share, reshare, repost or send count field. Reel shares remain unavailable for Instagram, as the earlier research assumed.

## What this changes for the map

- The Instagram fallback in the earlier collection research (instaloader logged out) **does not work**. Instagram now rests entirely on Business Discovery, so its pending result decides the whole Instagram route.
- TikTok via yt-dlp is confirmed, with two product-visible rules: counts at or above 10K are rounded to 100s, and follower counts need a separate Profile-page fetch.
- Facebook needs a designed hybrid collector (lister plus per-Post fetch), or a decision to accept a shallow window or fewer metrics. The per-Post volume test is a natural follow-up question.

## Checklist: Business Discovery setup (for the user)

You need: an Instagram **professional** account (Business or Creator) linked to a **Facebook Page**, and a Meta developer app. A fresh throwaway Instagram account is fine. It only queries; it never posts.

1. **Instagram professional account:** Instagram app → Settings → *Account type and tools* → *Switch to professional account* → pick Business (or Creator).
2. **Facebook Page:** create one at facebook.com/pages/create if you have none (any name and category).
3. **Link them:** Page → Settings → *Linked accounts* → Instagram → *Connect*, and log in with the Instagram account from step 1.
4. **Developer account:** developers.facebook.com → *Get started* (verify with phone or email if asked).
5. **App:** *My Apps* → *Create app* → pick the use case for managing Instagram with Facebook Login (or *Other* → *Business*) → finish. Leave it in **Development** mode. No App Review is needed because you have a role on the app.
6. **Token:** developers.facebook.com/tools/explorer → select your app → *User Token* → add permissions `instagram_basic`, `instagram_manage_insights`, `pages_show_list`, `pages_read_engagement`, `business_management` → *Generate Access Token* → in the dialog, tick your Page and Instagram account.
7. **Save it:** paste the token into `spikes/.fb_token` in the `farsight-spikes` worktree (gitignored). Do not paste it into chat or an issue.
8. Tell the agent it is there. The agent runs `python spikes/business_discovery_spike.py` and fills in row 1.
