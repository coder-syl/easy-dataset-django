"""
提示词管理视图
"""
from rest_framework import status
from rest_framework.decorators import api_view
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.shortcuts import get_object_or_404
import importlib
import os

from projects.models import Project
from llm.models import CustomPrompt
from common.response.result import success, error


def get_prompt_templates():
    """
    返回与 Node 端 lib/db/custom-prompts.js 中 getPromptTemplates 等价的模板结构。
    结构示例：
    {
      "generation": {
        "displayName": {"zh-CN": "...", "en": "..."},
        "prompts": { "QUESTION_PROMPT": { name, description, type }, ... }
      },
      ...
    }
    """
    return {
        "generation": {
            "displayName": {"zh-CN": "内容生成", "en": "Content Generation"},
            "prompts": {
                "QUESTION_PROMPT": {
                    "name": "基础问题生成",
                    "description": "根据文本内容生成高质量问题的基础提示词，变量：{{text}} 待生成问题的文本，{{textLength}} 文本字数，{{number}} 目标问题数量，可选 {{gaPrompt}} 用于体裁受众增强",
                    "type": "question",
                },
                "QUESTION_PROMPT_EN": {
                    "name": "Basic Question Generation",
                    "description": "Prompt for generating high-quality questions from text content in English. Variables: {{text}} source text, {{textLength}} text length, {{number}} question count, optional {{gaPrompt}} for GA enhancement",
                    "type": "question",
                },
                "ANSWER_PROMPT": {
                    "name": "基础答案生成",
                    "description": "基于给定文本和问题生成准确答案的基础提示词，变量：{{text}} 参考文本，{{question}} 需要回答的问题，{{templatePrompt}} 问题模版提示词，{{outputFormatPrompt}} 问题模版自定义输出格式",
                    "type": "answer",
                },
                "ANSWER_PROMPT_EN": {
                    "name": "Basic Answer Generation",
                    "description": "Prompt for generating accurate answers based on given text and questions in English. Variables: {{text}} reference text, {{question}} question to answer, {{templatePrompt}} question template prompt, {{outputFormatPrompt}} question template custom output format",
                    "type": "answer",
                },
                "ENHANCED_ANSWER_PROMPT": {
                    "name": "MGA增强答案生成",
                    "description": "结合体裁受众信息生成风格化答案的高级提示词，变量：{{text}} 参考文本，{{question}} 原始问题，可选 {{gaPrompt}} 表示体裁受众要求，{{templatePrompt}} 问题模版提示词，{{outputFormatPrompt}} 问题模版自定义输出格式",
                    "type": "enhancedAnswer",
                },
                "ENHANCED_ANSWER_PROMPT_EN": {
                    "name": "MGA Enhanced Answer Generation",
                    "description": "Advanced prompt for generating stylized answers with GA information in English. Variables: {{text}} reference content, {{question}} original question, optional {{gaPrompt}} for GA adaptation, {{templatePrompt}} question template prompt, {{outputFormatPrompt}} question template custom output format",
                    "type": "enhancedAnswer",
                },
                "GA_GENERATION_PROMPT": {
                    "name": "GA组合生成",
                    "description": "根据文本内容自动生成体裁受众组合的提示词，变量：{{text}} 原始文本",
                    "type": "ga-generation",
                },
                "GA_GENERATION_PROMPT_EN": {
                    "name": "GA Pair Generation",
                    "description": "Prompt for automatically generating GA pairs from text content in English. Variable: {{text}} source text",
                    "type": "ga-generation",
                },
                "DISTILL_QUESTIONS_PROMPT": {
                    "name": "问题蒸馏生成",
                    "description": "基于特定标签领域生成多样化高质量问题的蒸馏提示词，变量：{{currentTag}} 当前标签，{{tagPath}} 标签完整链路，{{count}} 目标问题数，可选 {{existingQuestions}} 用于避免重复",
                    "type": "distillQuestions",
                },
                "DISTILL_QUESTIONS_PROMPT_EN": {
                    "name": "Question Distillation",
                    "description": "Distillation prompt for generating questions for tag domains in English. Variables: {{currentTag}} current tag, {{tagPath}} tag path, {{count}} question count, optional {{existingQuestionsText}} for deduplication",
                    "type": "distillQuestions",
                },
                "ASSISTANT_REPLY_PROMPT": {
                    "name": "多轮对话回复生成",
                    "description": "生成多轮对话中助手角色回复的提示词，变量：{{scenario}} 对话场景，{{roleA}} 提问者角色，{{roleB}} 回答者角色，{{chunkContent}} 原始文本，{{conversationHistory}} 对话历史，{{currentRound}} 当前轮次，{{totalRounds}} 总轮次",
                    "type": "multiTurnConversation",
                },
                "ASSISTANT_REPLY_PROMPT_EN": {
                    "name": "Multi-turn Conversation Reply Generation",
                    "description": "Prompt for generating assistant role replies in multi-turn conversations. Variables: {{scenario}} conversation scenario, {{roleA}} questioner role, {{roleB}} responder role, {{chunkContent}} original text, {{conversationHistory}} conversation history, {{currentRound}} current round, {{totalRounds}} total rounds",
                    "type": "multiTurnConversation",
                },
                "NEXT_QUESTION_PROMPT": {
                    "name": "多轮对话问题生成",
                    "description": "基于对话历史生成下一轮问题的提示词，变量：{{scenario}} 对话场景，{{roleA}} 提问者角色，{{roleB}} 回答者角色，{{chunkContent}} 原始文本，{{conversationHistory}} 对话历史，{{nextRound}} 下一轮次，{{totalRounds}} 总轮次",
                    "type": "multiTurnConversation",
                },
                "NEXT_QUESTION_PROMPT_EN": {
                    "name": "Multi-turn Conversation Question Generation",
                    "description": "Prompt for generating next round questions based on conversation history. Variables: {{scenario}} conversation scenario, {{roleA}} questioner role, {{roleB}} responder role, {{chunkContent}} original text, {{conversationHistory}} conversation history, {{nextRound}} next round, {{totalRounds}} total rounds",
                    "type": "multiTurnConversation",
                },
                "IMAGE_QUESTION_PROMPT": {
                    "name": "图像问题生成",
                    "description": "基于图像内容生成高质量问题的专业提示词，用于构建视觉问答训练数据集。变量：{{number}} 目标问题数量",
                    "type": "imageQuestion",
                },
                "IMAGE_QUESTION_PROMPT_EN": {
                    "name": "Image Question Generation",
                    "description": "Professional prompt for generating high-quality questions based on image content for visual question-answering training datasets. Variables: {{number}} target question count",
                    "type": "imageQuestion",
                },
            },
        },
        "labeling": {
            "displayName": {"zh-CN": "标签管理", "en": "Label Management"},
            "prompts": {
                "LABEL_PROMPT": {
                    "name": "领域树生成",
                    "description": "根据文档目录结构自动生成领域分类标签树的提示词，变量：{{text}} 待分析目录文本",
                    "type": "label",
                },
                "LABEL_PROMPT_EN": {
                    "name": "Domain Tree Generation",
                    "description": "Prompt for generating domain label tree from document structure in English. Variable: {{text}} catalog content",
                    "type": "label",
                },
                "ADD_LABEL_PROMPT": {
                    "name": "问题标签匹配",
                    "description": "为生成的问题匹配最合适领域标签的智能匹配提示词，变量：{{label}} 标签数组，{{question}} 问题数组",
                    "type": "addLabel",
                },
                "ADD_LABEL_PROMPT_EN": {
                    "name": "Question Label Matching",
                    "description": "Intelligent matching prompt for assigning domain labels to questions in English. Variables: {{label}} label list, {{question}} question list",
                    "type": "addLabel",
                },
                "LABEL_REVISE_PROMPT": {
                    "name": "领域树修订",
                    "description": "在内容变化时对现有领域树进行增量修订的提示词，变量：{{existingTags}} 现有标签树，{{text}} 最新目录汇总，可选 {{deletedContent}}/{{newContent}} 表示删除或新增内容",
                    "type": "labelRevise",
                },
                "LABEL_REVISE_PROMPT_EN": {
                    "name": "Domain Tree Revision",
                    "description": "Prompt for incrementally revising domain tree in English environment. Variables: {{existingTags}} current tag tree, {{text}} combined TOC, optional {{deletedContent}}/{{newContent}} blocks",
                    "type": "labelRevise",
                },
                "DISTILL_TAGS_PROMPT": {
                    "name": "标签蒸馏生成",
                    "description": "基于现有标签体系生成更细粒度子标签的蒸馏提示词，变量：{{parentTag}} 当前父标签，{{path}}/{{tagPath}} 标签链路，{{count}} 子标签数量，可选 {{existingTagsText}} 表示已有子标签",
                    "type": "distillTags",
                },
                "DISTILL_TAGS_PROMPT_EN": {
                    "name": "Tag Distillation",
                    "description": "Distillation prompt for generating sub-tags based on tag system in English. Variables: {{parentTag}} parent tag, {{path}}/{{tagPath}} hierarchy path, {{count}} target number, optional {{existingTagsText}} existing sub-tags",
                    "type": "distillTags",
                },
            },
        },
        "optimization": {
            "displayName": {"zh-CN": "内容优化", "en": "Content Optimization"},
            "prompts": {
                "NEW_ANSWER_PROMPT": {
                    "name": "答案优化重写",
                    "description": "根据用户反馈建议对答案进行优化重写的提示词，变量：{{chunkContent}} 原始文本块，{{question}} 原始问题，{{answer}} 待优化答案，{{cot}} 待优化思维链，{{advice}} 优化建议",
                    "type": "newAnswer",
                },
                "NEW_ANSWER_PROMPT_EN": {
                    "name": "Answer Optimization Rewrite",
                    "description": "Prompt for optimizing and rewriting answers based on feedback in English. Variables: {{chunkContent}} original chunk, {{question}} question, {{answer}} answer, {{cot}} chain of thought, {{advice}} feedback",
                    "type": "newAnswer",
                },
                "OPTIMIZE_COT_PROMPT": {
                    "name": "思维链优化",
                    "description": "优化答案中思维链推理过程和逻辑结构的提示词，变量：{{originalQuestion}} 原始问题，{{answer}} 答案，{{originalCot}} 原始思维链",
                    "type": "optimizeCot",
                },
                "OPTIMIZE_COT_PROMPT_EN": {
                    "name": "Chain-of-Thought Optimization",
                    "description": "Prompt for optimizing chain-of-thought reasoning process in English. Variables: {{originalQuestion}} question, {{answer}} answer, {{originalCot}} original chain of thought",
                    "type": "optimizeCot",
                },
            },
        },
        "processing": {
            "displayName": {"zh-CN": "数据处理", "en": "Data Processing"},
            "prompts": {
                "DATA_CLEAN_PROMPT": {
                    "name": "文本数据清洗",
                    "description": "清理和标准化原始文本数据格式的提示词，变量：{{text}} 需清洗文本，{{textLength}} 文本字数",
                    "type": "dataClean",
                },
                "DATA_CLEAN_PROMPT_EN": {
                    "name": "Text Data Cleaning",
                    "description": "Prompt for cleaning and standardizing text data in English environment. Variables: {{text}} text to clean, {{text.length}} length placeholder",
                    "type": "dataClean",
                },
            },
        },
        "evaluation": {
            "displayName": {"zh-CN": "质量评估", "en": "Quality Evaluation"},
            "prompts": {
                "DATASET_EVALUATION_PROMPT": {
                    "name": "数据集质量评估",
                    "description": "对问答数据集进行多维度质量评估的专业提示词，变量：{{chunkContent}} 原始文本块内容，{{question}} 问题，{{answer}} 答案",
                    "type": "datasetEvaluation",
                },
                "DATASET_EVALUATION_PROMPT_EN": {
                    "name": "Dataset Quality Evaluation",
                    "description": "Professional prompt for multi-dimensional quality evaluation of Q&A datasets. Variables: {{chunkContent}} original text chunk, {{question}} question, {{answer}} answer",
                    "type": "datasetEvaluation",
                },
            },
        },
    }


