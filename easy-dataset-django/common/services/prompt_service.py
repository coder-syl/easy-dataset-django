"""
提示词服务
管理各种提示词模板
"""
from typing import Dict, Optional
from llm.models import CustomPrompt
from projects.models import Project
import json


# 默认提示词模板
ANSWER_PROMPT_ZH = """# Role: 微调数据集生成专家
## Profile:
- Description: 你是一名微调数据集生成专家，擅长从给定的内容中生成准确的问题答案，确保答案的准确性和相关性，你要直接回答用户问题，所有信息已内化为你的专业知识。

## Skills:
1. 答案必须基于给定的内容
2. 答案必须准确，不能胡编乱造
3. 答案必须与问题相关
4. 答案必须符合逻辑
5. 基于给定参考内容，用自然流畅的语言整合成一个完整答案，不需要提及文献来源或引用标记

## Workflow:
1. Take a deep breath and work on this problem step-by-step.
2. 首先，分析给定的文件内容
3. 然后，从内容中提取关键信息
4. 接着，生成与问题相关的准确答案
5. 最后，确保答案的准确性和相关性

## 参考内容：

------ 参考内容 Start ------
{{text}}
------ 参考内容 End ------

## 问题
{{question}}

## Constrains:
1. 答案必须基于给定的内容
2. 答案必须准确，必须与问题相关，不能胡编乱造
3. 答案必须充分、详细、包含所有必要的信息、适合微调大模型训练使用
4. 答案中不得出现 ' 参考 / 依据 / 文献中提到 ' 等任何引用性表述，只需呈现最终结论
{{templatePrompt}}
{{outputFormatPrompt}}
"""

ANSWER_PROMPT_EN = """# Role: Fine-tuning Dataset Generation Expert
## Profile:
- Description: You are an expert in generating fine-tuning datasets, skilled at generating accurate answers to questions from the given content, ensuring the accuracy and relevance of the answers.

## Skills:
1. The answer must be based on the given content.
2. The answer must be accurate and not fabricated.
3. The answer must be relevant to the question.
4. The answer must be logical.

## Workflow:
1. Take a deep breath and work on this problem step-by-step.
2. First, analyze the given file content.
3. Then, extract key information from the content.
4. Next, generate an accurate answer related to the question.
5. Finally, ensure the accuracy and relevance of the answer.

## Reference Content:

------ Reference Content Start ------
{{text}}
------ Reference Content End ------

## Question
{{question}}

## Constrains:
1. The answer must be based on the given content.
2. The answer must be accurate and relevant to the question, and no fabricated information is allowed.
3. The answer must be comprehensive and detailed, containing all necessary information, and it is suitable for use in the training of fine-tuning large language models.
{{templatePrompt}}
{{outputFormatPrompt}}
"""

QUESTION_PROMPT_ZH = """# Role: 文本问题生成专家
## Profile:
- Description: 你是一名专业的文本分析与问题设计专家，能够从复杂文本中提炼关键信息并产出可用于模型微调的高质量问题集合。
- Input Length: {{textLength}} 字
- Output Goal: 生成不少于 {{number}} 个高质量问题，用于构建问答训练数据集。

## Skills:
1. 能够全面理解原文内容，识别核心概念、事实与逻辑结构。
2. 擅长设计具有明确答案指向性的问题，覆盖文本多个侧面。
3. 善于控制问题难度与类型，保证多样性与代表性。
4. 严格遵守格式规范，确保输出可直接用于程序化处理。

## Workflow:
1. **文本解析**：通读全文，分段识别关键实体、事件、数值与结论。
2. **问题设计**：基于信息密度和重要性选择最佳提问切入点{{gaPromptNote}}。
3. **质量检查**：逐条校验问题，确保：
   - 问题答案可在原文中直接找到依据。
   - 问题之间主题不重复、角度不雷同。
   - 语言表述准确、无歧义且符合常规问句形式。
   {{gaPromptCheck}}

## Constraints:
1. 所有问题必须严格依据原文内容，不得添加外部信息或假设情境。
2. 问题需覆盖文本的不同主题、层级或视角，避免集中于单一片段。
3. 禁止输出与材料元信息相关的问题（如作者、章节、目录等）。
4. 问题不得包含"报告/文章/文献/表格中提到"等表述，需自然流畅。
5. 输出不少于 {{number}} 个问题，且保持格式一致。

## Output Format:
- 使用合法的 JSON 数组，仅包含字符串元素。
- 字段必须使用英文双引号。
- 严格遵循以下结构：
```
["问题1", "问题2", "..."]
```

## Text to Analyze:
{{text}}

## GA Instruction (Optional):
{{gaPrompt}}
"""

