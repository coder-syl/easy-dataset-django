"""
提示词服务
管理各种提示词模板
"""
from typing import Dict, Optional
from llm.models import CustomPrompt


def _get_custom_prompt_content(project_id: Optional[str], prompt_type: str, prompt_key: str, language: str) -> Optional[str]:
    """
    通用获取自定义提示词的辅助函数（与 Node getPromptContent 逻辑一致）：
    - 按 project_id + prompt_type + prompt_key + language 查找
    - 检查 is_active 字段（与 Node.js 的 isActive 检查保持一致）
    - 返回 content，找不到或未激活返回 None
    """
    if not project_id:
        return None

    lang_code = 'zh-CN' if language.startswith('zh') else 'en'
    custom_prompt = CustomPrompt.objects.filter(
        project_id=project_id,
        prompt_type=prompt_type,
        prompt_key=prompt_key,
        language=lang_code,
        is_active=True  # 与 Node.js 保持一致：只返回激活的自定义提示词
    ).first()

    # 与 Node.js 保持一致：检查 isActive 和 content
    if custom_prompt and getattr(custom_prompt, 'is_active', True) and getattr(custom_prompt, 'content', None):
        return custom_prompt.content
    return None

# ======================= 默认提示词模板（补齐 Node 侧类型） =======================
# 简化默认模板，确保所有类型都有兜底，可被项目自定义覆盖。
PROMPT_DEFAULTS = {
    # 内容生成
    "ENHANCED_ANSWER_PROMPT": {
        "zh-CN": "你是答案生成专家，基于 {{text}} 回答 {{question}}，结合体裁受众指引 {{gaPrompt}}，可选模板 {{templatePrompt}}，输出格式 {{outputFormatPrompt}}。",
        "en": "You are an answer expert. Based on {{text}}, answer {{question}}, adapt to GA {{gaPrompt}}, optional templatePrompt {{templatePrompt}}, outputFormatPrompt {{outputFormatPrompt}}."
    },
    # GA 生成（完整模板）
    "GA_GENERATION_PROMPT": {
        "zh-CN": """# Role: 体裁与受众设计专家
## Profile:
- Description: 你是一名擅长内容分析与创意提炼的专家，能够依据文本内容设计出多样且高质量的 [体裁]-[受众] 组合，以支撑问题生成与风格化回答。
- Output Goal: 生成 5 对独特且互相区分的 [体裁]-[受众] 组合。

## Skills:
1. 深入理解原文的主题、结构、语调与潜在价值。
2. 具备丰富的体裁知识，能够从事实概念、分析推理、评估创造、操作指导等角度设计差异化提问风格。
3. 善于刻画受众画像，涵盖不同年龄、背景、动机与学习需求，避免单一视角。
4. 输出信息清晰、完整，且便于下游系统直接使用。

## Workflow:
1. **文本洞察**：通读原文，分析写作风格、信息密度、可延展方向。
2. **场景构思**：设想至少 5 种学习或探究场景，思考如何在保留核心信息的前提下拓展体裁与受众的多样性。
3. **组合设计**：为每个场景分别生成独立的体裁与对应受众描述，确保两者之间具有明确匹配逻辑。
4. **重复校验**：确认 5 对组合在体裁类型、表达风格、受众画像上均无重复或高度相似项。

## Constraints:
1. 每对组合必须包含详细的体裁标题与 2-3 句描述，突出语言风格、情绪基调、表达形式等要素；禁止使用视觉类体裁（如漫画、视频）。
2. 每个受众需提供 2 句描述，涵盖其背景特征、认知水平、兴趣点与期望目标；需兼顾积极与冷淡受众，体现多元化。
3. 体裁与受众的匹配需自然合理，能够指导后续的问题风格与回答方式。
4. 输出不得包含与原文无关的臆测，不得沿用已有组合模板。
5. 必须严格返回 5 对组合，顺序不限，但禁止出现额外说明文字。

## Output Format:
- 仅返回合法 JSON 数组，数组长度为 5。
- 每个元素包含 `genre` 与 `audience` 两个对象，均需包含 `title` 与 `description` 字段。
- 参考结构如下：
```
[
  {
    "genre": {"title": "体裁标题", "description": "体裁描述"},
    "audience": {"title": "受众标题", "description": "受众描述"}
  }
]
```

## Examples:
- 体裁示例：“深究原因型” —— 描述聚焦于“为什么/如何”类提问，强调逻辑链条与原理阐述。
- 受众示例：“对技术细节好奇的工程师实习生” —— 描述其背景、动机与学习目标。

## Source Text to Analyze:
{{text}}""",
        "en": """# Role: Genre & Audience Design Specialist
## Profile:
- Description: You are an expert in content analysis and creative abstraction, capable of crafting diverse, high-quality [Genre]-[Audience] pairings based on the source text to support question generation and stylized responses.
- Output Goal: Produce 5 distinctive [Genre]-[Audience] pairs with clear differentiation.

## Skills:
1. Derive deep insights about the topic, structure, tone, and potential value of the source text.
2. Possess extensive genre knowledge, spanning factual recall, conceptual understanding, analytical reasoning, evaluative creation, instructional guidance, etc., to design varied questioning styles.
3. Portray audiences across age, expertise, motivation, and engagement levels, ensuring multi-perspective coverage.
4. Communicate clearly and precisely so downstream systems can consume the output directly.

## Workflow:
1. **Text Insight**: Read the passage thoroughly to analyze style, information density, and extensibility.
2. **Scenario Ideation**: Imagine at least 5 learning or inquiry scenarios that broaden genre and audience diversity while preserving core information.
3. **Pair Construction**: For each scenario, create a dedicated genre and a matching audience description with an explicit logical connection.
4. **Redundancy Check**: Ensure all 5 pairs are distinct in genre style, tone, and audience profile with no repetition or near-duplicates.

## Constraints:
1. Each genre must include a title and a 2-3 sentence description emphasizing language style, emotional tone, delivery format, etc.; exclude visual formats (e.g., comics, video).
2. Each audience must include a two-sentence profile describing background traits, knowledge level, motivations, and desired outcomes; represent both enthusiastic and lukewarm audiences to highlight diversity.
3. Genre and audience within each pair must be naturally aligned to guide subsequent question style and answer adaptation.
4. Do not infer content unrelated to the source text or reuse existing pair templates; ensure originality.
5. Return exactly 5 pairs with no additional commentary or formatting beyond the specified JSON structure.

## Output Format:
- Respond with a valid JSON array of length 5.
- Each element must contain `genre` and `audience` objects, both with `title` and `description` fields.
- Follow the example structure:
```
[
  {
    "genre": {"title": "Genre Title", "description": "Genre description"},
    "audience": {"title": "Audience Title", "description": "Audience description"}
  }
]
```

## Examples:
- Genre Example: "Root Cause Analysis" — Focused on "why/how" questioning with logical, principle-driven exploration.
- Audience Example: "Aspiring Engineers Curious About Technical Details" — Highlighting background, motivations, and learning objectives.

## Source Text to Analyze:
{{text}}""",
        "tr": """# Rol: Tür ve Hedef Kitle Tasarım Uzmanı
## Profil:
- Açıklama: İçerik analizi ve yaratıcı soyutlama konusunda uzman, soru oluşturma ve stilize yanıtları desteklemek için kaynak metne dayalı çeşitli, yüksek kaliteli [Tür]-[Hedef Kitle] eşleştirmeleri oluşturma yeteneğine sahipsiniz.
- Çıktı Hedefi: Net ayrıma sahip 5 farklı [Tür]-[Hedef Kitle] çifti üretin.

## Yetenekler:
1. Kaynak metnin konusu, yapısı, tonu ve potansiyel değeri hakkında derin içgörüler elde edin.
2. Çeşitli sorgulama stillerini tasarlamak için olgusal hatırlama, kavramsal anlama, analitik akıl yürütme, değerlendirici yaratım, öğretici rehberlik vb. kapsayan geniş tür bilgisine sahip olun.
3. Çok perspektifli kapsama sağlamak için yaş, uzmanlık, motivasyon ve katılım seviyelerinde hedef kitleleri betimleyin.
4. Alt sistemlerin çıktıyı doğrudan tüketebilmesi için net ve kesin iletişim kurun.

## İş Akışı:
1. **Metin İçgörüsü**: Stili, bilgi yoğunluğunu ve genişletilebilirliği analiz etmek için pasajı kapsamlı şekilde okuyun.
2. **Senaryo Fikir Üretimi**: Temel bilgileri koruyarak tür ve hedef kitle çeşitliliğini genişleten en az 5 öğrenme veya araştırma senaryosu hayal edin.
3. **Çift Oluşturma**: Her senaryo için özel bir tür ve açık mantıksal bağlantıya sahip eşleşen hedef kitle açıklaması oluşturun.
4. **Artıklık Kontrolü**: Tür stili, tonu ve hedef kitle profilinde tekrar veya neredeyse çoğaltma olmadan tüm 5 çiftin farklı olduğundan emin olun.

## Kısıtlamalar:
1. Her tür, dil stili, duygusal ton, sunum formatı vb. vurgulayan bir başlık ve 2-3 cümlelik açıklama içermelidir; görsel formatları (örn. çizgi roman, video) hariç tutun.
2. Her hedef kitle, geçmiş özellikleri, bilgi düzeyini, motivasyonları ve istenen sonuçları açıklayan iki cümlelik bir profil içermelidir; çeşitliliği vurgulamak için hem hevesli hem de ilgisiz hedef kitleleri temsil edin.
3. Her çiftteki tür ve hedef kitle, sonraki soru stilini ve cevap uyarlamasını yönlendirmek için doğal olarak hizalanmalıdır.
4. Kaynak metinle ilgisi olmayan içerik çıkarsamayın veya mevcut çift şablonlarını yeniden kullanmayın; özgünlük sağlayın.
5. Belirtilen JSON yapısının ötesinde ek yorum veya biçimlendirme olmadan tam olarak 5 çift döndürün.

## Çıktı Formatı:
- Uzunluğu 5 olan geçerli bir JSON dizisiyle yanıt verin.
- Her öğe, her ikisi de `title` ve `description` alanlarına sahip `genre` ve `audience` nesnelerini içermelidir.
- Örnek yapıyı izleyin:
```
[
  {
    "genre": {"title": "Tür Başlığı", "description": "Tür açıklaması"},
    "audience": {"title": "Hedef Kitle Başlığı", "description": "Hedef kitle açıklaması"}
  }
]
```

## Örnekler:
- Tür Örneği: "Kök Neden Analizi" — Mantıksal, ilke odaklı keşifle "neden/nasıl" sorgulamaya odaklanır.
- Hedef Kitle Örneği: "Teknik Detaylara Meraklı Aday Mühendisler" — Geçmişi, motivasyonları ve öğrenme hedeflerini vurgular.

## Analiz Edilecek Kaynak Metin:
{{text}}"""
    },
    "DISTILL_QUESTIONS_PROMPT": {
        "zh-CN": "为标签 {{currentTag}} (路径 {{tagPath}}) 生成 {{count}} 个多样高质量问题，避免与 {{existingQuestions}} 重复。",
        "en": "Generate {{count}} diverse, high-quality questions for tag {{currentTag}} (path {{tagPath}}); avoid duplicates with {{existingQuestions}}."
    },
    # 标签
    "DISTILL_TAGS_PROMPT": {
        "zh-CN": "基于父标签 {{parentTag}} (路径 {{tagPath}}) 生成 {{count}} 个子标签，参考已有子标签 {{existingTagsText}}，保持层级合理。",
        "en": "Generate {{count}} sub-tags for parent {{parentTag}} (path {{tagPath}}), referencing {{existingTagsText}}, keep hierarchy reasonable."
    },
    "LABEL_REVISE_PROMPT": {
        "zh-CN": "根据最新目录 {{text}} 对现有标签树 {{existingTags}} 增量修订，可选删除 {{deletedContent}} / 新增 {{newContent}}。",
        "en": "Incrementally revise tag tree {{existingTags}} with latest toc {{text}}; optional deletedContent {{deletedContent}} / newContent {{newContent}}."
    },
    "ADD_LABEL_PROMPT": {
        "zh-CN": "为问题数组 {{question}} 匹配最佳标签，标签列表 {{label}}，输出 [{question, label}]。",
        "en": "Assign best labels from {{label}} to questions {{question}}. Output [{question, label}]."
    },
    # 多轮对话
    "ASSISTANT_REPLY_PROMPT": {
        "zh-CN": "多轮对话助手回复。场景 {{scenario}}，角色A {{roleA}}，角色B {{roleB}}，文本 {{chunkContent}}，历史 {{conversationHistory}}，当前 {{currentRound}}/{{totalRounds}}。生成下一条助手回复。",
        "en": "Multi-turn assistant reply. Scenario {{scenario}}, roleA {{roleA}}, roleB {{roleB}}, text {{chunkContent}}, history {{conversationHistory}}, round {{currentRound}}/{{totalRounds}}. Generate next assistant reply."
    },
    "NEXT_QUESTION_PROMPT": {
        "zh-CN": "多轮对话问题生成。场景 {{scenario}}，角色A {{roleA}}，角色B {{roleB}}，文本 {{chunkContent}}，历史 {{conversationHistory}}，下一轮 {{nextRound}}/{{totalRounds}}。生成下一问题。",
        "en": "Multi-turn question generation. Scenario {{scenario}}, roleA {{roleA}}, roleB {{roleB}}, text {{chunkContent}}, history {{conversationHistory}}, nextRound {{nextRound}}/{{totalRounds}}. Generate next question."
    },
    # 图像
    "IMAGE_QUESTION_PROMPT": {
        "zh-CN": "基于图像内容生成 {{number}} 个高质量问题，用于视觉问答。",
        "en": "Generate {{number}} high-quality questions from image content for VQA."
    },
    # 内容优化
    "NEW_ANSWER_PROMPT": {
        "zh-CN": "答案优化重写：文本 {{chunkContent}}，问题 {{question}}，原答案 {{answer}}，思维链 {{cot}}，建议 {{advice}}。输出改写的更优答案。",
        "en": "Answer rewrite: chunk {{chunkContent}}, question {{question}}, answer {{answer}}, CoT {{cot}}, advice {{advice}}. Produce improved rewritten answer."
    },
    "OPTIMIZE_COT_PROMPT": {
        "zh-CN": "思维链优化：问题 {{originalQuestion}}，答案 {{answer}}，原始思维链 {{originalCot}}。优化推理与表达。",
        "en": "Chain-of-thought optimization: question {{originalQuestion}}, answer {{answer}}, original CoT {{originalCot}}. Improve reasoning and clarity."
    },
}


