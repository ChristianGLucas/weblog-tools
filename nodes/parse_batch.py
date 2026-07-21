from gen.messages_pb2 import BatchInput, BatchResult, LineError, LogEntry
from gen.axiom_context import AxiomContext

from nodes._weblog import (
    FORMAT_BY_NAME,
    MAX_BATCH_LINES,
    MAX_BLOB_BYTES,
    MAX_FORMAT_BYTES,
    parse_line,
    too_large,
)


def parse_batch(ax: AxiomContext, input: BatchInput) -> BatchResult:
    """Parse a multi-line blob of access-log lines into an array of
    structured LogEntry records, reporting which lines failed rather than
    aborting the whole batch on the first bad line. `format_name` selects a
    fixed format — "common", "combined", or "nginx_combined" (the default
    when left empty) — or "custom", in which case `format` must hold an
    Apache LogFormat directive string. Blank lines are skipped (not
    counted as errors). Bounded to 4 MiB and 200000 lines, checked on the
    raw input BEFORE any per-line parsing — an oversized blob is rejected
    deterministically with ok=false, never partially processed or OOMing.
    """
    blob = input.blob
    if too_large(blob, MAX_BLOB_BYTES):
        return BatchResult(
            ok=False,
            error_code="TOO_LARGE",
            error_message=f"blob exceeds {MAX_BLOB_BYTES} bytes",
        )

    format_name = input.format_name or "combined"
    if format_name == "custom":
        fmt = input.format
        if too_large(fmt, MAX_FORMAT_BYTES):
            return BatchResult(
                ok=False,
                error_code="TOO_LARGE",
                error_message=f"format exceeds {MAX_FORMAT_BYTES} bytes",
            )
        if fmt.strip() == "":
            return BatchResult(
                ok=False,
                error_code="INVALID_FORMAT",
                error_message="format_name is 'custom' but format is empty",
            )
    elif format_name in FORMAT_BY_NAME:
        fmt = FORMAT_BY_NAME[format_name]
    else:
        return BatchResult(
            ok=False,
            error_code="INVALID_FORMAT",
            error_message=f"unknown format_name '{format_name}' (expected common, combined, nginx_combined, or custom)",
        )

    lines = blob.splitlines()
    if len(lines) > MAX_BATCH_LINES:
        return BatchResult(
            ok=False,
            error_code="TOO_MANY_LINES",
            error_message=f"blob has {len(lines)} lines, exceeding the {MAX_BATCH_LINES} limit",
        )

    entries = []
    errors = []
    for i, line in enumerate(lines, start=1):
        if line.strip() == "":
            continue
        d = parse_line(line, fmt, format_name)
        if d["ok"]:
            entries.append(LogEntry(**d))
        else:
            errors.append(
                LineError(
                    line_number=i,
                    line=line[:512],
                    error_code=d["error_code"],
                    error_message=d["error_message"],
                )
            )

    return BatchResult(
        ok=True,
        entries=entries,
        errors=errors,
        total_lines=len(lines),
        parsed_count=len(entries),
        failed_count=len(errors),
    )
