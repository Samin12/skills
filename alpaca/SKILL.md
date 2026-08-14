---
name: alpaca
description: Use when the user wants to connect to Alpaca, inspect Alpaca account or market data, or place trades through the Alpaca MCP server.
---

# Alpaca

Use this skill when working with the Alpaca MCP server.

## Connection

- The plugin starts Alpaca's official MCP server with `uvx alpaca-mcp-server`.
- Credentials are loaded by `scripts/run-alpaca-mcp.sh` from `~/.config/alpaca-mcp/env`.
- If credentials are missing, tell the user to run `~/plugins/alpaca/scripts/configure-alpaca.sh`.
- The server defaults to paper trading through `ALPACA_PAPER_TRADE=true`.
- `ALPACA_TOOLSETS` can limit available capabilities. Useful sets include `account`, `trading`, `watchlists`, `assets`, `stock-data`, `crypto-data`, `options-data`, `corporate-actions`, and `news`.

## Safety

- Treat account information, positions, orders, API keys, and trading history as sensitive financial data.
- Confirm explicitly before placing, replacing, canceling, closing, liquidating, exercising, or marking options do-not-exercise.
- Be extra explicit when `ALPACA_PAPER_TRADE=false`, because that may place live trades.
- Do not give personalized investment advice. Present data, explain mechanics, and help the user inspect risks and alternatives.

## Useful Prompts

- "Show my Alpaca buying power and open positions."
- "Compare market snapshots for AAPL, TSLA, and NVDA."
- "Find option contracts for AAPL expiring next month."
- "Place a paper-trading limit order after I confirm the details."
