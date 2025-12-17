<template>
  <el-dialog
    v-model="dialogVisible"
    :title="$t('datasets.moreFilters', '更多筛选')"
    width="600px"
    @close="handleClose"
  >
    <el-form label-width="120px">
      <el-form-item :label="$t('datasets.status', '确认状态')">
        <el-radio-group :model-value="filterConfirmed" @update:model-value="$emit('update:filter-confirmed', $event)">
          <el-radio label="all">{{ $t('common.all', '全部') }}</el-radio>
          <el-radio label="confirmed">{{ $t('datasets.confirmed', '已确认') }}</el-radio>
          <el-radio label="unconfirmed">{{ $t('datasets.unconfirmed', '未确认') }}</el-radio>
        </el-radio-group>
      </el-form-item>

      <el-form-item :label="$t('datasets.hasCot', '思维链')">
        <el-radio-group :model-value="filterHasCot" @update:model-value="$emit('update:filter-has-cot', $event)">
          <el-radio label="all">{{ $t('common.all', '全部') }}</el-radio>
          <el-radio label="yes">{{ $t('common.yes', '有') }}</el-radio>
          <el-radio label="no">{{ $t('common.no', '无') }}</el-radio>
        </el-radio-group>
      </el-form-item>

      <el-form-item :label="$t('datasets.isDistill', '蒸馏数据集')">
        <el-radio-group :model-value="filterIsDistill" @update:model-value="$emit('update:filter-is-distill', $event)">
          <el-radio label="all">{{ $t('common.all', '全部') }}</el-radio>
          <el-radio label="yes">{{ $t('common.yes', '是') }}</el-radio>
          <el-radio label="no">{{ $t('common.no', '否') }}</el-radio>
        </el-radio-group>
      </el-form-item>

      <el-form-item :label="$t('datasets.scoreRange', '评分范围')">
        <el-slider
          v-model="localScoreRange"
          range
          :min="0"
          :max="5"
          :step="0.5"
          show-stops
          @change="handleScoreRangeChange"
        />
        <div class="score-range-text">
          {{ localScoreRange[0] }} - {{ localScoreRange[1] }}
        </div>
      </el-form-item>

      <el-form-item :label="$t('datasets.customTag', '自定义标签')">
        <el-select
          v-model="localCustomTag"
          filterable
          clearable
          :placeholder="$t('datasets.selectTag', '选择标签')"
          @change="$emit('update:filter-custom-tag', $event)"
        >
          <el-option
            v-for="tag in availableTags"
            :key="tag"
            :label="tag"
            :value="tag"
          />
        </el-select>
      </el-form-item>

      <el-form-item :label="$t('datasets.noteKeyword', '备注关键词')">
        <el-input
          v-model="localNoteKeyword"
          :placeholder="$t('datasets.noteKeywordPlaceholder', '输入备注关键词')"
          clearable
          @input="$emit('update:filter-note-keyword', $event)"
        />
      </el-form-item>

      <el-form-item :label="$t('datasets.chunkName', '文本块名称')">
        <el-input
          v-model="localChunkName"
          :placeholder="$t('datasets.chunkNamePlaceholder', '输入文本块名称')"
          clearable
          @input="$emit('update:filter-chunk-name', $event)"
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="handleClose">{{ $t('common.cancel', '取消') }}</el-button>
      <el-button @click="handleReset">{{ $t('common.reset', '重置') }}</el-button>
      <el-button type="primary" @click="handleApply">{{ $t('common.apply', '应用') }}</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch, computed } from 'vue';

const props = defineProps({
  open: {
    type: Boolean,
    default: false
  },
  filterConfirmed: {
    type: String,
    default: 'all'
  },
  filterHasCot: {
    type: String,
    default: 'all'
  },
  filterIsDistill: {
    type: String,
    default: 'all'
  },
  filterScoreRange: {
    type: Array,
    default: () => [0, 5]
  },
  filterCustomTag: {
    type: String,
    default: ''
  },
  filterNoteKeyword: {
    type: String,
    default: ''
  },
  filterChunkName: {
    type: String,
    default: ''
  },
  availableTags: {
    type: Array,
    default: () => []
  }
});

const emit = defineEmits([
  'update:open',
  'update:filter-confirmed',
  'update:filter-has-cot',
  'update:filter-is-distill',
  'update:filter-score-range',
  'update:filter-custom-tag',
  'update:filter-note-keyword',
  'update:filter-chunk-name',
  'reset-filters',
  'apply-filters'
]);

const dialogVisible = computed({
  get: () => props.open,
  set: (val) => emit('update:open', val)
});

const localScoreRange = ref([...props.filterScoreRange]);
const localCustomTag = ref(props.filterCustomTag);
const localNoteKeyword = ref(props.filterNoteKeyword);
const localChunkName = ref(props.filterChunkName);

watch(
  () => props.filterScoreRange,
  (newVal) => {
    localScoreRange.value = [...newVal];
  },
  { deep: true }
);

watch(
  () => props.filterCustomTag,
  (newVal) => {
    localCustomTag.value = newVal;
  }
);

watch(
  () => props.filterNoteKeyword,
  (newVal) => {
    localNoteKeyword.value = newVal;
  }
);

watch(
  () => props.filterChunkName,
  (newVal) => {
    localChunkName.value = newVal;
  }
);

const handleScoreRangeChange = (val) => {
  emit('update:filter-score-range', val);
};

const handleClose = () => {
  dialogVisible.value = false;
};

const handleReset = () => {
  emit('reset-filters');
};

const handleApply = () => {
  emit('apply-filters');
};
</script>

<style scoped>
.score-range-text {
  margin-top: 8px;
  text-align: center;
  color: var(--el-text-color-regular);
}
</style>

