from pathlib import Path
from src.agent import generate_recommendations

import streamlit as st

import plotly.express as px

from src.diagnosis import detect_all_risks
from src.reviews import (
    add_review_evidence_to_risks,
    analyze_review_themes,
    load_review_data,
)


from src.metrics import (
    calculate_row_metrics,
    load_sales_data,
    summarize_by_sku,
)


PROJECT_ROOT = Path(__file__).resolve().parent
SAMPLE_SALES_PATH = PROJECT_ROOT / "data" / "sample_sales.csv"
SAMPLE_REVIEWS_PATH = PROJECT_ROOT / "data" / "sample_reviews.csv"


st.set_page_config(
    page_title="GrowthPilot",
    page_icon="📈",
    layout="wide",
)

st.title("📈 GrowthPilot")
st.subheader("快消电商经营分析 Agent")
st.caption(
    "通过可验证的数据计算、异常诊断和本地AI，"
    "帮助运营人员发现SKU风险并生成行动建议。"
)


st.sidebar.header("数据输入")

uploaded_file = st.sidebar.file_uploader(
    "上传销售经营数据",
    type=["csv"],
)

if uploaded_file is None:
    sales_source = SAMPLE_SALES_PATH
    st.sidebar.info("当前使用模拟销售数据")
else:
    sales_source = uploaded_file
    st.sidebar.success("已加载用户上传的数据")


try:
    sales_data = load_sales_data(sales_source)
except ValueError as error:
    st.error(str(error))
    st.stop()


calculated_data = calculate_row_metrics(sales_data)
sku_summary = summarize_by_sku(sales_data)


total_gmv = calculated_data["gmv"].sum()
total_units = calculated_data["units_sold"].sum()
total_profit = calculated_data["gross_profit"].sum()
total_ad_spend = calculated_data["ad_spend"].sum()

overall_margin = (
    total_profit / total_gmv
    if total_gmv != 0
    else 0
)

overall_ad_roi = (
    total_gmv / total_ad_spend
    if total_ad_spend != 0
    else 0
)


st.header("经营概览")

metric_columns = st.columns(5)

metric_columns[0].metric(
    "GMV",
    f"¥{total_gmv:,.0f}",
)

metric_columns[1].metric(
    "销量",
    f"{total_units:,.0f}",
)

metric_columns[2].metric(
    "毛利",
    f"¥{total_profit:,.0f}",
)

metric_columns[3].metric(
    "毛利率",
    f"{overall_margin:.1%}",
)

metric_columns[4].metric(
    "广告 ROI",
    f"{overall_ad_roi:.2f}",
)


st.header("SKU经营表现")

display_summary = sku_summary[
    [
        "sku_id",
        "sku_name",
        "units_sold",
        "gmv",
        "gross_margin",
        "ad_roi",
        "return_rate",
        "stock_days",
    ]
].copy()

display_summary.columns = [
    "SKU编号",
    "商品名称",
    "销量",
    "GMV",
    "毛利率",
    "广告ROI",
    "退货率",
    "库存可售天数",
]

st.dataframe(
    display_summary,
    use_container_width=True,
    hide_index=True,
)
st.header("经营趋势")

daily_trend = (
    calculated_data.groupby(
        "date",
        as_index=False,
    )
    .agg(
        gmv=("gmv", "sum"),
        units_sold=("units_sold", "sum"),
        ad_spend=("ad_spend", "sum"),
    )
)

chart_left, chart_right = st.columns(2)

with chart_left:
    gmv_chart = px.line(
        daily_trend,
        x="date",
        y="gmv",
        title="每日GMV趋势",
        labels={
            "date": "日期",
            "gmv": "GMV",
        },
    )

    st.plotly_chart(
        gmv_chart,
        use_container_width=True,
    )

with chart_right:
    sku_chart = px.bar(
        sku_summary,
        x="sku_name",
        y="gmv",
        color="sku_name",
        title="各SKU的GMV贡献",
        labels={
            "sku_name": "商品",
            "gmv": "GMV",
        },
    )

    sku_chart.update_layout(
        showlegend=False,
    )

    st.plotly_chart(
        sku_chart,
        use_container_width=True,
    )


st.header("经营风险")

risks = detect_all_risks(sales_data)

if risks.empty:
    st.success("当前没有发现符合规则的经营风险。")
