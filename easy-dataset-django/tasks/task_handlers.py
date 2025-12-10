"""
任务处理函数
迁移自lib/services/tasks/
"""
import json
import logging
from typing import Dict
from django.utils import timezone
from .models import Task
from projects.models import Project
from chunks.models import Chunk
from questions.models import Question
from datasets.models import Dataset
from common.services.llm_service import LLMService
from common.services.prompt_service import get_question_prompt, get_answer_prompt
from common.services.domain_tree import handle_domain_tree

logger = logging.getLogger('tasks')


def update_task(task_id: str, data: Dict):
    """
    更新任务状态
    :param task_id: 任务ID
    :param data: 更新数据
    """
    try:
        task = Task.objects.get(id=task_id)
        
        # 如果更新状态为完成或失败，且未提供结束时间，则自动添加
        if 'status' in data:
            if data['status'] in [1, 2] and not data.get('end_time'):
                data['end_time'] = timezone.now()
        
        # 更新字段
        for key, value in data.items():
            if hasattr(task, key):
                setattr(task, key, value)
        
        task.save()
        return task
    except Task.DoesNotExist:
        return None


def process_question_generation_task(task: Task):
    """
    处理问题生成任务
    """
    try:
        # 解析模型信息
        try:
            model_info = json.loads(task.model_info) if isinstance(task.model_info, str) else task.model_info
        except:
            raise ValueError('模型信息解析失败')
        
        # 获取项目配置
        project = task.project
        from pathlib import Path
        task_config_path = Path('local-db') / str(project.id) / 'task-config.json'
        concurrency_limit = 2  # 默认并发数
        
        if task_config_path.exists():
            with open(task_config_path, 'r', encoding='utf-8') as f:
                task_config = json.load(f)
                concurrency_limit = task_config.get('concurrencyLimit', 2)
        
        # 查询所有未生成问题的文本块
        chunks = Chunk.objects.filter(
            project=project
        ).exclude(
            name__in=['Image Chunk', 'Distilled Content']
        ).prefetch_related('questions')
        
        # 过滤出没有问题的文本块
        chunks_without_questions = [chunk for chunk in chunks if chunk.questions.count() == 0]
        
        if len(chunks_without_questions) == 0:
            update_task(task.id, {
                'status': 1,  # 已完成
                'completed_count': 0,
                'total_count': 0,
                'detail': json.dumps({'stepInfo': '没有需要生成问题的文本块', 'totalChunks': 0, 'processedChunks': 0}, ensure_ascii=False),
                'note': '没有需要生成问题的文本块',
                'end_time': timezone.now()
            })
            return
        
        # 更新任务总数并初始化详情
        total_count = len(chunks_without_questions)
        task_message = {
            'stepInfo': '开始生成问题',
            'errorList': [],
            'logs': [],
            'processedChunks': 0,
            'totalChunks': total_count,
            'successCount': 0,
            'errorCount': 0,
            'totalQuestions': 0,
            'current': {'chunkId': '', 'chunkName': ''},
            'finishedList': []
        }
        update_task(task.id, {
            'total_count': total_count,
            'detail': json.dumps(task_message, ensure_ascii=False)
        })
        
        # 批量处理每个文本块
        success_count = 0
        error_count = 0
        total_questions = 0
        
        from questions.services import generate_questions_for_chunk
        
        for idx, chunk in enumerate(chunks_without_questions, start=1):
            try:
                # 检查任务状态
                latest_task = Task.objects.get(id=task.id)
                if latest_task.status in [2, 3]:  # 失败或已中断
                    task_message['stepInfo'] = '任务已被中断/失败，停止后续处理'
                    update_task(task.id, {
                        'detail': json.dumps(task_message, ensure_ascii=False),
                        'end_time': timezone.now()
                    })
                    return
                
                task_message['current'] = {'chunkId': str(chunk.id), 'chunkName': chunk.name}
                task_message['stepInfo'] = f'生成问题 {idx}/{total_count}: {chunk.name}'
                task_message['logs'].append({
                    'time': timezone.now().strftime('%H:%M:%S'),
                    'level': 'info',
                    'message': f'开始生成: {chunk.name}'
                })
                
                # 生成问题
                result = generate_questions_for_chunk(
                    str(project.id),
                    str(chunk.id),
                    {
                        'model': model_info,
                        'language': '中文' if task.language == 'zh-CN' else 'en',
                        'count': 5
                    }
                )
                
                success_count += 1
                total_questions += result.get('total', 0)
                
                task_message['successCount'] = success_count
                task_message['totalQuestions'] = total_questions
                task_message['finishedList'].append({
                    'chunkId': str(chunk.id),
                    'chunkName': chunk.name,
                    'status': 'success',
                    'questionsCount': result.get('total', 0),
                    'llm': result.get('llm', {})
                })
                task_message['logs'].append({
                    'time': timezone.now().strftime('%H:%M:%S'),
                    'level': 'success',
                    'message': f'生成完成: {chunk.name}, 问题数: {result.get("total", 0)}'
                })
            except Exception as e:
                error_count += 1
                err_msg = f'生成问题失败: {chunk.name}, 错误: {str(e)}'
                task_message['errorCount'] = error_count
                task_message['errorList'].append(err_msg)
                task_message['finishedList'].append({
                    'chunkId': str(chunk.id),
                    'chunkName': chunk.name,
                    'status': 'error',
                    'error': str(e)
                })
                task_message['logs'].append({
                    'time': timezone.now().strftime('%H:%M:%S'),
                    'level': 'error',
                    'message': err_msg
                })
            
            task_message['processedChunks'] = idx
            update_task(task.id, {
                'completed_count': success_count + error_count,
                'total_count': total_count,
                'detail': json.dumps(task_message, ensure_ascii=False)
            })
        
        # 任务完成
        final_status = 2 if (error_count > 0 and success_count == 0) else 1
        task_message['stepInfo'] = '问题生成完成' if final_status == 1 else '问题生成部分失败'
        update_task(task.id, {
            'status': final_status,
            'detail': json.dumps(task_message, ensure_ascii=False),
            'note': '' if final_status == 1 else '部分失败',
            'end_time': timezone.now()
        })
    except Exception as e:
        update_task(task.id, {
            'status': 2,  # 失败
            'detail': f'处理失败: {str(e)}',
            'note': f'处理失败: {str(e)}'
        })


