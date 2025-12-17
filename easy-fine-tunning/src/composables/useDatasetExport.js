import { useI18n } from 'vue-i18n';
import { ElMessage } from 'element-plus';
import { exportDatasets, fetchTagStatistics } from '@/api/dataset';
import http from '@/api/http';

/**
 * 数据集导出 Composable
 */
export function useDatasetExport(projectId) {
  const { t } = useI18n();

  /**
   * 处理和下载数据的通用函数
   */
  const processAndDownloadData = async (dataToExport, exportOptions) => {
    let formattedData;
    let mimeType = 'application/json';

    if (exportOptions.formatType === 'alpaca') {
      if (exportOptions.alpacaFieldType === 'instruction') {
        formattedData = dataToExport.map(({ question, answer, cot }) => ({
          instruction: question,
          input: '',
          output: cot && exportOptions.includeCOT
            ? `<think>${cot}</think>\n${answer}`
            : answer,
          system: exportOptions.systemPrompt || ''
        }));
      } else {
        formattedData = dataToExport.map(({ question, answer, cot }) => ({
          instruction: exportOptions.customInstruction || '',
          input: question,
          output: cot && exportOptions.includeCOT
            ? `<think>${cot}</think>\n${answer}`
            : answer,
          system: exportOptions.systemPrompt || ''
        }));
      }
    } else if (exportOptions.formatType === 'sharegpt') {
      formattedData = dataToExport.map(({ question, answer, cot }) => {
        const messages = [];
        if (exportOptions.systemPrompt) {
          messages.push({
            role: 'system',
            content: exportOptions.systemPrompt
          });
        }
        messages.push({
          role: 'user',
          content: question
        });
        messages.push({
          role: 'assistant',
          content:
            cot && exportOptions.includeCOT
              ? `<think>${cot}</think>\n${answer}`
              : answer
        });
        return { messages };
      });
    } else if (exportOptions.formatType === 'multilingualthinking') {
      formattedData = dataToExport.map(({ question, answer, cot }) => ({
        reasoning_language: exportOptions.reasoningLanguage || 'English',
        developer: exportOptions.systemPrompt || '',
        user: question,
        analysis: exportOptions.includeCOT && cot ? cot : null,
        final: answer,
        messages: [
          {
            content: exportOptions.systemPrompt || '',
            role: 'system',
            thinking: null
          },
          {
            content: question,
            role: 'user',
            thinking: null
          },
          {
            content: answer,
            role: 'assistant',
            thinking: exportOptions.includeCOT && cot ? cot : null
          }
        ]
      }));
    } else if (exportOptions.formatType === 'custom') {
      const { questionField, answerField, cotField, includeLabels, includeChunk, questionOnly } =
        exportOptions.customFields;
      formattedData = dataToExport.map(({ question, answer, cot, question_label, chunk_content }) => {
        const labels = question_label;
        const item = {
          [questionField]: question
        };

        if (!questionOnly) {
          item[answerField] = answer;
        }

        if (cot && exportOptions.includeCOT && cotField && !questionOnly) {
          item[cotField] = cot;
        }

        if (includeLabels && labels && labels.length > 0) {
          item.label = labels.split(' ')[1];
        }

        if (includeChunk && chunk_content) {
          item.chunk = chunk_content;
        }

        return item;
      });
    }

    let content;
    let fileExtension;

    if (exportOptions.fileFormat === 'jsonl') {
      content = formattedData.map((item) => JSON.stringify(item)).join('\n');
      fileExtension = 'jsonl';
    } else if (exportOptions.fileFormat === 'csv') {
      const headers = Object.keys(formattedData[0] || {});
      const csvRows = [
        headers.join(','),
        ...formattedData.map((item) =>
          headers
            .map((header) => {
              let field = item[header]?.toString() || '';
              if (exportOptions.formatType === 'sharegpt') field = JSON.stringify(item[header]);
              if (exportOptions.formatType === 'multilingualthinking') field = JSON.stringify(item[header]);
              if (field.includes(',') || field.includes('\n') || field.includes('"')) {
                field = `"${field.replace(/"/g, '""')}"`;
              }
              return field;
            })
            .join(',')
        )
      ];
      content = csvRows.join('\n');
      fileExtension = 'csv';
    } else {
      content = JSON.stringify(formattedData, null, 2);
      fileExtension = 'json';
    }

    const blob = new Blob([content], { type: mimeType || 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;

    const formatSuffixMap = {
      alpaca: 'alpaca',
      'multilingual-thinking': 'multilingual-thinking',
      sharegpt: 'sharegpt',
      custom: 'custom'
    };
    const formatSuffix = formatSuffixMap[exportOptions.formatType] || exportOptions.formatType || 'export';
    const balanceSuffix = exportOptions.balanceMode ? '-balanced' : '';
    const dateStr = new Date().toISOString().slice(0, 10);
    a.download = `datasets-${projectId}-${formatSuffix}${balanceSuffix}-${dateStr}.${fileExtension}`;

    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  /**
   * 分批导出数据集（用于大数据量）
   */
  const exportDatasetsStreaming = async (exportOptions, onProgress) => {
    try {
      const batchSize = exportOptions.batchSize || 1000;
      let offset = 0;
      let allData = [];
      let hasMore = true;
      let totalProcessed = 0;

      while (hasMore) {
        const requestBody = {
          batchMode: true,
          offset: offset,
          batchSize: batchSize
        };

        if (exportOptions.selectedIds && exportOptions.selectedIds.length > 0) {
          requestBody.selectedIds = exportOptions.selectedIds;
        } else if (exportOptions.confirmedOnly) {
          requestBody.status = 'confirmed';
        }

        if (exportOptions.balanceMode && exportOptions.balanceConfig) {
          requestBody.balanceMode = true;
          requestBody.balanceConfig = exportOptions.balanceConfig;
        }

        const response = await exportDatasets(projectId, requestBody);
        // Django 返回格式: {code: 0, data: {data: [], hasMore: boolean, offset: number}}
        const data = response?.data || response;
        const batchResult = data?.data || data;

        if (!batchResult || !batchResult.data || !Array.isArray(batchResult.data)) {
          console.error('批量导出响应格式错误:', batchResult);
          throw new Error('批量导出响应格式错误');
        }

        // 如果需要包含文本块内容，批量查询并填充
        if (exportOptions.customFields?.includeChunk && batchResult.data.length > 0) {
          const chunkNames = batchResult.data
            .map((item) => item.chunk_name || item.chunkName)
            .filter((name) => name);

          if (chunkNames.length > 0) {
            try {
              const chunkResponse = await http.post(`/projects/${projectId}/chunks/batch-content/`, {
                chunkNames
              });
              const chunkContentMap = chunkResponse?.data?.data || chunkResponse?.data || chunkResponse;

              batchResult.data.forEach((item) => {
                const chunkName = item.chunk_name || item.chunkName;
                if (chunkName && chunkContentMap[chunkName]) {
                  item.chunk_content = chunkContentMap[chunkName];
                }
              });
            } catch (chunkError) {
              console.error('获取文本块内容失败:', chunkError);
            }
          }
        }

        allData.push(...batchResult.data);
        hasMore = batchResult.hasMore;
        offset = batchResult.offset;
        totalProcessed += batchResult.data.length;

        if (onProgress) {
          onProgress({
            processed: totalProcessed,
            currentBatch: batchResult.data.length,
            hasMore
          });
        }

        if (hasMore) {
          await new Promise((resolve) => setTimeout(resolve, 100));
        }
      }

      await processAndDownloadData(allData, exportOptions);
      ElMessage.success(t('datasets.exportSuccess', '导出成功'));
      return true;
    } catch (error) {
      console.error('Streaming export failed:', error);
      ElMessage.error(error.message || t('datasets.exportFailed', '导出失败'));
      return false;
    }
  };

  /**
   * 导出数据集（保持向后兼容的原有功能）
   */
  const exportDatasetsFunc = async (exportOptions) => {
    try {
      const requestBody = {};

      if (exportOptions.selectedIds && exportOptions.selectedIds.length > 0) {
        requestBody.selectedIds = exportOptions.selectedIds;
      } else if (exportOptions.confirmedOnly) {
        requestBody.status = 'confirmed';
      }

      if (exportOptions.balanceMode && exportOptions.balanceConfig) {
        requestBody.balanceMode = true;
        requestBody.balanceConfig = exportOptions.balanceConfig;
      }

      const response = await exportDatasets(projectId, requestBody);
      // Django 返回格式: {code: 0, data: [...]}
      let dataToExport = response?.data || response;

      if (!Array.isArray(dataToExport)) {
        console.error('导出数据格式错误:', dataToExport);
        throw new Error('导出数据格式错误，期望数组格式');
      }

      await processAndDownloadData(dataToExport, exportOptions);
      ElMessage.success(t('datasets.exportSuccess', '导出成功'));
      return true;
    } catch (error) {
      ElMessage.error(error.message);
      return false;
    }
  };

  return {
    exportDatasets: exportDatasetsFunc,
    exportDatasetsStreaming
  };
}

