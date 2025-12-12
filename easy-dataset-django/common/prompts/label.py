import json


# 中文提示词模板
LABEL_PROMPT_ZH = """
# Role: 领域分类专家 & 知识图谱专家
- Description: 作为一名资深的领域分类专家和知识图谱专家，擅长从文本内容中提取核心主题，构建分类体系，并输出规定 JSON 格式的标签树。

## Skills:
1. 精通文本主题分析和关键词提取
2. 擅长构建分层知识体系
3. 熟练掌握领域分类方法论
4. 具备知识图谱构建能力
5. 精通JSON数据结构

## Goals:
1. 分析书籍目录内容
2. 识别核心主题和关键领域
3. 构建两级分类体系
4. 确保分类逻辑合理
5. 生成规范的JSON输出

## Workflow:
1. 仔细阅读完整的书籍目录内容
2. 提取关键主题和核心概念
3. 对主题进行分组和归类
4. 构建一级领域标签
5. 为适当的一级标签添加二级标签
6. 检查分类逻辑的合理性
7. 生成符合格式的JSON输出

## 需要分析的目录
{text}

## 限制
1. 一级领域标签数量5-10个
2. 二级领域标签数量1-10个
3. 最多两层分类层级
4. 分类必须与原始目录内容相关
5. 输出必须符合指定 JSON 格式，不要输出 JSON 外其他任何不相关内容
6. 标签的名字最多不要超过 6 个字
7. 在每个标签前加入序号（序号不计入字数）

## OutputFormat:
```json
[
  {{
    "label": "1 一级领域标签",
    "child": [
      {{"label": "1.1 二级领域标签1"}},
      {{"label": "1.2 二级领域标签2"}}
    ]
  }},
  {{
    "label": "2 一级领域标签(无子标签)"
  }}
]
```
"""

# 英文提示词模板
LABEL_PROMPT_EN = """
# Role: Domain Classification Expert & Knowledge Graph Expert
- Description: As a senior domain classification expert and knowledge graph expert, you are skilled at extracting core themes from text content, constructing classification systems, and performing knowledge categorization and labeling.

## Skills:
1. Proficient in text theme analysis and keyword extraction.
2. Good at constructing hierarchical knowledge systems.
3. Skilled in domain classification methodologies.
4. Capable of building knowledge graphs.
5. Proficient in JSON data structures.

## Goals:
1. Analyze the content of the book catalog.
2. Identify core themes and key domains.
3. Construct a two-level classification system.
4. Ensure the classification logic is reasonable.
5. Generate a standardized JSON output.

## Workflow:
1. Carefully read the entire content of the book catalog.
2. Extract key themes and core concepts.
3. Group and categorize the themes.
4. Construct primary domain labels (ensure no more than 10).
5. Add secondary labels to appropriate primary labels (no more than 10 per group).
6. Check the rationality of the classification logic.
7. Generate a JSON output that conforms to the format.

## Catalog to be analyzed
{text}

## Constraints
1. The number of primary domain labels should be between 5 and 10.
2. The number of secondary domain labels should be between 1 and 10 per primary label.
3. There should be at most two classification levels.
4. The classification must be relevant to the original catalog content.
5. The output must conform to the specified JSON format.
6. The names of the labels should not exceed 6 characters.
7. Do not output any content other than the JSON.
8. Add a serial number before each label (the serial number does not count towards the character limit).

## OutputFormat:
```json
[
  {{
    "label": "1 Primary Domain Label",
    "child": [
      {{"label": "1.1 Secondary Domain Label 1"}},
      {{"label": "1.2 Secondary Domain Label 2"}}
    ]
  }},
  {{
    "label": "2 Primary Domain Label (No Sub-labels)"
  }}
]
```
"""

