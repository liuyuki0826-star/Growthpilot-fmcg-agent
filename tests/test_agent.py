import pandas as pd

from src.agent import build_risk_prompt


def test_prompt_contains_evidence_and_constraints():
    risks = pd.DataFrame(
        [
            {
                "sku_id": "SKU001",
                "sku_name": "测试商品",
                "risk_type": "销量下降",
                "evidence": "最近7天销量下降50.0%",
            }
        ]
    )

    prompt = build_risk_prompt(risks)

    assert "最近7天销量下降50.0%" in prompt
    assert "不得添加证据中没有出现的数字" in prompt
    assert "不得把两个同时发生的现象直接判断为因果关系" in prompt
    assert "现有数据无法确认原因" in prompt