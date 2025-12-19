import { saveImageAnnotation, fetchImageDetail } from '@/api/images';
import { ElMessage } from 'element-plus';
import { useI18n } from 'vue-i18n';

// 简化版标注逻辑：当前 Django 端 images.annotations 接口只写入 note，
// 这里主要负责打开对话框、选择模板、编辑答案以及保存。

export function useImageAnnotation(projectIdRef, state, options = {}) {
  const { t } = useI18n();
  const projectId = () =>
    typeof projectIdRef === 'string' || typeof projectIdRef === 'number'
      ? projectIdRef
      : projectIdRef.value;

  const open = async (image) => {
    if (!image) return;
    state.loading = true;
    try {
      const detail = await fetchImageDetail(projectId(), image.id);
      state.currentImage = detail || image;
      state.open = true;
    } catch (e) {
      console.error('加载图片详情失败:', e);
      ElMessage.error(t('images.loadImageDetailFailed', '加载图片详情失败'));
    } finally {
      state.loading = false;
    }
  };

  const close = () => {
    state.open = false;
    state.currentImage = null;
    state.selectedTemplate = null;
    state.answer = '';
  };

  const handleTemplateChange = (tpl) => {
    state.selectedTemplate = tpl;
    state.answer = '';
  };

  const save = async (continueNext = false) => {
    if (!state.currentImage) {
      ElMessage.error(t('images.noImageSelected', '未选择图片'));
      return;
    }
    if (!state.selectedTemplate) {
      ElMessage.error(t('images.noTemplateSelected', '请选择问题'));
      return;
    }
    if (!state.answer || (Array.isArray(state.answer) && !state.answer.length)) {
      ElMessage.error(t('images.answerRequired', '请输入答案'));
      return;
    }

    state.saving = true;
    try {
      await saveImageAnnotation(projectId(), {
        imageId: state.currentImage.id,
        note: typeof state.answer === 'string' ? state.answer : JSON.stringify(state.answer),
      });
      ElMessage.success(t('images.annotationSuccess', '标注保存成功'));
      if (options.onSuccess) {
        await options.onSuccess();
      }
      if (continueNext && options.findNextImage) {
        const next = await options.findNextImage();
        if (next && next.imageId) {
          await open({ id: next.imageId, imageName: next.imageName });
          return;
        }
      }
      close();
    } catch (e) {
      console.error('保存标注失败:', e);
      ElMessage.error(t('images.annotationFailed', '保存标注失败'));
    } finally {
      state.saving = false;
    }
  };

  return {
    open,
    close,
    save,
    handleTemplateChange,
  };
}


