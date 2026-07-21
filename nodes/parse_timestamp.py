from gen.messages_pb2 import TimestampInput, TimestampResult
from gen.axiom_context import AxiomContext

from nodes._weblog import MAX_TIMESTAMP_BYTES, parse_timestamp as _parse_ts, too_large


def parse_timestamp(ax: AxiomContext, input: TimestampInput) -> TimestampResult:
    """Parse the embedded CLF/Apache access-log timestamp (the value logged
    by %t, e.g. "[01/Nov/2017:07:28:29 +0000]", brackets optional) into a
    normalized ISO 8601 instant — carrying the UTC offset the log line
    itself recorded, never the wall clock and never converted to a
    different zone. Month names must be the English abbreviations Apache
    always uses regardless of server locale. Input is capped at 128 bytes;
    a string that doesn't match the `DD/Mon/YYYY:HH:MM:SS +HHMM` grammar
    returns ok=false with a structured error.
    """
    ts = input.timestamp
    if ts.strip() == "":
        return TimestampResult(ok=False, error_code="EMPTY_INPUT", error_message="timestamp is empty")
    if too_large(ts, MAX_TIMESTAMP_BYTES):
        return TimestampResult(
            ok=False,
            error_code="TOO_LARGE",
            error_message=f"timestamp exceeds {MAX_TIMESTAMP_BYTES} bytes",
        )
    result = _parse_ts(ts)
    if result is None:
        return TimestampResult(
            ok=False,
            error_code="PARSE_ERROR",
            error_message="timestamp does not match 'DD/Mon/YYYY:HH:MM:SS +HHMM'",
        )
    iso8601, offset = result
    return TimestampResult(ok=True, iso8601=iso8601, timezone_offset=offset)
