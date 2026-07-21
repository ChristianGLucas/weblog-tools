from gen.messages_pb2 import ParseLineInput, LogEntry
from gen.axiom_context import AxiomContext

from nodes._weblog import COMBINED, MAX_LINE_BYTES, parse_line, too_large


def parse_combined_log_line(ax: AxiomContext, input: ParseLineInput) -> LogEntry:
    """Parse a single NCSA Combined Log Format line — Common Log Format plus
    the Referer and User-Agent headers — into its structured fields. Format:
    `%h %l %u %t "%r" %>s %b "%{Referer}i" "%{User-agent}i"`. Input is
    capped at 65536 bytes; a line that doesn't match the Combined grammar
    returns ok=false with a structured error rather than a crash.
    """
    line = input.line
    if too_large(line, MAX_LINE_BYTES):
        return LogEntry(
            raw_line=line[:512],
            format_string=COMBINED,
            format_name="combined",
            ok=False,
            error_code="TOO_LARGE",
            error_message=f"line exceeds {MAX_LINE_BYTES} bytes",
        )
    return LogEntry(**parse_line(line, COMBINED, "combined"))