QUESTION_PROMPT_EN = """# Role: Text Question Generation Expert
## Profile:
- Description: You are an expert in text analysis and question design, capable of extracting key information from complex passages and producing high-quality questions for fine-tuning datasets.
- Input Length: {{textLength}} characters
- Output Goal: Generate at least {{number}} high-quality questions suitable for training data.

## Skills:
1. Comprehend the source text thoroughly and identify core concepts, facts, and logical structures.
2. Design questions with clear answer orientation that cover multiple aspects of the text.
3. Balance difficulty and variety to ensure representative coverage of the content.
4. Enforce strict formatting so the output can be consumed programmatically.

## Workflow:
1. **Text Parsing**: Read the entire passage, segment it, and capture key entities, events, metrics, and conclusions.
2. **Question Design**: Select the most informative focal points to craft questions{{gaPromptNote}}.
3. **Quality Check**: Validate each question to ensure:
   - The answer can be located directly in the original text.
   - Questions do not duplicate topics or angles.
   - Wording is precise, unambiguous, and uses natural interrogative phrasing.
   {{gaPromptCheck}}

## Constraints:
1. Every question must be grounded strictly in the provided text; no external information or hypothetical scenarios.
2. Cover diverse themes, layers, or perspectives from the passage; avoid clustering around one segment.
3. Do not include questions about meta information (author, chapters, table of contents, etc.).
4. Avoid phrases such as "in the report/article/literature/table"; questions must read naturally.
5. Produce at least {{number}} questions with consistent formatting.

## Output Format:
- Return a valid JSON array containing only strings.
- Use double quotes for all strings.
- Follow this exact structure:
```
["Question 1", "Question 2", "..."]
```

## Text to Analyze:
{{text}}

## GA Instruction (Optional):
{{gaPrompt}}
"""

# 数据清洗提示词
CLEAN_PROMPT_ZH = """# Role: 数据清洗与润色专家
## Profile:
- 你擅长对原文进行去噪、去重复、去冗余、纠正错别字与格式问题，同时严格保持语义不失真。

## Goals:
1. 保留原文事实与语义，不增加或删除关键信息。
2. 去除无意义字符、重复段落、乱码与多余空白。
3. 适度分段，保证可读性。

## Output:
- 直接返回清洗后的正文文本，不要附加解释。

## Text:
{{text}}
"""

CLEAN_PROMPT_EN = """# Role: Text Cleaning Specialist
## Profile:
- You remove noise, duplicates, typos and formatting issues while preserving the original meaning.

## Goals:
1. Preserve facts and meaning; do not invent or drop key information.
2. Remove meaningless characters, duplicated paragraphs, garbled text, and extra whitespace.
3. Keep the text readable with light reformatting.

## Output:
- Return only the cleaned text, no explanations.

## Text:
{{text}}
"""


def get_answer_prompt(language: str, text: str, question: str, project_id: Optional[str] = None) -> str:
    """
    获取答案生成提示词
    :param language: 语言 (zh/en)
    :param text: 参考文本
    :param question: 问题
    :param project_id: 项目ID（用于获取自定义提示词）
    :return: 提示词
    """
    # 尝试获取自定义提示词
    if project_id:
        custom_prompt = CustomPrompt.objects.filter(
            project_id=project_id,
            prompt_type='answer',
            prompt_key='ANSWER_PROMPT',
            language='zh-CN' if language == '中文' else 'en'
        ).first()
        
        if custom_prompt:
            template = custom_prompt.content
        else:
            template = ANSWER_PROMPT_ZH if language == '中文' else ANSWER_PROMPT_EN
    else:
        template = ANSWER_PROMPT_ZH if language == '中文' else ANSWER_PROMPT_EN
    
    # 替换占位符
    prompt = template.replace('{{text}}', text).replace('{{question}}', question)
    prompt = prompt.replace('{{templatePrompt}}', '').replace('{{outputFormatPrompt}}', '')
    
    return prompt


def build_answer_prompt(language: str, context: Dict, project_id: Optional[str] = None) -> str:
    """
    兼容 Next 端调用的提示词构建函数
    :param language: 语言 (zh/en)
    :param context: 包含 text/question 或 content/templatePrompt/outputFormatPrompt
    :param project_id: 项目ID（用于获取自定义提示词）
    """
    text = context.get('text') or context.get('content') or ''
    question = context.get('question', '')
    template_prompt = context.get('templatePrompt', '')
    output_format_prompt = context.get('outputFormatPrompt', '')

    # 复用已有逻辑
    prompt = get_answer_prompt(language, text, question, project_id)
    prompt = prompt.replace('{{templatePrompt}}', template_prompt).replace('{{outputFormatPrompt}}', output_format_prompt)
    return prompt


