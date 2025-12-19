<template>
  <div class="image-filters">
    <div class="left">
      <el-input
        v-model="localImageName"
        :placeholder="$t('images.searchPlaceholder', '搜索图片名称...')"
        clearable
        @input="handleNameChange"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
    </div>
    <div class="right">
      <el-select
        v-model="localHasQuestions"
        class="filter-select"
        @change="val => emit('update:has-questions', val)"
      >
        <el-option :label="$t('common.all', '全部')" value="all" />
        <el-option :label="$t('images.withQuestions', '有问题')" value="true" />
        <el-option :label="$t('images.withoutQuestions', '无问题')" value="false" />
      </el-select>

      <el-select
        v-model="localHasDatasets"
        class="filter-select"
        @change="val => emit('update:has-datasets', val)"
      >
        <el-option :label="$t('common.all', '全部')" value="all" />
        <el-option :label="$t('images.withDatasets', '已生成')" value="true" />
        <el-option :label="$t('images.withoutDatasets', '未生成')" value="false" />
      </el-select>

      <el-segmented
        v-model="localViewMode"
        :options="viewOptions"
        @change="val => emit('update:view-mode', val)"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue';
import { Search, Grid, List } from '@element-plus/icons-vue';

const props = defineProps({
  imageName: {
    type: String,
    default: '',
  },
  hasQuestions: {
    type: String,
    default: 'all',
  },
  hasDatasets: {
    type: String,
    default: 'all',
  },
  viewMode: {
    type: String,
    default: 'grid',
  },
});

const emit = defineEmits([
  'update:image-name',
  'update:has-questions',
  'update:has-datasets',
  'update:view-mode',
]);

const localImageName = ref(props.imageName);
const localHasQuestions = ref(props.hasQuestions);
const localHasDatasets = ref(props.hasDatasets);
const localViewMode = ref(props.viewMode);

watch(() => props.imageName, val => {
  localImageName.value = val;
});
watch(() => props.hasQuestions, val => {
  localHasQuestions.value = val;
});
watch(() => props.hasDatasets, val => {
  localHasDatasets.value = val;
});
watch(() => props.viewMode, val => {
  localViewMode.value = val;
});

let debounceTimer = null;
const handleNameChange = (val) => {
  if (debounceTimer) {
    clearTimeout(debounceTimer);
  }
  debounceTimer = setTimeout(() => {
    emit('update:image-name', val);
  }, 400);
};

const viewOptions = [
  { label: 'grid', value: 'grid', icon: Grid },
  { label: 'list', value: 'list', icon: List },
];
</script>

<style scoped>
.image-filters {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  padding: 12px 0;
}

.left {
  flex: 1;
}

.right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.filter-select {
  width: 160px;
}
</style>


