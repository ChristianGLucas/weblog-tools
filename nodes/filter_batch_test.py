from gen.messages_pb2 import FilterBatchInput, FilterBatchResult, LogEntry
from nodes.filter_batch import filter_batch
from nodes._test_helpers import FakeAxiomContext


def _entries():
    return [
        LogEntry(ok=True, status=200, has_status=True, method="GET", path="/a"),
        LogEntry(ok=True, status=404, has_status=True, method="GET", path="/missing"),
        LogEntry(ok=True, status=500, has_status=True, method="POST", path="/submit"),
        LogEntry(ok=True, status=503, has_status=True, method="POST", path="/submit"),
    ]


def test_filter_batch_gte_status():
    ax = FakeAxiomContext()
    result = filter_batch(ax, FilterBatchInput(entries=_entries(), field="status", op="gte", value="500"))
    assert isinstance(result, FilterBatchResult)
    assert result.ok is True
    assert result.matched_count == 2
    assert [e.status for e in result.entries] == [500, 503]


def test_filter_batch_eq_method():
    ax = FakeAxiomContext()
    result = filter_batch(ax, FilterBatchInput(entries=_entries(), field="method", op="eq", value="POST"))
    assert result.ok is True
    assert result.matched_count == 2


def test_filter_batch_contains_path():
    ax = FakeAxiomContext()
    result = filter_batch(ax, FilterBatchInput(entries=_entries(), field="path", op="contains", value="miss"))
    assert result.ok is True
    assert result.matched_count == 1
    assert result.entries[0].path == "/missing"


def test_filter_batch_prefix_path():
    ax = FakeAxiomContext()
    result = filter_batch(ax, FilterBatchInput(entries=_entries(), field="path", op="prefix", value="/sub"))
    assert result.ok is True
    assert result.matched_count == 2


def test_filter_batch_ne_status():
    ax = FakeAxiomContext()
    result = filter_batch(ax, FilterBatchInput(entries=_entries(), field="status", op="ne", value="200"))
    assert result.ok is True
    assert result.matched_count == 3


def test_filter_batch_lt_status():
    ax = FakeAxiomContext()
    result = filter_batch(ax, FilterBatchInput(entries=_entries(), field="status", op="lt", value="500"))
    assert result.ok is True
    assert result.matched_count == 2


def test_filter_batch_no_matches_is_ok_empty_result():
    ax = FakeAxiomContext()
    result = filter_batch(ax, FilterBatchInput(entries=_entries(), field="status", op="eq", value="999"))
    assert result.ok is True
    assert result.matched_count == 0
    assert list(result.entries) == []


def test_filter_batch_unknown_field():
    ax = FakeAxiomContext()
    result = filter_batch(ax, FilterBatchInput(entries=_entries(), field="bogus", op="eq", value="x"))
    assert result.ok is False
    assert result.error_code == "UNKNOWN_FIELD"


def test_filter_batch_unknown_op():
    ax = FakeAxiomContext()
    result = filter_batch(ax, FilterBatchInput(entries=_entries(), field="status", op="bogus", value="1"))
    assert result.ok is False
    assert result.error_code == "UNKNOWN_OP"


def test_filter_batch_empty_entries():
    ax = FakeAxiomContext()
    result = filter_batch(ax, FilterBatchInput(entries=[], field="status", op="eq", value="1"))
    assert result.ok is False
    assert result.error_code == "EMPTY_INPUT"
