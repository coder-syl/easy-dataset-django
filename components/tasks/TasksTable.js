'use client';

import React, { useState } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Typography,
  CircularProgress,
  Box,
  TablePagination,
  IconButton,
  Collapse,
  Chip
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import { useTranslation } from 'react-i18next';
import { formatDistanceToNow } from 'date-fns';
import { zhCN, enUS } from 'date-fns/locale';

// 导入子组件
import TaskStatusChip from './TaskStatusChip';
import TaskProgress from './TaskProgress';
import TaskActions from './TaskActions';

export default function TasksTable({
  tasks,
  loading,
  handleAbortTask,
  handleDeleteTask,
  page,
  rowsPerPage,
  handleChangePage,
  handleChangeRowsPerPage,
  totalCount
}) {
  const { t, i18n } = useTranslation();
  const [expandedTasks, setExpandedTasks] = useState(new Set());

  // 格式化日期
  const formatDate = dateString => {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return formatDistanceToNow(date, {
      addSuffix: true,
      locale: i18n.language === 'zh-CN' ? zhCN : enUS
    });
  };

  // 计算任务运行时间
  const calculateDuration = (startTimeStr, endTimeStr) => {
    if (!startTimeStr || !endTimeStr) return '-';

    try {
      const startTime = new Date(startTimeStr);
      const endTime = new Date(endTimeStr);

      // 计算时间差（毫秒）
      const duration = endTime - startTime;

      // 将毫秒转换为人类可读格式
      const seconds = Math.floor(duration / 1000);

      if (seconds < 60) {
        return t('tasks.duration.seconds', { seconds });
      } else if (seconds < 3600) {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        return t('tasks.duration.minutes', { minutes, seconds: remainingSeconds });
      } else {
        const hours = Math.floor(seconds / 3600);
        const remainingMinutes = Math.floor((seconds % 3600) / 60);
        return t('tasks.duration.hours', { hours, minutes: remainingMinutes });
      }
    } catch (error) {
      console.error('计算运行时间出错:', error);
      return '-';
    }
  };

  // 解析模型信息
  const parseModelInfo = modelInfo => {
    // 如果已经是对象，直接使用
    if (modelInfo && typeof modelInfo === 'object') {
      return modelInfo.modelName || modelInfo.model_name || modelInfo.name || '-';
    }
    
    // 如果是字符串，尝试解析
    if (typeof modelInfo === 'string') {
      try {
        const parsedModel = JSON.parse(modelInfo);
        if (parsedModel && typeof parsedModel === 'object') {
          return parsedModel.modelName || parsedModel.model_name || parsedModel.name || '-';
        }
        return modelInfo;
      } catch (error) {
        // 如果不是有效的JSON，直接返回字符串
        return modelInfo || '-';
      }
    }
    
    // 其他情况返回默认值
    return '-';
  };

  // 任务类型本地化
  const getLocalizedTaskType = taskType => {
    return t(`tasks.types.${taskType}`, { defaultValue: taskType });
  };

  // 切换任务详情展开/折叠
  const toggleTaskDetail = taskId => {
    setExpandedTasks(prev => {
      const newSet = new Set(prev);
      if (newSet.has(taskId)) {
        newSet.delete(taskId);
      } else {
        newSet.add(taskId);
      }
      return newSet;
    });
  };

  // 解析任务详情
  const parseTaskDetail = detail => {
    if (!detail) return null;
    
    try {
      // 尝试解析为 JSON
      if (typeof detail === 'string') {
        const parsed = JSON.parse(detail);
        return parsed;
      }
      // 如果已经是对象，直接返回
      if (typeof detail === 'object') {
        return detail;
      }
    } catch (e) {
      // 如果不是 JSON，返回原始字符串
      return { message: detail };
    }
    
    return null;
  };

  // 渲染任务详情
  const renderTaskDetail = task => {
    const detail = parseTaskDetail(task.detail);
    if (!detail) return null;

    return (
      <Box sx={{ p: 2, bgcolor: 'background.default', borderTop: '1px solid', borderColor: 'divider' }}>
        <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 'bold' }}>
          {t('tasks.detail', { defaultValue: '任务详情' })}
        </Typography>
        
        {/* 如果是对象，显示结构化信息 */}
        {typeof detail === 'object' && detail !== null && (
          <Box sx={{ mt: 1 }}>
            {detail.stepInfo && (
              <Box sx={{ mb: 1 }}>
                <Typography variant="body2" color="text.secondary" component="span">
                  {t('tasks.detail.stepInfo', { defaultValue: '当前步骤' })}: 
                </Typography>
                <Typography variant="body2" component="span" sx={{ ml: 1, fontWeight: 'medium' }}>
                  {detail.stepInfo}
                </Typography>
              </Box>
            )}
            
            {detail.current && (
              <Box sx={{ mb: 1 }}>
                <Typography variant="body2" color="text.secondary" component="span">
                  {t('tasks.detail.current', { defaultValue: '当前处理' })}: 
                </Typography>
                <Typography variant="body2" component="span" sx={{ ml: 1 }}>
                  {detail.current.fileName && `${detail.current.fileName} `}
                  {detail.current.processedPage && detail.current.totalPage && 
                    `(${detail.current.processedPage}/${detail.current.totalPage} ${t('tasks.detail.pages', { defaultValue: '页' })})`}
                  {detail.current.chunksGenerated !== undefined && 
                    ` - ${t('tasks.detail.chunksGenerated', { defaultValue: '生成文本块' })}: ${detail.current.chunksGenerated}`}
                </Typography>
                {detail.current.status && (
                  <Chip 
                    label={detail.current.status === 'processing' ? t('tasks.detail.processing', { defaultValue: '处理中' }) : 
                           detail.current.status === 'completed' ? t('tasks.detail.completed', { defaultValue: '已完成' }) : 
                           detail.current.status}
                    size="small" 
                    color={detail.current.status === 'completed' ? 'success' : 'warning'}
                    sx={{ ml: 1, mt: 0.5 }}
                  />
                )}
              </Box>
            )}
            
            {/* LLM调用详情 */}
            {detail.llmCall && (
              <Box sx={{ mb: 2, p: 2, bgcolor: 'action.hover', borderRadius: 1, border: '1px solid', borderColor: 'divider' }}>
                <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 'bold', color: 'primary.main' }}>
                  {t('tasks.detail.llmCall', { defaultValue: '大模型调用详情' })}
                </Typography>
                <Box sx={{ mt: 1 }}>
                  <Typography variant="body2" sx={{ mb: 0.5 }}>
                    <strong>{t('tasks.detail.provider', { defaultValue: '提供商' })}:</strong> {detail.llmCall.provider || '-'}
                  </Typography>
                  <Typography variant="body2" sx={{ mb: 0.5 }}>
                    <strong>{t('tasks.detail.model', { defaultValue: '模型' })}:</strong> {detail.llmCall.model || '-'}
                  </Typography>
                  <Typography variant="body2" sx={{ mb: 0.5 }}>
                    <strong>{t('tasks.detail.action', { defaultValue: '操作' })}:</strong> {detail.llmCall.action || '-'}
                  </Typography>
                  {detail.llmCall.tocLength !== undefined && (
                    <Typography variant="body2" sx={{ mb: 0.5 }}>
                      <strong>{t('tasks.detail.tocLength', { defaultValue: '目录长度' })}:</strong> {detail.llmCall.tocLength} 字符
                    </Typography>
                  )}
                  {detail.llmCall.status && (
                    <Typography variant="body2" sx={{ mb: 0.5 }}>
                      <strong>{t('tasks.detail.status', { defaultValue: '状态' })}:</strong> 
                      <Chip 
                        label={detail.llmCall.status === 'calling' ? t('tasks.detail.calling', { defaultValue: '调用中' }) :
                               detail.llmCall.status === 'completed' ? t('tasks.detail.completed', { defaultValue: '已完成' }) :
                               detail.llmCall.status}
                        size="small" 
                        color={detail.llmCall.status === 'completed' ? 'success' : 'warning'}
                        sx={{ ml: 1 }}
                      />
                    </Typography>
                  )}
                  {detail.llmCall.tagsGenerated !== undefined && (
                    <Typography variant="body2" sx={{ mb: 0.5 }}>
                      <strong>{t('tasks.detail.tagsGenerated', { defaultValue: '生成标签数' })}:</strong> {detail.llmCall.tagsGenerated}
                    </Typography>
                  )}
                  {detail.llmCall.startTime && (
                    <Typography variant="body2" sx={{ mb: 0.5, color: 'text.secondary' }}>
                      <strong>{t('tasks.detail.startTime', { defaultValue: '开始时间' })}:</strong> {new Date(detail.llmCall.startTime).toLocaleString()}
                    </Typography>
                  )}
                  {detail.llmCall.endTime && (
                    <Typography variant="body2" sx={{ mb: 0.5, color: 'text.secondary' }}>
                      <strong>{t('tasks.detail.endTime', { defaultValue: '结束时间' })}:</strong> {new Date(detail.llmCall.endTime).toLocaleString()}
                    </Typography>
                  )}
                  {detail.llmCall.endpoint && (
                    <Typography variant="body2" sx={{ mb: 0.5, color: 'text.secondary', fontSize: '0.75rem', wordBreak: 'break-all' }}>
                      <strong>{t('tasks.detail.endpoint', { defaultValue: 'API端点' })}:</strong> {detail.llmCall.endpoint}
                    </Typography>
                  )}
                </Box>
              </Box>
            )}
            
            {detail.processedFiles !== undefined && detail.totalFiles !== undefined && (
              <Box sx={{ mb: 1 }}>
                <Typography variant="body2" color="text.secondary" component="span">
                  {t('tasks.detail.files', { defaultValue: '文件进度' })}: 
                </Typography>
                <Typography variant="body2" component="span" sx={{ ml: 1 }}>
                  {detail.processedFiles} / {detail.totalFiles}
                </Typography>
              </Box>
            )}
            
            {detail.finishedList && Array.isArray(detail.finishedList) && detail.finishedList.length > 0 && (
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  {t('tasks.detail.finishedFiles', { defaultValue: '已完成/已处理' })}:
                </Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.75 }}>
                  {detail.finishedList.map((item, idx) => (
                    <Box key={idx} sx={{ p: 1, border: '1px solid', borderColor: 'divider', borderRadius: 1, bgcolor: 'background.paper' }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
                        <Chip 
                          label={item.status || 'success'} 
                          size="small" 
                          color={item.status === 'error' ? 'error' : 'success'} 
                        />
                        <Typography variant="body2" sx={{ fontWeight: 600 }}>
                          {item.fileName || item.chunkName || item.chunkId || t('tasks.detail.item', { defaultValue: '条目' })}
                        </Typography>
                        {item.error && (
                          <Typography variant="body2" color="error">
                            {item.error}
                          </Typography>
                        )}
                      </Box>
                      {item.llm && (
                        <Box sx={{ mt: 1, p: 1, bgcolor: 'action.hover', borderRadius: 1 }}>
                          <Typography variant="body2" sx={{ mb: 0.5, fontWeight: 600 }}>
                            {t('tasks.detail.llmCall', { defaultValue: '大模型调用详情' })}
                          </Typography>
                          <Typography variant="body2" sx={{ mb: 0.25 }}>
                            <strong>{t('tasks.detail.provider', { defaultValue: '提供商' })}:</strong> {item.llm.provider || '-'}
                          </Typography>
                          <Typography variant="body2" sx={{ mb: 0.25 }}>
                            <strong>{t('tasks.detail.model', { defaultValue: '模型' })}:</strong> {item.llm.model || '-'}
                          </Typography>
                          {item.llm.promptPreview && (
                            <Typography variant="body2" sx={{ mb: 0.25, whiteSpace: 'pre-wrap' }}>
                              <strong>{t('tasks.detail.prompt', { defaultValue: '提示词' })}:</strong> {item.llm.promptPreview}
                            </Typography>
                          )}
                          {item.llm.answerPreview && (
                            <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                              <strong>{t('tasks.detail.answer', { defaultValue: '回答' })}:</strong> {item.llm.answerPreview}
                            </Typography>
                          )}
                        </Box>
                      )}
                    </Box>
                  ))}
                </Box>
              </Box>
            )}
            
            {detail.errorList && Array.isArray(detail.errorList) && detail.errorList.length > 0 && (
              <Box sx={{ mb: 1 }}>
                <Typography variant="body2" color="error" gutterBottom>
                  {t('tasks.detail.errors', { defaultValue: '错误信息' })}:
                </Typography>
                <Box component="ul" sx={{ m: 0, pl: 2 }}>
                  {detail.errorList.map((error, idx) => (
                    <Typography key={idx} component="li" variant="body2" color="error">
                      {error}
                    </Typography>
                  ))}
                </Box>
              </Box>
            )}
            
            {/* 处理日志 */}
            {detail.logs && Array.isArray(detail.logs) && detail.logs.length > 0 && (
              <Box sx={{ mb: 2, p: 2, bgcolor: 'background.paper', borderRadius: 1, border: '1px solid', borderColor: 'divider', maxHeight: '300px', overflow: 'auto' }}>
                <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 'bold' }}>
                  {t('tasks.detail.logs', { defaultValue: '处理日志' })}
                </Typography>
                <Box component="ul" sx={{ m: 0, pl: 2, listStyle: 'none' }}>
                  {detail.logs.map((log, idx) => (
                    <Box key={idx} component="li" sx={{ mb: 0.5, display: 'flex', alignItems: 'flex-start', gap: 1 }}>
                      <Typography 
                        variant="caption" 
                        sx={{ 
                          color: log.level === 'error' ? 'error.main' : 
                                 log.level === 'success' ? 'success.main' : 
                                 'text.secondary',
                          minWidth: '60px',
                          fontSize: '0.7rem'
                        }}
                      >
                        {log.time ? new Date(log.time).toLocaleTimeString() : ''}
                      </Typography>
                      <Chip 
                        label={log.level || 'info'} 
                        size="small" 
                        color={log.level === 'error' ? 'error' : 
                               log.level === 'success' ? 'success' : 
                               log.level === 'warning' ? 'warning' : 'default'}
                        sx={{ height: '18px', fontSize: '0.65rem' }}
                      />
                      <Typography variant="body2" sx={{ flex: 1, fontSize: '0.8rem' }}>
                        {log.message}
                      </Typography>
                    </Box>
                  ))}
                </Box>
              </Box>
            )}
            
            {/* 如果有其他字段，显示原始 JSON */}
            {!detail.stepInfo && !detail.current && !detail.processedFiles && detail.message && (
              <Typography variant="body2">
                {detail.message}
              </Typography>
            )}
          </Box>
        )}
        
        {/* 如果是字符串，直接显示 */}
        {typeof detail === 'string' && (
          <Typography variant="body2" sx={{ mt: 1, whiteSpace: 'pre-wrap' }}>
            {detail}
          </Typography>
        )}
      </Box>
    );
  };

  return (
    <React.Fragment>
      <TableContainer component={Paper} elevation={1} sx={{ borderRadius: 2, mb: 2 }}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>{t('tasks.table.type')}</TableCell>
              <TableCell>{t('tasks.table.status')}</TableCell>
              <TableCell>{t('tasks.table.progress')}</TableCell>
              <TableCell>{t('tasks.table.success')}</TableCell>
              <TableCell>{t('tasks.table.failed')}</TableCell>
              <TableCell>{t('tasks.table.createTime')}</TableCell>
              <TableCell>{t('tasks.table.duration')}</TableCell>
              <TableCell>{t('tasks.table.model')}</TableCell>
              <TableCell align="right">{t('tasks.table.actions')}</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {loading && (!Array.isArray(tasks) || tasks.length === 0) ? (
              <TableRow>
                <TableCell colSpan={10} align="center" sx={{ py: 6 }}>
                  <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                    <CircularProgress size={40} />
                    <Typography variant="body2" sx={{ mt: 2 }}>
                      {t('tasks.loading')}
                    </Typography>
                  </Box>
                </TableCell>
              </TableRow>
            ) : !Array.isArray(tasks) || tasks.length === 0 ? (
              <TableRow>
                <TableCell colSpan={10} align="center" sx={{ py: 6 }}>
                  <Typography variant="body1">{t('tasks.empty')}</Typography>
                </TableCell>
              </TableRow>
            ) : (
              tasks.map(task => {
                const isExpanded = expandedTasks.has(task.id);
                return (
                  <React.Fragment key={task.id}>
                    <TableRow>
                      <TableCell>
                        <IconButton
                          size="small"
                          onClick={() => toggleTaskDetail(task.id)}
                          sx={{ mr: 1 }}
                        >
                          {isExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                        </IconButton>
                        {getLocalizedTaskType(task.taskType)}
                      </TableCell>
                      <TableCell>
                        <TaskStatusChip status={task.status} />
                      </TableCell>
                      <TableCell>
                        <TaskProgress task={task} />
                      </TableCell>
                      <TableCell>{task.completedCount ? task.completedCount - (task.errorCount || 0) : 0}</TableCell>
                      <TableCell>{task.errorCount || 0}</TableCell>
                      <TableCell>{formatDate(task.createAt)}</TableCell>
                      <TableCell>{task.endTime ? calculateDuration(task.startTime, task.endTime) : '-'}</TableCell>
                      <TableCell>{parseModelInfo(task.modelInfo)}</TableCell>
                      <TableCell align="right">
                        <TaskActions task={task} onAbort={handleAbortTask} onDelete={handleDeleteTask} />
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell colSpan={10} sx={{ py: 0, border: 0 }}>
                        <Collapse in={isExpanded} timeout="auto" unmountOnExit>
                          {renderTaskDetail(task)}
                        </Collapse>
                      </TableCell>
                    </TableRow>
                  </React.Fragment>
                );
              })
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {Array.isArray(tasks) && tasks.length > 0 && (
        <TablePagination
          component="div"
          count={totalCount}
          page={page}
          onPageChange={handleChangePage}
          rowsPerPage={rowsPerPage}
          onRowsPerPageChange={handleChangeRowsPerPage}
          rowsPerPageOptions={[5, 10, 25]}
          labelRowsPerPage={t('datasets.rowsPerPage')}
          labelDisplayedRows={({ from, to, count }) => {
            // 根据实际分页操作计算正确的from和to
            const calculatedFrom = page * rowsPerPage + 1;
            const calculatedTo = Math.min((page + 1) * rowsPerPage, count);
            return t('datasets.pagination', {
              from: calculatedFrom,
              to: calculatedTo,
              count
            });
          }}
        />
      )}
    </React.Fragment>
  );
}
