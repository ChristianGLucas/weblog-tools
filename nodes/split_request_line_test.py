from gen.messages_pb2 import RequestLineInput, RequestLineParts
from nodes.split_request_line import split_request_line
from nodes._test_helpers import FakeAxiomContext


def test_split_request_line_standard():
    ax = FakeAxiomContext()
    result = split_request_line(ax, RequestLineInput(request_line="GET /apache_pb.gif HTTP/1.0"))
    assert isinstance(result, RequestLineParts)
    assert result.ok is True
    assert result.method == "GET"
    assert result.path == "/apache_pb.gif"
    assert result.protocol == "HTTP/1.0"


def test_split_request_line_with_query_string():
    ax = FakeAxiomContext()
    result = split_request_line(ax, RequestLineInput(request_line="GET /a/b?x=1&y=2 HTTP/1.1"))
    assert result.ok is True
    assert result.method == "GET"
    assert result.path == "/a/b?x=1&y=2"
    assert result.protocol == "HTTP/1.1"


def test_split_request_line_connect_method():
    ax = FakeAxiomContext()
    result = split_request_line(ax, RequestLineInput(request_line="CONNECT example.com:443 HTTP/1.1"))
    assert result.ok is True
    assert result.method == "CONNECT"
    assert result.path == "example.com:443"
    assert result.protocol == "HTTP/1.1"


def test_split_request_line_no_protocol_token():
    ax = FakeAxiomContext()
    result = split_request_line(ax, RequestLineInput(request_line="GET /old-http-0.9-style"))
    assert result.ok is True
    assert result.method == "GET"
    assert result.path == "/old-http-0.9-style"
    assert result.protocol == ""


def test_split_request_line_apache_malformed_dash_convention():
    # Apache logs a completely unparseable request line as the literal "-".
    ax = FakeAxiomContext()
    result = split_request_line(ax, RequestLineInput(request_line="-"))
    assert result.ok is False
    assert result.error_code == "MALFORMED"
    assert result.method == ""
    assert result.path == ""
    assert result.protocol == ""


def test_split_request_line_empty_input():
    ax = FakeAxiomContext()
    result = split_request_line(ax, RequestLineInput(request_line=""))
    assert result.ok is False
    assert result.error_code == "EMPTY_INPUT"


def test_split_request_line_large_target_no_crash():
    ax = FakeAxiomContext()
    huge = "GET " + ("a" * 200_000) + " HTTP/1.1"
    result = split_request_line(ax, RequestLineInput(request_line=huge))
    assert result.ok is True
    assert result.method == "GET"
    assert result.protocol == "HTTP/1.1"


def test_split_request_line_extra_whitespace_tokens_is_malformed():
    ax = FakeAxiomContext()
    result = split_request_line(ax, RequestLineInput(request_line="GET /a b c d HTTP/1.1"))
    assert result.ok is False
    assert result.error_code == "MALFORMED"
