#!/usr/bin/env python3
"""Central Excel-cell safety helpers for untrusted/imported values.

TENDER_FINDER intentionally creates a small number of workbook formulas in
its own code.  Those formulas must continue to be assigned directly.  Values
that came from a website, email, CSV, user-maintained registry, or prior
workbook must pass through this module before they are written to a workbook.
"""
from __future__ import annotations

import re
from datetime import date, datetime, time
from decimal import Decimal
from numbers import Number
from typing import Any, Iterable


EXCEL_CELL_TEXT_LIMIT = 32_767
FORMULA_PREFIXES = frozenset({"=", "+", "-", "@"})
_UNSUPPORTED_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0B-\x0C\x0E-\x1F]")


def _first_non_whitespace(text: str) -> str:
    for character in text:
        if not character.isspace():
            return character
    return ""


def escape_untrusted_excel_text(value: str, *, limit: int = EXCEL_CELL_TEXT_LIMIT) -> str:
    """Return external text that Excel will treat as literal cell content.

    A leading apostrophe is the standard Excel literal-text marker.  The
    check uses the first non-whitespace character so strings such as
    ``"   =HYPERLINK(...)"`` cannot evade the guard.  The original spacing is
    retained after the marker for audit fidelity.
    """
    if limit < 1:
        raise ValueError("Excel text limit must be at least 1")
    text = _UNSUPPORTED_CONTROL_CHARS.sub(" ", str(value))
    needs_literal_marker = _first_non_whitespace(text) in FORMULA_PREFIXES
    available = limit - 1 if needs_literal_marker else limit
    if len(text) > available:
        suffix = " ... [truncated]"
        keep = max(0, available - len(suffix))
        text = text[:keep] + suffix[: available - keep]
    return ("'" + text) if needs_literal_marker else text


def safe_untrusted_excel_value(value: Any, *, limit: int = EXCEL_CELL_TEXT_LIMIT) -> Any:
    """Sanitize external values without coercing real numbers or dates.

    ``None``, booleans, numeric values, and date/time objects retain their
    native openpyxl types.  Bytes are decoded as external text.  All other
    non-string objects are converted to a safe textual representation because
    openpyxl cannot reliably serialize arbitrary objects.
    """
    if value is None or isinstance(value, (bool, Number, Decimal, date, datetime, time)):
        return value
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="replace")
    if not isinstance(value, str):
        value = str(value)
    return escape_untrusted_excel_text(value, limit=limit)


def set_untrusted_cell(cell: Any, value: Any, *, limit: int = EXCEL_CELL_TEXT_LIMIT) -> Any:
    """Assign one external value to an openpyxl cell and return the cell."""
    cell.value = safe_untrusted_excel_value(value, limit=limit)
    return cell


def append_untrusted_row(
    worksheet: Any,
    values: Iterable[Any],
    *,
    limit: int = EXCEL_CELL_TEXT_LIMIT,
) -> None:
    """Append one row of external/imported values to an openpyxl worksheet."""
    worksheet.append([safe_untrusted_excel_value(value, limit=limit) for value in values])
