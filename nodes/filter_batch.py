from gen.messages_pb2 import FilterBatchInput, FilterBatchResult
from gen.axiom_context import AxiomContext

from nodes._weblog import FIELD_GETTERS

_OPS = {"eq", "ne", "gt", "gte", "lt", "lte", "contains", "prefix"}
_NUMERIC_OPS = {"gt", "gte", "lt", "lte"}


def _compare(actual: str, op: str, value: str) -> bool:
    if op == "eq":
        return actual == value
    if op == "ne":
        return actual != value
    if op == "contains":
        return value in actual
    if op == "prefix":
        return actual.startswith(value)
    if op in _NUMERIC_OPS:
        try:
            a = int(actual)
            v = int(value)
        except (ValueError, TypeError):
            return False
        if op == "gt":
            return a > v
        if op == "gte":
            return a >= v
        if op == "lt":
            return a < v
        if op == "lte":
            return a <= v
    return False


def filter_batch(ax: AxiomContext, input: FilterBatchInput) -> FilterBatchResult:
    """Filter a batch of already-parsed LogEntry records (typically chained
    from ParseBatch's `entries`) to those matching a single field
    predicate, e.g. field="status" op="gte" value="500" to find every
    server-error response. String ops: eq, ne, contains, prefix. Numeric
    ops: gt, gte, lt, lte — parse both the entry's field and `value` as
    integers; a non-numeric comparison (e.g. an empty status on a field
    that wasn't present) is a non-match, not an error. Supported fields:
    remote_host, ident, user, virtual_host, timestamp, method, path,
    protocol, status, bytes_sent, referer, user_agent.
    """
    if len(input.entries) == 0:
        return FilterBatchResult(ok=False, error_code="EMPTY_INPUT", error_message="entries is empty")
    getter = FIELD_GETTERS.get(input.field)
    if getter is None:
        return FilterBatchResult(
            ok=False,
            error_code="UNKNOWN_FIELD",
            error_message=f"unknown field '{input.field}'",
        )
    if input.op not in _OPS:
        return FilterBatchResult(
            ok=False,
            error_code="UNKNOWN_OP",
            error_message=f"unknown op '{input.op}' (expected one of {sorted(_OPS)})",
        )
    matched = [e for e in input.entries if _compare(getter(e), input.op, input.value)]
    return FilterBatchResult(ok=True, entries=matched, matched_count=len(matched))