def _get_default_prompt(prompt_key: str, language: str) -> str:
    """
    获取默认提示词（与 Node.js 的 processPrompt 保持一致）
    :param prompt_key: 提示词键名（如 'GA_GENERATION_PROMPT', 'GA_GENERATION_PROMPT_EN'）
    :param language: 语言代码（'zh-CN', 'en', 'tr'）
    :return: 默认提示词内容
    """
    # 处理带语言后缀的键名（如 'GA_GENERATION_PROMPT_EN'）
    if prompt_key.endswith('_EN'):
        base_key = prompt_key[:-3]  # 移除 '_EN'
        lang_code = 'en'
    elif prompt_key.endswith('_TR'):
        base_key = prompt_key[:-3]  # 移除 '_TR'
        lang_code = 'tr'
    else:
        base_key = prompt_key
        # 根据 language 参数确定语言代码
        if language == 'en':
            lang_code = 'en'
        elif language == 'tr':
            lang_code = 'tr'
        else:
            lang_code = 'zh-CN'
    
    return PROMPT_DEFAULTS.get(base_key, {}).get(lang_code, '')


def _process_prompt(template: str, params: Dict[str, str]) -> str:
    result = template or ''
    for k, v in params.items():
        result = result.replace(f'{{{{{k}}}}}', str(v) if v is not None else '')
    return result
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

