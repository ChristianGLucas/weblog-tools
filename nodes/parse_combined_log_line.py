from gen.messages_pb2 import ParseLineInput, LogEntry
from gen.axiom_context import AxiomContext

from nodes._weblog import COMBINED, parse_line


def parse_combined_log_line(ax: AxiomContext, input: ParseLineInput) -> LogEntry:
    """Parse a single NCSA Combined Log Format line — Common Log Format plus
    the Referer and User-Agent headers — into its structured fields. Format:
    `%h %l %u %t "%r" %>s %b "%{Referer}i" "%{User-agent}i"`. A line that
    doesn't match the Combined grammar returns ok=false with a structured
    error rather than a crash.
    """
    line = input.line
    return LogEntry(**parse_line(line, COMBINED, "combined"))