@swagger_auto_schema(
    method='get',
    operation_summary='获取默认提示词',
    responses={200: openapi.Response('默认提示词')}
)
@api_view(['GET'])
def default_prompts(request, project_id):
    """获取默认提示词"""
    try:
        project = get_object_or_404(Project, id=project_id)
        
        prompt_type = request.GET.get('promptType')
        prompt_key = request.GET.get('promptKey')
        
        if not prompt_type or not prompt_key:
            return error(message='promptType and promptKey are required', response_status=status.HTTP_400_BAD_REQUEST)
        
        # 动态导入提示词模块
        try:
            # 从common.services.prompt_service导入
            from common.services import prompt_service
            
            # 获取提示词常量
            prompt_content = getattr(prompt_service, prompt_key, None)
            
            if not prompt_content:
                return error(message=f'Prompt key {prompt_key} not found', response_status=status.HTTP_404_NOT_FOUND)
            
            return success(data={
                'content': prompt_content,
                'promptType': prompt_type,
                'promptKey': prompt_key
            })
        except ImportError as e:
            return error(message=f'Prompt module {prompt_type} not found: {str(e)}', response_status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(
    method='get',
    operation_summary='获取自定义提示词',
    responses={200: openapi.Response('自定义提示词列表')}
)
@swagger_auto_schema(
    method='post',
    operation_summary='保存自定义提示词',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'promptType': openapi.Schema(type=openapi.TYPE_STRING),
            'promptKey': openapi.Schema(type=openapi.TYPE_STRING),
            'language': openapi.Schema(type=openapi.TYPE_STRING),
            'content': openapi.Schema(type=openapi.TYPE_STRING),
            'prompts': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(type=openapi.TYPE_STRING)
            )
        }
    ),
    responses={200: openapi.Response('保存成功')}
)
@swagger_auto_schema(
    method='delete',
    operation_summary='删除自定义提示词',
    responses={200: openapi.Response('删除成功')}
)
@api_view(['GET', 'POST', 'DELETE'])
def custom_prompts(request, project_id):
    """自定义提示词管理"""
    try:
        project = get_object_or_404(Project, id=project_id)
    except Exception as e:
        return error(message='项目不存在', response_status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        try:
            prompt_type = request.GET.get('promptType')
            language = request.GET.get('language')
            
            # 获取自定义提示词
            queryset = CustomPrompt.objects.filter(project=project)
            
            if prompt_type:
                queryset = queryset.filter(prompt_type=prompt_type)
            if language:
                queryset = queryset.filter(language=language)
            
            custom_prompts_data = [{
                'id': cp.id,
                'promptType': cp.prompt_type,
                'promptKey': cp.prompt_key,
                'language': cp.language,
                'content': cp.content
            } for cp in queryset]
            
            # 获取模板列表（与 Node getPromptTemplates 等价）
            templates = get_prompt_templates()
            
            return success(data={
                'customPrompts': custom_prompts_data,
                'templates': templates
            })
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'POST':
        try:
            # 批量保存
            if 'prompts' in request.data and isinstance(request.data['prompts'], list):
                results = []
                for prompt_data in request.data['prompts']:
                    cp, created = CustomPrompt.objects.update_or_create(
                        project=project,
                        prompt_type=prompt_data.get('promptType'),
                        prompt_key=prompt_data.get('promptKey'),
                        language=prompt_data.get('language'),
                        defaults={'content': prompt_data.get('content', '')}
                    )
                    results.append({
                        'id': cp.id,
                        'created': created
                    })
                return success(data={'results': results})
            
            # 单个保存
            prompt_type = request.data.get('promptType')
            prompt_key = request.data.get('promptKey')
            language = request.data.get('language')
            content = request.data.get('content')
            
            if not all([prompt_type, prompt_key, language, content is not None]):
                return error(message='promptType, promptKey, language and content are required', response_status=status.HTTP_400_BAD_REQUEST)
            
            cp, created = CustomPrompt.objects.update_or_create(
                project=project,
                prompt_type=prompt_type,
                prompt_key=prompt_key,
                language=language,
                defaults={'content': content}
            )
            
            return success(data={'result': {
                'id': cp.id,
                'created': created
            }})
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'DELETE':
        try:
            prompt_type = request.GET.get('promptType')
            prompt_key = request.GET.get('promptKey')
            language = request.GET.get('language')
            
            if not all([prompt_type, prompt_key, language]):
                return error(message='promptType, promptKey and language are required', response_status=status.HTTP_400_BAD_REQUEST)
            
            deleted_count, _ = CustomPrompt.objects.filter(
                project=project,
                prompt_type=prompt_type,
                prompt_key=prompt_key,
                language=language
            ).delete()
            
            return success(data={'success': deleted_count > 0})
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)