def process_answer_generation_task(task: Task):
    """
    处理答案生成任务
    """
    try:
        # 解析模型信息
        try:
            model_info = json.loads(task.model_info) if isinstance(task.model_info, str) else task.model_info
        except:
            raise ValueError('模型信息解析失败')
        
        project = task.project
        
        # 查询未生成答案的问题
        questions = Question.objects.filter(
            project=project,
            answered=False,
            image_id__isnull=True
        )
        
        if questions.count() == 0:
            update_task(task.id, {
                'status': 1,
                'detail': json.dumps({'stepInfo': '没有需要处理的问题', 'totalQuestions': 0, 'processedQuestions': 0}, ensure_ascii=False),
                'note': '',
                'end_time': timezone.now()
            })
            return
        
        # 更新任务总数并初始化详情
        total_count = questions.count()
        task_message = {
            'stepInfo': '开始生成答案',
            'errorList': [],
            'logs': [],
            'processedQuestions': 0,
            'totalQuestions': total_count,
            'successCount': 0,
            'errorCount': 0,
            'current': {'questionId': '', 'chunkId': ''},
            'finishedList': []
        }
        update_task(task.id, {
            'total_count': total_count,
            'detail': json.dumps(task_message, ensure_ascii=False)
        })
        
        # 批量处理每个问题
        success_count = 0
        error_count = 0
        total_datasets = 0
        
        from datasets.services import generate_dataset_for_question
        
        for idx, question in enumerate(questions, start=1):
            try:
                # 检查任务状态
                latest_task = Task.objects.get(id=task.id)
                if latest_task.status in [2, 3]:
                    task_message['stepInfo'] = '任务已被中断/失败，停止后续处理'
                    update_task(task.id, {
                        'detail': json.dumps(task_message, ensure_ascii=False),
                        'end_time': timezone.now()
                    })
                    return
                
                task_message['current'] = {'questionId': str(question.id), 'chunkId': str(question.chunk_id)}
                task_message['stepInfo'] = f'生成答案 {idx}/{total_count}'
                task_message['logs'].append({
                    'time': timezone.now().strftime('%H:%M:%S'),
                    'level': 'info',
                    'message': f'开始生成答案，问题ID: {question.id}'
                })
                
                # 生成答案
                result = generate_dataset_for_question(
                    str(project.id),
                    str(question.id),
                    {
                        'model': model_info,
                        'language': '中文' if task.language == 'zh-CN' else 'en'
                    }
                )
                
                # 标记问题为已回答
                question.answered = True
                question.save()
                
                success_count += 1
                total_datasets += 1
                
                task_message['successCount'] = success_count
                task_message['finishedList'].append({
                    'questionId': str(question.id),
                    'chunkId': str(question.chunk_id),
                    'status': 'success'
                })
                task_message['logs'].append({
                    'time': timezone.now().strftime('%H:%M:%S'),
                    'level': 'success',
                    'message': f'生成答案完成，问题ID: {question.id}'
                })
            except Exception as e:
                error_count += 1
                err_msg = f'生成答案失败: 问题ID {question.id}, 错误: {str(e)}'
                task_message['errorCount'] = error_count
                task_message['errorList'].append(err_msg)
                task_message['finishedList'].append({
                    'questionId': str(question.id),
                    'chunkId': str(question.chunk_id),
                    'status': 'error',
                    'error': str(e)
                })
                task_message['logs'].append({
                    'time': timezone.now().strftime('%H:%M:%S'),
                    'level': 'error',
                    'message': err_msg
                })
            
            task_message['processedQuestions'] = idx
            update_task(task.id, {
                'completed_count': success_count + error_count,
                'total_count': total_count,
                'detail': json.dumps(task_message, ensure_ascii=False),
                'note': f'已处理: {success_count + error_count}/{total_count}, 成功: {success_count}, 失败: {error_count}, 共生成数据集: {total_datasets}'
            })
        
        # 任务完成
        final_status = 2 if (error_count > 0 and success_count == 0) else 1
        task_message['stepInfo'] = '答案生成完成' if final_status == 1 else '答案生成部分失败'
        update_task(task.id, {
            'status': final_status,
            'detail': json.dumps(task_message, ensure_ascii=False),
            'note': '' if final_status == 1 else '部分失败',
            'end_time': timezone.now()
        })
    except Exception as e:
        update_task(task.id, {
            'status': 2,
            'detail': f'处理失败: {str(e)}',
            'note': f'处理失败: {str(e)}'
        })