else:
    st.caption(
        f"规则引擎共识别出 {len(risks)} 条风险，"
        "以下结论均附带数据证据。"
    )

    for _, risk in risks.iterrows():
        risk_message = (
            f"**{risk['sku_id']}｜{risk['sku_name']}｜"
            f"{risk['risk_type']}**\n\n"
            f"数据证据：{risk['evidence']}"
        )

        if risk["severity"] == "high":
            st.error(risk_message)
        else:
            
            st.warning(risk_message)
st.header("用户评价洞察")

uploaded_reviews = st.sidebar.file_uploader(
    "上传用户评价数据",
    type=["csv"],
    key="review_uploader",
)

if uploaded_reviews is None:
    review_source = SAMPLE_REVIEWS_PATH
    st.sidebar.info("当前使用模拟评价数据")
else:
    review_source = uploaded_reviews
    st.sidebar.success("已加载用户上传的评价数据")


try:
    review_data = load_review_data(review_source)
except ValueError as error:
    st.error(str(error))
    st.stop()


risks_with_reviews = add_review_evidence_to_risks(
    risks,
    review_data,
)

review_summary = analyze_review_themes(review_data)

total_reviews = len(review_data)
average_rating = review_data["rating"].mean()
negative_review_count = (
    review_data["rating"] <= 2
).sum()

review_metric_columns = st.columns(3)

review_metric_columns[0].metric(
    "评价数量",
    f"{total_reviews:,}",
)

review_metric_columns[1].metric(
    "平均评分",
    f"{average_rating:.2f} / 5",
)

review_metric_columns[2].metric(
    "负面评价数量",
    f"{negative_review_count:,}",
)


review_summary["negative_rate_percent"] = (
    review_summary["negative_rate"] * 100
)

review_chart = px.bar(
    review_summary,
    x="theme",
    y="negative_rate_percent",
    color="average_rating",
    title="各评价主题负面率",
    labels={
        "theme": "评价主题",
        "negative_rate_percent": "负面率（%）",
        "average_rating": "平均评分",
    },
)

st.plotly_chart(
    review_chart,
    use_container_width=True,
)


review_display = review_summary[
    [
        "theme",
        "review_count",
        "average_rating",
        "negative_rate",
    ]
].copy()

review_display.columns = [
    "评价主题",
    "评价数量",
    "平均评分",
    "负面率",
]

st.dataframe(
    review_display,
    use_container_width=True,
    hide_index=True,
    column_config={
        "平均评分": st.column_config.NumberColumn(
            format="%.2f",
        ),
        "负面率": st.column_config.NumberColumn(
            format="%.1%%",
        ),
    },
)
st.header("AI运营建议")

st.caption(
    "AI只能根据上方规则引擎提供的证据生成建议，"
    "建议需要经过人工审核后才能进入报告。"
)

if "ai_recommendations" not in st.session_state:
    st.session_state.ai_recommendations = ""

if st.button(
    "生成AI建议",
    type="primary",
    disabled=risks.empty,
):
    try:
        with st.spinner("本地模型正在分析经营风险……"):
            st.session_state.ai_recommendations = (
               generate_recommendations(risks_with_reviews)
            )

    except RuntimeError as error:
        st.error(str(error))


if st.session_state.ai_recommendations:
    st.text_area(
        "审核并修改AI建议",
        key="ai_recommendations",
        height=420,
    )

    review_status = st.radio(
        "人工审核结果",
        options=[
            "待审核",
            "采纳",
            "修改后采纳",
            "拒绝",
        ],
        horizontal=True,
    )

    risk_report = "\n".join(
        [
            (
                f"- {risk['sku_id']}｜"
                f"{risk['sku_name']}｜"
                f"{risk['risk_type']}："
                f"{risk['evidence']}"
            )
            for _, risk in risks_with_reviews.iterrows()
        ]
    )

    report_content = f"""# GrowthPilot 经营分析报告

> 本报告基于模拟数据生成，仅用于产品演示。

## 经营概览

- GMV：¥{total_gmv:,.0f}
- 销量：{total_units:,.0f}
- 毛利：¥{total_profit:,.0f}
- 毛利率：{overall_margin:.1%}
- 广告ROI：{overall_ad_roi:.2f}

## 规则识别风险

{risk_report}

## AI运营建议

{st.session_state.ai_recommendations}

## 人工审核结果

{review_status}

## 使用说明

AI建议仅作为运营参考，未经人工确认不得自动执行。
"""

    st.download_button(
        label="下载经营分析报告",
        data=report_content,
        file_name="growthpilot_report.md",
        mime="text/markdown",
    )
