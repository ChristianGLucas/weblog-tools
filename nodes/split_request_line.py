from gen.messages_pb2 import RequestLineInput, RequestLineParts
from gen.axiom_context import AxiomContext

from nodes._weblog import split_request_line as _split


def split_request_line(ax: AxiomContext, input: RequestLineInput) -> RequestLineParts:
    """Split an HTTP request-line (the value logged by Apache's %r / an
    access log's "$request"), e.g. "GET /a/b?x=1 HTTP/1.1", into its three
    components: method, path (the raw request-target — may still carry a
    query string; feed it to url-tools for further parsing), and protocol.
    The same logic every Parse* node in this package uses internally to
    populate LogEntry.method/path/protocol, exposed standalone so a caller
    who already has a bare request-line string (not a full log line)
    doesn't need to round-trip it through a full log format. Apache's own
    convention — a completely unparseable request line logged as the
    literal "-" — yields ok=false, not a fabricated split.
    """
    rl = input.request_line
    if rl == "":
        return RequestLineParts(ok=False, error_code="EMPTY_INPUT", error_message="request_line is empty")
    method, path, protocol, ok = _split(rl)
    if not ok:
        return RequestLineParts(
            ok=False,
            error_code="MALFORMED",
            error_message="request_line does not have the form 'METHOD target [PROTOCOL]'",
        )
    return RequestLineParts(ok=True, method=method, path=path, protocol=protocol)
