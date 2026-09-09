import pandas as pd
import requests


DEFAULT_MODEL = "qwen2.5:3b"
DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434"


def build_risk_prompt(risks: pd.DataFrame) -> str:
    """把规则检测结果转换成受约束的提示词。"""

    evidence_lines = []

    for _, risk in risks.iterrows():
        evidence_lines.append(
            f"- {risk['sku_id']} {risk['sku_name']}："
            f"{risk['risk_type']}；证据：{risk['evidence']}"
        )

    evidence_text = "\n".join(evidence_lines)

    return f"""
你是一名快消电商运营分析助手。

以下风险已经由Python规则引擎计算并验证：

{evidence_text}

请根据以上证据生成中文运营建议。

必须遵守以下要求：
1. 不得编造证据中没有出现的销量、金额、利润或库存数字。
2. 不得把相关性直接描述为因果关系。
3. 原因不确定时使用“可能”，并说明需要补充哪些信息。
4. 每个风险分别输出：观察、可能原因、建议行动、验证指标。
5. 建议必须可由运营人员审核，不得声称已经自动执行。
6. 内容简洁，使用Markdown格式。
""".strip()

def build_risk_prompt(risks: pd.DataFrame) -> str:
    """把规则检测结果转换成严格受约束的提示词。"""

    evidence_lines = []

    for _, risk in risks.iterrows():
        evidence_lines.append(
            f"- SKU：{risk['sku_id']}\n"
            f"  商品：{risk['sku_name']}\n"
            f"  风险：{risk['risk_type']}\n"
            f"  已知证据：{risk['evidence']}"
        )

    evidence_text = "\n".join(evidence_lines)

    return f"""
你是快消电商运营分析助手。

你只能使用下面由Python规则引擎验证过的证据：

{evidence_text}

禁止事项：
- 不得添加证据中没有出现的数字。
- 不得猜测季节、竞品、价格、促销、消费者行为或广告内容。
- 不得把两个同时发生的现象直接判断为因果关系。
- 不得声称建议已经执行。

请对每一条风险单独使用以下固定格式：

## SKU编号 商品名称｜风险类型
- 观察：原样引用已知证据。
- 判断：如果证据不足，请明确写“现有数据无法确认原因”。
- 建议行动：给出1至2项需要人工执行的检查或调整。
- 需要补充的数据：列出确认原因需要的数据。
- 验证指标：列出建议执行后应持续观察的指标。

只输出以上分析，不要输出表格，不要添加开场白。
""".strip()
def generate_recommendations(
    risks: pd.DataFrame,
    model: str = DEFAULT_MODEL,
    base_url: str = DEFAULT_OLLAMA_URL,
) -> str:
    """调用本地Ollama生成运营建议。"""

    if risks.empty:
        return "当前未发现需要解释的经营风险。"

    prompt = build_risk_prompt(risks)

    try:
        response = requests.post(
            f"{base_url}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.2,
                },
            },
            timeout=180,
        )

        response.raise_for_status()
        result = response.json()

        return result["response"].strip()

    except requests.RequestException as error:
        raise RuntimeError(
            "无法连接本地Ollama，请确认Ollama应用已经运行。"
        ) from error