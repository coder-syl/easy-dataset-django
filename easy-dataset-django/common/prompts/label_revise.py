import json


def get_label_revise_prompt(language: str, context: dict, project_id: str):
    """
    增量修订领域树的提示词（参考 Node 逻辑，精简版）。
    context: {
      text: all toc,
      existingTags: filtered existing tags,
      newContent: new toc,
      deletedContent: deleted toc
    }
    """
    text = context.get('text', '')[:100000]
    existing = context.get('existingTags', [])
    new_content = context.get('newContent', '')
    deleted_content = context.get('deletedContent', '')

    existing_json = json.dumps(existing, ensure_ascii=False)

    if language == 'en':
        return (
            "You are an expert at revising a domain tree (taxonomy).\n"
            "Given the existing tags and updated table of contents, update only the changed parts.\n"
            "If files are deleted, remove related tags; if new content appears, add tags accordingly.\n"
            "Return pure JSON array of tags.\n"
            f"Existing tags (JSON):\n{existing_json}\n"
            f"New content TOC:\n{new_content}\n"
            f"Deleted content TOC:\n{deleted_content}\n"
            f"Full TOC (for reference):\n{text}\n"
            "Output example: same structure as input tags."
        )
    else:
        return (
            "你是领域树修订专家。\n"
            "给定现有标签树和更新后的目录，只修订变化部分：新增内容对应的标签应补充，删除的内容对应标签应移除。\n"
            "返回纯 JSON 数组，结构与现有标签一致（包含 children）。\n"
            f"现有标签（JSON）：\n{existing_json}\n"
            f"新增内容 TOC：\n{new_content}\n"
            f"删除内容 TOC：\n{deleted_content}\n"
            f"完整 TOC（参考）：\n{text}\n"
            "输出示例：结构与输入标签一致。"
        )


