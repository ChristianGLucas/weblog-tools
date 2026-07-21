from gen.messages_pb2 import ExtractFieldInput, ExtractFieldResult
from gen.axiom_context import AxiomContext

from nodes._weblog import FIELD_GETTERS


def extract_field(ax: AxiomContext, input: ExtractFieldInput) -> ExtractFieldResult:
    """Extract one field's value across a batch of already-parsed LogEntry
    records (typically chained from ParseBatch's `entries`) — e.g. every
    status code, every path, every remote IP. Returns exactly one value per
    input entry, in the same order, so the result can be zipped back
    against the input positionally; a status/bytes_sent that the source
    line didn't carry contributes an empty string, not a fabricated "0".
    Supported fields: remote_host, ident, user, virtual_host, timestamp,
    method, path, protocol, status, bytes_sent, referer, user_agent.
    """
    if len(input.entries) == 0:
        return ExtractFieldResult(ok=False, error_code="EMPTY_INPUT", error_message="entries is empty")
    getter = FIELD_GETTERS.get(input.field)
    if getter is None:
        return ExtractFieldResult(
            ok=False,
            error_code="UNKNOWN_FIELD",
            error_message=f"unknown field '{input.field}'",
        )
    values = [getter(e) for e in input.entries]
    return ExtractFieldResult(ok=True, values=values)
