from gen.messages_pb2 import ParseLineInput, LogEntry
from nodes.parse_nginx_log_line import parse_nginx_log_line
from nodes._test_helpers import FakeAxiomContext

# A representative line in nginx's default `log_format combined` shape:
# '$remote_addr - $remote_user [$time_local] "$request" $status
# $body_bytes_sent "$http_referer" "$http_user_agent"'. Field values below
# are the hand-verified oracle.
NGINX_EXAMPLE = (
    '203.0.113.42 - - [21/Jul/2026:10:15:32 +0000] '
    '"GET /index.html HTTP/1.1" 200 612 "-" "curl/8.4.0"'
)


def test_parse_nginx_log_line_default_combined():
    ax = FakeAxiomContext()
    result = parse_nginx_log_line(ax, ParseLineInput(line=NGINX_EXAMPLE))
    assert isinstance(result, LogEntry)
    assert result.ok is True
    assert result.format_name == "nginx_combined"
    assert result.remote_host == "203.0.113.42"
    assert result.ident == ""
    assert result.user == ""
    assert result.method == "GET"
    assert result.path == "/index.html"
    assert result.protocol == "HTTP/1.1"
    assert result.status == 200
    assert result.bytes_sent == 612
    assert result.timestamp == "2026-07-21T10:15:32+00:00"
    assert result.referer == ""
    assert result.user_agent == "curl/8.4.0"


def test_parse_nginx_log_line_with_referer_and_user():
    ax = FakeAxiomContext()
    line = (
        '198.51.100.7 - alice [21/Jul/2026:11:00:00 +0000] '
        '"POST /checkout HTTP/2.0" 302 0 '
        '"https://shop.example/cart" "Mozilla/5.0 (X11; Linux x86_64)"'
    )
    result = parse_nginx_log_line(ax, ParseLineInput(line=line))
    assert result.ok is True
    assert result.user == "alice"
    assert result.status == 302
    assert result.has_bytes_sent is True
    assert result.bytes_sent == 0
    assert result.referer == "https://shop.example/cart"


def test_parse_nginx_log_line_malformed():
    ax = FakeAxiomContext()
    result = parse_nginx_log_line(ax, ParseLineInput(line="not an nginx log line"))
    assert result.ok is False
    assert result.error_code == "PARSE_ERROR"