def process_file_processing_task(task: Task):
    """
    参考 Node 流程的文件处理任务（完整版，含领域树 LLM 修订）：
    - 读取 note 中的 fileList，逐个调用 split_project_file 分割文件，并累计 toc
    - 调用 handle_domain_tree (rebuild/revise/keep)，使用 LLM 生成/修订领域树标签
    - 按文件数量更新任务进度，记录错误
    """
    try:
        import json
        from chunks.services import split_project_file

        params = json.loads(task.note) if isinstance(task.note, str) else (task.note or {})
        project_id = params.get('projectId') or params.get('project_id')
        file_list_raw = params.get('fileList') or params.get('file_list') or []
        domain_tree_action = params.get('domainTreeAction') or params.get('domain_tree_action', 'rebuild')
        delete_toc = params.get('deleteToc') or params.get('delete_toc', '')

        # 规范化 fileList：确保是文件名数组
        file_list = []
        for item in file_list_raw:
            if isinstance(item, dict):
                # 从对象中提取文件名
                file_name = item.get('fileName') or item.get('file_name') or item.get('name')
                if file_name:
                    file_list.append(file_name)
            elif isinstance(item, str):
                # 直接是字符串（文件名）
                if item:
                    file_list.append(item)

        logger.debug(f'[Task {task.id}] 解析任务参数: projectId={project_id}, fileList原始数量={len(file_list_raw) if isinstance(file_list_raw, list) else 0}, fileList规范化后数量={len(file_list)}, domainTreeAction={domain_tree_action}')

        if not project_id:
            logger.error(f'[Task {task.id}] 项目ID为空')
            raise ValueError('项目ID不能为空')
        
        if not file_list or len(file_list) == 0:
            logger.warning(f'[Task {task.id}] 文件列表为空，跳过文件处理，仅处理领域树')
            # 如果文件列表为空，仍然可以处理领域树（如果 action 是 keep）
            if domain_tree_action == 'keep':
                update_task(task.id, {
                    'status': 1,
                    'detail': json.dumps({
                        'stepInfo': '无文件处理，任务完成',
                        'processedFiles': 0,
                        'totalFiles': 0,
                        'finishedList': [],
                        'errorList': []
                    }, ensure_ascii=False),
                    'end_time': timezone.now()
                })
                return
            else:
                logger.error(f'[Task {task.id}] 文件列表为空且领域树操作不是 keep，任务无法继续')
                raise ValueError('文件列表不能为空')

        total_files = len(file_list)
        processed_files = 0
        toc_aggregate = ''

        logger.info(f'[Task {task.id}] 开始处理文件处理任务: 项目ID={project_id}, 文件数={total_files}, 领域树操作={domain_tree_action}')

        # 构建详细的任务信息对象
        task_message = {
            'stepInfo': f'开始处理 {total_files} 个文件',
            'processedFiles': 0,
            'totalFiles': total_files,
            'current': {
                'fileName': '',
                'processedPage': 0,
                'totalPage': 0
            },
            'finishedList': [],
            'errorList': [],
            'logs': []  # 添加日志列表
        }
        
        # 添加初始日志
        task_message['logs'].append({
            'time': timezone.now().isoformat(),
            'level': 'info',
            'message': f'任务开始：准备处理 {total_files} 个文件'
        })

        update_task(task.id, {
            'status': 0,
            'detail': json.dumps(task_message, ensure_ascii=False),
            'total_count': total_files,
            'completed_count': 0,
            'start_time': timezone.now()
        })

        # 文件分割并累计 toc
        valid_files_processed = 0
        for file_item in file_list:
            # 兼容多种格式：{fileName: 'xxx'}, {file_name: 'xxx'}, 或直接是字符串
            if isinstance(file_item, dict):
                file_name = file_item.get('fileName') or file_item.get('file_name')
            else:
                file_name = str(file_item)
            
            if not file_name:
                logger.warning(f'[Task {task.id}] 跳过无效的文件项: {file_item}')
                continue
            
            valid_files_processed += 1
            try:
                logger.info(f'[Task {task.id}] 开始处理文件: {file_name}')
                
                # 添加日志
                task_message['logs'].append({
                    'time': timezone.now().isoformat(),
                    'level': 'info',
                    'message': f'开始处理文件: {file_name}'
                })
                
                # 更新当前处理文件信息
                task_message['current'] = {
                    'fileName': file_name,
                    'processedPage': 0,
                    'totalPage': 1,
                    'status': 'processing',
                    'startTime': timezone.now().isoformat()
                }
                task_message['stepInfo'] = f'正在处理文件: {file_name} ({processed_files + 1}/{total_files})'
                update_task(task.id, {
                    'detail': json.dumps(task_message, ensure_ascii=False)
                })
                
                # 添加文件分割日志
                task_message['logs'].append({
                    'time': timezone.now().isoformat(),
                    'level': 'info',
                    'message': f'正在分割文件: {file_name}'
                })
                update_task(task.id, {
                    'detail': json.dumps(task_message, ensure_ascii=False)
                })
                
                split_result = split_project_file(project_id, file_name)
                chunks_count = split_result.get('totalChunks', 0)
                toc_aggregate += (split_result.get('toc') or '') + '\n'
                processed_files += 1
                
                # 更新文件处理完成信息
                task_message['current']['status'] = 'completed'
                task_message['current']['endTime'] = timezone.now().isoformat()
                task_message['current']['chunksGenerated'] = chunks_count
                
                # 添加完成日志
                task_message['logs'].append({
                    'time': timezone.now().isoformat(),
                    'level': 'success',
                    'message': f'文件处理完成: {file_name}, 生成 {chunks_count} 个文本块'
                })
                
                # 更新已完成文件列表
                task_message['processedFiles'] = processed_files
                task_message['finishedList'].append({'fileName': file_name})
                task_message['current'] = {'fileName': '', 'processedPage': 0, 'totalPage': 0}
                task_message['stepInfo'] = f'已处理 {processed_files}/{total_files} 文件'
                
                logger.info(f'[Task {task.id}] 文件 {file_name} 处理完成, 生成 {split_result.get("totalChunks", 0)} 个文本块')
                update_task(task.id, {
                    'completed_count': processed_files,
                    'detail': json.dumps(task_message, ensure_ascii=False)
                })
            except Exception as e:
                error_msg = f'文件 {file_name} 处理失败: {str(e)}'
                logger.error(f'[Task {task.id}] {error_msg}', exc_info=True)
                task_message['errorList'].append(error_msg)
                task_message['current'] = {'fileName': '', 'processedPage': 0, 'totalPage': 0}
                task_message['stepInfo'] = f'处理文件时出错: {file_name}'
                update_task(task.id, {
                    'detail': json.dumps(task_message, ensure_ascii=False)
                })

        # 领域树处理（rebuild/revise/keep），使用 LLM
        try:
            logger.info(f'[Task {task.id}] 开始处理领域树, action={domain_tree_action}')
            task_message['stepInfo'] = f'开始处理领域树 (操作: {domain_tree_action})'
            
            model_info = json.loads(task.model_info) if isinstance(task.model_info, str) else task.model_info or {}
            language = '中文' if task.language.startswith('zh') else 'en'
            
            # 记录LLM调用信息
            llm_info = {
                'provider': model_info.get('providerName') or model_info.get('providerId', ''),
                'model': model_info.get('modelName') or model_info.get('modelId', ''),
                'endpoint': model_info.get('endpoint', ''),
                'action': domain_tree_action,
                'tocLength': len(toc_aggregate),
                'status': 'calling',
                'startTime': timezone.now().isoformat()
            }
            task_message['llmCall'] = llm_info
            
            # 添加LLM调用日志
            task_message['logs'].append({
                'time': timezone.now().isoformat(),
                'level': 'info',
                'message': f'开始调用大模型生成领域树 - 模型: {llm_info["model"]}, 提供商: {llm_info["provider"]}, 操作: {domain_tree_action}, 目录长度: {len(toc_aggregate)} 字符'
            })
            update_task(task.id, {
                'detail': json.dumps(task_message, ensure_ascii=False)
            })
            
            # 添加提示词准备日志
            task_message['logs'].append({
                'time': timezone.now().isoformat(),
                'level': 'info',
                'message': f'正在准备提示词，目录内容长度: {len(toc_aggregate)} 字符'
            })
            update_task(task.id, {
                'detail': json.dumps(task_message, ensure_ascii=False)
            })
            
            try:
                tags = handle_domain_tree(
                    project_id=project_id,
                    action=domain_tree_action,
                    all_toc=toc_aggregate,
                    new_toc=toc_aggregate,
                    delete_toc=delete_toc,
                    model=model_info,
                    language=language
                )
                
                # 更新LLM调用信息
                tags_count = len(tags) if tags else 0
                llm_info['status'] = 'completed'
                llm_info['endTime'] = timezone.now().isoformat()
                llm_info['tagsGenerated'] = tags_count
                task_message['llmCall'] = llm_info
                task_message['stepInfo'] = f'领域树处理完成, 生成 {tags_count} 个标签'
                
                # 添加LLM调用完成日志
                task_message['logs'].append({
                    'time': timezone.now().isoformat(),
                    'level': 'success',
                    'message': f'大模型调用完成 - 生成 {tags_count} 个领域树标签'
                })
            except Exception as llm_error:
                # 记录LLM调用错误
                error_msg = f'大模型调用失败: {str(llm_error)}'
                logger.error(f'[Task {task.id}] {error_msg}', exc_info=True)
                task_message['logs'].append({
                    'time': timezone.now().isoformat(),
                    'level': 'error',
                    'message': error_msg
                })
                llm_info['status'] = 'failed'
                llm_info['endTime'] = timezone.now().isoformat()
                llm_info['error'] = str(llm_error)
                task_message['llmCall'] = llm_info
                update_task(task.id, {
                    'detail': json.dumps(task_message, ensure_ascii=False)
                })
                raise
        except Exception as e:
            error_msg = f'领域树处理失败: {str(e)}'
            logger.error(f'[Task {task.id}] {error_msg}', exc_info=True)
            task_message['errorList'].append(error_msg)
            task_message['stepInfo'] = error_msg
            update_task(task.id, {
                'detail': json.dumps(task_message, ensure_ascii=False)
            })

        # 检查是否有有效文件被处理
        if valid_files_processed == 0:
            logger.error(f'[Task {task.id}] 没有有效文件被处理，所有文件项都被跳过')
            error_message = {
                'stepInfo': '任务处理失败：没有有效文件被处理',
                'errorList': ['所有文件项都无效或被跳过'],
                'processedFiles': 0,
                'totalFiles': total_files,
                'finishedList': [],
                'current': {'fileName': '', 'processedPage': 0, 'totalPage': 0}
            }
            update_task(task.id, {
                'status': 2,  # 失败
                'detail': json.dumps(error_message, ensure_ascii=False),
                'note': '处理失败：没有有效文件被处理',
                'end_time': timezone.now()
            })
            return
        
        logger.info(f'[Task {task.id}] 文件处理任务完成')
        task_message['stepInfo'] = '文件处理完成'
        update_task(task.id, {
            'status': 1,
            'detail': json.dumps(task_message, ensure_ascii=False),
            'end_time': timezone.now()
        })
    except Exception as e:
        logger.error(f'[Task {task.id}] 文件处理任务失败: {str(e)}', exc_info=True)
        error_message = {
            'stepInfo': f'任务处理失败: {str(e)}',
            'errorList': [f'任务处理失败: {str(e)}'],
            'processedFiles': processed_files if 'processed_files' in locals() else 0,
            'totalFiles': total_files if 'total_files' in locals() else 0,
            'finishedList': task_message.get('finishedList', []) if 'task_message' in locals() else [],
            'current': {'fileName': '', 'processedPage': 0, 'totalPage': 0}
        }
        update_task(task.id, {
            'status': 2,
            'detail': json.dumps(error_message, ensure_ascii=False),
            'note': f'处理失败: {str(e)}',
            'end_time': timezone.now()
        })


