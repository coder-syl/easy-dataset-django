'use client';

import { Box, Typography, Chip, Tooltip, alpha, CircularProgress } from '@mui/material';
import { useTranslation } from 'react-i18next';
import { useTheme } from '@mui/material/styles';
import { useState } from 'react';

/**
 * 数据集元数据展示组件
 */
export default function DatasetMetadata({ currentDataset, onViewChunk, projectId }) {
  const { t } = useTranslation();
  const theme = useTheme();
  
  // 从 currentDataset 中获取 projectId（如果没有作为 prop 传入）
  const projectIdValue = projectId || currentDataset?.project_id || currentDataset?.projectId;

  return (
    <Box sx={{ mb: 3 }}>
      <Typography variant="subtitle1" color="text.secondary" sx={{ mb: 1 }}>
        {t('datasets.metadata')}
      </Typography>
      <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
        <Chip label={`${t('datasets.model')}: ${currentDataset.model || ''}`} variant="outlined" />
        {currentDataset.question_label && (
          <Chip label={`${t('common.label')}: ${currentDataset.question_label}`} color="primary" variant="outlined" />
        )}
        <Chip
          label={`${t('datasets.createdAt')}: ${currentDataset.create_at ? new Date(currentDataset.create_at).toLocaleString('zh-CN') : t('datasets.invalidDate')}`}
          variant="outlined"
        />
        {currentDataset.chunk_name && (
          <Tooltip title={t('textSplit.viewChunk')}>
            <Chip
              label={`${t('datasets.chunkId')}: ${currentDataset.chunk_name}`}
              variant="outlined"
              color="info"
              onClick={async () => {
                try {
                  // 使用新API接口获取文本块内容
                  const response = await fetch(
                    `/api/projects/${projectIdValue}/chunks/name/?chunkName=${encodeURIComponent(currentDataset.chunk_name)}`
                  );

                  if (!response.ok) {
                    throw new Error(`获取文本块失败: ${response.statusText}`);
                  }

                  const respData = await response.json();
                  // Django 返回格式: {code: 0, data: {...}}
                  const chunkData = respData?.code === 0 ? respData?.data : respData;

                  // 调用父组件的方法显示文本块
                  onViewChunk({
                    name: chunkData.name || currentDataset.chunk_name,
                    content: chunkData.content || ''
                  });
                } catch (error) {
                  console.error('获取文本块内容失败:', error);
                  // 即使API请求失败，也尝试调用查看方法
                  onViewChunk({
                    name: currentDataset.chunk_name,
                    content: '内容加载失败，请重试'
                  });
                }
              }}
              sx={{ cursor: 'pointer' }}
            />
          </Tooltip>
        )}
        {currentDataset.confirmed && (
          <Chip
            label={t('datasets.confirmed')}
            sx={{
              backgroundColor: alpha(theme.palette.success.main, 0.1),
              color: theme.palette.success.dark,
              fontWeight: 'medium'
            }}
          />
        )}
      </Box>
    </Box>
  );
}
