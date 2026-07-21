from gen.messages_pb2 import ParseLineInput, LogEntry
from gen.axiom_context import AxiomContext

from nodes._weblog import NGINX_COMBINED, MAX_LINE_BYTES, parse_line, too_large


def parse_nginx_log_line(ax: AxiomContext, input: ParseLineInput) -> LogEntry:
    """Parse a single Nginx default (`combined`) access-log line into its
    structured fields. Nginx's default `log_format combined` directive is
    `'$remote_addr - $remote_user [$time_local] "$request" $status
    $body_bytes_sent "$http_referer" "$http_user_agent"'` — field-for-field
    identical grammar to Apache's Combined Log Format (nginx hardcodes a
    literal "-" where Apache's %l/ident would go, which is exactly what %l
    always logs in practice since identd is essentially extinct), so this
    node parses against that same grammar. Input is capped at 65536 bytes;
    a line that doesn't match returns ok=false with a structured error.
    """
    line = input.line
    if too_large(line, MAX_LINE_BYTES):
        return LogEntry(
            raw_line=line[:512],
            format_string=NGINX_COMBINED,
            format_name="nginx_combined",
            ok=False,
            error_code="TOO_LARGE",
            error_message=f"line exceeds {MAX_LINE_BYTES} bytes",
        )
    return LogEntry(**parse_line(line, NGINX_COMBINED, "nginx_combined"))
