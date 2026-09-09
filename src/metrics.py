from pathlib import Path

import pandas as pd


REQUIRED_COLUMNS = {
    "date",
    "platform",
    "sku_id",
    "sku_name",
    "category",
    "unit_price",
    "unit_cost",
    "units_sold",
    "ad_spend",
    "impressions",
    "clicks",
    "orders",
    "stock",
    "returns",
    "promotion_flag",
}


def load_sales_data(file_path: str | Path) -> pd.DataFrame:
    """读取销售CSV，并检查必要字段。"""

    data = pd.read_csv(file_path)

    missing_columns = REQUIRED_COLUMNS - set(data.columns)

    if missing_columns:
        missing_text = ", ".join(sorted(missing_columns))
        raise ValueError(f"销售数据缺少字段：{missing_text}")

    data["date"] = pd.to_datetime(
        data["date"],
        errors="coerce",
    )

    if data["date"].isna().any():
        raise ValueError("销售数据中存在无法识别的日期。")

    if data["sku_id"].isna().any():
        raise ValueError("销售数据中存在空白的sku_id。")

    return data

def calculate_row_metrics(data: pd.DataFrame) -> pd.DataFrame:
    """计算每条销售记录的经营指标。"""

    result = data.copy()

    result["gmv"] = (
        result["unit_price"]
        * result["units_sold"]
    )

    result["gross_profit"] = (
        result["unit_price"] - result["unit_cost"]
    ) * result["units_sold"]

    result["gross_margin"] = result["gross_profit"].div(
        result["gmv"].where(result["gmv"] != 0)
    )

    result["ad_roi"] = result["gmv"].div(
        result["ad_spend"].where(result["ad_spend"] != 0)
    )

    result["click_through_rate"] = result["clicks"].div(
        result["impressions"].where(result["impressions"] != 0)
    )

    result["conversion_rate"] = result["orders"].div(
        result["clicks"].where(result["clicks"] != 0)
    )

    result["return_rate"] = result["returns"].div(
        result["units_sold"].where(result["units_sold"] != 0)
    )

    result["stock_days"] = result["stock"].div(
        result["units_sold"].where(result["units_sold"] != 0)
    )

    return result
def summarize_by_sku(data: pd.DataFrame) -> pd.DataFrame:
    """按SKU汇总经营表现。"""

    result = calculate_row_metrics(data)

    summary = (
        result.groupby(
            ["sku_id", "sku_name", "category"],
            as_index=False,
        )
        .agg(
            units_sold=("units_sold", "sum"),
            gmv=("gmv", "sum"),
            gross_profit=("gross_profit", "sum"),
            ad_spend=("ad_spend", "sum"),
            impressions=("impressions", "sum"),
            clicks=("clicks", "sum"),
            orders=("orders", "sum"),
            returns=("returns", "sum"),
        )
    )

    # 每个平台只取最后一天的库存，再按SKU汇总
    latest_stock = (
        result.sort_values("date")
        .groupby(["sku_id", "platform"], as_index=False)
        .tail(1)
        .groupby("sku_id", as_index=False)
        .agg(stock=("stock", "sum"))
    )

    summary = summary.merge(
        latest_stock,
        on="sku_id",
        how="left",
    )

    number_of_days = result["date"].nunique()
    summary["daily_sales"] = (
        summary["units_sold"] / number_of_days
    )

    summary["gross_margin"] = summary["gross_profit"].div(
        summary["gmv"].where(summary["gmv"] != 0)
    )

    summary["ad_roi"] = summary["gmv"].div(
        summary["ad_spend"].where(summary["ad_spend"] != 0)
    )

    summary["click_through_rate"] = summary["clicks"].div(
        summary["impressions"].where(summary["impressions"] != 0)
    )

    summary["conversion_rate"] = summary["orders"].div(
        summary["clicks"].where(summary["clicks"] != 0)
    )

    summary["return_rate"] = summary["returns"].div(
        summary["units_sold"].where(summary["units_sold"] != 0)
    )

    summary["stock_days"] = summary["stock"].div(
        summary["daily_sales"].where(summary["daily_sales"] != 0)
    )

    return summary.sort_values(
        "gmv",
        ascending=False,
    )