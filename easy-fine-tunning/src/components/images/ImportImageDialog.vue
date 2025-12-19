<template>
  <el-dialog
    v-model="localOpen"
    :title="$t('images.importImages', '导入图片')"
    width="700px"
    @close="handleClose"
  >
    <el-tabs v-model="mode">
      <el-tab-pane :label="$t('images.importFromFiles', '从文件导入')" name="files" />
      <el-tab-pane :label="$t('images.importFromPdf', '从 PDF 导入')" name="pdf" />
      <el-tab-pane :label="$t('images.importFromZip', '从压缩包导入')" name="zip" />
    </el-tabs>

    <div v-if="mode === 'files'" class="tab-body">
      <el-alert
        type="info"
        :title="$t('images.importFilesTip', '选择图片文件（支持多选），选择完成后点击上传')"
        show-icon
        class="mb-2"
      />
      <div class="file-selector">
        <input
          ref="fileInput"
          type="file"
          multiple
          accept="image/*"
          style="display: none"
          @change="handleFileSelect"
        />
        <el-button
          type="primary"
          :icon="UploadFilled"
          :disabled="loading"
          @click="triggerFileSelect"
        >
          {{ $t('images.selectImages', '选择图片') }}
        </el-button>
        <span class="file-hint">
          {{ $t('images.selectImagesHint', '支持多选图片文件') }}
        </span>
      </div>
      
      <!-- 已选择的图片列表 -->
      <div v-if="selectedFiles.length > 0" class="file-list">
        <div class="file-list-header">
          <span>
            {{ $t('images.selectedImages', '已选择图片') }} ({{ selectedFiles.length }})
          </span>
          <el-button
            link
            type="danger"
            size="small"
            @click="clearAllFiles"
          >
            {{ $t('common.clearAll', '清空全部') }}
          </el-button>
        </div>
        <div class="file-list-content">
          <div
            v-for="(file, idx) in selectedFiles"
            :key="idx"
            class="file-item"
          >
            <div class="file-preview">
              <el-image
                v-if="file.preview"
                :src="file.preview"
                fit="cover"
                class="preview-image"
              />
              <el-icon v-else class="preview-icon"><Picture /></el-icon>
            </div>
            <div class="file-info">
              <div class="file-name" :title="file.name">{{ file.name }}</div>
              <div class="file-size">{{ formatFileSize(file.size) }}</div>
            </div>
            <el-button
              link
              type="danger"
              :icon="Delete"
              size="small"
              @click="removeFile(idx)"
            />
          </div>
        </div>
      </div>
    </div>

    <div v-else-if="mode === 'pdf'" class="tab-body">
      <el-alert
        type="info"
        :title="$t('images.pdfImportTip', '选择 PDF 文件，系统会自动转换为图片并导入')"
        show-icon
        class="mb-2"
      />
      <el-upload
        drag
        :auto-upload="false"
        :show-file-list="false"
        accept=".pdf"
        :on-change="handlePdfChange"
      >
        <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
        <div class="el-upload__text">
          <p>
            {{ selectedPdf ? selectedPdf.name : $t('images.clickToSelectPdf', '点击选择 PDF 文件') }}
          </p>
        </div>
      </el-upload>
    </div>

    <div v-else class="tab-body">
      <el-alert
        type="info"
        :title="$t('images.zipImportTip', '选择 ZIP 压缩包，系统会解压并导入其中的图片')"
        show-icon
        class="mb-2"
      />
      <el-upload
        drag
        :auto-upload="false"
        :show-file-list="false"
        accept=".zip"
        :on-change="handleZipChange"
      >
        <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
        <div class="el-upload__text">
          <p>
            {{ selectedZip ? selectedZip.name : $t('images.clickToSelectZip', '点击选择 ZIP 文件') }}
          </p>
        </div>
      </el-upload>
    </div>

    <template #footer>
      <el-button @click="handleClose">
        {{ $t('common.cancel') }}
      </el-button>
      <el-button
        v-if="mode === 'files'"
        type="primary"
        :loading="loading"
        :disabled="selectedFiles.length === 0"
        @click="handleImportFiles"
      >
        {{ $t('images.uploadImages', '上传图片') }} ({{ selectedFiles.length }})
      </el-button>
      <el-button
        v-else-if="mode === 'pdf'"
        type="primary"
        :loading="loading"
        :disabled="!selectedPdf"
        @click="handleImportPdf"
      >
        {{ $t('images.convertAndImport', '转换并导入') }}
      </el-button>
      <el-button
        v-else
        type="primary"
        :loading="loading"
        :disabled="!selectedZip"
        @click="handleImportZip"
      >
        {{ $t('images.extractAndImport', '解压并导入') }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch } from 'vue';
import { ElMessage } from 'element-plus';
import { UploadFilled, Picture, Delete } from '@element-plus/icons-vue';
import {
  uploadSingleImage,
  importImagesFromZip,
  importImagesFromPdf,
} from '@/api/images';

const props = defineProps({
  open: {
    type: Boolean,
    default: false,
  },
  projectId: {
    type: [String, Number],
    required: true,
  },
});

const emit = defineEmits(['update:open', 'success']);

const localOpen = ref(props.open);
watch(
  () => props.open,
  val => {
    localOpen.value = val;
  },
);
watch(localOpen, val => emit('update:open', val));

const mode = ref('files');
const loading = ref(false);
const selectedPdf = ref(null);
const selectedZip = ref(null);
const fileInput = ref(null);

// 存储选中的图片文件（包含预览）
const selectedFiles = ref([]);

// 格式化文件大小
const formatFileSize = (bytes) => {
  if (!bytes) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
};

