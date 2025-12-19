<template>
  <el-dialog
    v-model="localOpen"
    :title="$t('images.imageDatasets', '图片数据集')"
    width="900px"
    @close="handleClose"
  >
    <div v-loading="loading" class="dialog-content">
      <div v-if="datasets.length === 0" class="empty">
        <el-empty :description="$t('images.noDatasets', '该图片还没有数据集')" />
      </div>
      <div v-else>
        <el-table :data="datasets" border>
          <el-table-column
            :label="$t('datasets.question', '问题')"
            min-width="250"
            show-overflow-tooltip
          >
            <template #default="{ row }">
              {{ row.question }}
            </template>
          </el-table-column>
          <el-table-column
            :label="$t('datasets.answer', '答案')"
            min-width="250"
            show-overflow-tooltip
          >
            <template #default="{ row }">
              <div class="answer-cell">
                {{ getAnswerText(row) }}
              </div>
            </template>
          </el-table-column>
          <el-table-column
            :label="$t('imageDatasets.confirmed', '确认状态')"
            width="100"
          >
            <template #default="{ row }">
              <el-tag
                :type="row.confirmed ? 'success' : 'info'"
                size="small"
                effect="plain"
              >
                {{ row.confirmed ? $t('imageDatasets.confirmed', '已确认') : $t('imageDatasets.unconfirmed', '未确认') }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column
            :label="$t('imageDatasets.score', '评分')"
            width="100"
          >
            <template #default="{ row }">
              <el-rate
                v-model="row.score"
                disabled
                show-score
                text-color="#ff9900"
                score-template="{value}"
              />
            </template>
          </el-table-column>
          <el-table-column
            :label="$t('common.actions', '操作')"
            width="180"
            fixed="right"
          >
            <template #default="{ row }">
              <el-button
                size="small"
                link
                @click="handleViewDataset(row)"
              >
                {{ $t('common.view', '查看') }}
              </el-button>
              <el-button
                size="small"
                link
                @click="handleEditDataset(row)"
              >
                {{ $t('common.edit', '编辑') }}
              </el-button>
              <el-button
                size="small"
                link
                type="danger"
                @click="handleDeleteDataset(row)"
              >
                {{ $t('common.delete', '删除') }}
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>
    <template #footer>
      <el-button @click="handleClose">
        {{ $t('common.close', '关闭') }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import { fetchImageDatasets, deleteImageDataset } from '@/api/imageDatasets';

const props = defineProps({
  open: { type: Boolean, default: false },
  projectId: { type: [String, Number], required: true },
  image: { type: Object, default: null },
});

const emit = defineEmits(['update:open', 'success']);

const { t } = useI18n();
const router = useRouter();

const localOpen = ref(props.open);
watch(() => props.open, val => { localOpen.value = val; });
watch(localOpen, val => emit('update:open', val));

const loading = ref(false);
const datasets = ref([]);

watch(() => props.image, async (newImage) => {
  if (newImage && localOpen.value) {
    await fetchDatasetsData();
  }
}, { immediate: true });

watch(localOpen, async (val) => {
  if (val && props.image) {
    await fetchDatasetsData();
  }
});

const fetchDatasetsData = async () => {
  if (!props.image?.id && !props.image?.imageName) return;
  
  try {
    loading.value = true;
    const params = {};
    // 优先使用 imageId，如果没有则使用 imageName
    if (props.image.id || props.image.imageId) {
      params.imageId = props.image.id || props.image.imageId;
    } else if (props.image.imageName || props.image.image_name) {
      params.imageName = props.image.imageName || props.image.image_name;
    }
    
    const response = await fetchImageDatasets(props.projectId, params);
    
    // 处理响应数据
    let data = response;
    if (data && typeof data === 'object' && !Array.isArray(data) && 'data' in data) {
      datasets.value = Array.isArray(data.data) ? data.data : [];
    } else if (Array.isArray(data)) {
      datasets.value = data;
    } else {
      datasets.value = [];
    }
  } catch (e) {
    console.error('获取数据集列表失败:', e);
    ElMessage.error(t('common.fetchError', '获取失败'));
    datasets.value = [];
  } finally {
    loading.value = false;
  }
};

const getAnswerText = (dataset) => {
  if (dataset.answerType === 'label' && Array.isArray(dataset.answer)) {
    return dataset.answer.join(', ');
  }
  if (typeof dataset.answer === 'string') {
    try {
      const parsed = JSON.parse(dataset.answer);
      if (typeof parsed === 'object') {
        return JSON.stringify(parsed, null, 2);
      }
      return String(parsed);
    } catch {
      return dataset.answer;
    }
  }
  return String(dataset.answer || '');
};

const handleViewDataset = (dataset) => {
  // 跳转到数据集详情页
  router.push({
    name: 'image-dataset-detail',
    params: {
      projectId: props.projectId,
      datasetId: dataset.id,
    },
  });
  handleClose();
};

const handleEditDataset = (dataset) => {
  // 跳转到数据集详情页进行编辑
  router.push({
    name: 'image-dataset-detail',
    params: {
      projectId: props.projectId,
      datasetId: dataset.id,
    },
  });
  handleClose();
};

const handleDeleteDataset = async (dataset) => {
  try {
    await ElMessageBox.confirm(
      t('imageDatasets.deleteConfirm', '确定要删除这个数据集吗？'),
      t('common.confirmDelete', '确认删除'),
      { type: 'warning' },
    );
    await deleteImageDataset(props.projectId, dataset.id);
    ElMessage.success(t('imageDatasets.deleteSuccess', '删除成功'));
    await fetchDatasetsData();
    emit('success');
  } catch (e) {
    if (e !== 'cancel') {
      console.error('删除数据集失败:', e);
      ElMessage.error(t('imageDatasets.deleteFailed', '删除失败'));
    }
  }
};

const handleClose = () => {
  localOpen.value = false;
};
</script>

<style scoped>
.dialog-content {
  min-height: 200px;
}

.empty {
  padding: 40px 0;
}

.answer-cell {
  max-height: 60px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  word-break: break-word;
}
</style>

