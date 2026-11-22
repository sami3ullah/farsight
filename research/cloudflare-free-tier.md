# What can Cloudflare's free tier host for Farsight?

Research for issue #4 (parent map: #1). Sources checked 2026-11-22 against developers.cloudflare.com and the platforms' own terms. Limits change; re-check the linked pages before building.

## Answer

Cloudflare Workers Free can host Farsight's **web app, API, database and media store** for a single pilot brand at $0. It **cannot host a Research Run's collection and AI work**:

1. **AI via the `claude`/`codex` CLI cannot run on Cloudflare free.** Workers cannot spawn processes (`node:child_process` is a non-functional stub), and Containers - the only Cloudflare product that runs arbitrary binaries - requires Workers Paid.
2. **10 ms CPU per invocation and 50 external subrequests per invocation** on Free make a multi-minute, many-posts run fragile at best. It is only feasible by chopping it into hundreds of tiny Workflow steps, and even then daily caps (3,000 Workflow steps/day, 10 browser-minutes/day) bound it to a few runs per day.
3. **Collecting from Cloudflare egress is likely to be blocked or throttled** by Instagram, TikTok and Facebook (inference, see below), and every Worker subrequest is stamped with a `CF-Worker` header naming the owning zone.

Recommended topology to keep $0: **Cloudflare hosts the UI, API, D1 and R2; the Research Run executes on the user's own machine** (residential IP, logged-in CLI), then pushes Posts, metrics and media into Cloudflare. This should feed the hosting-topology and tech-stack tickets (#7 is blocked by this one).

## Product table (Workers Free)

| Product | Free-tier quotas and limits | Free? | Fits a Research Run? |
|---|---|---|---|
| **Workers** | 100,000 requests/day; **10 ms CPU** per HTTP request and per Cron invocation; no wall-time limit on HTTP while the client stays connected; `waitUntil` adds at most 30 s; **50 external subrequests/request**, 1,000 to Cloudflare services; 128 MB memory; 6 simultaneous outbound connections; 100 Workers/account; 64 MiB script [1] | Yes | Serving UI/API: yes. Running collection: no - 10 ms CPU and 50 fetches per invocation. |
| **Pages** | 500 builds/month, 1 concurrent build, 20 min build timeout, 20,000 files/site, 25 MiB/asset, 100 custom domains/project, 100 projects; Functions count against Workers quotas [2] | Yes | Static front end: yes. Functions have Workers limits. |
| **D1** | 10 databases, **500 MB per database**, 5 GB total; 5 M rows read/day, 100,000 rows written/day; 50 queries per Worker invocation; 30 s max query; 2 MB row; 100 bound params [3][4] | Yes | Yes for Brands, Profiles, Posts, metrics, Runs at pilot scale. 500 MB/DB is the ceiling to watch. |
| **R2** | 10 GB-month storage, 1 M Class A ops/month, 10 M Class B ops/month, **egress free**; Standard storage only [5] | Yes, but needs an "R2 subscription" via a checkout flow [6] | Images and thumbnails: yes. Many videos will hit 10 GB quickly. Checkout flow may ask for a payment method (not confirmed in docs). |
| **KV** | 100,000 reads/day, **1,000 writes/day**, 1,000 deletes/day, 1,000 lists/day, 1 GB storage; 1 write/s per key; 25 MiB value [4][7] | Yes | Config/cache only. 1,000 writes/day rules it out for Posts. |
| **Queues** | 10,000 operations/day; 24 h retention (fixed); 128 KB message; batch 100; consumer wall time 15 min [4][8] | Yes | Possible as a fan-out, but CPU/subrequest limits per consumer invocation still apply (see note A). |
| **Durable Objects** | SQLite-backed only on Free; 100,000 requests/day; 13,000 GB-s duration/day; 5 M rows read, 100,000 written/day; 5 GB total storage; alarm handlers 15 min wall time; 100 classes [4][9] | Yes (SQLite only) | Good fit for run state / progress streaming (WebSockets). Not for heavy CPU. |
| **Workflows** | 100,000 requests/day (shared with Workers); **10 ms CPU per step**; unlimited wall clock per step; **1,024 steps/workflow**; **3,000 steps/day**; 100 MB state/instance, 1 MiB per step result; 100 concurrent instances; 50 subrequests per step; 3 day retention [4][10] | Yes | The only Free-tier shape for a long run, but each step must fetch a few items with under 10 ms CPU, and 3,000 steps/day caps volume. |
| **Browser Rendering** (now "Browser Run") | **10 browser-minutes/day**; 3 concurrent browsers; 1 new browser per 20 s; 60 s idle timeout; Quick Actions 1 request per 10 s; 429 after daily cap until next UTC day [11] | Yes | No. 10 minutes/day is a fraction of one run. Requests are also signed as Cloudflare bot traffic [12]. |
| **Containers** | No Free allocation; Paid includes 25 GiB-h memory, 375 vCPU-min, 200 GB-h disk per month [13] | **No - Workers Paid only** [14] | Would be the way to run the CLI in the cloud, but violates $0. |
| **Cron Triggers** | 5 per account; 10 ms CPU; 15 min wall time [1] | Yes | Not needed (V1 has no scheduler). |
| **Workers AI** | 10,000 Neurons/day; operations fail when exceeded [15] | Yes | Small summaries only; not a substitute for Claude/Codex-quality Insights. |
| **Custom (sub)domain** | Needs an active Cloudflare zone you own; hostname must not already have a CNAME [16] | Docs list no plan restriction | Yes, e.g. `farsight.<your-domain>` on Workers Custom Domains or Pages custom domains. |
| **Workers Logs** | 200,000 events/day, 3 day retention [4] | Yes | Enough for a pilot. |