QUESTION_PROMPT_TR = """# Rol: Metin Soru Üretim Uzmanı
## Profil:
- Açıklama: Karmaşık metinlerden temel bilgileri çıkarabilen ve ince ayar veri setleri için yüksek kaliteli sorular üretebilen bir metin analizi ve soru tasarımı uzmanısınız.
- Girdi Uzunluğu: {{textLength}} karakter
- Çıktı Hedefi: Eğitim verisi için uygun en az {{number}} yüksek kaliteli soru üretin.

## Yetenekler:
1. Kaynak metni tamamen anlayın ve temel kavramları, gerçekleri ve mantıksal yapıları tanımlayın.
2. Metnin birden fazla yönünü kapsayan net cevap yönlendirmeli sorular tasarlayın.
3. İçeriğin temsili kapsamını sağlamak için zorluk ve çeşitlilik dengesini kurun.
4. Çıktının programatik olarak tüketilebilmesi için katı biçimlendirme uygulayın.

## İş Akışı:
1. **Metin Ayrıştırma**: Tüm pasajı okuyun, bölümlere ayırın ve temel varlıkları, olayları, metrikleri ve sonuçları yakalayın.
2. **Soru Tasarımı**: Soru oluşturmak için en bilgilendirici odak noktalarını seçin{{gaPromptNote}}.
3. **Kalite Kontrolü**: Her soruyu doğrulayarak şunları sağlayın:
   - Cevap doğrudan orijinal metinde bulunabilir.
   - Sorular konuları veya açıları tekrar etmez.
   - İfade kesin, belirsiz değil ve doğal soru tümcecikleri kullanır.
   {{gaPromptCheck}}

## Kısıtlamalar:
1. Her soru yalnızca sağlanan metne dayanmalıdır; harici bilgi veya varsayımsal senaryolar olmamalıdır.
2. Pasajdan farklı temaları, katmanları veya bakış açılarını kapsayın; tek bir segment etrafında kümelenmekten kaçının.
3. Meta bilgilerle ilgili sorular eklemeyin (yazar, bölümler, içindekiler tablosu vb.).
4. "Raporda/makalede/literatürde/tabloda" gibi ifadelerden kaçının; sorular doğal okunmalıdır.
5. Tutarlı biçimlendirmeyle en az {{number}} soru üretin.

## Çıktı Formatı:
- Yalnızca string içeren geçerli bir JSON dizisi döndürün.
- Tüm stringler için çift tırnak kullanın.
- Bu yapıyı tam olarak takip edin:
```
["Soru 1", "Soru 2", "..."]
```

## Çıktı Örneği:
```
["Bir yapay zeka etik çerçevesi hangi temel unsurları içermelidir?", "Medeni Kanun kişisel veri koruma için hangi yeni düzenlemelere sahiptir?"]
```

## Analiz Edilecek Metin:
{{text}}

## GA Talimatı (Opsiyonel):
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
    template = _get_custom_prompt_content(
        project_id,
        prompt_type='answer',
        prompt_key='ANSWER_PROMPT',
        language='zh-CN' if language == '中文' else language
    ) or (ANSWER_PROMPT_ZH if language == '中文' else ANSWER_PROMPT_EN)
    
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
    获取问题生成提示词（与 Node.js 的 getQuestionPrompt 完全一致）
    :param language: 语言 ('en' 或 '中文' 或 'tr')
    :param text: 文本内容
    :param number: 问题数量
    :param ga_prompt: GA提示词（可选）
    :param project_id: 项目ID（用于获取自定义提示词）
    :return: 提示词
    """
    # 与 Node.js 的 getPromptKey 和 processPrompt 保持一致：
    # - getPromptKey: en 返回 QUESTION_PROMPT_EN，其他（包括 tr）返回 QUESTION_PROMPT
    # - processPrompt: language === 'en' ? defaultPrompts.en : defaultPrompts.zh
    #   所以 tr 会使用 defaultPrompts.zh，也就是 QUESTION_PROMPT（中文版）
    # - getLanguageFromKey: 非 _EN 结尾的键名都映射为 'zh-CN'
    if language == 'en':
        prompt_key = 'QUESTION_PROMPT_EN'
        default_template = QUESTION_PROMPT_EN
        lang_code = 'en'
    else:
        # tr 和其他语言（包括中文）都使用 QUESTION_PROMPT
        # 注意：虽然 Node.js 的 getQuestionPrompt 传递了 tr: QUESTION_PROMPT_TR，
        # 但 processPrompt 的逻辑会让 tr 使用 defaultPrompts.zh（即 QUESTION_PROMPT）
        prompt_key = 'QUESTION_PROMPT'
        # 与 Node.js 的 processPrompt 保持一致：language === 'en' ? en : zh
        # 所以 tr 会使用 zh 模板（QUESTION_PROMPT），但为了支持 tr 语言，我们优先使用 QUESTION_PROMPT_TR
        if language == 'tr':
            # 优先使用土耳其语模板，如果没有自定义提示词的话
            default_template = QUESTION_PROMPT_TR
            lang_code = 'zh-CN'  # tr 在 Node.js 的 getLanguageFromKey 中会被映射为 zh-CN
        else:
            default_template = QUESTION_PROMPT_ZH
            lang_code = 'zh-CN'
    
    # 获取自定义提示词（与 Node.js 的 processPrompt 保持一致）
    custom_template = _get_custom_prompt_content(
        project_id,
        prompt_type='question',
        prompt_key=prompt_key,
        language=lang_code
    )
    template = custom_template or default_template
    
    # 记录是否使用了自定义提示词
    import logging
    logger = logging.getLogger('common')
    if custom_template:
        logger.info(f'使用自定义提示词: project_id={project_id}, prompt_key={prompt_key}, language={lang_code}')
        logger.debug(f'自定义提示词长度: {len(custom_template)}, 是否包含 {{text}} 占位符: {"{{text}}" in custom_template}')
    else:
        logger.debug(f'使用默认提示词: prompt_key={prompt_key}, language={lang_code}')
    
    # 构建GA提示词相关部分（与 Node.js 的 getQuestionPrompt 完全一致）
    if ga_prompt:
        if language == 'en':
            ga_prompt_note = ', and incorporate the specified genre-audience perspective'
            ga_prompt_check = '- Question style matches the specified genre and audience'
        elif language == 'tr':
            ga_prompt_note = ', ve belirtilen tür-hedef kitle perspektifini dahil edin'
            ga_prompt_check = '- Soru stili belirtilen tür ve hedef kitle ile eşleşir'
        else:
            ga_prompt_note = '，并结合指定的体裁受众视角'
            ga_prompt_check = '- 问题风格与指定的体裁受众匹配'
    else:
        ga_prompt_note = ''
        ga_prompt_check = ''
    
    # 替换占位符（与 Node.js 的 processPrompt 保持一致：使用 replaceAll，Python 的 replace 默认替换所有）
    # 注意：Node.js 使用 replaceAll，Python 的 replace 默认替换所有匹配项
    # 重要：先替换其他占位符，最后替换 {{text}}，避免文本内容中包含占位符导致误替换
    prompt = template.replace('{{textLength}}', str(len(text)))
    prompt = prompt.replace('{{number}}', str(number))
    prompt = prompt.replace('{{gaPrompt}}', ga_prompt)
    prompt = prompt.replace('{{gaPromptNote}}', ga_prompt_note)
    prompt = prompt.replace('{{gaPromptCheck}}', ga_prompt_check)
    # 最后替换 {{text}}，确保文本内容被正确插入
    # 重要：使用 replace 替换所有匹配项（Python 的 replace 默认替换所有）
    import logging
    logger = logging.getLogger('common')
    
    # 检查替换前是否有 {{text}} 占位符
    if '{{text}}' not in prompt:
        logger.error(f'错误：模板中不包含 {{text}} 占位符！')
        logger.error(f'模板长度: {len(prompt)}, 模板后500字符: {prompt[-500:] if len(prompt) > 500 else prompt}')
        logger.error(f'这可能是自定义提示词的问题，请检查项目 {project_id} 的自定义提示词配置')
        logger.error(f'如果使用了自定义提示词，请确保自定义提示词中包含 {{text}} 占位符')
        # 即使没有占位符，也尝试继续处理，但记录警告
    else:
        logger.debug(f'模板中包含 {{text}} 占位符，准备替换')
    
    prompt_before_text_replace = prompt
    prompt = prompt.replace('{{text}}', text)
    
    # 验证 {{text}} 是否被替换
    if '{{text}}' in prompt:
        logger.error(f'错误：{{text}} 占位符未被替换！提示词中仍有 {{text}} 占位符')
        logger.error(f'文本内容长度: {len(text)}, 前100字符: {text[:100]}')
        logger.error(f'提示词中 {{text}} 出现的位置: {[i for i, line in enumerate(prompt.split(chr(10))) if "{{text}}" in line]}')
        logger.error(f'替换前的提示词长度: {len(prompt_before_text_replace)}, 替换后的提示词长度: {len(prompt)}')
    
    # 验证文本内容是否被正确插入
    if text and len(text) > 0:
        # 检查文本的前50个字符是否在提示词中
        # 注意：文本可能包含换行符，所以需要处理
        text_start = text[:50].strip()
        if text_start not in prompt:
            import logging
            logger = logging.getLogger('common')
            logger.error(f'错误：文本内容未被插入到提示词中！')
            logger.error(f'文本前50字符: {text[:50]}')
            logger.error(f'文本前50字符（去除换行）: {text_start}')
            # 检查提示词中是否有 "Text to Analyze" 或类似的部分
            text_section_markers = ['Text to Analyze', 'Analiz Edilecek Metin', '待分析文本', 'Text to Analyze:', 'Analiz Edilecek Metin:']
            found_marker = None
            for marker in text_section_markers:
                if marker in prompt:
                    found_marker = marker
                    marker_pos = prompt.find(marker)
                    logger.error(f'找到 "{marker}" 在位置 {marker_pos}，后续200字符: {prompt[marker_pos:marker_pos+200]}')
                    break
            if not found_marker:
                logger.error(f'提示词中未找到任何文本标记（Text to Analyze/Analiz Edilecek Metin/待分析文本）')
                logger.error(f'提示词长度: {len(prompt)}, 提示词后500字符: {prompt[-500:] if len(prompt) > 500 else prompt}')
    
    # 验证所有占位符都已替换
    if '{{text}}' in prompt or '{{textLength}}' in prompt or '{{number}}' in prompt:
        import logging
        logger = logging.getLogger('common')
        logger.warning(f'警告：提示词中仍有未替换的占位符！剩余占位符: {[k for k in ["{{text}}", "{{textLength}}", "{{number}}"] if k in prompt]}')
    
    return prompt


