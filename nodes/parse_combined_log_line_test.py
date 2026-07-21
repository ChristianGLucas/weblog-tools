from gen.messages_pb2 import ParseLineInput, LogEntry
from nodes.parse_combined_log_line import parse_combined_log_line
from nodes._test_helpers import FakeAxiomContext

# The canonical Combined Log Format example from Apache's own
# mod_log_config documentation — an independent oracle for every field.
COMBINED_EXAMPLE = (
    '127.0.0.1 - frank [10/Oct/2000:13:55:36 -0700] '
    '"GET /apache_pb.gif HTTP/1.0" 200 2326 '
    '"http://www.example.com/start.html" '
    '"Mozilla/4.08 [en] (Win98; I ;Nav)"'
)


def test_parse_combined_log_line_apache_doc_example():
    ax = FakeAxiomContext()
    result = parse_combined_log_line(ax, ParseLineInput(line=COMBINED_EXAMPLE))
    assert isinstance(result, LogEntry)
    assert result.ok is True
    assert result.format_name == "combined"
    assert result.remote_host == "127.0.0.1"
    assert result.user == "frank"
    assert result.method == "GET"
    assert result.path == "/apache_pb.gif"
    assert result.protocol == "HTTP/1.0"
    assert result.status == 200
    assert result.bytes_sent == 2326
    assert result.timestamp == "2000-10-10T13:55:36-07:00"
    assert result.referer == "http://www.example.com/start.html"
    assert result.user_agent == "Mozilla/4.08 [en] (Win98; I ;Nav)"


def test_parse_combined_log_line_no_referer_dash():
    ax = FakeAxiomContext()
    line = (
        '203.0.113.9 - - [05/Mar/2026:08:00:00 +0000] '
        '"POST /api/login HTTP/1.1" 401 512 "-" "curl/8.4.0"'
    )
    result = parse_combined_log_line(ax, ParseLineInput(line=line))
    assert result.ok is True
    assert result.referer == ""
    assert result.user_agent == "curl/8.4.0"
    assert result.status == 401


def test_parse_combined_log_line_rejects_plain_clf_line():
    # A CLF line lacks the two trailing quoted fields Combined requires.
    ax = FakeAxiomContext()
    line = '127.0.0.1 - frank [10/Oct/2000:13:55:36 -0700] "GET /apache_pb.gif HTTP/1.0" 200 2326'
    result = parse_combined_log_line(ax, ParseLineInput(line=line))
    assert result.ok is False
    assert result.error_code == "PARSE_ERROR"


def test_parse_combined_log_line_empty_input():
    ax = FakeAxiomContext()
    result = parse_combined_log_line(ax, ParseLineInput(line=""))
    assert result.ok is False
    assert result.error_code == "EMPTY_INPUT"