def process_data_cleaning_task(task: Task):
    """处理数据清洗任务"""
    try:
        # 解析模型与语言
        model_info = json.loads(task.model_info) if isinstance(task.model_info, str) else task.model_info
        language = '中文' if task.language.startswith('zh') else 'en'

        # 过滤需要清洗的文本块
        chunks = Chunk.objects.filter(project_id=task.project_id).exclude(
            name__in=['Image Chunk', 'Distilled Content']
        )
        total = chunks.count()
        # 若无文本块，直接完成任务
        if total == 0:
            update_task(task.id, {
                'status': 1,
                'total_count': 0,
                'completed_count': 0,
                'detail': json.dumps({'stepInfo': '没有需要清洗的文本块', 'totalChunks': 0, 'processedChunks': 0}, ensure_ascii=False),
                'note': '没有需要清洗的文本块',
                'end_time': timezone.now()
            })
            return

        # 初始化任务进度详情（与 file-processing 一致的风格）
        task_message = {
            'stepInfo': '开始数据清洗',
            'errorList': [],
            'logs': [],
            'processedChunks': 0,
            'totalChunks': total,
            'successCount': 0,
            'errorCount': 0,
            'current': {'chunkId': '', 'chunkName': ''},
            'finishedList': []
        }
        total_original_length = 0
        total_cleaned_length = 0
        update_task(task.id, {
            'total_count': total,
            'detail': json.dumps(task_message, ensure_ascii=False)
        })

        from chunks.services import clean_chunk_content

        for idx, chunk in enumerate(chunks, start=1):
            # 若任务被外部标记为失败/中断，则停止
            latest = Task.objects.filter(id=task.id).first()
            if latest and latest.status in [2, 3]:
                task_message['stepInfo'] = '任务已被中断/失败，停止后续处理'
                update_task(task.id, {
                    'detail': json.dumps(task_message, ensure_ascii=False),
                    'end_time': timezone.now()
                })
                return

            task_message['current'] = {'chunkId': str(chunk.id), 'chunkName': chunk.name}
            task_message['stepInfo'] = f'清洗文本块 {idx}/{total}: {chunk.name}'
            task_message['logs'].append({
                'time': timezone.now().strftime('%H:%M:%S'),
                'level': 'info',
                'message': f'开始清洗: {chunk.name}'
            })

            try:
                clean_result = clean_chunk_content(str(task.project_id), str(chunk.id), model_info, language)
                total_original_length += clean_result.get('originalLength', 0)
                total_cleaned_length += clean_result.get('cleanedLength', 0)
                task_message['successCount'] += 1
                task_message['finishedList'].append({
                    'chunkId': str(chunk.id),
                    'chunkName': chunk.name,
                    'status': 'success',
                    'llm': clean_result.get('llm', {})
                })
                task_message['logs'].append({
                    'time': timezone.now().strftime('%H:%M:%S'),
                    'level': 'success',
                    'message': f'清洗完成: {chunk.name}'
                })
            except Exception as e:
                task_message['errorCount'] += 1
                err_msg = f'清洗失败: {chunk.name}, 错误: {str(e)}'
                task_message['errorList'].append(err_msg)
                task_message['finishedList'].append({
                    'chunkId': str(chunk.id),
                    'chunkName': chunk.name,
                    'status': 'error',
                    'error': str(e)
                })
                task_message['logs'].append({
                    'time': timezone.now().strftime('%H:%M:%S'),
                    'level': 'error',
                    'message': err_msg
                })

            task_message['processedChunks'] = idx
            update_task(task.id, {
                'completed_count': idx,
                'total_count': total,
                'detail': json.dumps(task_message, ensure_ascii=False),
                'note': f'已处理: {idx}/{total}, 成功: {task_message["successCount"]}, 失败: {task_message["errorCount"]}, 原始总长度: {total_original_length}, 清洗后总长度: {total_cleaned_length}'
            })

        # 结束状态
        final_status = 1 if task_message['errorCount'] == 0 else 2 if task_message['successCount'] == 0 else 1
        task_message['stepInfo'] = '数据清洗完成' if final_status == 1 else '数据清洗部分失败'
        update_task(task.id, {
            'status': final_status,
            'note': '' if final_status == 1 else '部分清洗失败',
            'detail': json.dumps(task_message, ensure_ascii=False),
            'end_time': timezone.now()
        })
    except Exception as e:
        update_task(task.id, {
            'status': 2,
            'detail': f'处理失败: {str(e)}',
            'note': f'处理失败: {str(e)}'
        })