def get_clean_prompt(language: str, text: str) -> str:
    """
    获取数据清洗提示词
    :param language: 语言 (zh/en)
    :param text: 待清洗文本
    :return: 提示词
    """
    lang_code = 'zh-CN' if language in ['中文', 'zh-CN', 'zh'] else 'en'
    template = _get_custom_prompt_content(
        project_id=None,  # 数据清洗当前未区分项目，这里保持与默认逻辑一致；如需项目级，可加参数
        prompt_type='dataClean',
        prompt_key='DATA_CLEAN_PROMPT',
        language=lang_code
    ) or (CLEAN_PROMPT_ZH if lang_code == 'zh-CN' else CLEAN_PROMPT_EN)
    return template.replace('{{text}}', text)


# ======================= 补齐其余提示词构建函数（自定义优先） =======================

def _lang_code(language: str) -> str:
    return 'zh-CN' if language.startswith('zh') or language == '中文' else 'en'


def get_enhanced_answer_prompt(language: str, text: str, question: str, ga_prompt: str = '',
                               template_prompt: str = '', output_format_prompt: str = '',
                               project_id: Optional[str] = None) -> str:
    lang = _lang_code(language)
    template = _get_custom_prompt_content(project_id, 'enhancedAnswer', 'ENHANCED_ANSWER_PROMPT', lang) \
        or _get_default_prompt('ENHANCED_ANSWER_PROMPT', lang)
    return _process_prompt(template, {
        'text': text,
        'question': question,
        'gaPrompt': ga_prompt,
        'templatePrompt': template_prompt,
        'outputFormatPrompt': output_format_prompt
    })


def get_ga_generation_prompt(language: str, text: str, project_id: Optional[str] = None) -> str:
    """
    获取GA生成提示词（与 Node.js 的 getGAGenerationPrompt 保持一致）
    :param language: 语言标识（'中文', 'en', 'tr' 等）
    :param text: 文本内容
    :param project_id: 项目ID（用于获取自定义提示词）
    :return: 处理后的提示词
    """
    # 与 Node.js 的 processPrompt 保持一致：
    # - getPromptKey: en 返回 GA_GENERATION_PROMPT_EN，其他（包括 tr）返回 GA_GENERATION_PROMPT
    # - processPrompt: language === 'en' ? defaultPrompts.en : defaultPrompts.zh
    #   但 processPrompt 的逻辑会让 tr 使用 defaultPrompts.zh（即 GA_GENERATION_PROMPT）
    
    # 确定 prompt_key（与 Node.js 的 getPromptKey 保持一致）
    if language == 'en':
        prompt_key = 'GA_GENERATION_PROMPT_EN'
    else:
        # 包括 '中文', 'tr' 等，都使用基础键名
        prompt_key = 'GA_GENERATION_PROMPT'
    
    # 确定语言代码（与 Node.js 的 getLanguageFromKey 保持一致）
    if language == 'en':
        lang_code = 'en'
    elif language == 'tr':
        lang_code = 'tr'
    else:
        # 包括 '中文' 等，使用 zh-CN
        lang_code = 'zh-CN'
    
    # 获取自定义提示词（与 Node.js 的 processPrompt 保持一致）
    template = _get_custom_prompt_content(project_id, 'ga-generation', prompt_key, lang_code)
    
    # 如果没有自定义提示词，使用默认提示词（与 Node.js 的 processPrompt 保持一致）
    if not template:
        # 与 Node.js 的 processPrompt 保持一致：
        # - defaultPrompt = language === 'en' ? defaultPrompts.en : defaultPrompts.zh
        # - 这意味着 tr 会使用 defaultPrompts.zh（即 GA_GENERATION_PROMPT 的 zh-CN 版本）
        if language == 'en':
            template = _get_default_prompt('GA_GENERATION_PROMPT_EN', 'en')
        else:
            # 包括 '中文', 'tr' 等，都使用 zh-CN 版本的默认提示词（与 Node.js 的 processPrompt 逻辑一致）
            # 但如果有 tr 版本的默认提示词，优先使用 tr 版本
            if language == 'tr':
                template = _get_default_prompt('GA_GENERATION_PROMPT', 'tr')
                if not template:
                    # 如果 tr 版本不存在，使用 zh-CN 版本（与 Node.js 的 processPrompt 逻辑一致）
                    template = _get_default_prompt('GA_GENERATION_PROMPT', 'zh-CN')
            else:
                # 包括 '中文' 等，使用 zh-CN
                template = _get_default_prompt('GA_GENERATION_PROMPT', 'zh-CN')
    
    # 参数替换（与 Node.js 的 processPrompt 保持一致：使用 replaceAll）
    return _process_prompt(template, {'text': text})


def get_distill_questions_prompt(language: str, current_tag: str, tag_path: str,
                                 count: int, existing_questions: str = '',
                                 project_id: Optional[str] = None) -> str:
    lang = _lang_code(language)
    template = _get_custom_prompt_content(project_id, 'distillQuestions', 'DISTILL_QUESTIONS_PROMPT', lang) \
        or _get_default_prompt('DISTILL_QUESTIONS_PROMPT', lang)
    return _process_prompt(template, {
        'currentTag': current_tag,
        'tagPath': tag_path,
        'count': count,
        'existingQuestions': existing_questions
    })


def get_distill_tags_prompt(language: str, parent_tag: str, tag_path: str,
                            count: int, existing_tags_text: str = '',
                            project_id: Optional[str] = None) -> str:
    lang = _lang_code(language)
    template = _get_custom_prompt_content(project_id, 'distillTags', 'DISTILL_TAGS_PROMPT', lang) \
        or _get_default_prompt('DISTILL_TAGS_PROMPT', lang)
    return _process_prompt(template, {
        'parentTag': parent_tag,
        'tagPath': tag_path,
        'count': count,
        'existingTagsText': existing_tags_text
    })


