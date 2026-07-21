from gen.messages_pb2 import ExtractFieldInput, ExtractFieldResult, LogEntry
from nodes.extract_field import extract_field
from nodes._test_helpers import FakeAxiomContext


def _entries():
    return [
        LogEntry(remote_host="1.1.1.1", path="/a", status=200, has_status=True, ok=True),
        LogEntry(remote_host="2.2.2.2", path="/b", status=404, has_status=True, ok=True),
        LogEntry(remote_host="3.3.3.3", path="/c", ok=True),  # no status
    ]


def test_extract_field_status():
    ax = FakeAxiomContext()
    result = extract_field(ax, ExtractFieldInput(entries=_entries(), field="status"))
    assert isinstance(result, ExtractFieldResult)
    assert result.ok is True
    assert list(result.values) == ["200", "404", ""]


def test_extract_field_remote_host():
    ax = FakeAxiomContext()
    result = extract_field(ax, ExtractFieldInput(entries=_entries(), field="remote_host"))
    assert result.ok is True
    assert list(result.values) == ["1.1.1.1", "2.2.2.2", "3.3.3.3"]


def test_extract_field_path():
    ax = FakeAxiomContext()
    result = extract_field(ax, ExtractFieldInput(entries=_entries(), field="path"))
    assert result.ok is True
    assert list(result.values) == ["/a", "/b", "/c"]


def test_extract_field_preserves_order_and_length():
    ax = FakeAxiomContext()
    entries = _entries()
    result = extract_field(ax, ExtractFieldInput(entries=entries, field="remote_host"))
    assert len(result.values) == len(entries)


def test_extract_field_unknown_field():
    ax = FakeAxiomContext()
    result = extract_field(ax, ExtractFieldInput(entries=_entries(), field="nonexistent"))
    assert result.ok is False
    assert result.error_code == "UNKNOWN_FIELD"


def test_extract_field_empty_entries():
    ax = FakeAxiomContext()
    result = extract_field(ax, ExtractFieldInput(entries=[], field="status"))
    assert result.ok is False
    assert result.error_code == "EMPTY_INPUT"
