"""table_for() is a pure function: tool name + already-parsed JSON result in,
{"columns", "rows"} (or None) out — no model, no network, deterministic. Fixtures mirror
the real shapes returned by restaurant-mcp-server (same fixtures as test_charts.py)."""

from chat_console.tables import TABLEABLE_TOOLS, table_for


def test_tableable_tools_list() -> None:
    assert TABLEABLE_TOOLS == (
        "get_top_items",
        "get_sales_report",
        "get_staff_performance",
        "get_void_report",
    )


def test_get_top_items_table() -> None:
    result = {
        "period": {},
        "items": [
            {
                "menu_item_id": 36,
                "name": "Çay",
                "category": "İçecekler",
                "quantity": 1314,
                "revenue": 39420.0,
            }
        ],
    }
    table = table_for("get_top_items", result)
    assert table["columns"] == ["Ürün", "Kategori", "Adet", "Gelir (TRY)"]
    assert table["rows"] == [["Çay", "İçecekler", 1314, "39,420.00"]]


def test_get_top_items_empty_is_none() -> None:
    assert table_for("get_top_items", {"period": {}, "items": []}) is None


def test_get_sales_report_table_any_grouping() -> None:
    # Unlike chart_for, a table is fine for weekday/channel groupings too — there's no
    # restriction to day/hour here.
    result = {
        "group_by": "weekday",
        "rows": [{"key": "Mon", "orders": 10, "revenue": 500.0, "avg_ticket": 50.0}],
    }
    table = table_for("get_sales_report", result)
    assert table["columns"] == ["Dönem", "Sipariş", "Ciro (TRY)", "Ort. Fiş (TRY)"]
    assert table["rows"] == [["Mon", 10, "500.00", "50.00"]]


def test_get_sales_report_empty_rows_is_none() -> None:
    assert table_for("get_sales_report", {"group_by": "day", "rows": []}) is None


def test_get_staff_performance_table() -> None:
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
            }
        ],
    }
    table = table_for("get_staff_performance", result)
    assert table["columns"] == ["Personel", "Rol", "Sipariş", "Ciro (TRY)", "Ort. Fiş (TRY)"]
    assert table["rows"] == [["Ayşe Demir", "cashier", 267, "386,638.00", "1,448.08"]]


def test_get_void_report_table_is_per_row_not_aggregated() -> None:
    # The chart aggregates by reason; the table stays one row per void entry so the item
    # name isn't lost.
    result = {
        "period": {},
        "voids": [
            {"name": "Beyti", "reason": "Yanlış sipariş girildi", "quantity": 2, "value": 1280.0},
            {"name": "Lahmacun", "reason": "Ürün beğenilmedi", "quantity": 7, "value": 1120.0},
        ],
    }
    table = table_for("get_void_report", result)
    assert table["columns"] == ["Ürün", "Sebep", "Adet", "Tutar (TRY)"]
    assert len(table["rows"]) == 2
    assert table["rows"][0] == ["Beyti", "Yanlış sipariş girildi", 2, "1,280.00"]


def test_get_void_report_empty_is_none() -> None:
    assert table_for("get_void_report", {"period": {}, "voids": []}) is None


def test_get_daily_summary_has_no_table() -> None:
    # A single summary record, not a list — stays as the headline+bar chart only.
    assert (
        table_for("get_daily_summary", {"net_sales": 100.0, "by_channel": {"dine_in": 100.0}})
        is None
    )


def test_unchartable_tool_is_none() -> None:
    assert table_for("get_menu_item", {"name": "Çay"}) is None
