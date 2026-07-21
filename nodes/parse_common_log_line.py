from gen.messages_pb2 import ParseLineInput, LogEntry
from gen.axiom_context import AxiomContext

from nodes._weblog import COMMON, MAX_LINE_BYTES, parse_line, too_large


def parse_common_log_line(ax: AxiomContext, input: ParseLineInput) -> LogEntry:
    """Parse a single Apache Common Log Format (CLF) line into its
    structured fields: remote host, ident, user, timestamp, request line
    (split into method/path/protocol), status, and response size. Format:
    `%h %l %u %t "%r" %>s %b`. Input is capped at 65536 bytes; a line that
    doesn't match the CLF grammar returns ok=false with a structured error
    rather than a crash.
    """
    line = input.line
    if too_large(line, MAX_LINE_BYTES):
        return LogEntry(
            raw_line=line[:512],
            format_string=COMMON,
            format_name="common",
            ok=False,
            error_code="TOO_LARGE",
            error_message=f"line exceeds {MAX_LINE_BYTES} bytes",
        )
    return LogEntry(**parse_line(line, COMMON, "common"))
