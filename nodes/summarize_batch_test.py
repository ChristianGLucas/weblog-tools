from gen.messages_pb2 import SummarizeBatchInput, BatchSummary, LogEntry
from nodes.summarize_batch import summarize_batch
from nodes._test_helpers import FakeAxiomContext


def test_summarize_batch_status_classes_and_methods_and_bytes():
    ax = FakeAxiomContext()
    entries = [
        LogEntry(ok=True, status=200, has_status=True, bytes_sent=100, has_bytes_sent=True, method="GET"),
        LogEntry(ok=True, status=200, has_status=True, bytes_sent=50, has_bytes_sent=True, method="GET"),
        LogEntry(ok=True, status=404, has_status=True, bytes_sent=0, has_bytes_sent=True, method="GET"),
        LogEntry(ok=True, status=500, has_status=True, bytes_sent=10, has_bytes_sent=True, method="POST"),
        LogEntry(ok=True, status=301, has_status=True, method="GET"),  # no bytes
    ]
    result = summarize_batch(ax, SummarizeBatchInput(entries=entries))
    assert isinstance(result, BatchSummary)
    assert result.ok is True
    assert result.total_entries == 5
    # 100 + 50 + 0 + 10 (the entry with no bytes_sent contributes nothing)
    assert result.total_bytes == 160

    by_class = {sc.status_class: sc.count for sc in result.status_classes}
    assert by_class == {"2xx": 2, "4xx": 1, "5xx": 1, "3xx": 1}

    by_method = {m.method: m.count for m in result.methods}
    assert by_method == {"GET": 4, "POST": 1}

    assert result.error_entry_count == 0


def test_summarize_batch_counts_failed_entries_separately():
    ax = FakeAxiomContext()
    entries = [
        LogEntry(ok=True, status=200, has_status=True, method="GET"),
        LogEntry(ok=False, error_code="PARSE_ERROR"),
    ]
    result = summarize_batch(ax, SummarizeBatchInput(entries=entries))
    assert result.ok is True
    assert result.total_entries == 2
    assert result.error_entry_count == 1
    by_class = {sc.status_class: sc.count for sc in result.status_classes}
    assert by_class == {"2xx": 1}


def test_summarize_batch_other_status_class():
    ax = FakeAxiomContext()
    entries = [LogEntry(ok=True, status=999, has_status=True, method="GET")]
    result = summarize_batch(ax, SummarizeBatchInput(entries=entries))
    by_class = {sc.status_class: sc.count for sc in result.status_classes}
    assert by_class == {"other": 1}


def test_summarize_batch_empty_entries():
    ax = FakeAxiomContext()
    result = summarize_batch(ax, SummarizeBatchInput(entries=[]))
    assert result.ok is False
    assert result.error_code == "EMPTY_INPUT"
