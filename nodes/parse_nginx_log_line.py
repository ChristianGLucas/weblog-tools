from gen.messages_pb2 import ParseLineInput, LogEntry
from gen.axiom_context import AxiomContext

from nodes._weblog import NGINX_COMBINED, parse_line


def parse_nginx_log_line(ax: AxiomContext, input: ParseLineInput) -> LogEntry:
    """Parse a single Nginx default (`combined`) access-log line into its
    structured fields. Nginx's default `log_format combined` directive is
    `'$remote_addr - $remote_user [$time_local] "$request" $status
    $body_bytes_sent "$http_referer" "$http_user_agent"'` — field-for-field
    identical grammar to Apache's Combined Log Format (nginx hardcodes a
    literal "-" where Apache's %l/ident would go, which is exactly what %l
    always logs in practice since identd is essentially extinct), so this
    node parses against that same grammar. A line that doesn't match
    returns ok=false with a structured error.
    """
    line = input.line
    return LogEntry(**parse_line(line, NGINX_COMBINED, "nginx_combined"))
