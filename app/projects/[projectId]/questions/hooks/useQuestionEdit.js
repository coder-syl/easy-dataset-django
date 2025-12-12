'use client';

import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import request from '@/lib/util/request';

export function useQuestionEdit(projectId, onSuccess) {
  const { t } = useTranslation();
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editMode, setEditMode] = useState('create');
  const [editingQuestion, setEditingQuestion] = useState(null);

  const handleOpenCreateDialog = () => {
    setEditMode('create');
    setEditingQuestion(null);
    setEditDialogOpen(true);
  };

  const handleOpenEditDialog = question => {
    setEditMode('edit');
    setEditingQuestion(question);
    setEditDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setEditDialogOpen(false);
    setEditingQuestion(null);
  };

  const handleSubmitQuestion = async formData => {
    try {
      const isCreate = editMode === 'create';
      const url = isCreate
        ? `/api/projects/${projectId}/questions`
        : `/api/projects/${projectId}/questions/${formData.id}`;
      const method = isCreate ? 'POST' : 'PATCH';

      // 构建请求数据，只包含有效值
      const payload = {
        question: formData.question,
        label: formData.label || ''
      };

      // 根据数据源类型添加相应的字段
      if (formData.sourceType === 'text') {
        if (!formData.chunkId) {
          throw new Error(t('questions.chunkIdRequired') || '文本块ID不能为空');
        }
        payload.chunk_id = formData.chunkId;
      } else if (formData.sourceType === 'image') {
        if (!formData.imageId) {
          throw new Error(t('questions.imageIdRequired') || '图片ID不能为空');
        }
        payload.image_id = formData.imageId;
        if (formData.imageName) {
          payload.image_name = formData.imageName;
        }
      }

      // 可选字段
      if (formData.gaPairId) {
        payload.ga_pair_id = formData.gaPairId;
      }
      if (formData.templateId) {
        payload.template_id = formData.templateId;
      }

      const response = await request(url, {
        method,
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || t('questions.operationFailed'));
      }

      // 获取更新后的问题数据
      const updatedQuestion = await response.json();

      // 直接更新问题列表中的数据，而不是重新获取整个列表
      if (onSuccess) {
        onSuccess(updatedQuestion);
      }
      handleCloseDialog();
    } catch (error) {
      console.error('操作失败:', error);
      // 显示错误信息给用户
      const errorMessage = error.message || t('questions.operationFailed') || '操作失败';
      alert(errorMessage);
      throw error; // 重新抛出错误，让调用者可以处理
    }
  };

  return {
    editDialogOpen,
    editMode,
    editingQuestion,
    handleOpenCreateDialog,
    handleOpenEditDialog,
    handleCloseDialog,
    handleSubmitQuestion
  };
}