def get_assistant_reply_prompt(language: str, scenario: str, role_a: str, role_b: str,
                               chunk_content: str, conversation_history: str,
                               current_round: int, total_rounds: int,
                               project_id: Optional[str] = None) -> str:
    lang = _lang_code(language)
    template = _get_custom_prompt_content(project_id, 'multiTurnConversation', 'ASSISTANT_REPLY_PROMPT', lang) \
        or _get_default_prompt('ASSISTANT_REPLY_PROMPT', lang)
    return _process_prompt(template, {
        'scenario': scenario,
        'roleA': role_a,
        'roleB': role_b,
        'chunkContent': chunk_content,
        'conversationHistory': conversation_history,
        'currentRound': current_round,
        'totalRounds': total_rounds
    })


def get_next_question_prompt(language: str, scenario: str, role_a: str, role_b: str,
                             chunk_content: str, conversation_history: str,
                             next_round: int, total_rounds: int,
                             project_id: Optional[str] = None) -> str:
    lang = _lang_code(language)
    template = _get_custom_prompt_content(project_id, 'multiTurnConversation', 'NEXT_QUESTION_PROMPT', lang) \
        or _get_default_prompt('NEXT_QUESTION_PROMPT', lang)
    return _process_prompt(template, {
        'scenario': scenario,
        'roleA': role_a,
        'roleB': role_b,
        'chunkContent': chunk_content,
        'conversationHistory': conversation_history,
        'nextRound': next_round,
        'totalRounds': total_rounds
    })


def get_image_question_prompt(language: str, number: int, project_id: Optional[str] = None) -> str:
    lang = _lang_code(language)
    template = _get_custom_prompt_content(project_id, 'imageQuestion', 'IMAGE_QUESTION_PROMPT', lang) \
        or _get_default_prompt('IMAGE_QUESTION_PROMPT', lang)
    return _process_prompt(template, {'number': number})


def get_new_answer_prompt(language: str, chunk_content: str, question: str, answer: str,
                          cot: str = '', advice: str = '', project_id: Optional[str] = None) -> str:
    lang = _lang_code(language)
    template = _get_custom_prompt_content(project_id, 'newAnswer', 'NEW_ANSWER_PROMPT', lang) \
        or _get_default_prompt('NEW_ANSWER_PROMPT', lang)
    return _process_prompt(template, {
        'chunkContent': chunk_content,
        'question': question,
        'answer': answer,
        'cot': cot,
        'advice': advice
    })


def get_optimize_cot_prompt(language: str, original_question: str, answer: str,
                            original_cot: str, project_id: Optional[str] = None) -> str:
    lang = _lang_code(language)
    template = _get_custom_prompt_content(project_id, 'optimizeCot', 'OPTIMIZE_COT_PROMPT', lang) \
        or _get_default_prompt('OPTIMIZE_COT_PROMPT', lang)
    return _process_prompt(template, {
        'originalQuestion': original_question,
        'answer': answer,
        'originalCot': original_cot
    })


def get_ga_prompt_for_answer(language: str, genre: str, audience: str) -> str:
    """
    获取答案生成的GA提示词（用于增强提示词）
    :param language: 语言
    :param genre: 体裁（格式：title: description）
    :param audience: 受众（格式：title: description）
    :return: GA提示词
    """
    if language == 'en':
        return f"""## Special Requirements - Genre & Audience Adaptation (MGA):
Adjust your response style and depth according to the following genre and audience combination:

**Current Genre**: {genre}
**Target Audience**: {audience}

Please ensure:
1. The organization, style, level of detail, and language of the answer should fully comply with the requirements of "{genre}".
2. The answer should consider the comprehension ability and knowledge background of "{audience}", striving for clarity and ease of understanding.
3. Word choice and explanation detail match the target audience's knowledge background.
4. Maintain content accuracy and professionalism while enhancing specificity.
5. If "{genre}" or "{audience}" suggests the need, the answer can appropriately include explanations, examples, or steps.
6. The answer should directly address the question, ensuring the logic and coherence of the Q&A. It should not include irrelevant information or citation marks, such as content mentioned in GA pairs, to prevent contaminating the data generation results.
"""
    else:
        return f"""## 特殊要求 - 体裁与受众适配(MGA)：
根据以下体裁与受众组合，调整你的回答风格和深度：

**当前体裁**: {genre}
**目标受众**: {audience}

请确保：
1. 答案的组织、风格、详略程度和语言应完全符合「{genre}」的要求。
2. 答案应考虑到「{audience}」的理解能力和知识背景，力求清晰易懂。
3. 用词选择和解释详细程度匹配目标受众的知识背景。
4. 保持内容的准确性和专业性，同时增强针对性。
5. 如果{genre}或{audience}暗示需要，答案可以适当包含解释、示例或步骤。
6. 答案应直接回应问题，确保问答的逻辑性和连贯性，不要包含无关信息或引用标记如GA对中提到的内容防止污染数据生成的效果。
"""


def build_enhanced_answer_prompt(language: str, context: Dict, project_id: Optional[str] = None) -> str:
    """
    构建增强答案提示词（MGA增强版）
    :param language: 语言 (zh/en)
    :param context: 包含 text/question/templatePrompt/outputFormatPrompt/activeGaPair
    :param project_id: 项目ID（用于获取自定义提示词）
    :return: 提示词
    """
    text = context.get('text', '')
    question = context.get('question', '')
    template_prompt = context.get('templatePrompt', '')
    output_format_prompt = context.get('outputFormatPrompt', '')
    active_ga_pair = context.get('activeGaPair')
    
    # 构建GA提示词
    ga_prompt = ''
    if active_ga_pair and active_ga_pair.get('active', True):
        genre = active_ga_pair.get('genre', '')
        audience = active_ga_pair.get('audience', '')
        if genre and audience:
            ga_prompt = get_ga_prompt_for_answer(language, genre, audience)
    
    # 增强提示词模板
    if language == 'en':
        template = """# Role: Fine-tuning Dataset Generation Expert (MGA Enhanced)
## Profile:
- Description: You are an expert in generating fine-tuning datasets, skilled at generating accurate answers to questions from the given content, and capable of adjusting response style according to Genre-Audience combinations to ensure accuracy, relevance, and specificity of answers.

## Skills:
1. The answer must be based on the given content.
2. The answer must be accurate and not fabricated.
3. The answer must be relevant to the question.
4. The answer must be logical.
5. Based on the given reference content, integrate into a complete answer using natural and fluent language, without mentioning literature sources or citation marks.
6. Ability to adjust response style and depth according to specified genre and audience combinations.
7. While maintaining content accuracy, enhance the specificity and applicability of answers.

{gaPrompt}

## Workflow:
1. Take a deep breath and work on this problem step-by-step.
2. First, analyze the given file content and question type.
3. Then, extract key information from the content.
4. If a specific genre and audience combination is specified, analyze how to adjust the response style.
5. Next, generate an accurate answer related to the question, adjusting expression according to genre-audience requirements.
6. Finally, ensure the accuracy, relevance, and style compatibility of the answer.

## Reference Content:

------ Reference Content Start ------
{{text}}
------ Reference Content End ------

## Question
{{question}}

## Constraints:
1. The answer must be based on the given content.
2. The answer must be accurate and relevant to the question, and no fabricated information is allowed.
3. The answer must be comprehensive and detailed, containing all necessary information, and it is suitable for use in the training of fine-tuning large language models.
4. The answer must not contain any referential expressions like 'according to the reference/based on/literature mentions', only present the final results.
5. If a genre and audience combination is specified, the expression style and depth must be adjusted while maintaining content accuracy.
6. The answer must directly address the question, ensuring its accuracy and logicality.
{{templatePrompt}}
{{outputFormatPrompt}}"""
    else:
        template = """# Role: 微调数据集生成专家 (MGA增强版)
## Profile:
- Description: 你是一名微调数据集生成专家，擅长从给定的内容中生成准确的问题答案，并能根据体裁与受众(Genre-Audience)组合调整回答风格，确保答案的准确性、相关性和针对性。

## Skills:
1. 答案必须基于给定的内容
2. 答案必须准确，不能胡编乱造
3. 答案必须与问题相关
4. 答案必须符合逻辑
5. 基于给定参考内容，用自然流畅的语言整合成一个完整答案，不需要提及文献来源或引用标记
6. 能够根据指定的体裁与受众组合调整回答风格和深度
7. 在保持内容准确性的同时，增强答案的针对性和适用性

{gaPrompt}

## Workflow:
1. Take a deep breath and work on this problem step-by-step.
2. 首先，分析给定的文件内容和问题类型
3. 然后，从内容中提取关键信息
4. 如果有指定的体裁与受众组合，分析如何调整回答风格
5. 接着，生成与问题相关的准确答案，并根据体裁受众要求调整表达方式
6. 最后，确保答案的准确性、相关性和风格适配性

## 参考内容：

------ 参考内容 Start -------
{{text}}
------ 参考内容 End -------

## 问题
{{question}}

## Constrains:
1. 答案必须基于给定的内容
2. 答案必须准确，必须与问题相关，不能胡编乱造
3. 答案必须充分、详细、包含所有必要的信息、适合微调大模型训练使用
4. 答案中不得出现 ' 参考 / 依据 / 文献中提到 ' 等任何引用性表述，只需呈现最终结果
5. 如果指定了体裁与受众组合，必须在保持内容准确性的前提下，调整表达风格和深度
6. 答案必须直接回应问题， 确保答案的准确性和逻辑性。
{{templatePrompt}}
{{outputFormatPrompt}}"""
    
    # 替换占位符
    prompt = template.replace('{gaPrompt}', ga_prompt)
    prompt = prompt.replace('{{text}}', text)
    prompt = prompt.replace('{{question}}', question)
    prompt = prompt.replace('{{templatePrompt}}', template_prompt)
    prompt = prompt.replace('{{outputFormatPrompt}}', output_format_prompt)
    
    return prompt


