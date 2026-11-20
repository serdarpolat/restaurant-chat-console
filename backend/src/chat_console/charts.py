"""Model-independent chart generation.

Placeholder — filled in at M3. Maps a successful MCP tool result straight to a Chart.js
config, without asking the model to produce chart data (PROJECT6_SCOPE.md section 5 —
the small local model can't be trusted to get limit/sort/group_by right, let alone a
chart spec). One pure function per chartable tool:

    get_top_items          -> horizontal bar (item name x quantity)
    get_sales_report       -> line (time x net_sales), only when grouped by hour/day
    get_staff_performance  -> bar (staff x revenue/count)
    get_void_report        -> bar (reason x count)
    get_daily_summary      -> single number + mini bar (by_channel)
"""

from __future__ import annotations

CHARTABLE_TOOLS = (
    "get_top_items",
    "get_sales_report",
    "get_staff_performance",
    "get_void_report",
    "get_daily_summary",
)


def chart_for(tool_name: str, result: dict) -> dict | None:
    """Return a Chart.js config for a tool result, or None if not chartable. M3."""
    raise NotImplementedError("M3: tool result -> Chart.js spec, one branch per tool above")
