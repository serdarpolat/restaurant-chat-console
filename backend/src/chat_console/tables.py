"""Model-independent table generation — same philosophy as charts.py (section 5): a
report tool's result is naturally a list of records, so show it as a real table
regardless of whether the model's own prose happens to include a markdown one. The
model's choice of wording is not reliable UI (a small local model may write the same
report as a table once and as a plain list the next time, per the same question asked two
ways) — this is deterministic, straight from the tool's structured JSON result.
"""

from __future__ import annotations

from typing import Any

TABLEABLE_TOOLS = (
    "get_top_items",
    "get_sales_report",
    "get_staff_performance",
    "get_void_report",
)


def _money(value: float) -> str:
    return f"{value:,.2f}"


def table_for(tool_name: str, result: dict[str, Any]) -> dict | None:
    """Return {"columns": [...], "rows": [[...], ...]} for a tool result, or None when
    there's nothing to show (an empty list)."""
    if tool_name == "get_top_items":
        items = result.get("items") or []
        if not items:
            return None
        return {
            "columns": ["Ürün", "Kategori", "Adet", "Gelir (TRY)"],
            "rows": [
                [i["name"], i["category"], i["quantity"], _money(i["revenue"])] for i in items
            ],
        }

    if tool_name == "get_sales_report":
        rows = result.get("rows") or []
        if not rows:
            return None
        # "key" is a date, an hour, a weekday or a channel name depending on group_by —
        # unlike chart_for, every grouping makes a fine table, so this isn't restricted
        # to day/hour the way the line chart is.
        return {
            "columns": ["Dönem", "Sipariş", "Ciro (TRY)", "Ort. Fiş (TRY)"],
            "rows": [
                [r["key"], r["orders"], _money(r["revenue"]), _money(r["avg_ticket"])] for r in rows
            ],
        }

    if tool_name == "get_staff_performance":
        staff = result.get("staff") or []
        if not staff:
            return None
        return {
            "columns": ["Personel", "Rol", "Sipariş", "Ciro (TRY)", "Ort. Fiş (TRY)"],
            "rows": [
                [s["name"], s["role"], s["orders"], _money(s["revenue"]), _money(s["avg_ticket"])]
                for s in staff
            ],
        }

    if tool_name == "get_void_report":
        voids = result.get("voids") or []
        if not voids:
            return None
        return {
            "columns": ["Ürün", "Sebep", "Adet", "Tutar (TRY)"],
            "rows": [[v["name"], v["reason"], v["quantity"], _money(v["value"])] for v in voids],
        }

    return None
