<template>
  <el-dialog
    v-model="dialogVisible"
    :title="$t('imageDatasets.filterDialogTitle', '筛选图像数据集')"
    width="400px"
    @close="handleClose"
  >
    <!-- 确认状态筛选 -->
    <el-form-item :label="$t('imageDatasets.statusFilter', '确认状态')">
      <el-select
        v-model="localStatusFilter"
        @change="handleStatusChange"
        style="width: 100%"
      >
        <el-option :label="$t('common.all', '全部')" value="all" />
        <el-option :label="$t('imageDatasets.confirmed', '已确认')" value="confirmed" />
        <el-option :label="$t('imageDatasets.unconfirmed', '未确认')" value="unconfirmed" />
      </el-select>
    </el-form-item>

    <!-- 评分范围筛选 -->
    <el-form-item :label="$t('imageDatasets.scoreFilter', '评分范围')">
      <div class="score-display">
        {{ localScoreFilter[0] }} - {{ localScoreFilter[1] }} {{ $t('imageDatasets.scoreUnit', '分') }}
      </div>
      <el-slider
        v-model="localScoreFilter"
        :min="0"
        :max="5"
        :step="1"
        :show-tooltip="true"
        :show-stops="true"
        @change="handleScoreChange"
      />
    </el-form-item>

    <template #footer>
      <el-button @click="handleReset">{{ $t('common.reset', '重置') }}</el-button>
      <el-button @click="handleClose">{{ $t('common.cancel', '取消') }}</el-button>
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
  statusFilter: {
    type: String,
    default: 'all'
  },
  scoreFilter: {
    type: Array,
    default: () => [0, 5]
  }
});

const emit = defineEmits([
  'update:open',
  'update:statusFilter',
  'update:scoreFilter',
  'reset',
  'apply',
  'close'
]);

const dialogVisible = computed({
  get: () => props.open,
  set: (val) => emit('update:open', val)
});

const localStatusFilter = ref(props.statusFilter);
const localScoreFilter = ref(Array.isArray(props.scoreFilter) ? [...props.scoreFilter] : [0, 5]);

watch(
  () => props.statusFilter,
  (val) => {
    localStatusFilter.value = val;
  }
);

watch(
  () => props.scoreFilter,
  (val) => {
    localScoreFilter.value = Array.isArray(val) ? [...val] : [0, 5];
  },
  { deep: true }
);

const handleStatusChange = (val) => {
  emit('update:statusFilter', val);
};

const handleScoreChange = (val) => {
  emit('update:scoreFilter', [...val]);
};

const handleReset = () => {
  localStatusFilter.value = 'all';
  localScoreFilter.value = [0, 5];
  emit('reset');
};

const handleApply = () => {
  emit('apply');
  dialogVisible.value = false;
};

const handleClose = () => {
  // 恢复原始值
  localStatusFilter.value = props.statusFilter;
  localScoreFilter.value = Array.isArray(props.scoreFilter) ? [...props.scoreFilter] : [0, 5];
  emit('close');
};
</script>

<style scoped>
.score-display {
  margin-bottom: 8px;
  font-size: 14px;
  color: var(--el-text-color-regular);
}
</style>

