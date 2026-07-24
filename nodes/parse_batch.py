from gen.messages_pb2 import BatchInput, BatchResult, LineError, LogEntry
from gen.axiom_context import AxiomContext

from nodes._weblog import FORMAT_BY_NAME, parse_line


def parse_batch(ax: AxiomContext, input: BatchInput) -> BatchResult:
    """Parse a multi-line blob of access-log lines into an array of
    structured LogEntry records, reporting which lines failed rather than
    aborting the whole batch on the first bad line. `format_name` selects a
    fixed format — "common", "combined" (the default when left empty), or
    "nginx_combined" — or "custom", in which case `format` must hold an
    Apache LogFormat directive string. Blank lines are skipped (not
    counted as errors).
    """
    blob = input.blob

    format_name = input.format_name or "combined"
    if format_name == "custom":
        fmt = input.format
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
