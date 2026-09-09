from src.diagnosis import detect_all_risks
from src.metrics import load_sales_data


def test_detect_expected_risks():
    data = load_sales_data("data/sample_sales.csv")
    risks = detect_all_risks(data)

    detected_risks = set(
        zip(
            risks["sku_id"],
            risks["risk_type"],
        )
    )

    assert ("SKU001", "销量下降") in detected_risks
    assert ("SKU003", "广告效率风险") in detected_risks
    assert ("SKU004", "库存不足") in detected_risks
    