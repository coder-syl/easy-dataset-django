import json


def get_label_prompt(language: str, context: dict, project_id: str):
    """
    重建领域树的提示词（参考 Node 逻辑，精简版）。
    :param language: '中文' or 'en'
    :param context: {'text': toc_text}
    :param project_id: 项目 ID（可用于个性化）
    """
    text = context.get('text', '')[:100000]
    if language == 'en':
        return (
            "You are an expert at building a domain tree (taxonomy).\n"
            "Given the document table of contents, generate a hierarchical JSON array of tags.\n"
            "Requirements:\n"
            "1. Use concise tag names.\n"
            "2. Maintain hierarchy with children.\n"
            "3. Return pure JSON, no extra text.\n"
            f"TOC:\n{text}\n"
            'Output format example:\n'
            '[{"label": "Computer Science", "children": [{"label": "AI", "children": []}]}]'
        )
    else:
        return (
            "你是构建领域树的专家。\n"
            "根据文档目录生成分层标签树（JSON 数组）。\n"
            "要求：\n"
            "1. 标签简洁。\n"
            "2. 保持父子层级（children）。\n"
            "3. 只返回 JSON，不要额外文字。\n"
            f"目录内容：\n{text}\n"
            '输出示例：\n'
            '[{"label": "计算机", "children": [{"label": "人工智能", "children": []}]}]'
        )


