# How Farsight can use a user's Claude or Codex subscription

Research for issue #2 (parent map: #1). Researched 2026-11-22. All "as of" dates below are the dates the source states or the date it was read (2026-11-22). Terms change often; re-check the linked primary sources before building.

Legend: **Confirmed** = stated in a primary source (Anthropic or OpenAI docs or terms, or the app's own repo or docs). **Reported** = secondary press only. **Uncertain** = not settled by any source found.

## Answer in short

1. **V1 route: drive the user's own, unmodified, logged-in CLI (`claude -p` or `codex exec`) on a machine that the subscriber controls.** Both vendors document this headless use, both bill it to the user's plan limits, and neither forbids it when the subscriber runs it for themselves. It costs $0 extra.
2. **That process cannot live on Cloudflare at $0, and should not run a pilot brand's subscription on infrastructure Farsight's owner controls.** Workers cannot spawn a CLI, Containers need the $5/month Workers Paid plan, and both vendors forbid a developer holding or intermediating another person's subscription tokens. So the hosted app (UI, data, collectors) and the AI runner must be split: the AI runner runs on the subscriber's own machine and talks to the hosted app.
3. **Session-token reuse is not a viable fallback.** Anthropic explicitly forbids it and has blocked it server-side since 2026-01-09. On the OpenAI side the legitimate replacement is "Sign in with ChatGPT" (SIWC), which is open to open-source and locally run apps but needs waitlist approval for hosted apps.
4. **A new $0 option outside the CLI:** since 2026-10-07, Claude Max ($100/month credit), Ultra ($200) and Team (up to $500 pooled) plans include monthly Claude API credits at no extra cost. A normal API key on those credits is allowed in a hosted app under the Commercial Terms. Pro plans don't get these credits. This is the only route found that works from Cloudflare at $0, and only if the user is on Max, Ultra or Team.

## 1. Running the CLIs headless

### Claude Code (`claude -p`): Confirmed (code.claude.com/docs/en/headless, read 2026-11-22)

- **Invocation:** `claude -p "<prompt>"` runs non-interactively and reads stdin (piped stdin is capped at 10MB). It exits 0 on success and non-zero on failure. Auth failures print as the result on stdout.
- **Structured output:** `--output-format json` returns `result`, `session_id`, usage and a `total_cost_usd` estimate. `--json-schema '<schema>'` puts schema-conforming output in `structured_output`. That field is missing if the run ends without valid output (for example, a refusal), so callers must check that it is there. `--output-format stream-json --verbose` streams events, including `system/api_retry` events with an `error` category such as `rate_limit`, `authentication_failed` or `billing_error`.
- **Tools and web:** built-in tools include Read, Edit, Bash, WebSearch and WebFetch. `--allowedTools`, `--permission-mode` (`dontAsk` for locked-down runs) and `--permission-prompts none` (v2.1.259+) control them. In v2.1.302+, `-p` runs start in Manual mode, which denies anything that needs approval.
- **Long-running work and sessions:** `--resume <session_id>` and `--continue` let one Run span several calls. Background work is capped at 10 idle minutes by default (`CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS`). SIGTERM exits 143 with the current turn unfinished. `--max-budget-usd` exists.
- **Gotcha (important):** `--bare` "doesn't use your subscription login" and never reads OAuth credentials. It needs `ANTHROPIC_API_KEY`. The docs say `--bare` "will become the default for `-p` in a future release". **Uncertain:** how subscription-login `-p` runs will work after that switch. Farsight's provider seam must not assume today's default, and should watch the Claude Code changelog.
- **Isolation without `--bare`:** a plain `-p` run loads hooks, MCP servers, CLAUDE.md and skills from the working directory and `~/.claude`. Farsight should run it in a dedicated empty working directory and pass its system prompt explicitly (`--append-system-prompt` or `--system-prompt`).
- **Agent SDK (TS/Python)** wraps the same binary and exposes the same features programmatically (code.claude.com/docs/en/agent-sdk/overview).

### Codex (`codex exec`): Confirmed (learn.chatgpt.com/docs/non-interactive-mode, /docs/auth, read 2026-11-22)

- **Invocation:** `codex exec "<prompt>"`. Progress goes to stderr and the final message to stdout. `--ephemeral` skips saving session files. `codex exec resume --last` or `resume <id>` continues a session. The sandbox is read-only by default (`--sandbox workspace-write` or `danger-full-access` to widen it). `--full-auto` "is no longer supported". It must run inside a git repo unless `--skip-git-repo-check` is passed.
- **Structured output:** `--json` gives a JSONL event stream. `--output-schema <file>` forces the final answer to match a JSON Schema. `-o/--output-last-message` writes the final message to a file.
- **Auth:** `codex exec` "reuses saved CLI auth". With ChatGPT sign-in, usage comes from the plan. With an API key it is billed at API rates. Tokens live in `~/.codex/auth.json` or the OS keyring. The docs: "Treat `~/.codex/auth.json` like a password". ChatGPT-auth automation is described as fine for "trusted scripts, schedulers, and private CI runners", with "API keys are still the recommended default for automation" and "Don't expose Codex execution in untrusted or public environments."
- **Embedding:** `codex app-server` (JSON-RPC over stdio) is OpenAI's documented way to embed Codex in a product. The Codex SDK (TypeScript) is the recommended way to automate jobs.
- **Web access:** Codex has a web search tool. **Uncertain:** I did not verify the exact current flag or config key (the CLI reference URL returned 404 on 2026-11-22). Check it at build time.

### Rate limits and concurrency on subscription plans

- **Claude (Confirmed, support article 11145838, read 2026-11-22):** Pro and Max have a 5-hour session limit and a weekly limit. Ultra has a weekly limit, and verified Ultra accounts have no 5-hour limit. Limits are "shared across Claude and Claude Code", so a Farsight Run eats into the user's chat usage too. No numbers are published. The Claude Code legal page says advertised limits "assume ordinary, individual usage of Claude Code and the Agent SDK". The Agent SDK support article (15036540, updates dated 2026-06-15 and 2026-10-07) confirms that Agent SDK, `claude -p` and third-party app usage "still draw from your subscription limits". A separate SDK credit was announced on 2026-05-13 and paused on 2026-06-15.
- **Codex (Confirmed, learn.chatgpt.com/docs/pricing, read 2026-11-22):** Plus has 5-hour windows (published ranges vary by model, and the page calls them estimates). Pro "currently" has no 5-hour limit. Weekly limits "may also apply". Users can buy credits, but Farsight must never trigger purchases.
- **Concurrency: Uncertain.** Neither vendor documents a cap on parallel CLI processes. Plan for 1-2 concurrent calls per Run, back off on `rate_limit` events, and show "limit reached, resumes at X" in the UI rather than failing the Run.

## 2. What the terms say about third-party apps

### Anthropic

- **Consumer Terms (effective 2025-10-08 per the page, read 2026-11-22), Section 3:** no access "through automated or non-human means, whether through a bot, script, or otherwise" except "via an Anthropic API Key or where we otherwise explicitly permit it". Section 2: no sharing credentials or making the account "available to anyone else". Claude Code headless and the Agent SDK are explicitly documented, which is reasonably read as "explicitly permitted" for the subscriber's own use. That reading is an inference, not a quote.
- **Claude Code "Legal and compliance" page (read 2026-11-22):** OAuth is "intended exclusively for purchasers of" Claude plans and "designed to support ordinary use of Claude Code and other native Anthropic applications". Developers building products "should use API key authentication". "Anthropic does not permit third-party developers to offer Claude.ai login into their own applications, or to route requests through Free, Pro, Max, or Ultra plan credentials on behalf of their users. Moreover, developers may not collect, store, or intermediate Claude.ai credentials or session tokens." It also says: "Nor does it prevent an end user from signing in to the unmodified Claude Code binary with their own Claude subscription, including where a platform hosts Claude Code". Such hosting requires accepting the Commercial Terms, leaving the binary unmodified, and that "Customers may not pay for, resell, or intermediate Claude usage on their end users' behalf". Enforcement "may [be done] without prior notice".
- **Agent SDK overview (read 2026-11-22):** "Unless previously approved, Anthropic does not allow third party developers to offer claude.ai login or rate limits for their products, including agents built on the Claude Agent SDK."
- **Possible non-commercial clause: Uncertain.** The copy of the Consumer Terms fetched on 2026-11-22 contained "Non-commercial use only. You agree that you will not use our Services for any commercial or business purposes" (Section 11), and stated it applies to EEA and Swiss consumers. Which regional variant governs the user's account was not settled. If it applies, running Farsight for a paying pilot brand on a personal Pro or Max plan is a breach risk. A Team plan (Commercial Terms) removes it.
- **Enforcement timeline:**
  - 2026-01-09: server-side checks stopped subscription OAuth tokens from working outside Claude Code. Tools had been "spoofing the Claude Code harness" (Reported: The Register 2026-02-20, VentureBeat. Anthropic's Thariq Shihipar: "Third-party harnesses using Claude subscriptions ... are prohibited by our Terms of Service").
  - Around 2026-02-19/20: the legal page was reworded to explicitly ban subscription OAuth "in any other product, tool, or service ... including the Agent SDK" (Reported: The Register. The wording has since changed to the current text quoted above).
  - 2026-03-19: OpenCode merged PR #18186 "anthropic legal requests", which removed its built-in Anthropic auth plugin (Confirmed: github.com/anomalyco/opencode/pull/18186).
  - 2026-04-04: subscription limits stopped covering third-party harnesses such as OpenClaw, which then needed "extra usage" (Reported: The Next Web, The Decoder).
  - 2026-05-13: Anthropic announced a separate monthly "Agent SDK credit" covering `claude -p`, own scripts and SDK-based third-party apps "(OpenClaw, Conductor, etc)", starting 2026-06-15 (Confirmed: @ClaudeDevs and Alex Albert posts on X).
  - 2026-06-15: paused "indefinitely". SDK, `claude -p` and third-party app usage still draw from subscription limits (Confirmed: support article 15036540, Conductor blog).
  - 2026-10-07: Max, Ultra and Team plans get monthly API credits (Confirmed: platform.claude.com api-credits-for-subscribers).
  - Account bans for subscription abuse were reported (The Register). No Anthropic count was found.

### OpenAI

- **Terms of Use (effective 2026-01-01):** do not "Automatically or programmatically extract data or Output", do not share credentials, do not "circumvent any rate limits or restrictions". Codex's headless modes are first-party documented, so using them for yourself is in scope.
- **Sign in with ChatGPT (SIWC):** OpenAI's official way for third-party apps to spend a user's plan.
  - SIWC Terms (effective 2026-11-04): tokens may be obtained "only through OpenAI's supported sign-in flow". "Any persistent storage of Authentication Tokens must be local and under the user's control". Requests "must originate from the user's local runtime or a remote runtime only that user controls". The terms ban "Pooling, transferring, reselling, gifting, or sharing ChatGPT plan usage or Authentication Tokens", say "Use the user's plan only for the application they connected", and require that users be able to use their plan "without paying you".
  - Availability (cookbook and quickstart, undated, read 2026-11-22): plan usage is open to "open-source projects, personal projects that run locally, and selected private apps". "If you're building a paid or remotely hosted app, join the waitlist". Eligible users are Plus and Pro. The help center (article 20001542, "updated 9 days ago") also lists Go and Business. Users can set per-app weekly caps.
  - Mechanics: browser OAuth with PKCE on a `127.0.0.1` callback, a dynamic client registration with a persisted opaque host ID, and scope `chatgpt.tokens.use.direct`. Calls go to the public Responses API with `store: false, stream: true`. `codex app-server` can also take that token through `ACCESS_TOKEN`.
  - Launch timing: DevDay 2026-09-29, with OpenCode, Devin, Amp, Warp and others as partners (Reported).

## 3. How existing "bring your own subscription" apps do it

| App | Mechanism | What happened |
|---|---|---|
| Conductor (Mac app) | Bundles and runs the native Claude Code and Codex binaries through the Claude Agent SDK, reusing the user's local login (conductor.build docs). | Named as an affected SDK app in the 2026-05-13 announcement. On 2026-06-15 it told users the change was "delayed indefinitely" and they could keep using their Claude plan. Still working as of 2026-11-22 (Confirmed). |
| OpenCode | Called Anthropic's API directly with subscription OAuth tokens and spoofed Claude Code headers. | Blocked server-side on 2026-01-09. Built-in auth removed on 2026-03-19 (PR #18186). Community plugins revived it unofficially. For OpenAI it moved to the official SIWC route as a launch partner (Reported). |
| OpenClaw | Third-party agent harness on subscription OAuth. | Lost subscription coverage on 2026-04-04 (Reported). |
| Crystal (stravu) | Ran Claude Code and Codex CLIs in parallel git worktrees. | Deprecated in February 2026 and replaced by Nimbalyst (Confirmed: repo README). |
| Cline | "Claude Code" provider spawns the user's `claude` CLI for each message. Separate OpenAI Codex OAuth option (docs.cline.bot). | No enforcement action found against the CLI-wrapping approach. |
| Zed | Runs "Claude Agent" and Codex as separate ACP processes. "Claude Agent owns its own authentication and billing". Codex "may support ChatGPT login" (zed.dev docs). | No enforcement action found. |

**Pattern:** apps that call the vendor API with lifted OAuth tokens got blocked or legal requests (OpenCode, OpenClaw). Apps that launch the vendor's own unmodified local binary under the user's own login (Conductor, Cline, Zed) survived. This is an observed pattern, not a vendor guarantee. Anthropic's SDK note still says it "does not allow third party developers to offer claude.ai login ... including agents built on the Claude Agent SDK", so even the surviving pattern depends on Anthropic's continued tolerance.

## 4. Session-token fallback

- **Claude: do not build it.** Explicitly forbidden ("may not collect, store, or intermediate Claude.ai credentials or session tokens"), blocked server-side since 2026-01-09, enforceable "without prior notice", with account bans reported. The risk is the user losing the Claude account they rely on.
- **Codex: replace it with SIWC.** Reading `~/.codex/auth.json` from another program is not sanctioned. SIWC is the sanctioned version and is allowed today for local and open-source use. It needs waitlist approval for a hosted app.
- **Conclusion:** the map's "session tokens if the CLI route fails" fallback should be dropped. The fallback order should be: CLI on the subscriber's machine, then (OpenAI) SIWC locally, then (Claude Max, Ultra or Team) included API credits with an API key.

## 5. Hosted Farsight and a pilot brand

| Option | $0? | Within terms? | Notes |
|---|---|---|---|
| A. CLI runs on Cloudflare | No | n/a | Workers cannot spawn processes. Containers need the $5/month Workers Paid plan (developers.cloudflare.com/containers/pricing). |
| B. Pilot brand's subscription runs on infrastructure the Farsight owner controls (VPS, owner's machine, stored tokens) | Maybe | **No** | Anthropic: no collecting or intermediating tokens, no "route requests ... on behalf of their users". SIWC: tokens must be stored locally under the user's control, with requests from a runtime "only that user controls". |
| C. **Local runner:** hosted UI, data and collectors on Cloudflare free tier. A small Farsight runner on the subscriber's own machine polls for Run jobs, calls their own `claude -p` or `codex exec`, and posts results back | Yes | Yes (best fit) | The pilot brand installs the runner and logs into their own CLI. Runs only progress while that machine is on. It matches the Conductor, Cline and Zed pattern and SIWC's "local runtime" rule. |
| D. Owner runs every Run on their own machine and subscription. The pilot brand only views results | Yes | **Uncertain** | No account sharing takes place (outputs are the owner's to share). But "ordinary, individual usage" and the possible non-commercial clause make this gray for a business pilot. |
| E. Included API credits (Max $100, Ultra $200, Team up to $500/month) with an API key, called from Cloudflare Workers | Yes, if on Max, Ultra or Team | Yes (Commercial Terms) | Credits "may only be used by the holder of the Anthropic account" and are non-transferable, so the owner's own app making the calls is fine. When credits run out, requests stop and "Usage is never charged to your Claude plan" (keep auto-reload off). Pro is not eligible. Conflicts with the map note "API keys wait for later". Treat it as an explicit decision for #1. |

## Recommendation

- **Provider seam:** one interface (`interpret(prompt, data, schema) -> structured result + usage`) with adapters for `claude -p --output-format json --json-schema` and `codex exec --json --output-schema`. Add an optional API-key adapter later (option E) and an optional SIWC adapter later. Keep tools off by default. Collectors supply the data, so the AI needs no web or file tools, which also matches the "AI interprets only" principle.
- **Topology:** hosted app on Cloudflare free tier plus a local runner on the subscriber's machine (option C). This is the only $0 shape that stays within both vendors' terms for a pilot brand using its own subscription.
- **Pilot brand:** they run the local runner with their own Claude or ChatGPT plan (C). If the owner has Max, Ultra or Team, option E lets Runs execute from the cloud without the pilot brand's machine.
- **Drop** the session-token fallback.

## Risks to carry into the spec

1. Anthropic policy volatility: four changes in 2026 (Jan block, Apr harness cut, May SDK credit, Jun pause). The SDK note still says third-party developers cannot "offer claude.ai login". Keep the provider seam swappable and Codex as a first-class alternative.
2. `--bare` becoming the default for `-p` would break subscription-login runs unless Anthropic adjusts. Pin the CLI version and test on upgrade.
3. Shared limits: Runs consume the user's chat and coding allowance. A heavy Run can hit a 5-hour window mid-way, so Runs need resumable, per-step progress.
4. Possible non-commercial clause in some Consumer Terms variants: verify the user's region and plan before a paid pilot.
5. Local runner availability: Runs depend on the subscriber's machine being on and logged in.
6. Structured output can be missing (refusal or limit). Validate every response against the schema and never let the AI produce figures.

## Sources (read 2026-11-22 unless noted)

- Anthropic: Claude Code headless - https://code.claude.com/docs/en/headless
- Anthropic: Claude Code legal and compliance - https://code.claude.com/docs/en/legal-and-compliance
- Anthropic: Agent SDK overview - https://code.claude.com/docs/en/agent-sdk/overview
- Anthropic: Consumer Terms - https://www.anthropic.com/legal/consumer-terms
- Anthropic: Credit terms - https://www.anthropic.com/legal/credit-terms
- Anthropic: Use the Agent SDK with your Claude plan - https://support.claude.com/en/articles/15036540-use-the-claude-agent-sdk-with-your-claude-plan
- Anthropic: Using Claude Code with Pro/Max - https://support.claude.com/en/articles/11145838-using-claude-code-with-your-pro-or-max-plan
- Anthropic: API credits for Max, Ultra, Team - https://platform.claude.com/docs/en/about-claude/api-credits-for-subscribers
- Anthropic on X, 2026-05-13 - https://x.com/ClaudeDevs/status/2054610152817619388 and https://x.com/alexalbert__/status/2054613082589298899
- OpenAI: Codex non-interactive mode - https://learn.chatgpt.com/docs/non-interactive-mode
- OpenAI: Codex auth - https://learn.chatgpt.com/docs/auth
- OpenAI: Codex pricing and limits - https://learn.chatgpt.com/docs/pricing
- OpenAI: Codex app-server with SIWC token - https://developers.openai.com/siwc/token-sharing-open-source/codex-app-server
- OpenAI: SIWC overview, quickstart, cookbook - https://developers.openai.com/siwc/token-sharing-open-source , https://developers.openai.com/siwc/quickstart , https://developers.openai.com/cookbook/articles/sign-in-with-chatgpt
- OpenAI: SIWC Terms (effective 2026-11-04) - https://openai.com/policies/sign-in-with-chatgpt-terms/
- OpenAI: Using your ChatGPT plan in other apps - https://help.openai.com/en/articles/20001542-using-your-chatgpt-plan-in-other-apps-and-sites
- OpenAI: Terms of Use (effective 2026-01-01) - https://openai.com/policies/row-terms-of-use/
- OpenCode PR #18186 (merged 2026-03-19) - https://github.com/anomalyco/opencode/pull/18186
- Conductor: Claude subscription update (2026-06-15) - https://www.conductor.build/blog/claude-subscription-update
- Crystal README - https://github.com/stravu/crystal
- Cline Claude Code provider - https://docs.cline.bot/provider-config/claude-code
- Zed external agents - https://zed.dev/docs/ai/external-agents
- Cloudflare Containers pricing - https://developers.cloudflare.com/containers/pricing/
- Secondary (Reported claims only): The Register 2026-02-20 https://www.theregister.com/2026/02/20/anthropic_clarifies_ban_third_party_claude_access ; VentureBeat https://venturebeat.com/technology/anthropic-reinstates-openclaw-and-third-party-agent-usage-on-claude-subscriptions-with-a-catch ; The Next Web 2026-04-04 https://thenextweb.com/news/anthropic-openclaw-claude-subscription-ban-cost/
