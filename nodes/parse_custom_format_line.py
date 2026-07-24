from gen.messages_pb2 import ParseCustomFormatInput, LogEntry
from gen.axiom_context import AxiomContext

from nodes._weblog import parse_line


def parse_custom_format_line(ax: AxiomContext, input: ParseCustomFormatInput) -> LogEntry:
    """Parse a single log line against a caller-supplied Apache LogFormat
    directive string, e.g. `%h %l %u %t "%r" %>s %b "%{Referer}i"
    "%{User-agent}i"`. Supports the full mod_log_config directive grammar
    (plain directives like %h/%l/%u/%s/%b/%r/%t, header directives like
    `%{Name}i`/`%{Name}o`, and the `%>`/`%<` first-vs-last modifiers for
    redirected requests) — any directive it doesn't have a dedicated
    LogEntry field for is still captured in the `directives` map, keyed by
    its exact token (e.g. "%D"). An invalid format string (unknown/malformed
    directive) or a line that doesn't match the format returns ok=false
    with a structured error rather than a crash.
    """
    fmt = input.format
    line = input.line
    if fmt.strip() == "":
        return LogEntry(
            raw_line=line[:512],
            format_string=fmt,
            format_name="custom",
            ok=False,
            error_code="EMPTY_INPUT",
            error_message="format is empty",
        )
    return LogEntry(**parse_line(line, fmt, "custom"))
