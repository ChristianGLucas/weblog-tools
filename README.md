# weblog-tools

Composable Axiom nodes for deterministic parsing of web-server ACCESS LOG
lines into structured records — built for the Axiom marketplace
(`christiangeorgelucas/weblog-tools`).

Wraps [apachelogs](https://github.com/jwodder/apachelogs) (MIT,
jwodder/apachelogs) — a typed Apache LogFormat parser that supports the full
`mod_log_config` directive grammar, including caller-supplied custom format
strings. Nginx's default `combined` access-log format is field-for-field
identical grammar to Apache's Combined Log Format, so this package parses
both with the same underlying grammar.

Distinct from `http-message-tools` (parses raw HTTP wire request/response
*messages*), `packet-tools` (network-layer packet decoding), and
`useragent-tools` (User-Agent string classification — the natural next hop
for this package's `user_agent` field): this package parses the textual LOG
LINES a web server writes to disk.

## Use it from your agent or app

Every node in this package is a **live, auto-scaling API endpoint** on the
[Axiom](https://axiomide.com) marketplace — call it from an AI agent or your own
code, with nothing to self-host.

**📦 See it on the marketplace:**
https://dev.axiomide.com/marketplace/christiangeorgelucas/weblog-tools@0.1.0

**Hook it up to an AI agent (MCP).** Add Axiom's hosted MCP server to any MCP
client and every node becomes a typed tool your agent can call — search the
catalog, inspect a schema, and invoke it directly.

```bash
# Claude Code
claude mcp add --transport http axiom https://api.axiomide.com/mcp \
  --header "Authorization: Bearer $AXIOM_API_KEY"
```

Claude Desktop, Cursor, or any config-based client:

```json
{
  "mcpServers": {
    "axiom": {
      "type": "http",
      "url": "https://api.axiomide.com/mcp",
      "headers": { "Authorization": "Bearer YOUR_AXIOM_API_KEY" }
    }
  }
}
```

**Call it from the CLI.**

```bash
axiom invoke christiangeorgelucas/weblog-tools/ParseCommonLogLine --input '{ ... }'
```

**Call it over HTTP.**

```bash
curl -X POST https://api.axiomide.com/invocations/v1/nodes/christiangeorgelucas/weblog-tools/0.1.0/ParseCommonLogLine \
  -H "Authorization: Bearer $AXIOM_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{ ... }'
```

> Input/output schema for each node is on the marketplace page above, or via
> `axiom inspect node christiangeorgelucas/weblog-tools/ParseCommonLogLine`.

### Get started free

Install the CLI:

```bash
# macOS / Linux — Homebrew
brew install axiomide/tap/axiom

# macOS / Linux — install script
curl -fsSL https://raw.githubusercontent.com/AxiomIDE/axiom-releases/main/install.sh | sh
```

**Windows:** download the `windows/amd64` `.zip` from the
[releases page](https://github.com/AxiomIDE/axiom-releases/releases), unzip it,
and put `axiom.exe` on your `PATH`.

Then `axiom version` to verify, `axiom login` (GitHub or Google) to authenticate,
and create an API key under **Console → API Keys**. Docs and sign-up at
**[axiomide.com](https://axiomide.com)**.

## Nodes

- **ParseCommonLogLine** — parse a single Apache Common Log Format (CLF) line.
- **ParseCombinedLogLine** — parse a single NCSA Combined Log Format line.
- **ParseNginxLogLine** — parse a single Nginx default (`combined`) access-log line.
- **ParseCustomFormatLine** — parse a line against a caller-supplied Apache LogFormat directive string.
- **ParseBatch** — parse a multi-line blob into an array of records, reporting which lines failed.
- **SplitRequestLine** — split an embedded request line into method/path/protocol.
- **ParseTimestamp** — normalize the embedded CLF timestamp into an ISO 8601 instant.
- **DetectFormat** — detect which known format (CLF/Combined/Nginx) a sample of lines best matches.
- **ExtractField** — extract a single field's value across a batch of parsed entries.
- **SummarizeBatch** — aggregate a batch into status-class counts, method counts, and total bytes.
- **FilterBatch** — filter a batch of parsed entries by a field predicate.

Every node is a pure, deterministic single-input to single-output transform —
no network calls, no wall-clock, no randomness. Batch input is bounded to 4
MiB (the Axiom node transport ceiling) and 200000 lines; a malformed line
returns a structured per-line error rather than crashing the whole batch.

## License

MIT — Copyright (c) 2026 Christian George Lucas.
