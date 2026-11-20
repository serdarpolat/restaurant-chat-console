"""chart_for() is a pure function: tool name + call args + already-parsed JSON result in,
Chart.js spec (or None) out — no model, no network, deterministic. Fixtures below mirror
the real shapes returned by restaurant-mcp-server (captured against the live demo data)."""

from chat_console.charts import CHARTABLE_TOOLS, chart_for


def test_chartable_tools_list() -> None:
    assert CHARTABLE_TOOLS == (
        "get_top_items",
        "get_sales_report",
        "get_staff_performance",
        "get_void_report",
        "get_daily_summary",
    )


def test_get_top_items_quantity_is_horizontal_bar() -> None:
    result = {
        "period": {"date_from": "2026-11-14", "date_to": "2026-11-21"},
        "items": [
            {
                "menu_item_id": 36,
                "name": "Çay",
                "category": "İçecekler",
                "quantity": 1314,
                "revenue": 39420.0,
            },
            {
                "menu_item_id": 30,
                "name": "Ayran",
                "category": "İçecekler",
                "quantity": 515,
                "revenue": 28870.0,
            },
        ],
    }
    spec = chart_for("get_top_items", {"limit": 2}, result)
    assert spec is not None
    assert spec["type"] == "bar"
    assert spec["options"]["indexAxis"] == "y"
    assert spec["data"]["labels"] == ["Çay", "Ayran"]
    assert spec["data"]["datasets"][0]["data"] == [1314, 515]


def test_get_top_items_sort_revenue_uses_revenue_metric() -> None:
    result = {
        "period": {},
        "items": [
            {
                "menu_item_id": 1,
                "name": "Lahmacun",
                "category": "x",
                "quantity": 513,
                "revenue": 82080.0,
            }
        ],
    }
    spec = chart_for("get_top_items", {"sort": "revenue"}, result)
    assert spec["data"]["datasets"][0]["data"] == [82080.0]


def test_get_top_items_no_rows_is_none() -> None:
    assert chart_for("get_top_items", {}, {"period": {}, "items": []}) is None


def test_get_sales_report_day_is_line_chart() -> None:
    result = {
        "date_from": "2026-11-14",
        "date_to": "2026-11-21",
        "group_by": "day",
        "total_orders": 738,
        "total_revenue": 1610342.0,
        "avg_ticket": 2182.04,
        "rows": [
            {"key": "2026-11-14", "orders": 147, "revenue": 302804.25, "avg_ticket": 2059.89},
            {"key": "2026-11-15", "orders": 128, "revenue": 284514.5, "avg_ticket": 2222.77},
        ],
    }
    spec = chart_for("get_sales_report", {"group_by": "day"}, result)
    assert spec["type"] == "line"
    assert spec["data"]["labels"] == ["2026-11-14", "2026-11-15"]
    assert spec["data"]["datasets"][0]["data"] == [302804.25, 284514.5]


def test_get_sales_report_weekday_grouping_has_no_chart() -> None:
    result = {
        "group_by": "weekday",
        "rows": [{"key": "Mon", "orders": 1, "revenue": 1.0, "avg_ticket": 1.0}],
    }
    assert chart_for("get_sales_report", {"group_by": "weekday"}, result) is None


def test_get_sales_report_empty_rows_is_none() -> None:
    assert (
        chart_for("get_sales_report", {"group_by": "day"}, {"group_by": "day", "rows": []}) is None
    )


def test_get_staff_performance_is_bar() -> None:
    result = {
        "period": {},
        "staff": [
            {
                "staff_id": 2,
                "name": "Ayşe Demir",
                "role": "cashier",
                "orders": 267,
                "revenue": 386638.0,
                "avg_ticket": 1448.08,
            },
        ],
    }
    spec = chart_for("get_staff_performance", {}, result)
    assert spec["type"] == "bar"
    assert spec["data"]["labels"] == ["Ayşe Demir"]
    assert spec["data"]["datasets"][0]["data"] == [386638.0]


def test_get_void_report_aggregates_by_reason() -> None:
    result = {
        "period": {},
        "voids": [
            {"name": "Beyti", "reason": "Yanlış sipariş girildi", "quantity": 2, "value": 1280.0},
            {
                "name": "Karışık Pide",
                "reason": "Yanlış sipariş girildi",
                "quantity": 3,
                "value": 1380.0,
            },
            {"name": "Lahmacun", "reason": "Ürün beğenilmedi", "quantity": 7, "value": 1120.0},
        ],
    }
    spec = chart_for("get_void_report", {}, result)
    # "Yanlış sipariş girildi" sums to 2+3=5 across two items; "Ürün beğenilmedi" is a
    # single row of 7 — the larger group should sort first.
    assert spec["data"]["labels"][0] == "Ürün beğenilmedi"
    assert spec["data"]["datasets"][0]["data"][0] == 7


def test_get_daily_summary_has_headline_and_channel_bar() -> None:
    result = {
        "date": "2026-11-20",
        "net_sales": 263240.0,
        "by_channel": {"dine_in": 208488.5, "delivery": 30881.0, "takeaway": 23870.5},
    }
    spec = chart_for("get_daily_summary", {}, result)
    assert spec["meta"]["headline"] == 263240.0
    assert spec["data"]["labels"] == ["dine_in", "delivery", "takeaway"]


def test_get_daily_summary_no_channel_data_is_none() -> None:
    assert chart_for("get_daily_summary", {}, {"net_sales": 0.0, "by_channel": {}}) is None


def test_unchartable_tool_is_none() -> None:
    assert chart_for("get_menu_item", {}, {"name": "Çay"}) is None
