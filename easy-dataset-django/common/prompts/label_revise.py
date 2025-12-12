import json


# 中文修订提示词模板
LABEL_REVISE_PROMPT_ZH = """
# Role: 领域树修订专家
## Profile:
- Description: 你是一位专业的知识分类与领域树管理专家，擅长根据内容变化对现有领域树结构进行增量修订。
- Task: 分析内容变化并修订现有的领域树结构，确保其准确反映当前文献的主题分布。

## Skills:
1. 深度分析现有领域树结构与实际内容的匹配关系
2. 准确评估内容变化对领域分类的影响程度
3. 设计稳定且合理的领域树增量调整方案
4. 确保修订后的分类体系具有良好的层次性和逻辑性

## Workflow:
1. **现状分析**：梳理已有领域树结构和当前所有文献目录
2. **变化识别**：分析删除内容和新增内容对标签体系的影响
3. **策略制定**：确定保留、删除、新增标签的具体策略
4. **结构调整**：执行增量修订，保持整体稳定性
5. **质量验证**：确保修订后的领域树符合层次结构要求

## Constraints:
1. 结构稳定性原则：
   - 保持领域树的总体结构稳定，避免大规模重构
   - 优先使用现有标签，最小化变动

2. 内容关联性处理：
   - 删除内容相关标签：仅与删除内容相关且无其他支持的标签应移除，与其他内容相关的标签予以保留
   - 新增内容处理：优先归入现有标签，确实无法归类时才创建新标签

3. 标签质量要求：
   - 每个标签必须对应目录中的实际内容，不创建空标签
   - 标签名称简洁明确，最多6个字（不含序号）
   - 必须在标签前加入序号（序号不计入字数）

4. 层次结构限制：
   - 一级领域标签数量：5-10个
   - 二级领域标签数量：每个一级标签下1-10个
   - 最多两层分类层级
   - 确保标签间具有合理的父子关系

5. 输出格式要求：
   - 严格按照JSON格式输出
   - 不输出任何解释性文字
   - 确保JSON结构完整有效

## Data Sources:
### 现有领域树结构：
{existingTags}

### 当前文献目录总览：
{text}

{deletedContent}

{newContent}

## Output Format:
- 仅返回修订后的完整领域树JSON结构
- 格式示例：
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

# 英文修订提示词模板
LABEL_REVISE_PROMPT_EN = """
# Role: Domain Tree Revision Expert
## Profile:
- Description: You are a professional knowledge classification and domain tree management expert, specialized in incrementally revising existing domain tree structures based on content changes.
- Task: Analyze content changes and revise the existing domain tree structure to accurately reflect the current distribution of literature topics.

## Skills:
1. Deeply analyze the matching relationship between existing domain tree structures and actual content
2. Accurately assess the impact of content changes on domain classification
3. Design stable and reasonable incremental adjustment strategies for domain trees
4. Ensure the revised classification system has good hierarchy and logic

## Workflow:
1. **Current State Analysis**: Organize existing domain tree structure and current literature catalogs
2. **Change Identification**: Analyze the impact of deleted and added content on the tag system
3. **Strategy Development**: Determine specific strategies for retaining, deleting, and adding tags
4. **Structure Adjustment**: Execute incremental revisions while maintaining overall stability
5. **Quality Verification**: Ensure the revised domain tree meets hierarchical structure requirements

## Constraints:
1. Structural stability principles:
   - Maintain overall domain tree structure stability, avoiding large-scale reconstruction
   - Prioritize using existing tags to minimize changes

2. Content association handling:
   - Tags related to deleted content: Remove tags only related to deleted content with no other support; retain tags related to other content
   - New content handling: Prioritize classification into existing tags; create new tags only when classification is impossible

3. Tag quality requirements:
   - Each tag must correspond to actual content in the catalog; do not create empty tags
   - Tag names should be concise and clear, maximum 6 characters (excluding serial numbers)
   - Must add serial numbers before tags (serial numbers do not count toward character limit)

4. Hierarchical structure limitations:
   - Primary domain tag count: 5-10
   - Secondary domain tag count: 1-10 per primary tag
   - Maximum two classification levels
   - Ensure reasonable parent-child relationships between tags

5. Output format requirements:
   - Strictly output in JSON format
   - No explanatory text
   - Ensure complete and valid JSON structure

