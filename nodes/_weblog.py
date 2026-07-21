"""Shared parsing/formatting helpers for christiangeorgelucas/weblog-tools.

All heavy lifting is delegated to apachelogs (MIT, jwodder/apachelogs) —
this module only adapts apachelogs' LogEntry objects into this package's
canonical LogEntry proto dict, splits request-lines (a directive apachelogs
does not itself decompose), and enforces this package's input-size bounds.
"""

from __future__ import annotations

import re
from typing import Optional

import apachelogs

# apachelogs stores %t's CONVERTED value (a datetime) in entry.directives,
# not the original wire text, so str()-ing it does not reproduce what the
# log line actually said (e.g. it turns "[21/Jul/2026:10:15:32 +0000]" into
# "2026-07-21 10:15:32+00:00" - a different format entirely). Apache's own
# %t directive always renders bracketed on the wire regardless of whether
# the LogFormat string itself has literal brackets around %t (it doesn't,
# in COMMON/COMBINED/nginx_combined) - the brackets are part of %t's own
# output. Re-extract the actual bracketed substring straight from the raw
# line so timestamp_raw/directives["%t"] reflect what was really logged.
_RAW_TIMESTAMP_RGX = re.compile(r"\[\d{2}/\w{3}/\d{4}:\d{2}:\d{2}:\d{2}\s*[+-]\d{4}\]")

# ── Named formats ────────────────────────────────────────────────────────

COMMON = apachelogs.COMMON
COMBINED = apachelogs.COMBINED
# Nginx's default `combined` log_format directive is:
#   '$remote_addr - $remote_user [$time_local] "$request" $status '
#   '$body_bytes_sent "$http_referer" "$http_user_agent"'
# Field-for-field this is Apache's Combined Log Format: nginx hardcodes a
# literal "-" where Apache's %l (identd) would go (nginx has no identd
# lookup), which is exactly what %l always logs anyway in practice. The two
# formats are therefore structurally identical and share one grammar.
NGINX_COMBINED = COMBINED

# ── Input-size bounds ────────────────────────────────────────────────────

MAX_LINE_BYTES = 65536
MAX_FORMAT_BYTES = 4096
MAX_TIMESTAMP_BYTES = 128
# The Axiom node gRPC transport ceiling is ~4 MiB; stay comfortably under it.
MAX_BLOB_BYTES = 4 * 1024 * 1024 - 65536
MAX_BATCH_LINES = 200_000
MAX_SAMPLE_LINES = 1000

_PARSER_CACHE: dict[str, "apachelogs.LogParser"] = {}


def _parser_for(fmt: str) -> "apachelogs.LogParser":
    p = _PARSER_CACHE.get(fmt)
    if p is None:
        p = apachelogs.LogParser(fmt)
        _PARSER_CACHE[fmt] = p
    return p


def too_large(s: str, limit: int) -> bool:
    return len(s.encode("utf-8", errors="surrogatepass")) > limit


# ── Request-line splitting ───────────────────────────────────────────────


def split_request_line(request_line: str) -> tuple[str, str, str, bool]:
    """Split a request-line ("METHOD target HTTP/x.y") into
    (method, path, protocol, ok). apachelogs exposes the whole request line
    via %r/`request_line` but does not itself decompose it into parts
    (there is no dedicated method/target/protocol directive in the Apache
    LogFormat grammar - %m/%U/%H are httpd 2.4-only extensions most access
    logs do not carry), so this package owns the split.

    Apache's own convention: a completely malformed request line is logged
    as the literal "-", and a request line usually has exactly three
    whitespace-separated tokens ("METHOD target HTTP/x.y"). A CONNECT
    request-target ("host:port") and unusual methods are all still valid
    tokens split the same way — the grammar here is "three tokens on
    whitespace", not method-specific parsing.
    """
    rl = request_line.strip()
    if rl == "" or rl == "-":
        return "", "", "", False
    parts = rl.split(" ")
    if len(parts) == 3:
        method, path, protocol = parts
        if method and path and protocol:
            return method, path, protocol, True
        return "", "", "", False
    if len(parts) == 2:
        # No protocol token (some malformed/old clients) — still recoverable.
        method, path = parts
        if method and path:
            return method, path, "", True
        return "", "", "", False
    if len(parts) == 1 and parts[0]:
        return parts[0], "", "", True
    return "", "", "", False


# ── Timestamp ─────────────────────────────────────────────────────────────


def parse_timestamp(raw: str) -> Optional[tuple[str, str]]:
    """Parse an Apache/CLF timestamp into (iso8601, offset). Returns None on
    failure. Uses apachelogs.parse_apache_timestamp, which preserves the
    UTC offset the timestamp itself carried - never the wall clock."""
    try:
        dt = apachelogs.parse_apache_timestamp(raw.strip())
    except ValueError:
        return None
    if dt is None:
        return None
    iso = dt.isoformat()
    off = dt.strftime("%z")
    offset = f"{off[:3]}:{off[3:]}" if off else ""
    return iso, offset


# ── Core entry adaptation ────────────────────────────────────────────────


