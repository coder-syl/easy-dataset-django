<template>
  <div class="file-upload-step">
    <el-upload
      ref="uploadRef"
      :auto-upload="false"
      :on-change="handleFileChange"
      :show-file-list="true"
      :limit="1"
      accept=".json,.jsonl,.csv"
      drag
    >
      <el-icon class="el-icon--upload"><upload-filled /></el-icon>
      <div class="el-upload__text">
        {{ $t('import.dropFile', '将文件拖到此处，或') }}
        <em>{{ $t('import.clickUpload', '点击上传') }}</em>
      </div>
      <template #tip>
        <div class="el-upload__tip">
          {{ $t('import.supportedFormats', '支持 JSON、JSONL、CSV 格式文件') }}
        </div>
      </template>
    </el-upload>

    <div v-if="uploadedFiles.length > 0" class="uploaded-files">
      <el-card v-for="(file, index) in uploadedFiles" :key="index" class="file-card">
        <template #header>
          <div class="file-header">
            <el-icon><Document /></el-icon>
            <span>{{ file.name }}</span>
            <el-icon class="check-icon"><Check /></el-icon>
          </div>
        </template>
        <div class="file-info">
          <p>{{ $t('import.fileSize', '文件大小') }}: {{ formatFileSize(file.size) }}</p>
          <p>{{ $t('import.records', '记录数') }}: {{ file.recordCount || 0 }}</p>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { ElMessage } from 'element-plus';
import { UploadFilled, Document, Check } from '@element-plus/icons-vue';
import { useI18n } from 'vue-i18n';

const props = defineProps({
  onDataLoaded: {
    type: Function,
    required: true
  },
  onError: {
    type: Function,
    default: () => {}
  }
});

const { t } = useI18n();
const uploadRef = ref(null);
const uploadedFiles = ref([]);

// 健壮的CSV解析函数，支持多行字段和引号转义
const parseCSV = (text) => {
  const result = [];
  const lines = [];
  let currentLine = '';
  let inQuotes = false;

  // 逐字符解析，正确处理引号内的换行符
  for (let i = 0; i < text.length; i++) {
    const char = text[i];
    const nextChar = text[i + 1];

    if (char === '"') {
      if (inQuotes && nextChar === '"') {
        // 转义的引号
        currentLine += '"';
        i++; // 跳过下一个引号
      } else {
        // 切换引号状态
        inQuotes = !inQuotes;
      }
    } else if (char === '\n' && !inQuotes) {
      // 行结束（不在引号内）
      if (currentLine.trim()) {
        lines.push(currentLine);
      }
      currentLine = '';
    } else {
      currentLine += char;
    }
  }

  // 添加最后一行
  if (currentLine.trim()) {
    lines.push(currentLine);
  }

  if (lines.length < 2) {
    throw new Error('CSV文件格式不正确，至少需要标题行和一行数据');
  }

  // 解析标题行
  const headers = parseCSVLine(lines[0]);

  // 解析数据行
  for (let i = 1; i < lines.length; i++) {
    const values = parseCSVLine(lines[i]);
    if (values.length > 0) {
      const obj = {};
      headers.forEach((header, index) => {
        obj[header] = values[index] || '';
      });
      result.push(obj);
    }
  }

  return result;
};

// 解析单行CSV，处理逗号分隔和引号转义
const parseCSVLine = (line) => {
  const result = [];
  let current = '';
  let inQuotes = false;

  for (let i = 0; i < line.length; i++) {
    const char = line[i];
    const nextChar = line[i + 1];

    if (char === '"') {
      if (inQuotes && nextChar === '"') {
        // 转义的引号
        current += '"';
        i++; // 跳过下一个引号
      } else {
        // 切换引号状态
        inQuotes = !inQuotes;
      }
    } else if (char === ',' && !inQuotes) {
      // 字段分隔符（不在引号内）
      result.push(current.trim());
      current = '';
    } else {
      current += char;
    }
  }

  // 添加最后一个字段
  result.push(current.trim());

  return result;
};

// 检测并转换ShareGPT格式为Alpaca格式
const convertShareGPTToAlpaca = (item) => {
  // 检查是否包含conversations字段且格式正确
  if (item.conversations && Array.isArray(item.conversations)) {
    const conversations = item.conversations;

    // 查找system、human、gpt消息
    let systemMessage = '';
    let instruction = '';
    let output = '';

    for (const conv of conversations) {
      if (conv.from === 'system' && conv.value) {
        systemMessage = conv.value;
      } else if (conv.from === 'human' && conv.value) {
        instruction = conv.value;
      } else if (conv.from === 'gpt' && conv.value) {
        output = conv.value;
        break; // 只取第一轮对话
      }
    }

    // 如果有system消息，将其作为instruction的前缀
    if (systemMessage && instruction) {
      instruction = `${systemMessage}\n\n${instruction}`;
    } else if (systemMessage && !instruction) {
      instruction = systemMessage;
    }

    // 转换为Alpaca格式
    return {
      instruction: instruction || '',
      input: '', // ShareGPT格式通常没有单独的input字段
      output: output || '',
      // 保留其他字段
      ...Object.fromEntries(Object.entries(item).filter(([key]) => key !== 'conversations'))
    };
  }

  return item; // 如果不是ShareGPT格式，返回原始数据
};

const handleFileChange = async (file) => {
  try {
    const text = await file.raw.text();
    const extension = file.name.split('.').pop().toLowerCase();
    let data = [];

    if (extension === 'json') {
      const parsed = JSON.parse(text);
      data = Array.isArray(parsed) ? parsed : [parsed];
    } else if (extension === 'jsonl') {
      data = text
        .split('\n')
        .filter((line) => line.trim())
        .map((line) => JSON.parse(line));
    } else if (extension === 'csv') {
      // 更健壮的CSV解析，支持多行字段和引号转义
      data = parseCSV(text);
      if (data.length === 0) {
        throw new Error('CSV文件格式不正确或没有数据');
      }
    } else {
      throw new Error('不支持的文件格式');
    }

    if (data.length === 0) {
      throw new Error('文件中没有找到有效数据');
    }

    // 检测并转换ShareGPT格式为Alpaca格式
    data = data.map(convertShareGPTToAlpaca);

    // 生成预览数据（取前5条记录，每个字段值截取前100字符）
    const preview = data.slice(0, 5).map((item) => {
      const previewItem = {};
      Object.keys(item).forEach((key) => {
        const value = String(item[key] || '');
        previewItem[key] = value.length > 100 ? value.substring(0, 100) + '...' : value;
      });
      return previewItem;
    });

    uploadedFiles.value = [
      {
        name: file.name,
        size: file.size,
        recordCount: data.length
      }
    ];

    const sourceInfo = {
      type: 'file',
      fileName: file.name,
      fileSize: file.size,
      datasetName: file.name.replace(/\.[^/.]+$/, ''),
      totalRecords: data.length
    };

    props.onDataLoaded(data, preview, sourceInfo);
  } catch (error) {
    ElMessage.error(error.message || t('import.parseError', '文件解析失败'));
    props.onError(error.message);
  }
};

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
};
</script>

<style scoped>
.file-upload-step {
  padding: 20px;
}

.uploaded-files {
  margin-top: 20px;
}

.file-card {
  margin-top: 12px;
}

.file-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.check-icon {
  margin-left: auto;
  color: var(--el-color-success);
}

.file-info {
  font-size: 14px;
  color: var(--el-text-color-regular);
}

.file-info p {
  margin: 4px 0;
}
</style>