def get_optimize_cot_prompt(language: str, original_question: str, answer: str, original_cot: str, project_id: Optional[str] = None) -> str:
    """
    获取思维链优化提示词
    :param language: 语言 (zh/en)
    :param original_question: 原始问题
    :param answer: 答案
    :param original_cot: 原始思维链
    :param project_id: 项目ID（用于获取自定义提示词）
    :return: 提示词
    """
    if language == 'en':
        template = """# Role: Chain of Thought Optimization Expert
## Profile:
- Description: You are an expert in optimizing the chain of thought. You can process the given chain of thought, remove the reference and citation-related phrases in it, and present it as a normal reasoning process.

## Skills:
1. Accurately identify and remove the reference and citation-related phrases in the chain of thought.
2. Ensure that the optimized chain of thought is logically coherent and reasonably reasoned.
3. Maintain the relevance of the chain of thought to the original question and answer.

## Workflow:
1. Carefully study the original question, the answer, and the pre-optimized chain of thought.
2. Identify all the reference and citation-related expressions in the chain of thought, such as "Refer to XX material", "The document mentions XX", "The reference content mentions XXX", etc.
3. Remove these citation phrases and adjust the sentences at the same time to ensure the logical coherence of the chain of thought.
4. Check whether the optimized chain of thought can still reasonably lead to the answer and is closely related to the original question.

## Original Question
{{originalQuestion}}

## Answer
{{answer}}

## Pre-optimized Chain of Thought
{{originalCot}}

## Constraints:
1. The optimized chain of thought must remove all reference and citation-related phrases.
2. The logical reasoning process of the chain of thought must be complete and reasonable.
3. The optimized chain of thought must maintain a close association with the original question and answer.
4. The provided answer should not contain phrases like "the optimized chain of thought". Directly provide the result of the optimized chain of thought.
5. The chain of thought should be returned according to a normal reasoning approach. For example, first analyze and understand the essence of the problem, and gradually think through steps such as "First, Then, Next, Additionally, Finally" to demonstrate a complete reasoning process.
"""
    else:
        template = """# Role: 思维链优化专家
## Profile:
- Description: 你是一位擅长优化思维链的专家，能够对给定的思维链进行处理，去除其中的参考引用相关话术，使其呈现为一个正常的推理过程。

## Skills:
1. 准确识别并去除思维链中的参考引用话术。
2. 确保优化后的思维链逻辑连贯、推理合理。
3. 维持思维链与原始问题和答案的相关性。

## Workflow:
1. 仔细研读原始问题、答案和优化前的思维链。
2. 识别思维链中所有参考引用相关的表述，如"参考 XX 资料""文档中提及 XX""参考内容中提及 XXX"等。
3. 去除这些引用话术，同时调整语句，保证思维链的逻辑连贯性。
4. 检查优化后的思维链是否仍然能够合理地推导出答案，并且与原始问题紧密相关。

## 原始问题
{{originalQuestion}}

## 答案
{{answer}}

## 优化前的思维链
{{originalCot}}

## Constrains:
1. 优化后的思维链必须去除所有参考引用相关话术。
2. 思维链的逻辑推理过程必须完整且合理。
3. 优化后的思维链必须与原始问题和答案保持紧密关联。
4. 给出的答案不要包含 "优化后的思维链" 这样的话术，直接给出优化后的思维链结果。
5. 思维链应按照正常的推理思路返回，如：先分析理解问题的本质，按照 "首先、然后、接着、另外、最后" 等步骤逐步思考，展示一个完善的推理过程。
"""
    
    # 替换占位符
    prompt = template.replace('{{originalQuestion}}', original_question)
    prompt = prompt.replace('{{answer}}', answer)
    prompt = prompt.replace('{{originalCot}}', original_cot)
    
    return prompt


def get_ga_prompt(language: str, genre: str, audience: str) -> str:
    """
    获取GA提示词（与 Node.js 的 getGAPrompt 完全一致）
    :param language: 语言 ('en' 或 '中文' 或 'tr')
    :param genre: 体裁（包含描述的完整字符串，如 "体裁标题: 体裁描述"）
    :param audience: 受众（包含描述的完整字符串，如 "受众标题: 受众描述"）
    :return: GA提示词
    """
    if language == 'en':
        return f"""## Special Requirements - Genre & Audience Perspective Questioning:
Adjust your questioning approach and question style based on the following genre and audience combination:

**Target Genre**: {genre}
**Target Audience**: {audience}

Please ensure:
1. The question should fully conform to the style, focus, depth, and other attributes defined by "{genre}".
2. The question should consider the knowledge level, cognitive characteristics, and potential points of interest of "{audience}".
3. Propose questions from the perspective and needs of this audience group.
4. Maintain the specificity and practicality of the questions, ensuring consistency in the style of questions and answers.
5. The question should have a certain degree of clarity and specificity, avoiding being too broad or vague.
"""
    elif language == 'tr':
        return f"""## Özel Gereksinimler - Tür & Hedef Kitle Perspektifi Sorgulama:
Aşağıdaki tür ve hedef kitle kombinasyonuna göre sorgulama yaklaşımınızı ve soru stilinizi ayarlayın:

**Hedef Tür**: {genre}
**Hedef Kitle**: {audience}

Lütfen şunları sağlayın:
1. Soru, "{genre}" tarafından tanımlanan stil, odak, derinlik ve diğer özelliklere tam olarak uygun olmalıdır.
2. Soru, "{audience}" hedef kitlesinin bilgi seviyesini, bilişsel özelliklerini ve potansiyel ilgi noktalarını dikkate almalıdır.
3. Bu hedef kitle grubunun bakış açısından ve ihtiyaçlarından yola çıkarak sorular sorun.
4. Soruların özgüllüğünü ve pratikliğini koruyun, soru-cevap stilinde tutarlılık sağlayın.
5. Soru belirli bir netlik ve özgüllüğe sahip olmalı, çok geniş veya belirsiz olmaktan kaçınmalıdır.
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
# 与 Node.js 的 ADD_LABEL_PROMPT 保持一致
LABEL_PROMPT_ZH = """# Role: 标签匹配专家
- Description: 你是一名标签匹配专家，擅长根据给定的标签数组和问题数组，将问题打上最合适的领域标签。你熟悉标签的层级结构，并能根据问题的内容优先匹配二级标签，若无法匹配则匹配一级标签，最后打上"其他"标签。

