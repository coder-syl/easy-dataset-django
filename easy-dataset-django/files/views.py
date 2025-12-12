"""
文件管理视图
"""
import logging
from rest_framework import status
from rest_framework.decorators import api_view
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator
import hashlib
from pathlib import Path

from projects.models import Project
from .models import UploadFile
from .serializers import UploadFileSerializer
from common.response.result import success, error

logger = logging.getLogger('files')


def get_file_md5(file_path):
    """计算文件MD5"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


@swagger_auto_schema(
    method='get',
    operation_summary='获取文件列表',
    responses={200: openapi.Response('文件列表')}
)
@swagger_auto_schema(
    method='post',
    operation_summary='上传文件',
    responses={200: openapi.Response('上传成功')}
)
@swagger_auto_schema(
    method='delete',
    operation_summary='删除文件',
    responses={200: openapi.Response('删除成功')}
)
@api_view(['GET', 'POST', 'DELETE'])
def file_list_upload_delete(request, project_id):
    """文件列表、上传、删除"""
    try:
        project = get_object_or_404(Project, id=project_id)
        logger.info(f'[{project_id}] 文件操作请求: {request.method}')
    except Exception as e:
        logger.error(f'[{project_id}] 项目不存在: {str(e)}', exc_info=True)
        return error(message='项目不存在', response_status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        try:
            # 获取查询参数
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('pageSize', 10))
            file_name = request.GET.get('fileName', '')
            get_all_ids = request.GET.get('getAllIds') == 'true'
            
            logger.debug(f'[{project_id}] 获取文件列表: page={page}, pageSize={page_size}, fileName={file_name}, getAllIds={get_all_ids}')
            
            # 构建查询
            queryset = UploadFile.objects.filter(project=project)
            if file_name:
                queryset = queryset.filter(file_name__icontains=file_name)
            
            # 如果只需要ID列表
            if get_all_ids:
                all_files = queryset.values_list('id', flat=True)
                logger.info(f'[{project_id}] 获取所有文件ID列表, 共 {len(all_files)} 个文件')
                return success(data={'allFileIds': [str(id) for id in all_files]})
            
            # 分页
            paginator = Paginator(queryset, page_size)
            page_obj = paginator.get_page(page)
            
            serializer = UploadFileSerializer(page_obj.object_list, many=True)
            logger.info(f'[{project_id}] 获取文件列表成功: 总数={paginator.count}, 当前页={page}, 返回 {len(serializer.data)} 个文件')
            return success(data={
                'data': serializer.data,
                'total': paginator.count,
                'page': page,
                'pageSize': page_size
            })
        except Exception as e:
            logger.error(f'[{project_id}] 获取文件列表失败: {str(e)}', exc_info=True)
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'POST':
        try:
            # 从请求头获取文件名
            file_name = request.headers.get('x-file-name') or request.headers.get('X-File-Name')
            if file_name:
                import urllib.parse
                file_name = urllib.parse.unquote(file_name)
            
            logger.info(f'[{project_id}] 开始上传文件: {file_name}')
            
            if not file_name:
                logger.warning(f'[{project_id}] 请求头中不包含文件名')
                return error(message='请求头中不包含文件名 (x-file-name)', response_status=status.HTTP_400_BAD_REQUEST)
            
            # 检查文件类型
            supported_extensions = ['.md', '.markdown', '.txt', '.pdf', '.docx', '.epub']
            file_ext = Path(file_name).suffix.lower()
            if file_ext not in supported_extensions:
                logger.warning(f'[{project_id}] 不支持的文件格式: {file_ext}, 文件名: {file_name}')
                return error(
                    message=f'不支持的文件格式。支持的格式: {", ".join(supported_extensions)}',
                    response_status=status.HTTP_400_BAD_REQUEST
                )
            
            # 获取文件数据
            file_data = request.body
            file_size = len(file_data) if file_data else 0
            logger.debug(f'[{project_id}] 文件大小: {file_size} 字节')
            
            if not file_data:
                logger.warning(f'[{project_id}] 文件数据为空')
                return error(message='文件数据为空', response_status=status.HTTP_400_BAD_REQUEST)
            
            # 创建项目文件目录
            project_root = Path('local-db') / project_id / 'files'
            project_root.mkdir(parents=True, exist_ok=True)
            logger.debug(f'[{project_id}] 项目文件目录: {project_root}')
            
            # 保存原始文件
            original_file_path = project_root / file_name
            with open(original_file_path, 'wb') as f:
                f.write(file_data)
            logger.info(f'[{project_id}] 原始文件已保存: {original_file_path}')
            
            # 处理文件（提取内容并转换为Markdown）
            try:
                from common.services.file_processor import get_file_content, save_processed_file
                
                logger.info(f'[{project_id}] 开始处理文件: {file_name}, 类型: {file_ext}')
                # 提取内容并转换为Markdown
                content, md_file_name = get_file_content(str(original_file_path), file_name)
                logger.info(f'[{project_id}] 文件内容提取完成, 内容长度: {len(content)} 字符, Markdown文件名: {md_file_name}')
                
                # 保存Markdown文件
                md_file_path = save_processed_file(str(original_file_path), content, md_file_name)
                logger.info(f'[{project_id}] Markdown文件已保存: {md_file_path}')
                
                # 计算文件信息（使用原始文件）
                md5 = get_file_md5(original_file_path)
                logger.debug(f'[{project_id}] 文件MD5: {md5}')
                
                # 创建文件记录（保存原始文件名，但实际使用Markdown文件）
                file_info = UploadFile.objects.create(
                    project=project,
                    file_name=file_name,  # 保存原始文件名
                    file_ext=file_ext,
                    path=str(project_root),
                    size=file_size,
                    md5=md5
                )
                logger.info(f'[{project_id}] 文件记录已创建: fileId={file_info.id}, fileName={file_name}, size={file_size}, processed=True')
                
                return success(data={
                    'message': '文件上传并处理成功',
                    'fileName': file_name,
                    'mdFileName': md_file_name,
                    'filePath': str(original_file_path),
                    'mdFilePath': md_file_path,
                    'fileId': file_info.id,
                    'processed': True
                })
            except Exception as e:
                # 如果处理失败，仍然保存原始文件
                logger.error(f'[{project_id}] 文件处理失败: {str(e)}', exc_info=True)
                md5 = get_file_md5(original_file_path)
                
                file_info = UploadFile.objects.create(
                    project=project,
                    file_name=file_name,
                    file_ext=file_ext,
                    path=str(project_root),
                    size=file_size,
                    md5=md5
                )
                logger.warning(f'[{project_id}] 文件记录已创建但处理失败: fileId={file_info.id}, fileName={file_name}, error={str(e)}')
                
                return success(data={
                    'message': f'文件上传成功，但处理失败: {str(e)}',
                    'fileName': file_name,
                    'filePath': str(original_file_path),
                    'fileId': file_info.id,
                    'processed': False,
                    'error': str(e)
                })
        except Exception as e:
            logger.error(f'[{project_id}] 文件上传失败: {str(e)}', exc_info=True)
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'DELETE':
        try:
            file_id = request.GET.get('fileId')
            domain_tree_action = request.GET.get('domainTreeAction', 'keep')  # 默认 'keep'
            
            logger.info(f'[{project_id}] 开始删除文件: fileId={file_id}, domainTreeAction={domain_tree_action}')
            
            if not file_id:
                logger.warning(f'[{project_id}] 文件ID不能为空')
                return error(message='文件ID不能为空', response_status=status.HTTP_400_BAD_REQUEST)
            
            file_info = get_object_or_404(UploadFile, id=file_id, project=project)
            file_name = file_info.file_name
            file_path_str = file_info.path
            file_ext = file_info.file_ext
            
            # 0. 在删除前获取被删除文件的 TOC（用于领域树修订，与 Node.js 的 getProjectTocByName 保持一致）
            delete_toc = None
            try:
                project_root = Path('local-db') / project_id
                toc_dir = project_root / 'toc'
                base_name = Path(file_name).stem
                toc_path = toc_dir / f"{base_name}-toc.json"
                
                if toc_path.exists():
                    import json
                    with open(toc_path, 'r', encoding='utf-8') as f:
                        toc_data = json.load(f)
                        # 转换为 Markdown 格式（与 Node.js 的 getProjectTocByName 保持一致）
                        # Node.js 返回格式: "### File：文件名\n" + markdownTOC + "\n"
                        md_file_name = file_name if file_name.endswith('.md') else file_name.replace(Path(file_name).suffix, '.md')
                        delete_toc = f'### File：{md_file_name}\n'
                        
                        if isinstance(toc_data, dict) and 'toc' in toc_data:
                            toc_content = toc_data['toc']
                            if isinstance(toc_content, str):
                                delete_toc += toc_content + '\n'
                            else:
                                # 如果是列表格式，转换为 Markdown
                                from common.services.domain_tree import _toc_to_markdown
                                delete_toc += _toc_to_markdown(toc_content, is_nested=True) + '\n'
                        else:
                            # 兼容旧格式
                            from common.services.domain_tree import _toc_to_markdown
                            delete_toc += _toc_to_markdown(toc_data, is_nested=True) + '\n'
                    logger.debug(f'[{project_id}] 已获取被删除文件的 TOC: {len(delete_toc) if delete_toc else 0} 字符')
            except Exception as e:
                logger.warning(f'[{project_id}] 获取被删除文件的 TOC 失败: {str(e)}')
                # 即使获取 TOC 失败，不影响删除流程
            
            # 1. 获取与文件关联的所有文本块
            from chunks.models import Chunk
            chunks = Chunk.objects.filter(project=project, file_id=file_id)
            chunk_ids = list(chunks.values_list('id', flat=True))
            
            # 记录统计数据
            stats = {
                'chunks': len(chunk_ids),
                'questions': 0,
                'datasets': 0
            }
            
            # 2. 找出所有关联的问题和数据集
            question_ids = []
            dataset_ids = []
            
            if chunk_ids:
                from questions.models import Question
                from datasets.models import Dataset
                
                # 统计问题数量
                questions = Question.objects.filter(chunk_id__in=chunk_ids)
                stats['questions'] = questions.count()
                question_ids = list(questions.values_list('id', flat=True))
                
                # 统计数据集数量（通过 question_id）
                if question_ids:
                    datasets = Dataset.objects.filter(question_id__in=question_ids)
                    stats['datasets'] = datasets.count()
                    dataset_ids = list(datasets.values_list('id', flat=True))
            
            logger.info(f'[{project_id}] 删除统计: chunks={stats["chunks"]}, questions={stats["questions"]}, datasets={stats["datasets"]}')
            
            # 3. 使用事务批量删除所有数据库数据（按照外键依赖关系从外到内删除）
            from django.db import transaction
            
            with transaction.atomic():
                # 先删除数据集
                if dataset_ids:
                    from datasets.models import Dataset
                    Dataset.objects.filter(id__in=dataset_ids).delete()
                    logger.info(f'[{project_id}] 已删除 {len(dataset_ids)} 个数据集')
                
                # 再删除问题（虽然设置了 CASCADE，但为了统计和明确性，显式删除）
                if question_ids:
                    from questions.models import Question
                    Question.objects.filter(id__in=question_ids).delete()
                    logger.info(f'[{project_id}] 已删除 {len(question_ids)} 个问题')
                
                # 然后删除文本块
                if chunk_ids:
                    Chunk.objects.filter(id__in=chunk_ids).delete()
                    logger.info(f'[{project_id}] 已删除 {len(chunk_ids)} 个文本块')
                
                # 最后删除文件记录
                file_info.delete()
                logger.info(f'[{project_id}] 文件记录已删除: fileId={file_id}, fileName={file_name}')
            
            # 4. 删除文件系统中的文件（在事务外执行，避免影响数据库操作）
            file_path = Path(file_path_str) / file_name
            if file_path.exists():
                file_path.unlink()
                logger.info(f'[{project_id}] 物理文件已删除: {file_path}')
            else:
                logger.warning(f'[{project_id}] 物理文件不存在: {file_path}')
            
            # 5. 删除 Markdown 文件（如果存在）
            if file_ext != '.md':
                md_file_name = file_name.replace(Path(file_name).suffix, '.md')
                md_file_path = Path(file_path_str) / md_file_name
                if md_file_path.exists():
                    md_file_path.unlink()
                    logger.info(f'[{project_id}] Markdown文件已删除: {md_file_path}')
            
            # 6. 删除 TOC 文件
            try:
                project_root = Path('local-db') / project_id
                toc_dir = project_root / 'toc'
                base_name = Path(file_name).stem
                toc_path = toc_dir / f"{base_name}-toc.json"
                
                if toc_path.exists():
                    toc_path.unlink()
                    logger.info(f'[{project_id}] TOC文件已删除: {toc_path}')
            except Exception as e:
                logger.warning(f'[{project_id}] 删除TOC文件失败: {str(e)}')
                # 即使 TOC 文件删除失败，不影响整体结果
            
            # 7. 处理领域树更新（与 Node.js 保持一致）
            # 如果选择了保持领域树不变，直接返回删除结果
            if domain_tree_action == 'keep':
                logger.info(f'[{project_id}] 保持领域树不变')
                return success(data={
                    'message': '文件删除成功',
                    'stats': stats,
                    'domainTreeAction': 'keep',
                    'cascadeDelete': True
                })
            
            # 处理领域树更新
            try:
                # 从请求体获取模型信息和语言（与 Node.js 保持一致）
                model = None
                language = '中文'
                try:
                    import json
                    request_body = json.loads(request.body) if request.body else {}
                    model = request_body.get('model')
                    language = request_body.get('language', '中文')
                except Exception as e:
                    logger.warning(f'[{project_id}] 解析请求体失败，使用默认值: {str(e)}')
                    # 如果无法解析请求体，使用默认值（与 Node.js 保持一致）
                    if not model:
                        model = {
                            'providerId': 'openai',
                            'modelName': 'gpt-3.5-turbo',
                            'apiKey': ''
                        }
                
                # 获取项目的所有剩余文本块和 TOC
                from chunks.services import get_project_chunks
                chunks_result = get_project_chunks(project_id, filter_type='')
                remaining_chunks = chunks_result.get('chunks', [])
                remaining_toc = chunks_result.get('fileResult', {}).get('toc', '')
                
                # 如果不存在文本块，说明项目已经没有文件了，清空领域树
                if not remaining_chunks or len(remaining_chunks) == 0:
                    logger.info(f'[{project_id}] 删除后项目无文本块，清空领域树')
                    from tags.models import Tag
                    Tag.objects.filter(project=project).delete()
                    return success(data={
                        'message': '文件删除成功，领域树已清空',
                        'stats': stats,
                        'domainTreeAction': domain_tree_action,
                        'cascadeDelete': True
                    })
                
                # 调用领域树处理模块（与 Node.js 保持一致）
                from common.services.domain_tree import handle_domain_tree
                handle_domain_tree(
                    project_id=project_id,
                    action=domain_tree_action,
                    all_toc=remaining_toc,
                    delete_toc=delete_toc,
                    model=model,
                    language=language
                )
                logger.info(f'[{project_id}] 领域树更新完成: action={domain_tree_action}')
            except Exception as e:
                logger.error(f'[{project_id}] 更新领域树失败: {str(e)}', exc_info=True)
                # 即使领域树更新失败，也不影响文件删除的结果（与 Node.js 保持一致）
            
            return success(data={
                'message': '文件删除成功',
                'stats': stats,
                'domainTreeAction': domain_tree_action,
                'cascadeDelete': True
            })
        except Exception as e:
            logger.error(f'[{project_id}] 文件删除失败: {str(e)}', exc_info=True)
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(
    method='post',
    operation_summary='批量生成GA对',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'fileIds': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
            'modelConfigId': openapi.Schema(type=openapi.TYPE_STRING),
            'language': openapi.Schema(type=openapi.TYPE_STRING),
            'appendMode': openapi.Schema(type=openapi.TYPE_BOOLEAN)
        }
    ),
    responses={200: openapi.Response('生成成功')}
)
@api_view(['POST'])
def batch_generate_ga(request, project_id):
    """批量生成GA对"""
    try:
        project = get_object_or_404(Project, id=project_id)
        
        file_ids = request.data.get('fileIds', [])
        model_config_id = request.data.get('modelConfigId')
        language = request.data.get('language', '中文')
        append_mode = request.data.get('appendMode', False)
        
        if not file_ids or not isinstance(file_ids, list) or len(file_ids) == 0:
            return error(message='File IDs array is required', response_status=status.HTTP_400_BAD_REQUEST)
        
        if not model_config_id:
            return error(message='Model configuration ID is required', response_status=status.HTTP_400_BAD_REQUEST)
        
        # 验证文件
        valid_files = []
        invalid_file_ids = []
        
        for file_id in file_ids:
            try:
                file_info = UploadFile.objects.filter(id=file_id, project=project).first()
                if file_info:
                    valid_files.append(file_info)
                else:
                    invalid_file_ids.append(file_id)
            except:
                invalid_file_ids.append(file_id)
        
        if len(valid_files) == 0:
            return error(message='No valid files found', response_status=status.HTTP_404_NOT_FOUND)
        
        # 集成批量生成GA对的逻辑
        from .services import batch_generate_ga_pairs
        from llm.models import ModelConfig
        
        try:
            # 获取模型配置
            model_config_obj = ModelConfig.objects.get(id=model_config_id, project=project)
            model_config = {
                'provider_id': model_config_obj.provider_id,
                'endpoint': model_config_obj.endpoint,
                'api_key': model_config_obj.api_key,
                'model_id': model_config_obj.model_id,
                'model_name': model_config_obj.model_name,
                'temperature': model_config_obj.temperature,
                'max_tokens': model_config_obj.max_tokens,
                'top_p': model_config_obj.top_p,
                'top_k': model_config_obj.top_k
            }
            
            # 批量生成GA对
            results = batch_generate_ga_pairs(
                project_id,
                valid_files,
                model_config,
                language,
                append_mode
            )
            
            # 统计结果
            success_count = len([r for r in results if r.get('success')])
            failure_count = len([r for r in results if not r.get('success')])
            
            return success(data={
                'success': True,
                'data': results,
                'summary': {
                    'total': len(results),
                    'success': success_count,
                    'failure': failure_count,
                    'processed': len(valid_files),
                    'skipped': len(invalid_file_ids)
                },
                'message': f'Generated GA pairs for {success_count} files, {failure_count} failed, {len(invalid_file_ids)} files not found'
            })
        except Exception as e:
            return error(message=f'批量生成GA对失败: {str(e)}', response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