def process_dataset_evaluation_task(task: Task):
    """处理数据集评估任务"""
    try:
        model_info = json.loads(task.model_info) if isinstance(task.model_info, str) else task.model_info
        datasets = Dataset.objects.filter(project_id=task.project_id)
        total = datasets.count()
        success_count = 0
        error_count = 0
        task_message = {
            'stepInfo': '开始数据集评估',
            'errorList': [],
            'logs': [],
            'processedDatasets': 0,
            'totalDatasets': total,
            'successCount': 0,
            'errorCount': 0,
            'finishedList': []
        }
        update_task(task.id, {
            'total_count': total,
            'detail': json.dumps(task_message, ensure_ascii=False)
        })

        from datasets.evaluation_views import evaluate_dataset

        for idx, ds in enumerate(datasets, start=1):
            try:
                class DummyRequest:
                    data = {'model': model_info, 'language': task.language}
                evaluate_dataset(DummyRequest(), str(task.project_id), str(ds.id))
                success_count += 1
                task_message['finishedList'].append({'datasetId': str(ds.id), 'status': 'success'})
                task_message['logs'].append({
                    'time': timezone.now().strftime('%H:%M:%S'),
                    'level': 'success',
                    'message': f'评估完成: {ds.id}'
                })
            except Exception as e:
                error_count += 1
                task_message['finishedList'].append({'datasetId': str(ds.id), 'status': 'error', 'error': str(e)})
                task_message['errorList'].append(f'评估失败: {ds.id}, 错误: {str(e)}')
                task_message['logs'].append({
                    'time': timezone.now().strftime('%H:%M:%S'),
                    'level': 'error',
                    'message': f'评估失败: {ds.id}, 错误: {str(e)}'
                })
            task_message['successCount'] = success_count
            task_message['errorCount'] = error_count
            task_message['processedDatasets'] = idx
            update_task(task.id, {
                'completed_count': success_count + error_count,
                'total_count': total,
                'detail': json.dumps(task_message, ensure_ascii=False)
            })

        final_status = 1 if error_count == 0 else 2 if success_count == 0 else 1
        update_task(task.id, {
            'status': final_status,
            'note': '' if final_status == 1 else '部分失败',
            'detail': json.dumps(task_message, ensure_ascii=False),
            'end_time': timezone.now()
        })
    except Exception as e:
        update_task(task.id, {
            'status': 2,
            'detail': f'处理失败: {str(e)}',
            'note': f'处理失败: {str(e)}'
        })


