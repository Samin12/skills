# Connection & auth

The single most common reason an Eden tool call fails is **the connection, not your arguments**. Diagnose that first — most agents waste turns "fixing" a payload that was never the problem.

## How auth works

- Hosted endpoint: `https://mcp.eden.so/mcp`, Streamable HTTP transport, **OAuth**.
- Clients (Claude Code, Codex, Cursor, ChatGPT) run the OAuth flow once against `https://oauth.eden.so`, then hold an **access token** they refresh periodically and send as `Authorization: Bearer <token>` on every request.
- The server is **stateless**: no `mcp-session-id` is issued, and every request is authorized by the bearer token it carries. Your client refreshing its token is all the "session management" there is. (A stale `mcp-session-id` from an older client is simply ignored.)

## The failure you will actually hit: stale OAuth

Symptoms (any of these, usually mid-conversation after things were working):

- Transport error: `Auth error: OAuth authorization required`
- `Unauthorized: Authorization Bearer token required`
- A JSON-RPC error with code `-32001`
- A tool result with `"status": "auth-expired"`

Root cause, in order of likelihood:

1. **The OAuth access token expired and the client couldn't refresh it** (refresh token revoked/expired, or `oauth.eden.so` was briefly unreachable during the refresh).
2. **The token was never valid** (misconfigured client, wrong header).

### Recovery

This is almost always a **reconnect**, not a code or argument change. Do **not** rewrite your payload, switch tools, or shell out to a subprocess — none of that touches the transport.

1. **Reconnect / re-authenticate the Eden MCP in your client.**
   - Claude Code / Cursor / ChatGPT: re-run the Eden connector's OAuth login (disconnect → reconnect if the client offers it). The client obtains a fresh access token.
   - Codex and other CLI clients: re-run the MCP auth/login step for the Eden server, then retry.
2. **After reconnecting, retry the original call unchanged.** If it now succeeds, the problem was the token — confirmed.
3. **If it still fails after a clean reconnect**, it is a real permission/identity problem, not a stale token — see "Is it auth or permission?" below.

### What NOT to do (this is how agents corrupt state)

- ❌ Don't keep retrying the same call hoping the transport heals — it won't until the client re-auths.
- ❌ Don't fall back to a shell/subprocess that calls the API with `--dangerously-bypass-approvals` or a hand-built token. You'll operate as a different identity (or none) and leave inconsistent rows.
- ❌ Don't "work around" it by creating a fresh copy of a record and leaving the original broken. A transport auth failure says nothing about the record — once reconnected, edit the real record in place (`eden_update_scheduled_post`, `eden_update_note`, …).
- ❌ Don't tell the user the feature is broken. Tell them the **connection needs re-authorizing**, which they can do in seconds.

## Is it auth or permission?

Use the layer the error came from:

| Signal                                                                            | Layer         | Meaning                                             | Action                                                              |
| --------------------------------------------------------------------------------- | ------------- | --------------------------------------------------- | ------------------------------------------------------------------- |
| Transport error before any tool result (`OAuth authorization required`, `-32001`) | **Transport** | Token, not the request                              | **Reconnect** the MCP, then retry                                   |
| Tool result `{ "ok": false, "status": "auth-expired" }`                           | Tool          | Token reached Eden but was rejected (401)           | Tell the user to refresh the Eden credential, then retry once       |
| Tool result `{ "ok": false, "status": "forbidden" }`                              | Tool          | Authenticated, but not allowed on **this** resource | Confirm the id/workspace with a `list_*` tool; do **not** reconnect |

`forbidden` ≠ `auth-expired`. Reconnecting fixes an expired token; it will never fix a `forbidden`, because you're already authenticated — you just lack access to that specific workspace/list/post. See <errors.md>.

## Personal Access Tokens (non-OAuth clients)

For automation clients that can't run the OAuth flow (n8n, Zapier, Make, scripts), Eden supports user-generated **Personal Access Tokens** (`eden_pat_…`), created in Eden under Settings → Integrations. Send it as `Authorization: Bearer eden_pat_…`. A PAT doesn't "expire mid-session" the way an OAuth access token rotates — if a PAT call returns `auth-expired`, the token was revoked or is wrong; regenerate it in Settings.

## Reporting connection trouble upstream

If reconnecting reliably fails for a user on the hosted server, the useful signal for the Eden team is which layer refused: a `-32001` from `mcp.eden.so` means the bearer token was rejected at the transport; an `auth-expired` tool result means the token reached Eden's API and was rejected there. Include the exact error string and whether the client is on OAuth or a PAT. (Server internals live in `apps/servers/mcp-server-http`; the server is stateless, so "a redeploy dropped my session" is no longer a real failure mode.)
