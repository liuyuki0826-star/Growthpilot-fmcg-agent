import pandas as pd


def prepare_daily_sku_data(data: pd.DataFrame) -> pd.DataFrame:
    """把不同平台的数据汇总成SKU每日表现。"""

    daily_data = (
        data.groupby(
            ["date", "sku_id", "sku_name"],
            as_index=False,
        )
        .agg(
            units_sold=("units_sold", "sum"),
            ad_spend=("ad_spend", "sum"),
            stock=("stock", "sum"),
        )
        .sort_values(["sku_id", "date"])
    )

    return daily_data


def detect_recent_risks(data: pd.DataFrame) -> pd.DataFrame:
    """识别近期销量下降和库存风险。"""

    daily_data = prepare_daily_sku_data(data)
    risk_records = []

    for sku_id, sku_data in daily_data.groupby("sku_id"):
        sku_data = sku_data.sort_values("date")

        recent_period = sku_data.tail(7)
        previous_period = sku_data.iloc[-14:-7]

        if len(previous_period) < 7:
            continue

        sku_name = sku_data["sku_name"].iloc[0]

        recent_sales = recent_period["units_sold"].sum()
        previous_sales = previous_period["units_sold"].sum()

        sales_change = (
            recent_sales - previous_sales
        ) / previous_sales

        if sales_change <= -0.30:
            risk_records.append(
                {
                    "sku_id": sku_id,
                    "sku_name": sku_name,
                    "risk_type": "销量下降",
                    "severity": "high",
                    "metric": "sales_change",
                    "metric_value": sales_change,
                    "evidence": (
                        f"最近7天销量较此前7天下降"
                        f"{abs(sales_change):.1%}"
                    ),
                }
            )

        latest_stock = recent_period.iloc[-1]["stock"]
        recent_daily_sales = recent_period["units_sold"].mean()

        if recent_daily_sales > 0:
            stock_days = latest_stock / recent_daily_sales
        else:
            stock_days = None

        if stock_days is not None and stock_days < 3:
            risk_records.append(
                {
                    "sku_id": sku_id,
                    "sku_name": sku_name,
                    "risk_type": "库存不足",
                    "severity": "high",
                    "metric": "stock_days",
                    "metric_value": stock_days,
                    "evidence": (
                        f"当前库存预计仅支持"
                        f"{stock_days:.1f}天销售"
                    ),
                }
            )

    return pd.DataFrame(risk_records)

def detect_ad_spend_risks(data: pd.DataFrame) -> pd.DataFrame:
    """识别广告费用上涨但销量没有同步增长的情况。"""

    daily_data = prepare_daily_sku_data(data)
    risk_records = []

    for sku_id, sku_data in daily_data.groupby("sku_id"):
        sku_data = (
            sku_data.sort_values("date")
            .reset_index(drop=True)
        )

        best_risk = None

        for window_end in range(14, len(sku_data) + 1):
            previous_period = sku_data.iloc[
                window_end - 14:window_end - 7
            ]
            current_period = sku_data.iloc[
                window_end - 7:window_end
            ]

            previous_ad_spend = previous_period["ad_spend"].sum()
            current_ad_spend = current_period["ad_spend"].sum()

            previous_sales = previous_period["units_sold"].sum()
            current_sales = current_period["units_sold"].sum()

            if previous_ad_spend == 0 or previous_sales == 0:
                continue

            ad_spend_change = (
                current_ad_spend - previous_ad_spend
            ) / previous_ad_spend

            sales_change = (
                current_sales - previous_sales
            ) / previous_sales

            if ad_spend_change >= 0.50 and sales_change <= 0.20:
                candidate = {
                    "sku_id": sku_id,
                    "sku_name": sku_data["sku_name"].iloc[0],
                    "risk_type": "广告效率风险",
                    "severity": "medium",
                    "metric": "ad_spend_change",
                    "metric_value": ad_spend_change,
                    "evidence": (
                        f"广告费用上升{ad_spend_change:.1%}，"
                        f"销量仅变化{sales_change:.1%}"
                    ),
                }

                if (
                    best_risk is None
                    or ad_spend_change
                    > best_risk["metric_value"]
                ):
                    best_risk = candidate

        if best_risk is not None:
            risk_records.append(best_risk)

    return pd.DataFrame(risk_records)


def detect_all_risks(data: pd.DataFrame) -> pd.DataFrame:
    """汇总所有风险检测结果。"""

    recent_risks = detect_recent_risks(data)
    ad_risks = detect_ad_spend_risks(data)

    risk_tables = [
        table
        for table in [recent_risks, ad_risks]
        if not table.empty
    ]

    if not risk_tables:
        return pd.DataFrame()

    return pd.concat(
        risk_tables,
        ignore_index=True,
    )