<template>
  <el-dialog
    v-model="dialogVisible"
    :title="$t('exportDialog.balancedExportTitle', '平衡导出')"
    width="700px"
    @close="handleClose"
  >
    <div class="balance-export-content">
      <div class="description">
        {{ $t('exportDialog.balancedExportDescription', '按标签平衡导出数据集，可以设置每个标签导出的数量') }}
      </div>

      <el-alert v-if="error" :title="error" type="error" :closable="false" style="margin-bottom: 16px" />

      <div v-if="loading" class="loading-container">
        <el-icon class="is-loading" :size="40"><Loading /></el-icon>
      </div>

      <template v-else>
        <!-- 批量设置 -->
        <div class="quick-settings">
          <div class="quick-settings-title">{{ $t('exportDialog.quickSettings', '快速设置') }}</div>
          <div class="quick-settings-buttons">
            <el-button size="small" @click="setAllToSameCount(50)">
              {{ $t('exportDialog.setAllTo50', '全部设为50') }}
            </el-button>
            <el-button size="small" @click="setAllToSameCount(100)">
              {{ $t('exportDialog.setAllTo100', '全部设为100') }}
            </el-button>
            <el-button size="small" @click="setAllToSameCount(200)">
              {{ $t('exportDialog.setAllTo200', '全部设为200') }}
            </el-button>
            <el-input-number
              v-model="customCount"
              :min="0"
              size="small"
              style="width: 120px"
              @keyup.enter="setAllToSameCount(customCount)"
            />
            <el-button size="small" @click="setAllToSameCount(customCount)">
              {{ $t('exportDialog.customAmount', '自定义数量') }}
            </el-button>
          </div>
        </div>

        <!-- 标签配置表格 -->
        <el-table :data="balanceConfig" border style="margin-top: 16px">
          <el-table-column :label="$t('exportDialog.tagName', '标签名称')" width="200">
            <template #default="{ row }">
              <el-tag size="small">{{ row.tagLabel }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column :label="$t('exportDialog.availableCount', '可用数量')" width="120" align="right">
            <template #default="{ row }">
              {{ row.availableCount }}
            </template>
          </el-table-column>
          <el-table-column :label="$t('exportDialog.exportCount', '导出数量')" width="150" align="right">
            <template #default="{ row }">
              <el-input-number
                v-model="row.maxCount"
                :min="0"
                :max="row.availableCount"
                size="small"
                style="width: 100px"
                @change="updateTotalCount"
              />
            </template>
          </el-table-column>
        </el-table>

        <!-- 统计信息 -->
        <div class="statistics">
          <div class="stat-item">
            <strong>{{ $t('exportDialog.totalExportCount', '总导出数量') }}: {{ totalCount }}</strong>
          </div>
          <div class="stat-item">
            {{ $t('exportDialog.tagCount', '标签数量') }}: {{ activeTagCount }} / {{ balanceConfig.length }}
          </div>
        </div>
      </template>
    </div>

    <template #footer>
      <el-button @click="handleClose">{{ $t('common.cancel', '取消') }}</el-button>
      <el-button type="primary" @click="handleExport" :disabled="loading || totalCount === 0">
        {{ $t('exportDialog.export', '导出') }} ({{ totalCount }})
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { Loading } from '@element-plus/icons-vue';
import http from '@/api/http';

const props = defineProps({
  open: {
    type: Boolean,
    default: false
  },
  projectId: {
    type: String,
    required: true
  },
  confirmedOnly: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['update:open', 'export']);

const { t } = useI18n();

const dialogVisible = computed({
  get: () => props.open,
  set: (val) => emit('update:open', val)
});

const loading = ref(false);
const error = ref('');
const tagStats = ref([]);
const balanceConfig = ref([]);
const totalCount = ref(0);
const customCount = ref(100);

// 获取标签统计
const fetchTagStats = async () => {
  try {
    loading.value = true;
    error.value = '';
    const url = `/projects/${props.projectId}/datasets/export?confirmed=${props.confirmedOnly ? 'true' : 'false'}`;
    const response = await http.get(url);

    // 处理 Django 响应格式
    const stats = response?.data || response;

    if (!Array.isArray(stats)) {
      console.error('标签统计数据格式错误:', stats);
      throw new Error('标签统计数据格式错误');
    }

    tagStats.value = stats;

    // 初始化平衡配置
    const initialConfig = stats.map((stat) => ({
      tagLabel: stat.tagLabel || stat.tag_label,
      maxCount: Math.min(stat.datasetCount || stat.dataset_count || 0, 100),
      availableCount: stat.datasetCount || stat.dataset_count || 0
    }));

    balanceConfig.value = initialConfig;
    updateTotalCount();
  } catch (err) {
    error.value = err.message || t('errors.getTagStatsFailed', '获取标签统计失败');
  } finally {
    loading.value = false;
  }
};

// 更新总数
const updateTotalCount = () => {
  totalCount.value = balanceConfig.value.reduce((sum, config) => sum + (config.maxCount || 0), 0);
};

// 设置所有标签为相同数量
const setAllToSameCount = (count) => {
  balanceConfig.value = balanceConfig.value.map((config) => ({
    ...config,
    maxCount: Math.min(Math.max(0, parseInt(count) || 0), config.availableCount)
  }));
  updateTotalCount();
};

const activeTagCount = computed(() => {
  return balanceConfig.value.filter((c) => c.maxCount > 0).length;
});

const handleClose = () => {
  dialogVisible.value = false;
};

const handleExport = () => {
  const validConfig = balanceConfig.value.filter((config) => config.maxCount > 0);

  if (validConfig.length === 0) {
    error.value = t('export.balancedExport.atLeastOneTag', '请至少为一个标签设置大于0的数量');
    return;
  }

  emit('export', {
    balanceMode: true,
    balanceConfig: validConfig
  });

  handleClose();
};

watch(
  () => props.open,
  (val) => {
    if (val) {
      fetchTagStats();
    } else {
      error.value = '';
      balanceConfig.value = [];
      totalCount.value = 0;
    }
  }
);
</script>

<style scoped>
.balance-export-content {
  min-height: 300px;
}

.description {
  font-size: 14px;
  color: var(--el-text-color-regular);
  margin-bottom: 16px;
}

.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 200px;
}

.quick-settings {
  padding: 16px;
  background-color: var(--el-fill-color-lighter);
  border-radius: 4px;
  margin-bottom: 16px;
}

.quick-settings-title {
  font-weight: 600;
  font-size: 13px;
  margin-bottom: 12px;
}

.quick-settings-buttons {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}

.statistics {
  margin-top: 16px;
  padding: 12px;
  background-color: var(--el-color-primary-light-9);
  border-radius: 4px;
  display: flex;
  gap: 16px;
}

.stat-item {
  font-size: 14px;
}
</style>

