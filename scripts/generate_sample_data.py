import csv
import random
from datetime import date, timedelta
from pathlib import Path


# 固定随机结果，保证每次运行生成相同的数据
random.seed(42)


# 找到项目根目录，并准备数据文件夹
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)


# 模拟快消商品
PRODUCTS = [
    {
        "sku_id": "SKU001",
        "sku_name": "无糖青柠气泡水",
        "category": "饮料",
        "unit_price": 6.9,
        "unit_cost": 3.2,
        "base_sales": 120,
    },
    {
        "sku_id": "SKU002",
        "sku_name": "原味燕麦早餐棒",
        "category": "食品",
        "unit_price": 12.9,
        "unit_cost": 6.5,
        "base_sales": 80,
    },
    {
        "sku_id": "SKU003",
        "sku_name": "清爽控油洗发水",
        "category": "个人护理",
        "unit_price": 39.9,
        "unit_cost": 18.0,
        "base_sales": 45,
    },
    {
        "sku_id": "SKU004",
        "sku_name": "婴儿柔湿巾",
        "category": "家庭护理",
        "unit_price": 19.9,
        "unit_cost": 9.0,
        "base_sales": 65,
    },
    {
        "sku_id": "SKU005",
        "sku_name": "高蛋白酸奶",
        "category": "食品",
        "unit_price": 9.9,
        "unit_cost": 5.8,
        "base_sales": 100,
    },
]

PLATFORMS = ["Tmall", "JD", "Douyin"]

START_DATE = date(2026, 8, 1)
DAYS = 30

PLATFORM_FACTOR = {
    "Tmall": 1.0,
    "JD": 0.8,
    "Douyin": 1.2,
}

sales_rows = []

for day_number in range(DAYS):
    current_date = START_DATE + timedelta(days=day_number)

    for platform in PLATFORMS:
        for product in PRODUCTS:
            promotion_flag = current_date.weekday() >= 5

            sales_factor = random.uniform(0.85, 1.15)
            if promotion_flag:
                sales_factor *= 1.25

            units_sold = int(
                product["base_sales"]
                * PLATFORM_FACTOR[platform]
                * sales_factor
            )

            unit_price = product["unit_price"]
            ad_spend = round(random.uniform(180, 650), 2)
            stock = int(product["base_sales"] * random.uniform(8, 25))

            # 异常1：SKU001最后7天销量明显下降
            if product["sku_id"] == "SKU001" and day_number >= 23:
                units_sold = int(units_sold * 0.45)

            # 异常2：SKU003广告投入突然升高，但销量没有同步增长
            if product["sku_id"] == "SKU003" and 12 <= day_number <= 18:
                ad_spend = round(ad_spend * 2.8, 2)

            # 异常3：SKU004最后6天库存不足，限制了销量
            if product["sku_id"] == "SKU004" and day_number >= 24:
                stock = random.randint(5, 25)
                units_sold = int(units_sold * 0.35)

            impressions = random.randint(8000, 30000)
            clicks = int(impressions * random.uniform(0.02, 0.06))
            orders = min(
                units_sold,
                int(clicks * random.uniform(0.10, 0.25)),
            )
            returns = int(units_sold * random.uniform(0.01, 0.06))

            sales_rows.append(
                {
                    "date": current_date.isoformat(),
                    "platform": platform,
                    "sku_id": product["sku_id"],
                    "sku_name": product["sku_name"],
                    "category": product["category"],
                    "unit_price": unit_price,
                    "unit_cost": product["unit_cost"],
                    "units_sold": units_sold,
                    "ad_spend": ad_spend,
                    "impressions": impressions,
                    "clicks": clicks,
                    "orders": orders,
                    "stock": stock,
                    "returns": returns,
                    "promotion_flag": promotion_flag,
                }
            )

            output_path = DATA_DIR / "sample_sales.csv"

with output_path.open(
    mode="w",
    newline="",
    encoding="utf-8-sig",
) as csv_file:
    fieldnames = list(sales_rows[0].keys())

    writer = csv.DictWriter(
        csv_file,
        fieldnames=fieldnames,
    )

    writer.writeheader()
    writer.writerows(sales_rows)

print(f"成功生成模拟销售数据：{output_path}")
print(f"数据行数：{len(sales_rows)}")