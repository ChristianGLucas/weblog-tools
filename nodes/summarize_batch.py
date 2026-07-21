from collections import OrderedDict

from gen.messages_pb2 import SummarizeBatchInput, BatchSummary, MethodCount, StatusClassCount
from gen.axiom_context import AxiomContext


def _status_class(status: int) -> str:
    if 200 <= status < 300:
        return "2xx"
    if 300 <= status < 400:
        return "3xx"
    if 400 <= status < 500:
        return "4xx"
    if 500 <= status < 600:
        return "5xx"
    return "other"


def summarize_batch(ax: AxiomContext, input: SummarizeBatchInput) -> BatchSummary:
    """Aggregate a batch of already-parsed LogEntry records (typically
    chained from ParseBatch's `entries`) into summary statistics: counts by
    status class (2xx/3xx/4xx/5xx/other), counts by HTTP method, and total
    response bytes across entries that carried a size. A pure aggregation
    over already-parsed input — it never re-parses raw_line. Entries with
    ok=false (parse failures, if the caller chose to include them from
    upstream) are counted separately in error_entry_count and excluded from
    the other statistics.
    """
    if len(input.entries) == 0:
        return BatchSummary(ok=False, error_code="EMPTY_INPUT", error_message="entries is empty")

    total_bytes = 0
    status_counts = OrderedDict()
    method_counts = OrderedDict()
    error_entry_count = 0

    for e in input.entries:
        if not e.ok:
            error_entry_count += 1
            continue
        if e.has_status:
            cls = _status_class(e.status)
            status_counts[cls] = status_counts.get(cls, 0) + 1
        if e.has_bytes_sent:
            total_bytes += e.bytes_sent
        method = e.method
        method_counts[method] = method_counts.get(method, 0) + 1

    return BatchSummary(
        ok=True,
        total_entries=len(input.entries),
        total_bytes=total_bytes,
        status_classes=[StatusClassCount(status_class=k, count=v) for k, v in status_counts.items()],
        methods=[MethodCount(method=k, count=v) for k, v in method_counts.items()],
        error_entry_count=error_entry_count,
    )
