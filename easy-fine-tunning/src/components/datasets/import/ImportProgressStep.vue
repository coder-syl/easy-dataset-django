<template>
  <div class="import-progress-step">
    <el-progress
      :percentage="progressPercentage"
      :status="completed ? 'success' : undefined"
      :stroke-width="20"
    />
    <div class="progress-text">
      {{ currentStep }}
    </div>
    <div class="import-stats">
      <div class="stat-item">
        <div class="stat-label">{{ $t('import.total', '总数') }}</div>
        <div class="stat-value">{{ importStats.total }}</div>
      </div>
      <div class="stat-item">
        <div class="stat-label">{{ $t('import.success', '成功') }}</div>
        <div class="stat-value success">{{ importStats.success }}</div>
      </div>
      <div class="stat-item">
        <div class="stat-label">{{ $t('import.failed', '失败') }}</div>
        <div class="stat-value error">{{ importStats.failed }}</div>
      </div>
      <div class="stat-item">
        <div class="stat-label">{{ $t('import.skipped', '跳过') }}</div>
        <div class="stat-value warning">{{ importStats.skipped }}</div>
      </div>
    </div>
    <el-alert
      v-if="importStats.errors.length > 0"
      :title="$t('import.errors', '错误信息')"
      type="error"
      :closable="false"
      style="margin-top: 16px"
    >
      <ul>
        <li v-for="(error, index) in importStats.errors.slice(0, 10)" :key="index">
          {{ error }}
        </li>
        <li v-if="importStats.errors.length > 10">
          {{ moreErrorsText }}
        </li>
      </ul>
    </el-alert>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import { importDatasets } from '@/api/dataset';

const props = defineProps({
  projectId: {
    type: String,
    required: true
  },
  importData: {
    type: Object,
    required: true
  },
  onImportComplete: {
    type: Function,
    required: true
  },
  onError: {
    type: Function,
    default: () => {}
  }
});

const { t } = useI18n();

const progress = ref(0);
const currentStep = ref(t('import.preparingData', '准备数据...'));
const importStats = ref({
  total: 0,
  processed: 0,
  success: 0,
  failed: 0,
  skipped: 0,
  errors: []
});
const completed = ref(false);

const progressPercentage = computed(() => {
  if (importStats.value.total === 0) return 0;
  return Math.floor((importStats.value.processed / importStats.value.total) * 100);
});

// 更多错误文本（使用计算属性避免模板解析错误）
const moreErrorsText = computed(() => {
  const count = importStats.value.errors.length - 10;
  return t('import.moreErrors', '还有 {count} 个错误...', { count });
});

const parseTagsField = (tagsValue) => {
  if (!tagsValue) return [];
  if (Array.isArray(tagsValue)) return tagsValue;
  if (typeof tagsValue === 'string') {
    try {
      return JSON.parse(tagsValue);
    } catch {
      return tagsValue.split(',').map((t) => t.trim());
    }
  }
  return [];
};

const getOtherFields = (item, mapping) => {
  const other = {};
  const mappedFields = Object.values(mapping).filter((f) => f);
  Object.keys(item).forEach((key) => {
    if (!mappedFields.includes(key)) {
      other[key] = item[key];
    }
  });
  return other;
};

onMounted(() => {
  startImport();
});

const startImport = async () => {
  try {
    currentStep.value = t('import.preparingData', '准备数据...');
    const rawData = props.importData.rawData || [];
    const fieldMapping = props.importData.fieldMapping || {};
    const sourceInfo = props.importData.sourceInfo || {};

    importStats.value.total = rawData.length;

    // 转换数据格式
    const convertedData = rawData.map((item) => {
      // 支持 question 映射多个字段，拼接为一个字符串
      const qFields = fieldMapping.question;
      const question = Array.isArray(qFields)
        ? qFields
            .map((f) => item[f] || '')
            .filter((v) => v && String(v).trim())
            .join('\n')
        : item[qFields] || '';
      
      const converted = {
        question,
        answer: item[fieldMapping.answer] || '',
        cot: fieldMapping.cot ? item[fieldMapping.cot] || '' : '',
        question_label: '',
        chunk_name: sourceInfo.datasetName || sourceInfo.fileName || 'Imported Data',
        chunk_content: `Imported from ${sourceInfo.type || 'file'}`,
        model: 'imported',
        confirmed: false,
        score: 0,
        tags: fieldMapping.tags ? JSON.stringify(parseTagsField(item[fieldMapping.tags])) : '[]',
        note: '',
        other: JSON.stringify(getOtherFields(item, fieldMapping))
      };
      return converted;
    });

    progress.value = 25;
    currentStep.value = t('import.uploadingData', '上传数据...');

    // 分批上传数据
    const batchSize = 500;
    let success = 0;
    let failed = 0;
    let skipped = 0;
    const errors = [];

    for (let i = 0; i < convertedData.length; i += batchSize) {
      const batch = convertedData.slice(i, i + batchSize);

      try {
        const response = await importDatasets(props.projectId, {
          datasets: batch,
          sourceInfo
        });

        // Django 返回格式: {code: 0, data: {success: number, total: number, failed: number, skipped: number, errors: []}}
        const data = response?.data || response;
        success += data.success || 0;
        failed += data.failed || 0;
        skipped += data.skipped || 0;
        if (data.errors && Array.isArray(data.errors)) {
          errors.push(...data.errors);
        }

        importStats.value = {
          total: rawData.length,
          processed: Math.min(i + batchSize, rawData.length),
          success,
          failed,
          skipped,
          errors: errors.slice(0, 50) // 限制错误数量
        };

        progress.value = 25 + Math.floor(((i + batchSize) / convertedData.length) * 75);
      } catch (error) {
        failed += batch.length;
        errors.push(`批次 ${Math.floor(i / batchSize) + 1}: ${error.message}`);
        importStats.value.failed = failed;
        importStats.value.errors = errors.slice(0, 50);
      }
    }

    progress.value = 100;
    currentStep.value = t('import.completed', '导入完成');
    completed.value = true;

    importStats.value.processed = rawData.length;

    setTimeout(() => {
      props.onImportComplete();
    }, 1000);
  } catch (error) {
    props.onError(error.message);
  }
};
</script>

<style scoped>
.import-progress-step {
  padding: 20px;
}

.progress-text {
  margin-top: 16px;
  text-align: center;
  color: var(--el-text-color-regular);
  font-size: 14px;
}

.import-stats {
  display: flex;
  justify-content: space-around;
  margin-top: 24px;
  padding: 16px;
  background-color: var(--el-bg-color-page);
  border-radius: 8px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.stat-label {
  font-size: 14px;
  color: var(--el-text-color-regular);
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.stat-value.success {
  color: var(--el-color-success);
}

.stat-value.error {
  color: var(--el-color-error);
}

.stat-value.warning {
  color: var(--el-color-warning);
}
</style>

