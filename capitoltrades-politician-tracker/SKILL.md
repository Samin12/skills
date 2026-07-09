---
name: capitoltrades-politician-tracker
description: Scrape a politician's stock trading disclosures from CapitolTrades.com and report which trades are newly disclosed since the last check. Use this whenever the user wants to track, monitor, or check a member of Congress's stock trades — phrases like "what is [politician] trading", "track [senator/rep]'s trades", "check CapitolTrades for X", "any new disclosures from [politician]", or when given a capitoltrades.com/politicians/<ID> URL. Also use this to set up a recurring daily/weekly trade-tracking routine for a politician (pair with the `schedule` skill). Works for any politician on CapitolTrades, not just one specific person.
---

# CapitolTrades Politician Tracker

Members of Congress must disclose stock trades under the STOCK Act, usually filed 15-45 days after the trade date. CapitolTrades.com aggregates these disclosures per politician. This skill scrapes a politician's page and reports only what's **new** since the last check, so repeated runs (especially scheduled ones) don't re-report the same trades every time.

## When you don't have a politician ID yet

CapitolTrades URLs look like `https://www.capitoltrades.com/politicians/<ID>` where `<ID>` is CapitolTrades' own code (e.g. `K000389` for Ro Khanna — this happens to look like a bioguide ID but treat it as an opaque CapitolTrades identifier). If the user gives a name instead of a URL:

1. Try `firecrawl scrape "https://www.capitoltrades.com/politicians?q=<name>" --wait-for 3000 --only-main-content` and look for a matching profile link, or
2. Use the `firecrawl-search` skill to search `site:capitoltrades.com/politicians <name>`.

Once you have the URL, confirm the identity by checking the page's `<h1>` name and party/chamber/state line (see "Identify the politician" below) before reporting anything — don't assume the ID matches the name the user said, since CapitolTrades IDs aren't mnemonic.

## Step 1: Scrape the page

The page is a JS-rendered SPA — the trades table won't be in the initial HTML, so a render wait is required:

```bash
firecrawl scrape "https://www.capitoltrades.com/politicians/<ID>" --wait-for 3000 --only-main-content -o .firecrawl/capitoltrades-<ID>.md
```

If you need the politician's display name (e.g. for a first-time report or to confirm identity), scrape once without `--only-main-content` and with `-f markdown` to a `.json` path, or just grep the plain markdown output for the `# Name` heading near the top of the page — CapitolTrades renders the politician's name as an H1 followed by a `Party · Chamber · State` line.

## Step 2: Parse the trades table

The scraped markdown contains a table shaped like:

```
| Traded Issuer | Published | Traded | Filed After | Type | Size |  |
| --- | --- | --- | --- | --- | --- | --- |
| ### [Bank of Montreal](.../issuers/429991)<br>BMO:US | 09:05<br>Yesterday | 23 Jun<br>2026 | days<br>12 | buy | 15K–50K | [Goto trade detail page.](.../trades/20003800812) |
```

For each row extract:
- **Issuer** — the link text before `<br>`
- **Ticker** — the text after `<br>` (e.g. `BMO:US`)
- **Traded date** — the "Traded" column
- **Type** — buy or sell
- **Size** — the dollar range
- **Trade ID** — the numeric ID at the end of the trade detail URL (e.g. `20003800812`) — this is the unique key for diffing, NOT the issuer or date, since a politician can trade the same stock multiple times.

Only the first page of results is needed for tracking new disclosures — CapitolTrades sorts by most-recently-published first, so anything new always appears on page 1.

## Step 3: Diff against saved state

Maintain one state file per politician at `.firecrawl/state/capitoltrades-<ID>-seen.json` (or, for a scheduled task, under that task's own storage directory) — a JSON array of trade IDs already reported:

```json
["20003800812", "20003800813", "..."]
```

- **First run (no state file yet):** treat every trade ID on page 1 as the baseline. Report them all as the initial snapshot, then write the state file.
- **Later runs:** load the state file, diff the current page-1 trade IDs against it. Only IDs *not* in the saved list are "new."
- **After reporting:** merge the new IDs into the saved list, and cap it at the most recent ~500 entries so the file doesn't grow unbounded.

## Step 4: Report

If there are new trades, present them as a markdown table and lead with a one-line summary:

> [Politician] disclosed N new trade(s) since the last check.

| Issuer | Ticker | Trade Date | Type | Size |
| --- | --- | --- | --- | --- |
| ... | ... | ... | ... | ... |

If nothing is new, just say so briefly — don't re-list old trades or pad the response:

> No new [Politician] trades disclosed since the last check.

Keep this concise. It's a diff notification, not a research report — resist the urge to add commentary, sector analysis, or speculation about *why* a trade was made unless the user asks for that separately.

## Setting up a recurring check

If the user wants this to run automatically (daily, weekly, etc.), use the `schedule` skill to create a scheduled task. Give that task its own self-contained prompt including: the exact CapitolTrades URL, the politician's name, and the path to its state file — scheduled runs start fresh each time with no memory of this conversation, so the prompt must carry everything needed to repeat steps 1-4 above.