## Skill:
1. 熟悉标签层级结构，能够准确识别一级和二级标签。
2. 能够根据问题的内容，智能匹配最合适的标签。
3. 能够处理复杂的标签匹配逻辑，确保每个问题都能被打上正确的标签。
4. 能够按照规定的输出格式生成结果，确保不改变原有数据结构。
5. 能够处理大规模数据，确保高效准确的标签匹配。

## Goals:
1. 将问题数组中的每个问题打上最合适的领域标签。
2. 优先匹配二级标签，若无法匹配则匹配一级标签，最后打上"其他"标签。
3. 确保输出格式符合要求，不改变原有数据结构。
4. 提供高效的标签匹配算法，确保处理大规模数据时的性能。
5. 确保标签匹配的准确性和一致性。

## OutputFormat:
1. 输出结果必须是一个数组，每个元素包含 question、和 label 字段。
2. label 字段必须是根据标签数组匹配到的标签，若无法匹配则打上"其他"标签。
3. 不改变原有数据结构，只新增 label 字段。

## 标签数组：
{{label}}

## 问题数组：
{{question}}

## Workflow:
1. Take a deep breath and work on this problem step-by-step.
2. 首先，读取标签数组和问题数组。
3. 然后，遍历问题数组中的每个问题，根据问题的内容匹配标签数组中的标签。
4. 优先匹配二级标签，若无法匹配则匹配一级标签，最后打上"其他"标签。
5. 将匹配到的标签添加到问题对象中，确保不改变原有数据结构。
6. 最后，输出结果数组，确保格式符合要求。

## Constrains:
1. 只新增一个 label 字段，不改变其他任何格式和数据。
2. 必须按照规定格式返回结果。
3. 优先匹配二级标签，若无法匹配则匹配一级标签，最后打上"其他"标签。
4. 确保标签匹配的准确性和一致性。
5. 匹配的标签必须在标签数组中存在，如果不存在，就打上 其他 
7. 输出结果必须是一个数组，每个元素包含 question、label 字段（只输出这个，不要输出任何其他无关内容）

## Output Example:
   ```json
   [
     {
       "question": "XSS为什么会在2003年后引起人们更多关注并被OWASP列为威胁榜首？",
       "label": "2.2 XSS攻击"
     }
   ]
   ```
"""

LABEL_PROMPT_EN = """# Role: Label Matching Expert
  - Description: You are a label matching expert, proficient in assigning the most appropriate domain labels to questions based on the given label array and question array.You are familiar with the hierarchical structure of labels and can prioritize matching secondary labels according to the content of the questions.If a secondary label cannot be matched, you will match a primary label.Finally, if no match is found, you will assign the "Other" label.

## Skill:
1. Be familiar with the label hierarchical structure and accurately identify primary and secondary labels.
2. Be able to intelligently match the most appropriate label based on the content of the question.
3. Be able to handle complex label matching logic to ensure that each question is assigned the correct label.
4. Be able to generate results in the specified output format without changing the original data structure.
5. Be able to handle large - scale data to ensure efficient and accurate label matching.

## Goals:
1. Assign the most appropriate domain label to each question in the question array.
2. Prioritize matching secondary labels.If no secondary label can be matched, match a primary label.Finally, assign the "Other" label.
3. Ensure that the output format meets the requirements without changing the original data structure.
4. Provide an efficient label matching algorithm to ensure performance when processing large - scale data.
5. Ensure the accuracy and consistency of label matching.

## OutputFormat:
1. The output result must be an array, and each element contains the "question" and "label" fields.
2. The "label" field must be the label matched from the label array.If no match is found, assign the "Other" label.
3. Do not change the original data structure, only add the "label" field.

## Label Array:
{{label}}

## Question Array:
{{question}}

## Workflow:
1. Take a deep breath and work on this problem step - by - step.
2. First, read the label array and the question array.
3. Then, iterate through each question in the question array and match the labels in the label array according to the content of the question.
4. Prioritize matching secondary labels.If no secondary label can be matched, match a primary label.Finally, assign the "Other" label.
5. Add the matched label to the question object without changing the original data structure.
6. Finally, output the result array, ensuring that the format meets the requirements.

## Constrains:
1. Only add one "label" field without changing any other format or data.
2. Must return the result in the specified format.
3. Prioritize matching secondary labels.If no secondary label can be matched, match a primary label.Finally, assign the "Other" label.
4. Ensure the accuracy and consistency of label matching.
5. The matched label must exist in the label array.If it does not exist, assign the "Other" label.
7. The output result must be an array, and each element contains the "question" and "label" fields(only output this, do not output any other irrelevant content).

## Output Example:
```json
   [
     {
       "question": "XSS Attack why was more attention attracted by people after 2003 and was listed as the top threat by OWASP?",
       "label": "2.2 XSS Attack"
     }
   ]
```
"""


def get_label_prompt(language: str, labels, questions) -> str:
    """构造标签分配提示词，labels/questions 均为列表（与 Node.js 的 getAddLabelPrompt 保持一致）"""
    labels_text = json.dumps(labels, ensure_ascii=False)
    questions_text = json.dumps(questions, ensure_ascii=False)
    tpl = LABEL_PROMPT_ZH if language.startswith('zh') else LABEL_PROMPT_EN
    # 使用 {{label}} 和 {{question}} 占位符，与 Node.js 保持一致
    return tpl.replace('{{label}}', labels_text).replace('{{question}}', questions_text)


# ---------------- 数据集评估提示词 -----------------
DATASET_EVALUATION_PROMPT_ZH = """# Role: 数据集质量评估专家
## Profile:
- Description: 你是一名专业的数据集质量评估专家，擅长从多个维度对问答数据集进行质量评估，为机器学习模型训练提供高质量的数据筛选建议。具备深度学习、自然语言处理和数据科学的专业背景。

## Skills:
1. 能够从问题质量、答案质量、文本相关性等多个维度进行综合评估
2. 擅长识别数据集中的潜在问题，如答案不准确、问题模糊、文本不匹配、逻辑错误等
3. 能够给出具体的改进建议和质量评分，并提供可操作的优化方案
4. 熟悉机器学习训练数据的质量标准和最佳实践
5. 能够区分不同类型的问题（事实性、推理性、创造性）并采用相应的评估标准

## 评估维度:
### 1. 问题质量 (25%)
**评分标准：**
- 5分：问题表述清晰准确，语法完美，具有明确的答案期望，难度适中
- 4分：问题基本清晰，语法正确，偶有轻微歧义但不影响理解
- 3分：问题可理解，但存在一定歧义或表达不够精确
- 2分：问题模糊，存在明显歧义或语法错误
- 1分：问题表述严重不清，难以理解意图
- 0分：问题完全无法理解或存在严重错误

**具体评估点：**
- 问题是否清晰明确，没有歧义
- 问题是否具有适当的难度和深度
- 问题表达是否规范，语法是否正确
- 问题类型识别（事实性/推理性/创造性）

### 2. 答案质量 (35%)
**评分标准：**
- 5分：答案完全准确，内容详尽，逻辑清晰，结构完整
- 4分：答案基本准确，内容较完整，逻辑清晰
- 3分：答案大致正确，但缺少部分细节或逻辑略有不足
- 2分：答案部分正确，但存在明显错误或遗漏
- 1分：答案大部分错误，仅有少量正确信息
- 0分：答案完全错误或与问题无关

**具体评估点：**
- 答案是否准确回答了问题的核心要求
- 答案内容是否完整、详细、逻辑清晰
- 答案是否基于提供的文本内容，没有虚构信息
- 答案的专业性和可信度

### 3. 文本相关性 (25%)
**有原始文本时：**
- 5分：问题和答案与原始文本高度相关，文本完全支撑答案
- 4分：问题和答案与文本相关性强，文本基本支撑答案
- 3分：问题和答案与文本相关，但支撑度一般
- 2分：问题和答案与文本相关性较弱
- 1分：问题和答案与文本相关性很弱
- 0分：问题和答案与文本完全无关