Note A: the Queues limits page lists consumer CPU as "30 s default, up to 5 min" for both plans [8], while the Workers limits page gives Free a 10 ms CPU limit per invocation [1]. Similarly the Durable Objects page lists 30 s CPU without a plan split [9]. Treat the Free CPU budget as 10 ms until tested; the pages do not resolve it.

Note B: the Durable Objects page gives 10 GB per SQLite object in the table but 1 GB for Free in its FAQ [9]. Plan for 1 GB.

## What forces Workers Paid ($5/month)

- Running the `claude`/`codex` CLI or any binary in Cloudflare (Containers) [14].
- More than 10 ms CPU per invocation or more than 50 external fetches per invocation [1].
- More than 10 browser-minutes/day of headless browsing [11].
- More than 3,000 Workflow steps/day, or a D1 database above 500 MB [3][10].
- More than 10,000 Workers AI Neurons/day [15].
- KV writes above 1,000/day or more than 100,000 requests/day [1][7] (unlikely for one pilot brand).

## Does a Research Run fit the free tier?

**Not as one job, and not with the planned AI access.**

- **Wall clock is not the problem.** HTTP requests have no wall limit while connected, Workflow steps have unlimited wall clock, and Queue consumers / DO alarms get 15 min [1][10].
- **CPU and fan-out are.** 10 ms of CPU covers little more than parsing one modest JSON response; 50 external fetches per invocation is below one run of "many Posts and media". A Workflow can chain up to 1,024 steps, but at 3,000 steps/day [4] a run of, say, 5 Competitors x 3 platforms x 50 Posts with media would use most of a day's budget.
- **AI is the blocker.** V1's AI path is the user's logged-in `claude`/`codex` CLI. Workers cannot spawn processes [17], Containers are Paid-only [14], and calling the Anthropic/OpenAI API needs API keys, which #1 defers. Workers AI's 10,000 Neurons/day [15] is free but a different, weaker model set.
- **Media analysis** (transcripts, on-screen text) needs CPU and AI beyond these budgets.

Conclusion: the Research Run should run locally (a local worker process or CLI command) and sync results to the hosted app. Cloudflare then only serves reads plus small writes, comfortably inside free quotas.

## Will Instagram/TikTok/Facebook block Cloudflare egress?

**Likely yes for unauthenticated scraping; treat it as unreliable.** This is inference: no platform publishes an IP blocklist.

- Every Worker `fetch()` carries a `CF-Worker` header set to the owning zone [18], so the target can identify and filter Worker traffic. Browser Rendering requests carry non-removable `cf-brapi-*` headers and Web Bot Auth signatures proving they come from Cloudflare [12].
- Workers egress from Cloudflare's shared datacenter network, not a residential IP. Instaloader's maintainers report that Instagram applies "stricter limits for anonymous access" from shared-IP services such as cloud, VPN and proxies [19].
- TikTok's Terms forbid using "automated scripts to collect information from or otherwise interact with the Services" [20]. Meta's Instagram Terms and Automated Data Collection Terms likewise require permission for automated collection (pages did not render for direct quoting; check [21]).
- Logged-in sessions reportedly fare better [19], but running a personal session from Cloudflare IPs risks account checkpoints.

Practical consequence: collect from the user's machine (residential IP, the same machine that runs the CLI). This reinforces the local Research Run topology above.

## Sources

1. Workers limits - https://developers.cloudflare.com/workers/platform/limits/
2. Pages limits - https://developers.cloudflare.com/pages/platform/limits/
3. D1 limits - https://developers.cloudflare.com/d1/platform/limits/
4. Workers pricing (free quotas for Workers, KV, Queues, Workflows, D1, DO, Logs) - https://developers.cloudflare.com/workers/platform/pricing/
5. R2 pricing - https://developers.cloudflare.com/r2/pricing/
6. R2 get started ("You need a Cloudflare account with an R2 subscription") - https://developers.cloudflare.com/r2/get-started/
7. KV limits - https://developers.cloudflare.com/kv/platform/limits/
8. Queues limits - https://developers.cloudflare.com/queues/platform/limits/
9. Durable Objects limits - https://developers.cloudflare.com/durable-objects/platform/limits/
10. Workflows limits - https://developers.cloudflare.com/workflows/reference/limits/
11. Browser Rendering limits - https://developers.cloudflare.com/browser-rendering/limits/
12. Browser Rendering automatic request headers - https://developers.cloudflare.com/browser-rendering/reference/automatic-request-headers/
13. Containers pricing - https://developers.cloudflare.com/containers/pricing/
14. Containers overview ("Available on Workers Paid plan") - https://developers.cloudflare.com/containers/
15. Workers AI pricing - https://developers.cloudflare.com/workers-ai/platform/pricing/
16. Workers Custom Domains - https://developers.cloudflare.com/workers/configuration/routing/custom-domains/
17. Workers Node.js compatibility (`node:child_process` is a stub) - https://developers.cloudflare.com/workers/runtime-apis/nodejs/
18. Cloudflare HTTP headers (`CF-Worker`) - https://developers.cloudflare.com/fundamentals/reference/http-headers/
19. Instaloader troubleshooting - https://instaloader.github.io/troubleshooting.html
20. TikTok Terms of Service, section 5 - https://www.tiktok.com/legal/page/row/terms-of-service/en
21. Instagram Terms of Use - https://help.instagram.com/581066165581870 ; Meta Automated Data Collection Terms - https://www.facebook.com/legal/automated_data_collection_terms
