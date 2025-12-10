import json
import re


def extract_json_from_llm_output(text: str):
    """
    从 LLM 输出中提取 JSON（参考 Node 逻辑，简化版）。
    """
    if not text:
        return []
    # 尝试直接解析
    try:
        return json.loads(text)
    except Exception:
        pass

    # 正则提取第一个 JSON 块
    match = re.search(r'(\[.*\]|\{.*\})', text, re.S)
    if match:
        candidate = match.group(1)
        try:
            return json.loads(candidate)
        except Exception:
            return []
    return []


