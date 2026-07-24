from gen.messages_pb2 import DetectFormatInput, DetectFormatResult
from gen.axiom_context import AxiomContext

from nodes._weblog import COMBINED, COMMON, matches_format


def detect_format(ax: AxiomContext, input: DetectFormatInput) -> DetectFormatResult:
    """Detect which known access-log format ("common" or
    "combined_or_nginx" — Apache Combined and Nginx's default combined
    format share one grammar and cannot be told apart by shape alone) a
    line or sample of lines best matches, by attempting a full match
    against each known format's grammar. Reports a "best_guess" plus every
    format that matched at least one sample line: "unknown" when nothing
    matched, "ambiguous" when different lines in the sample matched
    different formats. Blank lines are skipped.
    """
    lines = list(input.lines)
    if len(lines) == 0:
        return DetectFormatResult(ok=False, error_code="EMPTY_INPUT", error_message="lines is empty")

    checked = 0
    common_hits = 0
    combined_hits = 0
    for line in lines:
        if line.strip() == "":
            continue
        checked += 1
        if matches_format(line, COMBINED):
            combined_hits += 1
        elif matches_format(line, COMMON):
            common_hits += 1

    matched_formats = []
    if common_hits > 0:
        matched_formats.append("common")
    if combined_hits > 0:
        matched_formats.append("combined_or_nginx")

    lines_matched = common_hits + combined_hits
    if checked == 0:
        best_guess = "unknown"
    elif len(matched_formats) == 0:
        best_guess = "unknown"
    elif len(matched_formats) > 1:
        best_guess = "ambiguous"
    elif combined_hits > 0:
        best_guess = "combined_or_nginx"
    else:
        best_guess = "common"

    return DetectFormatResult(
        ok=True,
        best_guess=best_guess,
        matched_formats=matched_formats,
        lines_checked=checked,
        lines_matched=lines_matched,
    )
