from gen.messages_pb2 import BatchInput, BatchResult
from nodes.parse_batch import parse_batch
from nodes._weblog import MAX_BATCH_LINES, MAX_BLOB_BYTES
from nodes._test_helpers import FakeAxiomContext

GOOD_LINE_1 = (
    '127.0.0.1 - frank [10/Oct/2000:13:55:36 -0700] '
    '"GET /apache_pb.gif HTTP/1.0" 200 2326 "-" "-"'
)
GOOD_LINE_2 = (
    '10.0.0.9 - - [10/Oct/2000:13:56:00 -0700] '
    '"GET /favicon.ico HTTP/1.1" 404 0 "-" "-"'
)
BAD_LINE = "this line matches no known format"


def test_parse_batch_mixed_good_and_bad_lines():
    ax = FakeAxiomContext()
    blob = "\n".join([GOOD_LINE_1, BAD_LINE, GOOD_LINE_2])
    result = parse_batch(ax, BatchInput(blob=blob, format_name="combined"))
    assert isinstance(result, BatchResult)
    assert result.ok is True
    assert result.total_lines == 3
    assert result.parsed_count == 2
    assert result.failed_count == 1
    assert len(result.entries) == 2
    assert result.entries[0].remote_host == "127.0.0.1"
    assert result.entries[1].status == 404
    assert len(result.errors) == 1
    assert result.errors[0].line_number == 2
    assert result.errors[0].error_code == "PARSE_ERROR"


def test_parse_batch_default_format_is_combined():
    ax = FakeAxiomContext()
    result = parse_batch(ax, BatchInput(blob=GOOD_LINE_1))
    assert result.ok is True
    assert result.parsed_count == 1
    assert result.entries[0].format_name == "combined"


def test_parse_batch_skips_blank_lines():
    ax = FakeAxiomContext()
    blob = f"{GOOD_LINE_1}\n\n\n{GOOD_LINE_2}\n"
    result = parse_batch(ax, BatchInput(blob=blob, format_name="combined"))
    assert result.ok is True
    assert result.total_lines == 4  # splitlines() counts the blank lines
    assert result.parsed_count == 2
    assert result.failed_count == 0


def test_parse_batch_common_format():
    ax = FakeAxiomContext()
    line = '1.2.3.4 - - [01/Jan/2026:00:00:00 +0000] "GET / HTTP/1.1" 200 100'
    result = parse_batch(ax, BatchInput(blob=line, format_name="common"))
    assert result.ok is True
    assert result.parsed_count == 1
    assert result.entries[0].format_name == "common"


def test_parse_batch_custom_format():
    ax = FakeAxiomContext()
    result = parse_batch(
        ax,
        BatchInput(blob="10.0.0.1 200", format_name="custom", format="%h %>s"),
    )
    assert result.ok is True
    assert result.parsed_count == 1
    assert result.entries[0].status == 200


def test_parse_batch_custom_format_missing_string_is_rejected():
    ax = FakeAxiomContext()
    result = parse_batch(ax, BatchInput(blob="x", format_name="custom", format=""))
    assert result.ok is False
    assert result.error_code == "INVALID_FORMAT"


def test_parse_batch_unknown_format_name_rejected():
    ax = FakeAxiomContext()
    result = parse_batch(ax, BatchInput(blob="x", format_name="bogus"))
    assert result.ok is False
    assert result.error_code == "INVALID_FORMAT"


def test_parse_batch_oversized_blob_rejected_before_parsing():
    ax = FakeAxiomContext()
    huge = "a" * (MAX_BLOB_BYTES + 10)
    result = parse_batch(ax, BatchInput(blob=huge, format_name="combined"))
    assert result.ok is False
    assert result.error_code == "TOO_LARGE"
    assert result.parsed_count == 0


def test_parse_batch_too_many_lines_rejected():
    ax = FakeAxiomContext()
    blob = "\n".join(["x"] * (MAX_BATCH_LINES + 1))
    result = parse_batch(ax, BatchInput(blob=blob, format_name="combined"))
    assert result.ok is False
    assert result.error_code == "TOO_MANY_LINES"