## Data Sources:
### Existing Domain Tree Structure:
{existingTags}

### Current Literature Catalog Overview:
{text}

{deletedContent}

{newContent}

## Output Format:
- Return only the revised complete domain tree JSON structure
- Format example:
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

# 土耳其语修订提示词模板
LABEL_REVISE_PROMPT_TR = """
# Rol: Alan Ağacı Revizyon Uzmanı
## Profil:
- Açıklama: Bilgi sınıflandırması ve alan ağacı yönetiminde uzman, içerik değişikliklerine dayalı olarak mevcut alan ağacı yapılarını aşamalı olarak revize etme konusunda uzmanlaşmış profesyonel bir uzmansınız.
- Görev: İçerik değişikliklerini analiz edin ve mevcut literatür konularının dağılımını doğru şekilde yansıtmak için alan ağacı yapısını revize edin.

## Yetenekler:
1. Mevcut alan ağacı yapıları ile gerçek içerik arasındaki eşleşme ilişkisini derinlemesine analiz etme
2. İçerik değişikliklerinin alan sınıflandırması üzerindeki etkisini doğru şekilde değerlendirme
3. Alan ağaçları için istikrarlı ve makul aşamalı ayarlama stratejileri tasarlama
4. Revize edilen sınıflandırma sisteminin iyi hiyerarşi ve mantığa sahip olmasını sağlama

## İş Akışı:
1. **Mevcut Durum Analizi**: Mevcut alan ağacı yapısını ve güncel literatür kataloglarını düzenleyin
2. **Değişiklik Tanımlama**: Silinen ve eklenen içeriğin etiket sistemi üzerindeki etkisini analiz edin
3. **Strateji Geliştirme**: Etiketleri koruma, silme ve ekleme için belirli stratejiler belirleyin
4. **Yapı Ayarlaması**: Genel istikrarı koruyarak aşamalı revizyonları uygulayın
5. **Kalite Doğrulama**: Revize edilen alan ağacının hiyerarşik yapı gereksinimlerini karşıladığından emin olun

## Kısıtlamalar:
1. Yapısal istikrar ilkeleri:
   - Genel alan ağacı yapısının istikrarını koruyun, büyük ölçekli yeniden yapılandırmadan kaçının
   - Değişiklikleri en aza indirmek için mevcut etiketleri kullanmaya öncelik verin

2. İçerik ilişkilendirme işleme:
   - Silinen içerikle ilgili etiketler: Yalnızca silinen içerikle ilgili ve başka desteği olmayan etiketleri kaldırın; diğer içerikle ilgili etiketleri koruyun
   - Yeni içerik işleme: Mevcut etiketlere sınıflandırmaya öncelik verin; sınıflandırma imkansız olduğunda yalnızca yeni etiketler oluşturun

3. Etiket kalite gereksinimleri:
   - Her etiket katalogdaki gerçek içeriğe karşılık gelmelidir; boş etiketler oluşturmayın
   - Etiket adları kısa ve net olmalıdır, maksimum 6 karakter (seri numaraları hariç)
   - Etiketlerin önüne seri numaraları eklenmelidir (seri numaraları karakter limitine dahil değildir)

4. Hiyerarşik yapı kısıtlamaları:
   - Birincil alan etiketi sayısı: 5-10
   - İkincil alan etiketi sayısı: Her birincil etiket altında 1-10
   - Maksimum iki sınıflandırma seviyesi
   - Etiketler arasında makul ebeveyn-çocuk ilişkileri sağlayın

5. Çıktı formatı gereksinimleri:
   - Katı şekilde JSON formatında çıktı verin
   - Açıklayıcı metin yok
   - Tam ve geçerli JSON yapısını sağlayın

## Veri Kaynakları:
### Mevcut Alan Ağacı Yapısı:
{existingTags}

### Güncel Literatür Kataloğu Genel Görünümü:
{text}

{deletedContent}

{newContent}

## Çıktı Formatı:
- Yalnızca revize edilmiş tam alan ağacı JSON yapısını döndürün
- Format örneği:
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
    "label": "2 Birincil Alan Etiketi (Alt Etiket Yok)"
  }}
]
```
"""


