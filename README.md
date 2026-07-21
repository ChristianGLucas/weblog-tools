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
