<template>
  <div class="datasets-overview">
    <el-card>
      <div style="display:flex;justify-content:space-between;align-items:center;">
        <div>
          <h3>{{ $t('datasets.overviewTitle','数据集总览') }}</h3>
          <div style="color:var(--el-text-color-secondary)">{{ $t('datasets.overviewDesc','查看各类数据集统计并导出') }}</div>
        </div>
        <div>
          <el-button type="primary" @click="openExportDialog">{{ $t('datasets.export','导出') }}</el-button>
        </div>
      </div>
    </el-card>

    <el-row :gutter="20" style="margin-top:16px;">
      <el-col :span="8">
        <el-card>
          <div style="font-weight:600">{{ $t('datasets.singleTurn','单轮') }}</div>
          <div style="font-size:20px;margin-top:8px;">{{ overview.counts.single }}</div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <div style="font-weight:600">{{ $t('datasets.multiTurn','多轮') }}</div>
          <div style="font-size:20px;margin-top:8px;">{{ overview.counts.multi }}</div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <div style="font-weight:600">{{ $t('datasets.imageQA','图片') }}</div>
          <div style="font-size:20px;margin-top:8px;">{{ overview.counts.image }}</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Full export dialog (reuses existing ExportDatasetDialog) -->
    <ExportDatasetDialog
      v-model:open="showExport"
      :project-id="projectId"
      @export="handleExport"
      @balanced-export="handleBalancedExport"
    />
    <ExportProgressDialog v-model:open="exportProgress.show" :progress="exportProgress" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { fetchDatasetsOverview, exportCombinedDatasets, exportCombinedDatasetsJSON } from '@/api/datasetsOverview';
import { format as formatDateFns } from 'date-fns';
import ExportDatasetDialog from '@/components/datasets/ExportDatasetDialog.vue';
import ExportProgressDialog from '@/components/datasets/ExportProgressDialog.vue';
import { useDatasetExport } from '@/composables/useDatasetExport';
const route = useRoute();
const projectId = route.params.projectId;

const overview = ref({
  counts: { single: 0, multi: 0, image: 0 },
  lastUpdated: null,
  samples: {}
});

const showExport = ref(false);
// export dialog state is handled by ExportDatasetDialog, we'll react to its emitted options
const exportProgress = ref({ show: false, processed: 0, total: 0, hasMore: false });

const openExportDialog = () => {
  showExport.value = true;
};

const loadOverview = async () => {
  try {
    const res = await fetchDatasetsOverview(projectId);
    overview.value = res;
  } catch (e) {
    console.error(e);
  }
};

onMounted(loadOverview);
    const { exportDatasets, exportDatasetsStreaming } = useDatasetExport(projectId);

    const handleExport = async (exportOptions) => {
      try {
        const options = {
          ...exportOptions,
          selectedIds: exportOptions.selectedIds || []
        };

        const STREAMING_THRESHOLD = 1000;
        const needsChunkContent = options.formatType === 'custom' && options.customFields?.includeChunk;

        let totalCount = 0;
        if (options.selectedIds && options.selectedIds.length > 0) {
          totalCount = options.selectedIds.length;
        } else {
          totalCount = overview.value.counts.single + overview.value.counts.multi + overview.value.counts.image;
        }

        let success = false;
        if (totalCount > STREAMING_THRESHOLD || needsChunkContent) {
          exportProgress.value = { show: true, processed: 0, total: totalCount, hasMore: true };
          success = await exportDatasetsStreaming(options, (progress) => {
            exportProgress.value = { ...exportProgress.value, processed: progress.processed, hasMore: progress.hasMore };
          });
          exportProgress.value = { show: false, processed: 0, total: 0, hasMore: false };
        } else {
          success = await exportDatasets(options);
        }

        if (success) {
          showExport.value = false;
        }
      } catch (err) {
        console.error('Overview export failed', err);
      }
    };

    const handleBalancedExport = async (options) => {
      await handleExport(options);
    };
</script>

<style scoped>
.datasets-overview {
  padding: 20px;
  max-width: 1100px;
  margin: 0 auto;
}
</style>


