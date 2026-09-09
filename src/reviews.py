from pathlib import Path

import pandas as pd


REQUIRED_REVIEW_COLUMNS = {
    "review_id",
    "date",
    "platform",
    "sku_id",
    "rating",
    "review_text",
}


THEME_KEYWORDS = {
    "口味口感": [
        "口感",
        "味道",
        "甜",
        "气泡",
    ],
    "包装问题": [
        "包装",
        "破损",
        "漏液",
        "凹陷",
        "瓶盖",
    ],
    "价格反馈": [
        "价格",
        "贵",
        "活动",
    ],
    "物流冷链": [
        "到货",
        "运输",
        "物流",
        "冷藏",
        "冰",
    ],
    "库存问题": [
        "库存",
        "缺货",
    ],
    "产品效果": [
        "效果",
        "控油",
        "清爽",
        "柔软",
        "水分",
    ],
    "保质期": [
        "保质期",
        "日期",
    ],
}


def load_review_data(file_path: str | Path) -> pd.DataFrame:
    """读取并验证用户评价数据。"""

    data = pd.read_csv(file_path)

    missing_columns = (
        REQUIRED_REVIEW_COLUMNS - set(data.columns)
    )

    if missing_columns:
        missing_text = ", ".join(
            sorted(missing_columns)
        )
        raise ValueError(
            f"评价数据缺少字段：{missing_text}"
        )

    data["date"] = pd.to_datetime(
        data["date"],
        errors="coerce",
    )

    if data["date"].isna().any():
        raise ValueError(
            "评价数据中存在无法识别的日期。"
        )

    invalid_rating = ~data["rating"].between(1, 5)

    if invalid_rating.any():
        raise ValueError(
            "评价评分必须在1到5之间。"
        )

    return data


def classify_review_themes(text: str) -> list[str]:
    """根据透明关键词规则识别评价主题。"""

    matched_themes = []

    for theme, keywords in THEME_KEYWORDS.items():
        if any(
            keyword in str(text)
            for keyword in keywords
        ):
            matched_themes.append(theme)

    if not matched_themes:
        matched_themes.append("其他")

    return matched_themes


def analyze_review_themes(
    data: pd.DataFrame,
) -> pd.DataFrame:
    """统计各评价主题的数量、评分和负面率。"""

    result = data.copy()

    result["theme"] = result["review_text"].apply(
        classify_review_themes
    )

    result = result.explode("theme")

    summary = (
        result.groupby(
            "theme",
            as_index=False,
        )
        .agg(
            review_count=("review_id", "count"),
            average_rating=("rating", "mean"),
            negative_reviews=(
                "rating",
                lambda ratings: (ratings <= 2).sum(),
            ),
        )
    )

    summary["negative_rate"] = (
        summary["negative_reviews"]
        / summary["review_count"]
    )

    return summary.sort_values(
        ["negative_rate", "review_count"],
        ascending=[False, False],
    )
def add_review_evidence_to_risks(
    risks: pd.DataFrame,
    reviews: pd.DataFrame,
    days: int = 7,
) -> pd.DataFrame:
    """把近期用户评价证据添加到SKU风险中。"""

    result = risks.copy()

    if result.empty or reviews.empty:
        return result

    latest_date = reviews["date"].max()
    start_date = latest_date - pd.Timedelta(
        days=days - 1
    )

    recent_reviews = reviews[
        reviews["date"] >= start_date
    ].copy()

    for index, risk in result.iterrows():
        sku_reviews = recent_reviews[
            recent_reviews["sku_id"]
            == risk["sku_id"]
        ]

        if sku_reviews.empty:
            review_evidence = "最近7天没有用户评价数据"
        else:
            review_count = len(sku_reviews)
            average_rating = sku_reviews["rating"].mean()

            negative_reviews = sku_reviews[
                sku_reviews["rating"] <= 2
            ]

            negative_count = len(negative_reviews)
            negative_rate = (
                negative_count / review_count
            )

            if negative_reviews.empty:
                main_negative_theme = "未发现明确负面主题"
            else:
                negative_themes = (
                    negative_reviews["review_text"]
                    .apply(classify_review_themes)
                    .explode()
                )

                main_negative_theme = (
                    negative_themes.value_counts()
                    .index[0]
                )

            review_evidence = (
                f"最近7天共有{review_count}条评价，"
                f"平均评分{average_rating:.2f}，"
                f"负面评价{negative_count}条"
                f"（{negative_rate:.1%}），"
                f"主要负面主题：{main_negative_theme}"
            )

        result.at[index, "evidence"] = (
            f"{risk['evidence']}；"
            f"用户评价证据：{review_evidence}"
        )

    return result