def process_multi_turn_generation_task(task: Task):
    """处理多轮对话生成任务"""
    try:
        model_info = json.loads(task.model_info) if isinstance(task.model_info, str) else task.model_info
        questions = Question.objects.filter(project_id=task.project_id, answered=True)
        total = questions.count()
        success_count = 0
        error_count = 0
        task_message = {
            'stepInfo': '开始多轮对话生成',
            'errorList': [],
            'logs': [],
            'processedItems': 0,
            'totalItems': total,
            'successCount': 0,
            'errorCount': 0,
            'finishedList': []
        }
        update_task(task.id, {
            'total_count': total,
            'detail': json.dumps(task_message, ensure_ascii=False)
        })

        from conversations.services import generate_multi_turn_conversation

        config = {
            'model': model_info,
            'language': '中文' if task.language.startswith('zh') else 'en',
            'rounds': 3
        }

        for idx, q in enumerate(questions, start=1):
            try:
                generate_multi_turn_conversation(str(task.project_id), str(q.id), config)
                success_count += 1
                task_message['finishedList'].append({'questionId': str(q.id), 'status': 'success'})
                task_message['logs'].append({
                    'time': timezone.now().strftime('%H:%M:%S'),
                    'level': 'success',
                    'message': f'对话生成完成: 问题ID {q.id}'
                })
            except Exception as e:
                error_count += 1
                task_message['finishedList'].append({'questionId': str(q.id), 'status': 'error', 'error': str(e)})
                task_message['errorList'].append(f'对话生成失败: 问题ID {q.id}, 错误: {str(e)}')
                task_message['logs'].append({
                    'time': timezone.now().strftime('%H:%M:%S'),
                    'level': 'error',
                    'message': f'对话生成失败: 问题ID {q.id}, 错误: {str(e)}'
                })
            task_message['successCount'] = success_count
            task_message['errorCount'] = error_count
            task_message['processedItems'] = idx
            update_task(task.id, {
                'completed_count': success_count + error_count,
                'total_count': total,
                'detail': json.dumps(task_message, ensure_ascii=False)
            })

        final_status = 1 if error_count == 0 else 2 if success_count == 0 else 1
        update_task(task.id, {
            'status': final_status,
            'note': '' if final_status == 1 else '部分失败',
            'detail': json.dumps(task_message, ensure_ascii=False),
            'end_time': timezone.now()
        })
    except Exception as e:
        update_task(task.id, {
            'status': 2,
            'detail': f'处理失败: {str(e)}',
            'note': f'处理失败: {str(e)}'
        })


