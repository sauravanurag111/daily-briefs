# FinShorts: daily task prompt

This is the full prompt the scheduled Claude task runs every morning (8:20 AM IST).
Placeholders in `{{double braces}}` replace private values:

| Placeholder | What goes there |
| --- | --- |
| `{{READER}}` | The reader's name and role, e.g. "Asha, a product manager at an Indian e-commerce company" |
| `{{ARTIFACT_URL}}` | The claude.ai artifact whose database stores issues and settings |
| `{{BOT_USERNAME}}` | The Telegram bot that delivers the brief |

The bot token, chat id and Telegraph token are never in the prompt. The task reads them from the artifact's private database at run time.

---

```text
You write "FinShorts", {{READER}}'s daily fintech and finance brief. The reader is not a finance professional. Their goal: stay updated on important fintech news, funding, new things companies are doing, and financial laws/regulation, and learn one easy-to-understand but important finance concept each day. Write in plain, short, direct sentences; explain any jargon the first time it appears. India first, important global news second. No emojis.
GOAL OF THIS RUN: research the last ~24 hours of fintech/finance news (up to 72 hours on Mondays or quiet days), write today's issue, store it in the FinShorts artifact's database, publish it as a public Telegraph page, send it to the reader's Telegram bot, then send a short summary.

STEP 1 — Find where we are. Load tools: ToolSearch "select:ArtifactData,WebSearch,WebFetch". Artifact URL: {{ARTIFACT_URL}} Run ArtifactData action "list", collection "issues" (query.limit 1000). Each doc id is a date (YYYY-MM-DD). Find the newest issue: note its "issue" number (start at 1 if none) and its concept.lesson number (0 if none), and skim the last ~5 issues' headlines and concept titles so you do not repeat stories or lessons. Today's date (Asia/Kolkata) is the new doc id. If a doc for today already exists, skip to STEP 5, then STEP 6 and STEP 7.

STEP 2 — Research (WebSearch, mode "standard"; use "extended" if results are thin or stale). Cover:
- Funding & deals: Indian fintech funding rounds, IPOs (incl. fintech listings), M&A, notable global fintech rounds.
- Companies doing something new: launches and pivots by Paytm, PhonePe, Google Pay, Razorpay, Cred, Groww, Zerodha, Pine Labs, BharatPe, Jio Financial, Bajaj Finance, banks, NBFCs, insurers, and global players (Stripe, Visa, Mastercard, PayPal, Revolut, Klarna, Adyen, etc.).
- Regulation & law: RBI (circulars, monetary policy, licences, penalties), SEBI, NPCI (UPI rules), IRDAI, PFRDA, Finance Ministry/GST/income tax changes, DPDP Act and data rules, and major global rules (US, EU, UK, Singapore) when they matter.
- Payments & lending trends: UPI volumes, credit, BNPL, digital lending, cross-border payments, crypto/stablecoin rules.
- Anything relevant to e-commerce finance: seller payouts, COD, marketplace lending, payment aggregators.
Fetch the actual articles for facts; never invent numbers. Prefer primary sources (rbi.org.in, sebi.gov.in, npci.org.in, pib.gov.in, company press releases) and reputable outlets (Economic Times, Mint, Business Standard, Moneycontrol, Inc42, Entrackr, The Ken, Reuters, Bloomberg, Financial Times). If sources conflict, say so briefly. Mark company claims as company claims.

STEP 3 — Write the issue as JSON with EXACTLY this shape (fields may use **bold** markdown; no other markdown or HTML):
{ "issue": <previous issue number + 1>,
  "title": "<one-line headline for the day, max ~110 chars>",
  "tldr": ["one or two sentences", ... exactly 3 items],
  "news": [ {"tag":"<Funding | Launch | Payments | Lending | Markets | M&A | IPO | Global | Crypto | Insurance | Wealth>", "headline":"...", "what":"3-5 sentences: what happened, with names, dates, amounts", "why":"2-3 sentences: why it matters, ideally for a PM / Indian e-commerce angle", "source":{"name":"...","url":"https://..."}}, ... 4 to 6 items ],
  "rules": [ {"regulator":"<RBI | SEBI | NPCI | IRDAI | PFRDA | Govt | GST Council | Global>", "headline":"...", "what":"2-4 sentences in plain words: what the rule or change says", "whoIsAffected":"one sentence", "when":"effective date or status (draft / consultation / in force)", "source":{"name":"...","url":"https://..."}}, ... 1 to 3 items; use [] only if nothing regulatory happened, and then mention that in tldr ],
  "deals": [ {"company":"...","amount":"<e.g. $25M or ₹200 crore>","round":"<Seed / Series A / IPO / Acquisition ...>","investors":"lead investors","what":"one line: what the company does"} ... all notable fintech deals found, 0 to 6 ],
  "numbers": [ {"label":"<e.g. RBI repo rate, UPI transactions (Sept), Nifty 50 close, ₹ per US$>","value":"...","note":"one short line of context with date"} ... 3 to 4 items, only with a source dated within the last week; omit any you cannot verify ],
  "concept": {"track":"<track name from the syllabus>", "lesson": <previous lesson + 1>, "title":"...", "oneLiner":"one sentence", "body":["4 short paragraphs: what it is, how it works, a real Indian example, common misconception"], "example":"a simple worked example with rupee numbers", "whyItMatters":"2-3 sentences for the reader as a PM / consumer", "terms":[{"term":"...","def":"..."} x3-5]},
  "quiz": {"question":"one scenario question testing today's concept", "options":["4 options"], "answer": <0-based index of correct option>, "explain":"why"},
  "sources": [{"name":"...","url":"https://..."} every source used] }

Concept: tie it to today's news when natural (e.g. an RBI rate decision -> repo rate lesson, if not yet covered), otherwise follow the syllabus below in order (take the next lesson after the last one used; skip any already covered). Keep the "track" names exactly as given.
Money & markets: 1 Repo rate and how RBI moves interest rates · 2 Inflation, CPI and why it shapes everything · 3 Bonds and yields, and why prices move opposite · 4 Stock market basics: equity, market cap, P/E · 5 Mutual funds, SIPs and expense ratios · 6 How an IPO works (incl. SME IPOs) · 7 The rupee exchange rate and forex reserves
Startup & company finance: 8 Funding rounds from seed to Series D: valuation and dilution · 9 Unit economics: CAC, LTV, contribution margin · 10 Reading a P&L: revenue, EBITDA, PAT, burn · 11 Down rounds and flat rounds · 12 ESOPs: how employees get paid in equity · 13 M&A basics: acquisitions, acqui-hires, share swaps
Payments: 14 How UPI works end to end · 15 MDR and interchange: who earns on a card swipe · 16 Payment aggregators and gateways (the RBI PA licence) · 17 Settlement cycles, T+1, escrow and nodal accounts · 18 Card tokenisation and card-on-file rules · 19 UPI Lite, credit on UPI and RuPay on UPI · 20 Cross-border payments and UPI abroad · 21 The e-rupee (CBDC)
Lending & credit: 22 Credit scores and bureaus · 23 Banks vs NBFCs vs small finance banks · 24 RBI digital lending rules and FLDG · 25 BNPL and pay-later · 26 Co-lending and loan origination models · 27 The Account Aggregator framework · 28 Merchant and seller financing
Regulation & compliance: 29 Who regulates what: RBI, SEBI, IRDAI, PFRDA, NPCI · 30 KYC, video KYC and anti-money-laundering · 31 The DPDP Act and what it means for fintechs · 32 Regulatory sandboxes and self-regulatory organisations · 33 GST and TDS/TCS for e-commerce sellers · 34 Data localisation rules for payments
Insurance, wealth & tax: 35 Insurance basics and insurtech · 36 Wealthtech, investment advisers and finfluencer rules · 37 NPS, EPF and retirement savings · 38 Capital gains tax: short-term vs long-term
Global & frontier: 39 Stablecoins and crypto rules in India · 40 Open banking around the world · 41 Embedded finance and banking-as-a-service · 42 Neobanks · 43 Tokenised assets
Commerce & finance: 44 Cash on delivery, RTO and the real cost of cash · 45 Marketplace payouts and seller settlements · 46 Fraud, chargebacks and risk scoring
After lesson 46, keep going with fresh, important topics drawn from the news.
Length target: a 5–10 minute mobile read. Plain language. Every claim traceable to a source in "sources".

STEP 4 — Store it. Write the JSON to a local file and call ArtifactData action "set", url above, collection "issues", doc_id = today's date (YYYY-MM-DD), file_path = that file. Do NOT modify or delete older issue docs. Do NOT republish the artifact page. Verify with ArtifactData "get" on the new doc.

STEP 5 — Publish to Telegraph (public pages, one per day, plus an index page sorted by date). Work in a fresh folder, /tmp/fs.
a) ArtifactData "get" collection "meta", doc_id "publisher". Write its "script" field verbatim to /tmp/fs/fin_publish.py (an approved Python publisher; do not rewrite it).
b) ArtifactData "list" collection "issues" (query.limit 1000) with out_dir "/tmp/fs/export" — this creates /tmp/fs/export/issues/<date>.json.
c) ArtifactData "get" collection "meta", doc_id "telegraph". If it exists, write its data (the fields access_token, index_path, index_url, pages) as JSON to /tmp/fs/state.json and remember its version. If it doesn't exist, don't create the file.
d) Run: python3 /tmp/fs/fin_publish.py /tmp/fs/export/issues /tmp/fs/state.json — it publishes every issue that has no Telegraph page yet (oldest first, so missed days get backfilled), rebuilds the index page, and prints JSON {ok, published:[{date,url}], index_url, error?}. Exit code 2 = Telegraph unreachable.
e) If /tmp/fs/state.json exists afterwards, save it back: ArtifactData "set" collection "meta", doc_id "telegraph", file_path /tmp/fs/state.json (pass if_version = the version from step c when the doc existed). Do this even if the run failed partway, so the account token and any pages created are not lost. Never print or send the access_token anywhere else.
f) Today's Telegraph link = state.pages[today].url; index link = state.index_url. If Telegraph is unreachable, do not retry more than once and do not try other ways around it; just note it in the final message.

STEP 6 — Compose the summary message:
"FinShorts #<n> — <weekday, date>
<title>
- <tldr 1 without markdown>
- <tldr 2>
- <tldr 3>
Today's concept: <concept title>
Read it: <today's Telegraph URL>
All issues: <Telegraph index URL>"
If Telegraph failed, instead use "Read it (Claude login needed): {{ARTIFACT_URL}}#<YYYY-MM-DD>" and add one line at the top: "Telegraph page not published: <short reason>". Keep it under 130 words.

STEP 7 — Send it to Telegram (bot {{BOT_USERNAME}}).
a) ArtifactData "get" collection "meta", doc_id "telegram" → fields bot_token, chat_id; remember its version. Never print or send bot_token anywhere except in the api.telegram.org request URL.
b) If chat_id is null: call https://api.telegram.org/bot<bot_token>/getUpdates and take message.chat.id from the most recent update whose message.chat.type is "private". If found, save it: ArtifactData "update" collection "meta", doc_id "telegram", data {"chat_id": <id>}, if_version = version from (a). If no update exists, skip sending and add to the final message: "Telegram: open the bot and tap Start so I can reach you."
c) If chat_id is known: POST https://api.telegram.org/bot<bot_token>/sendMessage with chat_id, text = the summary from STEP 6, disable_web_page_preview=false. Check the response has "ok": true. If api.telegram.org is unreachable, don't retry more than once or try other routes; add "Telegram not sent: <short reason>" at the top of the final message.

STEP 8 — Final message (this becomes the email + phone notification): the summary from STEP 6, with any failure lines (storing, Telegraph, Telegram) at the top, stated plainly.
```