def entry_to_dict(
    entry: "apachelogs.LogEntry", raw_line: str, format_string: str, format_name: str
) -> dict:
    """Adapt an apachelogs.LogEntry into this package's canonical LogEntry
    proto kwargs dict."""
    directives = {k: ("" if v is None else str(v)) for k, v in entry.directives.items()}

    remote_host = getattr(entry, "remote_host", None) or ""
    ident = getattr(entry, "remote_logname", None) or ""
    user = getattr(entry, "remote_user", None) or ""
    # %v -> `virtual_host`; %V -> `server_name` (ServerName per
    # UseCanonicalName) is a related but distinct directive - prefer the
    # more common %v, fall back to %V if that's what the format carried.
    virtual_host = getattr(entry, "virtual_host", None) or ""
    if not virtual_host:
        virtual_host = getattr(entry, "server_name", None) or ""

    request_line = getattr(entry, "request_line", None) or ""
    method, path, protocol, split_ok = split_request_line(request_line)

    status = getattr(entry, "final_status", None)
    if status is None:
        status = getattr(entry, "status", None)
    has_status = status is not None

    bytes_sent = getattr(entry, "bytes_sent", None)
    has_bytes_sent = bytes_sent is not None

    headers_in = getattr(entry, "headers_in", None) or {}
    referer = headers_in.get("Referer") or ""
    user_agent = headers_in.get("User-Agent") or ""

    timestamp_iso = ""
    rt = getattr(entry, "request_time", None)
    if rt is not None:
        timestamp_iso = rt.isoformat()

    # Recover the actual wire text for %t (see _RAW_TIMESTAMP_RGX comment
    # above) rather than str()-ing the already-converted datetime.
    timestamp_raw = ""
    if "%t" in directives:
        m = _RAW_TIMESTAMP_RGX.search(raw_line)
        timestamp_raw = m.group(0) if m else directives["%t"]
        directives["%t"] = timestamp_raw

    return dict(
        raw_line=raw_line,
        format_string=format_string,
        format_name=format_name,
        remote_host=remote_host,
        ident=ident,
        user=user,
        virtual_host=virtual_host,
        timestamp=timestamp_iso,
        timestamp_raw=timestamp_raw,
        request_line=request_line,
        method=method if split_ok else "",
        path=path if split_ok else "",
        protocol=protocol if split_ok else "",
        status=int(status) if has_status else 0,
        has_status=has_status,
        bytes_sent=int(bytes_sent) if has_bytes_sent else 0,
        has_bytes_sent=has_bytes_sent,
        referer=referer,
        user_agent=user_agent,
        directives=directives,
        ok=True,
        error_code="",
        error_message="",
    )


def matches_format(line: str, format_string: str) -> bool:
    """True iff `line` fully matches `format_string`'s grammar (used by
    DetectFormat - a lighter-weight check than a full parse)."""
    stripped = line.rstrip("\r\n").strip()
    if stripped == "":
        return False
    try:
        parser = _parser_for(format_string)
        parser.parse(stripped)
        return True
    except Exception:
        return False


def parse_line(line: str, format_string: str, format_name: str) -> dict:
    """Parse one line against a format string, returning a LogEntry kwargs
    dict (either a successful parse or a structured ok=False failure)."""
    stripped = line.rstrip("\r\n")
    if stripped == "":
        return dict(
            raw_line=line,
            format_string=format_string,
            format_name=format_name,
            ok=False,
            error_code="EMPTY_INPUT",
            error_message="line is empty",
        )
    try:
        parser = _parser_for(format_string)
    except apachelogs.Error as e:
        return dict(
            raw_line=line,
            format_string=format_string,
            format_name=format_name,
            ok=False,
            error_code="INVALID_FORMAT",
            error_message=str(e),
        )
    try:
        entry = parser.parse(stripped)
    except apachelogs.InvalidEntryError as e:
        return dict(
            raw_line=line,
            format_string=format_string,
            format_name=format_name,
            ok=False,
            error_code="PARSE_ERROR",
            error_message=str(e),
        )
    except Exception as e:  # defensive: never crash the node on bad input
        return dict(
            raw_line=line,
            format_string=format_string,
            format_name=format_name,
            ok=False,
            error_code="PARSE_ERROR",
            error_message=str(e),
        )
    return entry_to_dict(entry, line, format_string, format_name)


FORMAT_BY_NAME = {
    "common": COMMON,
    "combined": COMBINED,
    "nginx_combined": NGINX_COMBINED,
}

# Field accessors shared by ExtractField and FilterBatch. Each returns the
# field's string representation for a LogEntry proto message ("" for an
# absent status/bytes_sent, matching has_status/has_bytes_sent semantics).
FIELD_GETTERS = {
    "remote_host": lambda e: e.remote_host,
    "ident": lambda e: e.ident,
    "user": lambda e: e.user,
    "virtual_host": lambda e: e.virtual_host,
    "timestamp": lambda e: e.timestamp,
    "method": lambda e: e.method,
    "path": lambda e: e.path,
    "protocol": lambda e: e.protocol,
    "status": lambda e: str(e.status) if e.has_status else "",
    "bytes_sent": lambda e: str(e.bytes_sent) if e.has_bytes_sent else "",
    "referer": lambda e: e.referer,
    "user_agent": lambda e: e.user_agent,
}
