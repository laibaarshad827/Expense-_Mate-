"""
Basic input validators (format / required-field checks).

They carry no business rules and touch no database, so they sit outside every
layer and can be used by controllers - and by the legacy modules that are
rewritten in Part C - without creating a dependency cycle.
"""

from datetime import date


def is_valid_amount(amount_str):
    try:
        amount = float(amount_str)
    except (TypeError, ValueError):
        return False, None
    if amount <= 0:
        return False, None
    return True, round(amount, 2)


def is_valid_date(date_str: str) -> bool:
    try:
        year, month, day = (int(part) for part in date_str.split("-"))
        date(year, month, day)
        return True
    except Exception:
        return False


def is_valid_txn_type(txn_type: str) -> bool:
    return txn_type in ("income", "expense")