def get_label_revise_prompt(language: str, context: dict, project_id: str):
    """
    增量修订领域树的提示词（与 Node.js 保持一致）。
    :param language: '中文', 'en', 'tr' 或其他语言标识
    :param context: {
        text: all toc,
        existingTags: filtered existing tags,
        newContent: new toc,
        deletedContent: deleted toc
    }
    :param project_id: 项目 ID（可用于个性化，当前版本暂未使用）
    :return: 完整的提示词字符串
    """
    text = context.get('text', '')[:100000]
    existing_tags = context.get('existingTags', [])
    new_content = context.get('newContent', '')
    deleted_content = context.get('deletedContent', '')
    
    # 将现有标签转换为JSON字符串
    existing_json = json.dumps(existing_tags, ensure_ascii=False, indent=2)
    
    # 根据语言生成删除内容和新增内容的描述文本（与 Node.js 保持一致）
    deleted_content_text = ''
    new_content_text = ''
    
    # 标准化语言标识（支持多种格式）
    lang_key = language.lower() if language else 'zh'
    if 'en' in lang_key:
        lang_key = 'en'
    elif 'tr' in lang_key:
        lang_key = 'tr'
    else:
        lang_key = 'zh'  # 默认使用中文
    
    if deleted_content:
        messages = {
            'en': f"## Deleted Content\nHere are the table of contents from the deleted literature:\n{deleted_content}",
            'tr': f"## Silinen İçerik\nİşte silinen literatürdeki içindekiler tablosu:\n{deleted_content}",
            'zh': f"## 被删除的内容\n以下是本次要删除的文献目录信息：\n{deleted_content}"
        }
        deleted_content_text = messages.get(lang_key, messages['zh'])
    
    if new_content:
        messages = {
            'en': f"## New Content\nHere are the table of contents from the newly added literature:\n{new_content}",
            'tr': f"## Yeni İçerik\nİşte yeni eklenen literatürdeki içindekiler tablosu:\n{new_content}",
            'zh': f"## 新增的内容\n以下是本次新增的文献目录信息：\n{new_content}"
        }
        new_content_text = messages.get(lang_key, messages['zh'])
    
    # 根据语言选择对应的提示词模板（与 Node.js 的 processPrompt 逻辑完全一致）
    # Node.js 的 getPromptKey 函数：只有 en 返回 baseKey_EN，其他都返回 baseKey
    # Node.js 的 getLanguageFromKey 函数：只有以 _EN 结尾返回 en，其他返回 zh-CN
    # Node.js 的 defaultPrompt 选择：language === 'en' ? defaultPrompts.en : defaultPrompts.zh
    # 注意：Node.js 的 processPrompt 对于 tr 也会使用 defaultPrompts.zh，而不是 defaultPrompts.tr
    
    base_key = 'LABEL_REVISE_PROMPT'
    
    # 确定 promptKey（与 Node.js 的 getPromptKey 一致）
    if lang_key == 'en' or lang_key == 'en-us' or lang_key == 'en_us':
        prompt_key = f'{base_key}_EN'
        lang_code = 'en'  # 与 Node.js 的 getLanguageFromKey 一致
        default_template = LABEL_REVISE_PROMPT_EN
    else:
        # 对于 tr 和其他语言，都返回基础键名（与 Node.js 一致）
        prompt_key = base_key
        lang_code = 'zh-CN'  # 与 Node.js 的 getLanguageFromKey 一致（不是 _EN 结尾就返回 zh-CN）
        # 默认提示词选择（与 Node.js 的 processPrompt 一致：只有 en 用 en，其他用 zh）
        # 但为了更好的用户体验，如果明确是 tr，使用土耳其语模板
        if 'tr' in lang_key:
            default_template = LABEL_REVISE_PROMPT_TR
        else:
            default_template = LABEL_REVISE_PROMPT_ZH
    
    # 尝试获取项目自定义提示词（与 Node.js 的 processPrompt 逻辑一致）
    template = default_template
    if project_id:
        try:
            from llm.models import CustomPrompt
            custom_prompt = CustomPrompt.objects.filter(
                project_id=project_id,
                prompt_type='labelRevise',
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
    prompt = template.format(
        existingTags=existing_json,
        text=text,
        deletedContent=deleted_content_text,
        newContent=new_content_text
    )
    
    return prompt