def process_data_distillation_task(task: Task):
    """处理数据蒸馏任务（占位符）"""
    update_task(task.id, {
        'status': 1,
        'note': '数据蒸馏任务待实现',
        'detail': json.dumps({'stepInfo': '数据蒸馏任务待实现', 'finishedList': [], 'logs': []}, ensure_ascii=False),
        'end_time': timezone.now()
    })


def process_image_question_generation_task(task: Task):
    """处理图像问题生成任务"""
    try:
        model_info = json.loads(task.model_info) if isinstance(task.model_info, str) else task.model_info
        language = 'zh' if task.language.startswith('zh') else 'en'
        from images.models import Image
        from images.services import generate_questions_for_image

        images = Image.objects.filter(project_id=task.project_id)
        total = images.count()
        success_count = 0
        error_count = 0
        task_message = {
            'stepInfo': '开始图像问题生成',
            'errorList': [],
            'logs': [],
            'processedImages': 0,
            'totalImages': total,
            'successCount': 0,
            'errorCount': 0,
            'finishedList': []
        }
        update_task(task.id, {
            'total_count': total,
            'detail': json.dumps(task_message, ensure_ascii=False)
        })

        for idx, img in enumerate(images, start=1):
            try:
                generate_questions_for_image(str(task.project_id), str(img.id), {
                    'model': model_info,
                    'language': language,
                    'count': 3
                })
                success_count += 1
                task_message['finishedList'].append({'imageId': str(img.id), 'status': 'success'})
                task_message['logs'].append({
                    'time': timezone.now().strftime('%H:%M:%S'),
                    'level': 'success',
                    'message': f'图像问题生成完成: {img.id}'
                })
            except Exception as e:
                error_count += 1
                task_message['finishedList'].append({'imageId': str(img.id), 'status': 'error', 'error': str(e)})
                task_message['errorList'].append(f'图像问题生成失败: {img.id}, 错误: {str(e)}')
                task_message['logs'].append({
                    'time': timezone.now().strftime('%H:%M:%S'),
                    'level': 'error',
                    'message': f'图像问题生成失败: {img.id}, 错误: {str(e)}'
                })
            task_message['successCount'] = success_count
            task_message['errorCount'] = error_count
            task_message['processedImages'] = idx
            update_task(task.id, {
                'completed_count': success_count + error_count,
                'total_count': total,
                'detail': json.dumps(task_message, ensure_ascii=False)
            })

        final_status = 1 if error_count == 0 else 2 if success_count == 0 else 1
        update_task(task.id, {
            'status': final_status,
            'note': '' if final_status == 1 else '部分失败',
            'detail': json.dumps(task_message, ensure_ascii=False),
            'end_time': timezone.now()
        })
    except Exception as e:
        update_task(task.id, {
            'status': 2,
            'detail': f'处理失败: {str(e)}',
            'note': f'处理失败: {str(e)}'
        })


