from __future__ import annotations

from typing import Any, Dict, Optional


def parse_rating(raw: Optional[str]) -> Optional[float]:
    """
    Parse rating strings like '4.1/5', 'NEW', '-', or None into a float.
    """
    if not raw:
        return None

    raw = raw.strip()
    if not raw or raw in {"NEW", "-", "NEW\\n"}:
        return None

    # Some entries look like '4.1/5' or '4.1'
    try:
        if "/" in raw:
            raw = raw.split("/", 1)[0]
        value = float(raw)
        if value <= 0:
            return None
        return value
    except ValueError:
        return None


def parse_cost_for_two(raw: Optional[str]) -> Optional[int]:
    """
    Parse approximate cost strings into integer rupees.

    Examples:
      '800' -> 800
      '1,200' -> 1200
    """
    if raw is None:
        return None
    text = str(raw).strip()
    if not text or text == "nan":
        return None
    # Remove commas and non-digit suffixes
    digits = "".join(ch for ch in text if ch.isdigit())
    if not digits:
        return None
    try:
        value = int(digits)
        if value <= 0:
            return None
        return value
    except ValueError:
        return None


def normalize_bool(raw: Optional[str]) -> Optional[bool]:
    """
    Normalize Yes/No style fields into booleans.
    Returns None if the value is unknown.
    """
    if raw is None:
        return None
    text = str(raw).strip().lower()
    if not text:
        return None
    if text in {"yes", "y", "true", "t"}:
        return True
    if text in {"no", "n", "false", "f"}:
        return False
    return None


def normalize_cuisines(raw: Optional[str]) -> Optional[str]:
    """
    Normalize cuisines field into a comma-separated, lowercased list.
    """
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None

    parts = [p.strip() for p in text.split(",") if p.strip()]
    if not parts:
        return None
    # Keep original casing for display but de-duplicate
    seen = set()
    normalized: list[str] = []
    for p in parts:
        key = p.lower()
        if key not in seen:
            seen.add(key)
            normalized.append(p)
    return ", ".join(normalized)


def clean_record(raw_row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform a raw dataset row dict into a cleaned structure that matches
    the Restaurant ORM fields.
    """
    return {
        "name": (raw_row.get("name") or "").strip(),
        "url": (raw_row.get("url") or None),
        "address": (raw_row.get("address") or None),
        "location": (raw_row.get("location") or None),
        "listed_in_city": (raw_row.get("listed_in(city)") or None),
        "listed_in_type": (raw_row.get("listed_in(type)") or None),
        "rest_type": (raw_row.get("rest_type") or None),
        "online_order": normalize_bool(raw_row.get("online_order")),
        "book_table": normalize_bool(raw_row.get("book_table")),
        "rating": parse_rating(raw_row.get("rate")),
        "votes": int(raw_row["votes"]) if raw_row.get("votes") not in (None, "") else None,
        "approx_cost_for_two": parse_cost_for_two(raw_row.get("approx_cost(for two people)")),
        "cuisines": normalize_cuisines(raw_row.get("cuisines")),
        "dish_liked": raw_row.get("dish_liked") or None,
        "reviews_list": raw_row.get("reviews_list") or None,
        "menu_item": raw_row.get("menu_item") or None,
        "phone": raw_row.get("phone") or None,
    }


__all__ = [
    "parse_rating",
    "parse_cost_for_two",
    "normalize_bool",
    "normalize_cuisines",
    "clean_record",
]

