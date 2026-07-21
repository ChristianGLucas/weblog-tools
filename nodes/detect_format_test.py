from gen.messages_pb2 import DetectFormatInput, DetectFormatResult
from nodes.detect_format import detect_format
from nodes._test_helpers import FakeAxiomContext

CLF_LINE = '127.0.0.1 - frank [10/Oct/2000:13:55:36 -0700] "GET /apache_pb.gif HTTP/1.0" 200 2326'
COMBINED_LINE = (
    '127.0.0.1 - frank [10/Oct/2000:13:55:36 -0700] "GET /apache_pb.gif HTTP/1.0" '
    '200 2326 "http://www.example.com/start.html" "Mozilla/4.08 [en] (Win98; I ;Nav)"'
)


def test_detect_format_common():
    ax = FakeAxiomContext()
    result = detect_format(ax, DetectFormatInput(lines=[CLF_LINE]))
    assert isinstance(result, DetectFormatResult)
    assert result.ok is True
    assert result.best_guess == "common"
    assert list(result.matched_formats) == ["common"]
    assert result.lines_checked == 1
    assert result.lines_matched == 1


def test_detect_format_combined_or_nginx():
    ax = FakeAxiomContext()
    result = detect_format(ax, DetectFormatInput(lines=[COMBINED_LINE]))
    assert result.ok is True
    assert result.best_guess == "combined_or_nginx"
    assert list(result.matched_formats) == ["combined_or_nginx"]


def test_detect_format_unknown():
    ax = FakeAxiomContext()
    result = detect_format(ax, DetectFormatInput(lines=["this is not a log line"]))
    assert result.ok is True
    assert result.best_guess == "unknown"
    assert list(result.matched_formats) == []
    assert result.lines_matched == 0


def test_detect_format_ambiguous_sample():
    ax = FakeAxiomContext()
    result = detect_format(ax, DetectFormatInput(lines=[CLF_LINE, COMBINED_LINE]))
    assert result.ok is True
    assert result.best_guess == "ambiguous"
    assert set(result.matched_formats) == {"common", "combined_or_nginx"}
    assert result.lines_checked == 2
    assert result.lines_matched == 2


def test_detect_format_skips_blank_lines():
    ax = FakeAxiomContext()
    result = detect_format(ax, DetectFormatInput(lines=[CLF_LINE, "", "   "]))
    assert result.ok is True
    assert result.lines_checked == 1
    assert result.best_guess == "common"


def test_detect_format_empty_lines_list():
    ax = FakeAxiomContext()
    result = detect_format(ax, DetectFormatInput(lines=[]))
    assert result.ok is False
    assert result.error_code == "EMPTY_INPUT"


def test_detect_format_too_many_lines():
    ax = FakeAxiomContext()
    result = detect_format(ax, DetectFormatInput(lines=[CLF_LINE] * 1001))
    assert result.ok is False
    assert result.error_code == "TOO_MANY_LINES"
