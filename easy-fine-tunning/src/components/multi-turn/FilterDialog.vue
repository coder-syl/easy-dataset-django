<template>
  <el-dialog
    v-model="dialogVisible"
    :title="$t('datasets.filtersTitle', '筛选条件')"
    width="500px"
    @close="$emit('close')"
  >
    <el-form :model="localFilters" label-width="120px">
      <el-form-item :label="$t('settings.multiTurnRoleA', '角色A')">
        <el-input v-model="localFilters.roleA" :placeholder="$t('settings.multiTurnRoleA', '角色A')" />
      </el-form-item>
      <el-form-item :label="$t('settings.multiTurnRoleB', '角色B')">
        <el-input v-model="localFilters.roleB" :placeholder="$t('settings.multiTurnRoleB', '角色B')" />
      </el-form-item>
      <el-form-item :label="$t('datasets.conversationScenario', '对话场景')">
        <el-input v-model="localFilters.scenario" :placeholder="$t('datasets.conversationScenario', '对话场景')" />
      </el-form-item>
      <el-form-item :label="$t('datasets.scoreRange', '评分范围')">
        <div class="score-range">
          <el-input-number
            v-model="localFilters.scoreMin"
            :min="0"
            :max="5"
            :step="0.1"
            :precision="1"
            :placeholder="$t('datasets.minScore', '最低分')"
            style="width: 100%"
          />
          <span class="range-separator">-</span>
          <el-input-number
            v-model="localFilters.scoreMax"
            :min="0"
            :max="5"
            :step="0.1"
            :precision="1"
            :placeholder="$t('datasets.maxScore', '最高分')"
            style="width: 100%"
          />
        </div>
      </el-form-item>
      <el-form-item :label="$t('datasets.filterConfirmationStatus', '确认状态')">
        <el-select v-model="localFilters.confirmed" :placeholder="$t('datasets.filterConfirmationStatus', '确认状态')" clearable>
          <el-option :label="$t('common.all', '全部')" value="" />
          <el-option :label="$t('datasets.confirmed', '已确认')" value="true" />
          <el-option :label="$t('datasets.unconfirmed', '未确认')" value="false" />
        </el-select>
      </el-form-item>
    </el-form>
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleReset">{{ $t('datasets.resetFilters', '重置') }}</el-button>
        <el-button @click="$emit('close')">{{ $t('common.cancel', '取消') }}</el-button>
        <el-button type="primary" @click="handleApply">{{ $t('datasets.applyFilters', '应用') }}</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch } from 'vue';

const props = defineProps({
  open: {
    type: Boolean,
    default: false
  },
  filters: {
    type: Object,
    default: () => ({
      roleA: '',
      roleB: '',
      scenario: '',
      scoreMin: '',
      scoreMax: '',
      confirmed: ''
    })
  }
});

const emit = defineEmits(['close', 'reset', 'apply', 'update:filters']);

const dialogVisible = ref(props.open);

watch(
  () => props.open,
  (newVal) => {
    dialogVisible.value = newVal;
    if (newVal) {
      localFilters.value = { ...props.filters };
    }
  }
);

watch(dialogVisible, (newVal) => {
  if (!newVal) {
    emit('close');
  }
});

const localFilters = ref({ ...props.filters });

watch(
  () => props.filters,
  (newVal) => {
    localFilters.value = { ...newVal };
  },
  { deep: true }
);

const handleReset = () => {
  localFilters.value = {
    roleA: '',
    roleB: '',
    scenario: '',
    scoreMin: '',
    scoreMax: '',
    confirmed: ''
  };
  emit('reset');
};

const handleApply = () => {
  emit('update:filters', { ...localFilters.value });
  emit('apply');
};
</script>

<style scoped>
.score-range {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
}

.range-separator {
  color: var(--el-text-color-secondary);
  font-size: 14px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>

