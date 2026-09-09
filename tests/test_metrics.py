import pandas as pd

from src.metrics import calculate_row_metrics


def test_calculate_row_metrics():
    sample_data = pd.DataFrame(
        [
            {
                "unit_price": 10.0,
                "unit_cost": 6.0,
                "units_sold": 100,
                "ad_spend": 200.0,
                "impressions": 1000,
                "clicks": 100,
                "orders": 20,
                "stock": 500,
                "returns": 5,
            }
        ]
    )

    result = calculate_row_metrics(sample_data)
    row = result.iloc[0]

    assert row["gmv"] == 1000
    assert row["gross_profit"] == 400
    assert row["gross_margin"] == 0.4
    assert row["ad_roi"] == 5
    assert row["click_through_rate"] == 0.1
    assert row["conversion_rate"] == 0.2
    assert row["return_rate"] == 0.05
    assert row["stock_days"] == 5