def get_question_prompt(language: str, text: str, number: int = 5, 
                       ga_prompt: str = '', project_id: Optional[str] = None) -> str:
    """
    获取问题生成提示词
    :param language: 语言 (zh/en)
    :param text: 文本内容
    :param number: 问题数量
    :param ga_prompt: GA提示词（可选）
    :param project_id: 项目ID（用于获取自定义提示词）
    :return: 提示词
    """
    # 尝试获取自定义提示词
    if project_id:
        custom_prompt = CustomPrompt.objects.filter(
            project_id=project_id,
            prompt_type='question',
            prompt_key='QUESTION_PROMPT',
            language='zh-CN' if language == '中文' else 'en'
        ).first()
        
        if custom_prompt:
            template = custom_prompt.content
        else:
            template = QUESTION_PROMPT_ZH if language == '中文' else QUESTION_PROMPT_EN
    else:
        template = QUESTION_PROMPT_ZH if language == '中文' else QUESTION_PROMPT_EN
    
    # 构建GA提示词相关部分
    ga_prompt_note = ', 并结合指定的体裁受众视角' if (ga_prompt and language == '中文') else ', and incorporate the specified genre-audience perspective' if ga_prompt else ''
    ga_prompt_check = '- 问题风格与指定的体裁受众匹配' if (ga_prompt and language == '中文') else '- Question style matches the specified genre and audience' if ga_prompt else ''
    
    # 替换占位符
    prompt = template.replace('{{textLength}}', str(len(text)))
    prompt = prompt.replace('{{number}}', str(number))
    prompt = prompt.replace('{{text}}', text)
    prompt = prompt.replace('{{gaPrompt}}', ga_prompt)
    prompt = prompt.replace('{{gaPromptNote}}', ga_prompt_note)
    prompt = prompt.replace('{{gaPromptCheck}}', ga_prompt_check)
    
    return prompt


def get_clean_prompt(language: str, text: str) -> str:
    """
    获取数据清洗提示词
    :param language: 语言 (zh/en)
    :param text: 待清洗文本
    :return: 提示词
    """
    template = CLEAN_PROMPT_ZH if language in ['中文', 'zh-CN', 'zh'] else CLEAN_PROMPT_EN
    return template.replace('{{text}}', text)


def get_ga_prompt(language: str, genre: str, audience: str) -> str:
    """
    获取GA提示词
    :param language: 语言
    :param genre: 体裁
    :param audience: 受众
    :return: GA提示词
    """
    if language == 'en':
        return f"""## Special Requirements - Genre & Audience Perspective Questioning:
**Target Genre**: {genre}
**Target Audience**: {audience}

Please ensure:
1. The question should fully conform to the style, focus, depth, and other attributes defined by "{genre}".
2. The question should consider the knowledge level, cognitive characteristics, and potential points of interest of "{audience}".
3. Propose questions from the perspective and needs of this audience group.
4. Maintain the specificity and practicality of the questions, ensuring consistency in the style of questions and answers.
5. The question should have a certain degree of clarity and specificity, avoiding being too broad or vague.
"""
    else:
        return f"""**目标体裁**: {genre}
**目标受众**: {audience}

请确保：
1. 问题应完全符合「{genre}」所定义的风格、焦点和深度等等属性。
2. 问题应考虑到「{audience}」的知识水平、认知特点和潜在兴趣点。
3. 从该受众群体的视角和需求出发提出问题
4. 保持问题的针对性和实用性，确保问题-答案的风格一致性
5. 问题应具有一定的清晰度和具体性，避免过于宽泛或模糊。
"""


# ---------------- 标签分配提示词 -----------------
LABEL_PROMPT_ZH = """你是一个标注助手，请为每个问题选择最合适的标签。
可选标签列表（不要输出列表，只用于选择）：
{{labels}}

输出要求：
- 必须返回合法 JSON 数组，每个元素包含 question 和 label 字段。
- label 必须从给定的标签列表中选择，若确实无匹配请填空字符串 ""。
格式示例：
[{"question":"Q1","label":"标签A"},{"question":"Q2","label":""}]

待标注问题：
{{questions}}
"""

LABEL_PROMPT_EN = """You are a labeling assistant. For each question, pick the best label from the provided list.
Label choices (do NOT output this list, only pick from it):
{{labels}}

Output requirements:
- Return a valid JSON array, each element has question and label fields.
- label must be chosen from the list; if none fits, use empty string "".
Example:
[{"question":"Q1","label":"LabelA"},{"question":"Q2","label":""}]

Questions to label:
{{questions}}
"""


def get_label_prompt(language: str, labels, questions) -> str:
    """构造标签分配提示词，labels/questions 均为列表"""
    labels_text = json.dumps(labels, ensure_ascii=False)
    questions_text = json.dumps(questions, ensure_ascii=False)
    tpl = LABEL_PROMPT_ZH if language.startswith('zh') else LABEL_PROMPT_EN
    return tpl.replace('{{labels}}', labels_text).replace('{{questions}}', questions_text)

