from gen.messages_pb2 import ParseLineInput, LogEntry
from nodes.parse_common_log_line import parse_common_log_line
from nodes._test_helpers import FakeAxiomContext

# The canonical CLF example line straight from Apache's own mod_log_config
# documentation (httpd.apache.org/docs/current/mod/mod_log_config.html) — an
# independent, hand-verifiable oracle for every field: host=127.0.0.1,
# ident="-" (unknown), user=frank, time=10/Oct/2000:13:55:36 -0700,
# request="GET /apache_pb.gif HTTP/1.0", status=200, size=2326.
CLF_EXAMPLE = (
    '127.0.0.1 - frank [10/Oct/2000:13:55:36 -0700] '
    '"GET /apache_pb.gif HTTP/1.0" 200 2326'
)


def test_parse_common_log_line_apache_doc_example():
    ax = FakeAxiomContext()
    result = parse_common_log_line(ax, ParseLineInput(line=CLF_EXAMPLE))
    assert isinstance(result, LogEntry)
    assert result.ok is True
    assert result.format_name == "common"
    assert result.remote_host == "127.0.0.1"
    assert result.ident == ""  # "-" -> unknown -> empty
    assert result.user == "frank"
    assert result.method == "GET"
    assert result.path == "/apache_pb.gif"
    assert result.protocol == "HTTP/1.0"
    assert result.status == 200
    assert result.has_status is True
    assert result.bytes_sent == 2326
    assert result.has_bytes_sent is True
    # hand-computed from "10/Oct/2000:13:55:36 -0700"
    assert result.timestamp == "2000-10-10T13:55:36-07:00"
    # CLF has no Referer/User-Agent directives at all
    assert result.referer == ""
    assert result.user_agent == ""


def test_parse_common_log_line_unsent_bytes_dash():
    ax = FakeAxiomContext()
    line = '10.0.0.5 - - [01/Jan/2026:00:00:00 +0000] "GET / HTTP/1.1" 304 -'
    result = parse_common_log_line(ax, ParseLineInput(line=line))
    assert result.ok is True
    assert result.status == 304
    assert result.has_bytes_sent is False
    assert result.bytes_sent == 0


def test_parse_common_log_line_malformed_returns_structured_error():
    ax = FakeAxiomContext()
    result = parse_common_log_line(ax, ParseLineInput(line="this is not a log line at all"))
    assert result.ok is False
    assert result.error_code == "PARSE_ERROR"
    assert result.error_message != ""


def test_parse_common_log_line_empty_input():
    ax = FakeAxiomContext()
    result = parse_common_log_line(ax, ParseLineInput(line=""))
    assert result.ok is False
    assert result.error_code == "EMPTY_INPUT"


def test_parse_common_log_line_too_large():
    ax = FakeAxiomContext()
    huge = "a" * 70000
    result = parse_common_log_line(ax, ParseLineInput(line=huge))
    assert result.ok is False
    assert result.error_code == "TOO_LARGE"


def test_parse_common_log_line_rejects_combined_shaped_line():
    # A Combined-format line has two extra trailing quoted fields CLF's
    # grammar doesn't expect — CLF parsing must not silently swallow them.
    ax = FakeAxiomContext()
    line = CLF_EXAMPLE + ' "http://example.com/" "Mozilla/5.0"'
    result = parse_common_log_line(ax, ParseLineInput(line=line))
    assert result.ok is False
    assert result.error_code == "PARSE_ERROR"


def test_parse_common_log_line_is_deterministic():
    ax = FakeAxiomContext()
    r1 = parse_common_log_line(ax, ParseLineInput(line=CLF_EXAMPLE))
    r2 = parse_common_log_line(ax, ParseLineInput(line=CLF_EXAMPLE))
    assert r1.remote_host == r2.remote_host
    assert r1.timestamp == r2.timestamp
    assert r1.status == r2.status
