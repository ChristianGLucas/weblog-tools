from gen.messages_pb2 import ParseLineInput, LogEntry
from gen.axiom_context import AxiomContext

from nodes._weblog import COMMON, parse_line


def parse_common_log_line(ax: AxiomContext, input: ParseLineInput) -> LogEntry:
    """Parse a single Apache Common Log Format (CLF) line into its
    structured fields: remote host, ident, user, timestamp, request line
    (split into method/path/protocol), status, and response size. Format:
    `%h %l %u %t "%r" %>s %b`. A line that doesn't match the CLF grammar
    returns ok=false with a structured error rather than a crash.
    """
    line = input.line
    return LogEntry(**parse_line(line, COMMON, "common"))