def process_image_dataset_generation_task(task: Task):
    """处理图像数据集生成任务"""
    try:
        model_info = json.loads(task.model_info) if isinstance(task.model_info, str) else task.model_info
        language = 'zh' if task.language.startswith('zh') else 'en'
        from images.models import Image
        from images.services import generate_dataset_for_image

        images = Image.objects.filter(project_id=task.project_id)
        total = images.count()
        success_count = 0
        error_count = 0
        task_message = {
            'stepInfo': '开始图像数据集生成',
            'errorList': [],
            'logs': [],
            'processedImages': 0,
            'totalImages': total,
            'successCount': 0,
            'errorCount': 0,
            'finishedList': []
        }
        update_task(task.id, {
            'total_count': total,
            'detail': json.dumps(task_message, ensure_ascii=False)
        })

        for idx, img in enumerate(images, start=1):
            try:
                # 简单用图像名称作为问题
                question = f"描述这张图片: {img.image_name}"
                generate_dataset_for_image(str(task.project_id), str(img.id), question, {
                    'model': model_info,
                    'language': language,
                    'previewOnly': False
                })
                success_count += 1
                task_message['finishedList'].append({'imageId': str(img.id), 'status': 'success'})
                task_message['logs'].append({
                    'time': timezone.now().strftime('%H:%M:%S'),
                    'level': 'success',
                    'message': f'图像数据集生成完成: {img.id}'
                })
            except Exception as e:
                error_count += 1
                task_message['finishedList'].append({'imageId': str(img.id), 'status': 'error', 'error': str(e)})
                task_message['errorList'].append(f'图像数据集生成失败: {img.id}, 错误: {str(e)}')
                task_message['logs'].append({
                    'time': timezone.now().strftime('%H:%M:%S'),
                    'level': 'error',
                    'message': f'图像数据集生成失败: {img.id}, 错误: {str(e)}'
                })
            task_message['successCount'] = success_count
            task_message['errorCount'] = error_count
            task_message['processedImages'] = idx
            update_task(task.id, {
                'completed_count': success_count + error_count,
                'total_count': total,
                'detail': json.dumps(task_message, ensure_ascii=False)
            })

        final_status = 1 if error_count == 0 else 2 if success_count == 0 else 1
        update_task(task.id, {
            'status': final_status,
            'note': '' if final_status == 1 else '部分失败',
            'detail': json.dumps(task_message, ensure_ascii=False),
            'end_time': timezone.now()
        })
    except Exception as e:
        update_task(task.id, {
            'status': 2,
            'detail': f'处理失败: {str(e)}',
            'note': f'处理失败: {str(e)}'
        })