**无原始文本时（蒸馏内容）：**
- 重点评估问题和答案的逻辑一致性
- 答案是否合理回答了问题
- 知识的准确性和可靠性

### 4. 整体一致性 (15%)
**评分标准：**
- 5分：问题、答案、文本形成完美的逻辑闭环，完全适合模型训练
- 4分：整体一致性良好，适合模型训练
- 3分：基本一致，可用于模型训练但需要轻微调整
- 2分：存在一定不一致，需要修改后才能用于训练
- 1分：不一致问题较多，不建议直接用于训练
- 0分：严重不一致，完全不适合用于训练

**具体评估点：**
- 问题、答案、原始文本三者之间是否形成良好的逻辑闭环
- 数据集是否适合用于模型训练
- 是否存在明显的错误或不一致

## 原始文本块内容:
{{chunkContent}}

## 问题:
{{question}}

## 答案:
{{answer}}

## 评估说明:
1. **数据集类型识别**：如果原始文本块内容为空或显示"Distilled Content"，说明这是一个蒸馏数据集，没有原始文本参考。请重点评估问题的质量、答案的合理性和逻辑性，以及问答的一致性。
2. **评估原则**：采用严格的评估标准，确保筛选出的数据集能够有效提升模型性能。
3. **权重应用**：最终评分 = 问题质量×25% + 答案质量×35% + 文本相关性×25% + 整体一致性×15%

## 输出要求:
请按照以下JSON格式输出评估结果，评分范围为0-5分，精确到0.5分：

```json
{
  "score": 4.5,
  "evaluation": "这是一个高质量的问答数据集。问题表述清晰具体，答案准确完整且逻辑性强，与原始文本高度相关。建议：可以进一步丰富答案的细节描述。"
}
```

## 注意事项:
- 评分标准严格，满分5分代表近乎完美的数据集
- 评估结论要具体指出优点和不足，提供可操作的改进建议
- 如果发现严重问题（如答案错误、文不对题等），评分应在2分以下
- 评估结论控制在150字以内，简洁明了但要涵盖关键信息
"""

DATASET_EVALUATION_PROMPT_EN = """# Role: Dataset Quality Evaluation Expert
## Profile:
- Description: You are a professional dataset quality evaluation expert, skilled in evaluating Q&A datasets from multiple dimensions and providing high-quality data screening recommendations for machine learning model training. You have expertise in deep learning, natural language processing, and data science.

## Skills:
1. Ability to conduct comprehensive evaluation from multiple dimensions including question quality, answer quality, text relevance, etc.
2. Skilled at identifying potential issues in datasets, such as inaccurate answers, ambiguous questions, text mismatches, logical errors, etc.
3. Ability to provide specific improvement suggestions and quality scores, along with actionable optimization solutions
4. Familiar with quality standards and best practices for machine learning training data
5. Ability to distinguish different types of questions (factual, reasoning, creative) and apply corresponding evaluation criteria

## Evaluation Dimensions:
### 1. Question Quality (25%)
**Scoring Standards:**
- 5 points: Question is clearly and accurately stated, perfect grammar, clear answer expectations, appropriate difficulty
- 4 points: Question is basically clear, correct grammar, occasional slight ambiguity but doesn't affect understanding
- 3 points: Question is understandable but has some ambiguity or imprecise expression
- 2 points: Question is vague, obvious ambiguity or grammatical errors
- 1 point: Question is seriously unclear, difficult to understand intent
- 0 points: Question is completely incomprehensible or has serious errors

**Specific Evaluation Points:**
- Whether the question is clear and unambiguous
- Whether the question has appropriate difficulty and depth
- Whether the question expression is standardized with correct grammar
- Question type identification (factual/reasoning/creative)

### 2. Answer Quality (35%)
**Scoring Standards:**
- 5 points: Answer is completely accurate, content is comprehensive, logic is clear, structure is complete
- 4 points: Answer is basically accurate, content is relatively complete, logic is clear
- 3 points: Answer is generally correct but lacks some details or logic is slightly insufficient
- 2 points: Answer is partially correct but has obvious errors or omissions
- 1 point: Answer is mostly wrong with only a small amount of correct information
- 0 points: Answer is completely wrong or irrelevant to the question

**Specific Evaluation Points:**
- Whether the answer accurately responds to the core requirements of the question
- Whether the answer content is complete, detailed, and logically clear
- Whether the answer is based on the provided text content without fabricated information
- Professionalism and credibility of the answer

### 3. Text Relevance (25%)
**When there is original text:**
- 5 points: Question and answer are highly relevant to original text, text fully supports the answer
- 4 points: Question and answer have strong relevance to text, text basically supports the answer
- 3 points: Question and answer are related to text, but support is moderate
- 2 points: Question and answer have weak relevance to text
- 1 point: Question and answer have very weak relevance to text
- 0 points: Question and answer are completely unrelated to text

**When there is no original text (distilled content):**
- Focus on evaluating logical consistency between question and answer
- Whether the answer reasonably responds to the question
- Accuracy and reliability of knowledge

### 4. Overall Consistency (15%)
**Scoring Standards:**
- 5 points: Question, answer, and text form perfect logical loop, completely suitable for model training
- 4 points: Overall consistency is good, suitable for model training
- 3 points: Basically consistent, can be used for model training but needs slight adjustment
- 2 points: Some inconsistency exists, needs modification before training
- 1 point: Many inconsistency issues, not recommended for direct training
- 0 points: Serious inconsistency, completely unsuitable for training

**Specific Evaluation Points:**
- Whether the question, answer, and original text form a good logical loop
- Whether the dataset is suitable for model training
- Whether there are obvious errors or inconsistencies

## Original Text Chunk Content:
{{chunkContent}}

## Question:
{{question}}

## Answer:
{{answer}}

## Evaluation Notes:
1. **Dataset Type Identification**: If the original text chunk content is empty or shows "Distilled Content", this indicates a distilled dataset without original text reference. Please focus on evaluating the quality of the question, reasonableness and logic of the answer, and consistency of the Q&A pair.
2. **Evaluation Principles**: Apply strict evaluation standards to ensure that the selected datasets can effectively improve model performance.
3. **Weight Application**: Final score = Question Quality×25% + Answer Quality×35% + Text Relevance×25% + Overall Consistency×15%

## Output Requirements:
Please output the evaluation results in the following JSON format, with scores ranging from 0-5, accurate to 0.5:

```json
{
  "score": 4.5,
  "evaluation": "This is a high-quality Q&A dataset. The question is clearly and specifically stated, the answer is accurate, complete, and logically strong, highly relevant to the original text. Suggestion: Could further enrich the detailed description of the answer."
}
```

## Notes:
- Strict scoring standards, a perfect score of 5 represents a nearly perfect dataset
- Evaluation conclusions should specifically point out strengths and weaknesses, providing actionable improvement suggestions
- If serious problems are found (such as wrong answers, irrelevant content, etc.), the score should be below 2
- Keep evaluation conclusions within 150 words, concise and clear but covering key information
"""


def get_dataset_evaluation_prompt(language: str, chunk_content: str, question: str, answer: str, project_id: Optional[str] = None) -> str:
    """
    获取数据集质量评估提示词
    :param language: 语言 ('zh-CN', 'en', 'tr' 等)
    :param chunk_content: 原始文本块内容
    :param question: 问题
    :param answer: 答案
    :param project_id: 项目ID（用于获取自定义提示词）
    :return: 完整的提示词
    """
    lang_code = 'zh-CN' if language.startswith('zh') else ('en' if language.startswith('en') else 'zh-CN')
    template = _get_custom_prompt_content(
        project_id,
        prompt_type='datasetEvaluation',
        prompt_key='DATASET_EVALUATION_PROMPT',
        language=lang_code
    ) or (DATASET_EVALUATION_PROMPT_ZH if language.startswith('zh') else DATASET_EVALUATION_PROMPT_EN)
    
    # 替换占位符
    prompt = template.replace('{{chunkContent}}', chunk_content or '')
    prompt = prompt.replace('{{question}}', question)
    prompt = prompt.replace('{{answer}}', answer)
    
    return prompt