// 触发文件选择
const triggerFileSelect = () => {
  fileInput.value?.click();
};

// 处理文件选择
const handleFileSelect = (event) => {
  const files = Array.from(event.target.files || []);
  if (files.length === 0) return;

  // 过滤出图片文件
  const imageFiles = files.filter((file) => {
    const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/bmp', 'image/webp', 'image/svg+xml'];
    return validTypes.includes(file.type) || file.name.match(/\.(jpg|jpeg|png|gif|bmp|webp|svg)$/i);
  });

  if (imageFiles.length === 0) {
    ElMessage.warning('请选择图片文件');
    return;
  }

  // 为每个文件创建预览
  imageFiles.forEach((file) => {
    // 检查是否已存在（根据文件名）
    const exists = selectedFiles.value.some(f => f.name === file.name && f.size === file.size);
    if (exists) {
      return;
    }

    const fileObj = {
      name: file.name,
      size: file.size,
      file: file, // 原始文件对象
      preview: null
    };

    // 创建预览
    if (file.type.startsWith('image/')) {
      const reader = new FileReader();
      reader.onload = (e) => {
        fileObj.preview = e.target.result;
      };
      reader.readAsDataURL(file);
    }

    selectedFiles.value.push(fileObj);
  });

  // 清空 input，以便可以再次选择相同文件
  if (fileInput.value) {
    fileInput.value.value = '';
  }

  ElMessage.success(`已添加 ${imageFiles.length} 张图片`);
};

// 移除文件
const removeFile = (idx) => {
  // 释放预览 URL
  if (selectedFiles.value[idx].preview && selectedFiles.value[idx].preview.startsWith('data:')) {
    // data URL 不需要释放
  }
  selectedFiles.value.splice(idx, 1);
};

// 清空所有文件
const clearAllFiles = () => {
  selectedFiles.value = [];
};

// 上传图片
const handleImportFiles = async () => {
  if (selectedFiles.value.length === 0) {
    ElMessage.warning('请先选择图片');
    return;
  }

  loading.value = true;
  let successCount = 0;
  let failCount = 0;
  const errors = [];

  try {
    // 逐个上传文件
    for (const fileObj of selectedFiles.value) {
      try {
        await uploadSingleImage(props.projectId, fileObj.file, fileObj.name);
        successCount++;
      } catch (error) {
        console.error(`上传文件 ${fileObj.name} 失败:`, error);
        failCount++;
        errors.push(fileObj.name);
      }
    }

    if (successCount > 0) {
      ElMessage.success(`成功上传 ${successCount} 张图片${failCount > 0 ? `，失败 ${failCount} 张` : ''}`);
      emit('success');
      handleClose();
    } else {
      ElMessage.error('所有图片上传失败');
    }
  } catch (e) {
    console.error('图片上传失败:', e);
    ElMessage.error('上传失败: ' + (e.message || '未知错误'));
  } finally {
    loading.value = false;
  }
};

const handlePdfChange = (file) => {
  selectedPdf.value = file.raw;
};

const handleZipChange = (file) => {
  selectedZip.value = file.raw;
};

const handleImportPdf = async () => {
  if (!selectedPdf.value) return;
  loading.value = true;
  try {
    const form = new FormData();
    form.append('file', selectedPdf.value);
    await importImagesFromPdf(props.projectId, form);
    ElMessage.success('PDF 导入成功');
    emit('success');
    handleClose();
  } catch (e) {
    console.error('PDF 导入失败:', e);
  } finally {
    loading.value = false;
  }
};

const handleImportZip = async () => {
  if (!selectedZip.value) return;
  loading.value = true;
  try {
    const form = new FormData();
    form.append('file', selectedZip.value);
    await importImagesFromZip(props.projectId, form);
    ElMessage.success('压缩包导入成功');
    emit('success');
    handleClose();
  } catch (e) {
    console.error('ZIP 导入失败:', e);
  } finally {
    loading.value = false;
  }
};

const handleClose = () => {
  if (loading.value) return;
  selectedFiles.value = [];
  selectedPdf.value = null;
  selectedZip.value = null;
  mode.value = 'files';
  if (fileInput.value) {
    fileInput.value.value = '';
  }
  localOpen.value = false;
};
</script>

<style scoped>
.tab-body {
  padding: 12px 0;
}

.mb-2 {
  margin-bottom: 12px;
}

.file-selector {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.file-hint {
  font-size: 14px;
  color: var(--el-text-color-secondary);
}

.file-list {
  margin-top: 16px;
  max-height: 400px;
  overflow-y: auto;
}

.file-list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
  font-weight: 500;
  color: var(--el-text-color-primary);
  margin-bottom: 12px;
}

.file-list-content {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
}

.file-item {
  display: flex;
  flex-direction: column;
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  padding: 8px;
  position: relative;
  transition: all 0.2s;
}

.file-item:hover {
  border-color: var(--el-color-primary);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.file-preview {
  width: 100%;
  height: 120px;
  border-radius: 4px;
  overflow: hidden;
  background-color: var(--el-fill-color-lighter);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 8px;
}

.preview-image {
  width: 100%;
  height: 100%;
}

.preview-icon {
  font-size: 48px;
  color: var(--el-text-color-placeholder);
}

.file-info {
  flex: 1;
  min-width: 0;
}

.file-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--el-text-color-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-bottom: 4px;
}

.file-size {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.file-item .el-button {
  position: absolute;
  top: 4px;
  right: 4px;
  opacity: 0;
  transition: opacity 0.2s;
}

.file-item:hover .el-button {
  opacity: 1;
}
</style>


