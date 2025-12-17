<template>
  <div class="field-mapping-step">
    <el-alert
      v-if="previewData && previewData.length > 0"
      :title="$t('import.previewData', '预览数据（前5条）')"
      type="info"
      :closable="false"
      style="margin-bottom: 16px"
    />

    <el-table v-if="previewData && previewData.length > 0" :data="previewData" border max-height="300">
      <el-table-column
        v-for="field in availableFields"
        :key="field"
        :prop="field"
        :label="field"
        min-width="150"
      />
    </el-table>

    <el-form label-width="150px" style="margin-top: 24px">
      <el-form-item :label="$t('import.mapQuestion', '映射问题字段')" required>
        <el-select
          v-model="fieldMapping.question"
          :placeholder="$t('import.selectField', '选择字段')"
          multiple
          style="width: 100%"
        >
          <el-option
            v-for="field in availableFields"
            :key="field"
            :label="field"
            :value="field"
          />
        </el-select>
        <div class="field-help">
          {{ $t('import.questionFieldHelp', '支持选择多个字段（如 Alpaca 格式的 instruction + input）') }}
        </div>
      </el-form-item>

      <el-form-item :label="$t('import.mapAnswer', '映射答案字段')" required>
        <el-select
          v-model="fieldMapping.answer"
          :placeholder="$t('import.selectField', '选择字段')"
          style="width: 100%"
        >
          <el-option
            v-for="field in availableFields"
            :key="field"
            :label="field"
            :value="field"
          />
        </el-select>
      </el-form-item>

      <el-form-item :label="$t('import.mapCOT', '映射思维链字段')">
        <el-select
          v-model="fieldMapping.cot"
          :placeholder="$t('import.selectField', '选择字段（可选）')"
          clearable
          style="width: 100%"
        >
          <el-option
            v-for="field in availableFields"
            :key="field"
            :label="field"
            :value="field"
          />
        </el-select>
      </el-form-item>

      <el-form-item :label="$t('import.mapTags', '映射标签字段')">
        <el-select
          v-model="fieldMapping.tags"
          :placeholder="$t('import.selectField', '选择字段（可选）')"
          clearable
          style="width: 100%"
        >
          <el-option
            v-for="field in availableFields"
            :key="field"
            :label="field"
            :value="field"
          />
        </el-select>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue';

const props = defineProps({
  previewData: {
    type: Array,
    default: () => []
  },
  onMappingComplete: {
    type: Function,
    required: true
  },
  onError: {
    type: Function,
    default: () => {}
  }
});

const availableFields = ref([]);
const fieldMapping = ref({
  question: '',
  answer: '',
  cot: '',
  tags: ''
});

// 智能字段识别（支持 Alpaca: instruction + input -> question，output -> answer）
const smartFieldMapping = (fields) => {
  const mapping = {
    question: '',
    answer: '',
    cot: '',
    tags: ''
  };

  const lower = fields.map((f) => f.toLowerCase());
  const instructionIdx = lower.findIndex((f) => f.includes('instruction'));
  const inputIdx = lower.findIndex((f) => f.includes('input'));
  const outputIdx = lower.findIndex((f) => f.includes('output'));

  // Alpaca 格式的优先识别
  if (instructionIdx !== -1 && inputIdx !== -1) {
    // 如果同时有instruction和input字段，将它们组合为question
    mapping.question = [fields[instructionIdx], fields[inputIdx]];
  } else if (instructionIdx !== -1) {
    // 如果只有instruction字段（比如从ShareGPT转换而来），直接映射为question
    mapping.question = fields[instructionIdx];
  }

  if (outputIdx !== -1) {
    mapping.answer = fields[outputIdx];
  }

  const questionKeywords = ['question', 'input', 'query', 'prompt', 'instruction', '问题', '输入', '指令'];
  const answerKeywords = ['answer', 'output', 'response', 'completion', 'target', '答案', '输出', '回答'];
  const cotKeywords = ['cot', 'reasoning', 'explanation', 'thinking', 'rationale', '思维链', '推理', '解释'];
  const tagKeywords = ['tag', 'tags', 'label', 'labels', 'category', 'categories', '标签', '类别'];

  fields.forEach((field) => {
    const fieldLower = field.toLowerCase();

    if (!mapping.question || (typeof mapping.question === 'string' && !mapping.question)) {
      if (questionKeywords.some((keyword) => fieldLower.includes(keyword))) {
        mapping.question = field;
      }
    } else if (!mapping.answer) {
      if (answerKeywords.some((keyword) => fieldLower.includes(keyword))) {
        mapping.answer = field;
      }
    } else if (!mapping.cot) {
      if (cotKeywords.some((keyword) => fieldLower.includes(keyword))) {
        mapping.cot = field;
      }
    } else if (!mapping.tags) {
      if (tagKeywords.some((keyword) => fieldLower.includes(keyword))) {
        mapping.tags = field;
      }
    }
  });

  return mapping;
};

onMounted(() => {
  if (props.previewData && props.previewData.length > 0) {
    const fields = Object.keys(props.previewData[0]);
    availableFields.value = fields;

    // 智能识别字段映射
    const smartMapping = smartFieldMapping(fields);
    fieldMapping.value = { ...smartMapping };

    // 如果没有自动识别到，至少设置第一个字段
    if (!fieldMapping.value.question && fields.length > 0) {
      fieldMapping.value.question = fields[0];
    }
    if (!fieldMapping.value.answer && fields.length > 1) {
      fieldMapping.value.answer = fields[1];
    }
  }
});

watch(
  () => fieldMapping.value,
  (newMapping) => {
    // 确保 question 是数组或字符串
    const question = Array.isArray(newMapping.question)
      ? newMapping.question
      : newMapping.question
        ? [newMapping.question]
        : [];
    
    if (question.length > 0 && newMapping.answer) {
      props.onMappingComplete({ ...newMapping, question });
    }
  },
  { deep: true }
);
</script>

<style scoped>
.field-mapping-step {
  padding: 20px;
}

.field-help {
  margin-top: 4px;
  font-size: 12px;
  color: var(--el-text-color-placeholder);
}
</style>