# 土耳其语提示词模板
LABEL_PROMPT_TR = """
# Rol: Alan Sınıflandırma Uzmanı & Bilgi Grafiği Uzmanı
- Açıklama: Kıdemli bir alan sınıflandırma uzmanı ve bilgi grafiği uzmanı olarak, metin içeriğinden temel temaları çıkarmada, sınıflandırma sistemleri oluşturmada ve bilgi kategorizasyonu ve etiketlemesinde yeteneklisiniz.

## Yetenekler:
1. Metin tema analizi ve anahtar kelime çıkarımında yetkin.
2. Hiyerarşik bilgi sistemleri oluşturmada iyi.
3. Alan sınıflandırma metodolojilerinde yetenekli.
4. Bilgi grafikleri oluşturma yeteneği.
5. JSON veri yapılarında yetkin.

## Hedefler:
1. Kitap kataloğunun içeriğini analiz edin.
2. Temel temaları ve anahtar alanları tanımlayın.
3. İki seviyeli bir sınıflandırma sistemi oluşturun.
4. Sınıflandırma mantığının makul olduğundan emin olun.
5. Standart bir JSON çıktısı oluşturun.

## İş Akışı:
1. Kitap kataloğunun tüm içeriğini dikkatlice okuyun.
2. Temel temaları ve çekirdek kavramları çıkarın.
3. Temaları gruplandırın ve kategorize edin.
4. Birincil alan etiketleri oluşturun (10'dan fazla olmadığından emin olun).
5. Uygun birincil etiketlere ikincil etiketler ekleyin (grup başına 10'dan fazla olmayacak şekilde).
6. Sınıflandırma mantığının mantıklılığını kontrol edin.
7. Formata uygun bir JSON çıktısı oluşturun.

## Analiz edilecek katalog
{text}

## Kısıtlamalar
1. Birincil alan etiketi sayısı 5 ile 10 arasında olmalıdır.
2. İkincil alan etiketi sayısı birincil etiket başına 1 ile 10 arasında olmalıdır.
3. En fazla iki sınıflandırma seviyesi olmalıdır.
4. Sınıflandırma orijinal katalog içeriğiyle alakalı olmalıdır.
5. Çıktı belirtilen JSON formatına uygun olmalıdır.
6. Etiket adları 6 karakteri geçmemelidir.
7. JSON dışında başka herhangi bir içerik çıktılamayın.
8. Her etiketin önüne bir seri numarası ekleyin (seri numarası karakter sınırına dahil değildir).

## ÇıktıFormatı:
```json
[
  {{
    "label": "1 Birincil Alan Etiketi",
    "child": [
      {{"label": "1.1 İkincil Alan Etiketi 1"}},
      {{"label": "1.2 İkincil Alan Etiketi 2"}}
    ]
  }},
  {{
    "label": "2 Birincil Alan Etiketi (Alt etiket yok)"
  }}
]
```
"""


def get_label_prompt(language: str, context: dict, project_id: str):
    """
    重建领域树的提示词（与 Node.js 保持一致）。
    :param language: '中文', 'en', 'tr' 或其他语言标识
    :param context: {'text': toc_text}
    :param project_id: 项目 ID（用于获取自定义提示词，与 Node.js 保持一致）
    :return: 完整的提示词字符串
    """
    text = context.get('text', '')[:100000]
    
    # 根据语言选择对应的提示词模板（与 Node.js 的 processPrompt 逻辑完全一致）
    # Node.js 的 getPromptKey 函数：只有 en 返回 baseKey_EN，其他都返回 baseKey
    # Node.js 的 getLanguageFromKey 函数：只有以 _EN 结尾返回 en，其他返回 zh-CN
    # Node.js 的 defaultPrompt 选择：language === 'en' ? defaultPrompts.en : defaultPrompts.zh
    # 注意：Node.js 的 processPrompt 对于 tr 也会使用 defaultPrompts.zh，而不是 defaultPrompts.tr
    
    base_key = 'LABEL_PROMPT'
    lang_key = language.lower() if language else 'zh'
    
    # 确定 promptKey（与 Node.js 的 getPromptKey 一致）
    if lang_key == 'en' or lang_key == 'en-us' or lang_key == 'en_us':
        prompt_key = f'{base_key}_EN'
        lang_code = 'en'  # 与 Node.js 的 getLanguageFromKey 一致
        default_template = LABEL_PROMPT_EN
    else:
        # 对于 tr 和其他语言，都返回基础键名（与 Node.js 一致）
        prompt_key = base_key
        lang_code = 'zh-CN'  # 与 Node.js 的 getLanguageFromKey 一致（不是 _EN 结尾就返回 zh-CN）
        # 默认提示词选择（与 Node.js 的 processPrompt 一致：只有 en 用 en，其他用 zh）
        # 但为了更好的用户体验，如果明确是 tr，使用土耳其语模板
        if 'tr' in lang_key:
            default_template = LABEL_PROMPT_TR
        else:
            default_template = LABEL_PROMPT_ZH
    
    # 尝试获取项目自定义提示词（与 Node.js 的 processPrompt 逻辑一致）
    template = default_template
    if project_id:
        try:
            from llm.models import CustomPrompt
            custom_prompt = CustomPrompt.objects.filter(
                project_id=project_id,
                prompt_type='label',
                prompt_key=prompt_key,
                language=lang_code,
                is_active=True
            ).first()
            
            if custom_prompt and custom_prompt.content:
                template = custom_prompt.content
        except Exception as e:
            import logging
            logger = logging.getLogger('common')
            logger.warning(f'获取项目自定义提示词失败，使用默认提示词: {str(e)}')
            template = default_template
    
    # 替换模板中的变量
    prompt = template.format(text=text)
    
    return prompt


