from gen.messages_pb2 import ParseCustomFormatInput, LogEntry
from nodes.parse_custom_format_line import parse_custom_format_line
from nodes._test_helpers import FakeAxiomContext

# A custom format extending Combined with %D (request duration in
# microseconds) — a directive with no dedicated LogEntry field, so it must
# surface via the `directives` escape hatch.
CUSTOM_FORMAT = '%h %l %u %t "%r" %>s %b "%{Referer}i" "%{User-agent}i" %D'
CUSTOM_LINE = (
    '198.51.100.20 - - [21/Jul/2026:09:30:00 +0000] '
    '"GET /health HTTP/1.1" 200 15 "-" "-" 4231'
)


def test_parse_custom_format_line_with_duration_directive():
    ax = FakeAxiomContext()
    result = parse_custom_format_line(
        ax, ParseCustomFormatInput(format=CUSTOM_FORMAT, line=CUSTOM_LINE)
    )
    assert isinstance(result, LogEntry)
    assert result.ok is True
    assert result.format_name == "custom"
    assert result.format_string == CUSTOM_FORMAT
    assert result.remote_host == "198.51.100.20"
    assert result.status == 200
    assert result.bytes_sent == 15
    # %D has no dedicated field — must be recoverable via the directives map.
    assert result.directives["%D"] == "4231"


def test_parse_custom_format_line_minimal_format():
    ax = FakeAxiomContext()
    result = parse_custom_format_line(
        ax, ParseCustomFormatInput(format="%h %>s", line="10.1.1.1 500")
    )
    assert result.ok is True
    assert result.remote_host == "10.1.1.1"
    assert result.status == 500


def test_parse_custom_format_line_unknown_directive_is_invalid_format():
    ax = FakeAxiomContext()
    result = parse_custom_format_line(
        ax, ParseCustomFormatInput(format="%h %Q", line="10.1.1.1 x")
    )
    assert result.ok is False
    assert result.error_code == "INVALID_FORMAT"


def test_parse_custom_format_line_mismatched_line():
    ax = FakeAxiomContext()
    result = parse_custom_format_line(
        ax, ParseCustomFormatInput(format=CUSTOM_FORMAT, line="totally the wrong shape")
    )
    assert result.ok is False
    assert result.error_code == "PARSE_ERROR"


def test_parse_custom_format_line_empty_format():
    ax = FakeAxiomContext()
    result = parse_custom_format_line(
        ax, ParseCustomFormatInput(format="", line="10.1.1.1")
    )
    assert result.ok is False
    assert result.error_code == "EMPTY_INPUT"
