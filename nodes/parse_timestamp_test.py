from gen.messages_pb2 import TimestampInput, TimestampResult
from nodes.parse_timestamp import parse_timestamp
from nodes._test_helpers import FakeAxiomContext


def test_parse_timestamp_with_brackets():
    ax = FakeAxiomContext()
    result = parse_timestamp(ax, TimestampInput(timestamp="[10/Oct/2000:13:55:36 -0700]"))
    assert isinstance(result, TimestampResult)
    assert result.ok is True
    # Hand-computed: 10 October 2000, 13:55:36, UTC-07:00 — independent of
    # apachelogs' own internals, just ISO 8601 formatting rules applied to
    # the same fields the input literally spells out.
    assert result.iso8601 == "2000-10-10T13:55:36-07:00"
    assert result.timezone_offset == "-07:00"


def test_parse_timestamp_without_brackets():
    ax = FakeAxiomContext()
    result = parse_timestamp(ax, TimestampInput(timestamp="21/Jul/2026:00:00:00 +0000"))
    assert result.ok is True
    assert result.iso8601 == "2026-07-21T00:00:00+00:00"
    assert result.timezone_offset == "+00:00"


def test_parse_timestamp_positive_offset_preserved_not_converted():
    # The offset must be carried through exactly as logged — never
    # converted to UTC or any other zone, and never the wall clock.
    ax = FakeAxiomContext()
    result = parse_timestamp(ax, TimestampInput(timestamp="[15/Jun/2026:23:59:59 +0530]"))
    assert result.ok is True
    assert result.iso8601 == "2026-06-15T23:59:59+05:30"
    assert result.timezone_offset == "+05:30"


def test_parse_timestamp_invalid_month_name():
    ax = FakeAxiomContext()
    result = parse_timestamp(ax, TimestampInput(timestamp="[10/Foo/2000:13:55:36 -0700]"))
    assert result.ok is False
    assert result.error_code == "PARSE_ERROR"


def test_parse_timestamp_garbage_input():
    ax = FakeAxiomContext()
    result = parse_timestamp(ax, TimestampInput(timestamp="not a timestamp"))
    assert result.ok is False
    assert result.error_code == "PARSE_ERROR"


def test_parse_timestamp_empty_input():
    ax = FakeAxiomContext()
    result = parse_timestamp(ax, TimestampInput(timestamp=""))
    assert result.ok is False
    assert result.error_code == "EMPTY_INPUT"


def test_parse_timestamp_too_large():
    ax = FakeAxiomContext()
    result = parse_timestamp(ax, TimestampInput(timestamp="x" * 200))
    assert result.ok is False
    assert result.error_code == "TOO_LARGE"


def test_parse_timestamp_deterministic():
    ax = FakeAxiomContext()
    r1 = parse_timestamp(ax, TimestampInput(timestamp="[10/Oct/2000:13:55:36 -0700]"))
    r2 = parse_timestamp(ax, TimestampInput(timestamp="[10/Oct/2000:13:55:36 -0700]"))
    assert r1.iso8601 == r2.iso8601
