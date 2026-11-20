"""Model-independent chart generation.

Maps a successful MCP tool result straight to a Chart.js config, without asking the model
to produce chart data (PROJECT6_SCOPE.md section 5 — the small local model can't be
trusted to get limit/sort/group_by right, let alone a chart spec). One pure function per
chartable tool, fed the tool's own call args (to pick e.g. get_top_items' sort metric) and
its already-parsed JSON result — never the model's text:

    get_top_items          -> horizontal bar (item name x quantity/revenue)
    get_sales_report        -> line (date/hour x revenue), only when grouped by day/hour
    get_staff_performance   -> bar (staff name x revenue)
    get_void_report         -> bar (reason x quantity, aggregated across items)
    get_daily_summary       -> headline number (net sales) + mini bar (by_channel)
"""

from __future__ import annotations

from typing import Any

CHARTABLE_TOOLS = (
    "get_top_items",
    "get_sales_report",
    "get_staff_performance",
    "get_void_report",
    "get_daily_summary",
)

# Nuxt UI's semantic palette (app.config.ts): primary/secondary/success/warning/error, so a
# chart's colors match the rest of the UI instead of inventing a second palette.
_VIOLET = "#8b5cf6"
_CYAN = "#22d3ee"
_EMERALD = "#34d399"
_AMBER = "#fbbf24"
_PINK = "#f472b6"
_PALETTE = (_VIOLET, _CYAN, _EMERALD, _AMBER, _PINK)


def _bar(
    labels: list[str],
    values: list[float],
    label: str,
    *,
    horizontal: bool = False,
    color: str = _VIOLET,
) -> dict:
    return {
        "type": "bar",
        "data": {
            "labels": labels,
            "datasets": [
                {"label": label, "data": values, "backgroundColor": color, "borderRadius": 6}
            ],
        },
        "options": {
            "indexAxis": "y" if horizontal else "x",
            "plugins": {"legend": {"display": False}},
        },
    }


def chart_for(tool_name: str, args: dict[str, Any], result: dict[str, Any]) -> dict | None:
    """Return a Chart.js config (plus optional `meta.headline`) for a tool result, or None
    when there's nothing worth plotting (no rows, or an unsupported grouping)."""
    if tool_name == "get_top_items":
        items = result.get("items") or []
        if not items:
            return None
        metric = "revenue" if args.get("sort") == "revenue" else "quantity"
        items = items[:10]
        return _bar(
            [i["name"] for i in items],
            [i[metric] for i in items],
            "Gelir (TRY)" if metric == "revenue" else "Adet",
            horizontal=True,
            color=_VIOLET,
        )

    if tool_name == "get_sales_report":
        if result.get("group_by") not in ("day", "hour"):
            return None  # weekday/channel read better as a table than a time series
        rows = result.get("rows") or []
        if not rows:
            return None
        return {
            "type": "line",
            "data": {
                "labels": [r["key"] for r in rows],
                "datasets": [
                    {
                        "label": "Ciro (TRY)",
                        "data": [r["revenue"] for r in rows],
                        "borderColor": _CYAN,
                        "backgroundColor": f"{_CYAN}33",
                        "tension": 0.3,
                        "fill": True,
                    }
                ],
            },
            "options": {"plugins": {"legend": {"display": False}}},
        }

    if tool_name == "get_staff_performance":
        staff = result.get("staff") or []
        if not staff:
            return None
        return _bar(
            [s["name"] for s in staff], [s["revenue"] for s in staff], "Ciro (TRY)", color=_EMERALD
        )

    if tool_name == "get_void_report":
        voids = result.get("voids") or []
        if not voids:
            return None
        # Same reason can show up under several item names — aggregate by reason, not row.
        by_reason: dict[str, float] = {}
        for v in voids:
            by_reason[v["reason"]] = by_reason.get(v["reason"], 0) + v["quantity"]
        top = sorted(by_reason.items(), key=lambda kv: kv[1], reverse=True)[:8]
        return _bar([k for k, _ in top], [v for _, v in top], "Adet", horizontal=True, color=_PINK)

    if tool_name == "get_daily_summary":
        by_channel: dict[str, float] = result.get("by_channel") or {}
        if not by_channel:
            return None
        spec = _bar(
            list(by_channel.keys()),
            list(by_channel.values()),
            "Ciro (TRY)",
            horizontal=True,
            color=_AMBER,
        )
        spec["meta"] = {"headline": result.get("net_sales"), "headlineLabel": "Net ciro (TRY)"}
        return spec

    return None
