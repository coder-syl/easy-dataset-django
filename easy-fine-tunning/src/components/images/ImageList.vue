<template>
  <div>
    <div v-if="!images || !images.length" class="empty">
      <el-empty :description="$t('images.noImages', '还没有图片')" />
    </div>
    <div v-else>
      <el-table
        :data="images"
        border
        style="width: 100%"
      >
        <el-table-column type="selection" width="50" />
        <el-table-column
          :label="$t('images.preview', '预览')"
          width="80"
        >
          <template #default="{ row }">
            <el-image
              :src="row.base64 || row.path"
              :alt="row.imageName"
              fit="cover"
              class="thumb"
              @click="preview(row)"
            />
          </template>
        </el-table-column>
        <el-table-column
          prop="imageName"
          :label="$t('images.fileName', '文件名')"
          min-width="180"
        >
          <template #default="{ row }">
            <el-tooltip :content="row.imageName">
              <span class="ellipsis">{{ row.imageName }}</span>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column
          :label="$t('images.questionCount', '问题数')"
          width="100"
        >
          <template #default="{ row }">
            <el-button
              v-if="(row.questionCount || 0) > 0"
              link
              type="primary"
              size="small"
              @click.stop="$emit('view-questions', row)"
            >
              {{ row.questionCount || 0 }}
            </el-button>
            <span v-else>{{ row.questionCount || 0 }}</span>
          </template>
        </el-table-column>
        <el-table-column
          :label="$t('images.datasetCount', '数据集数')"
          width="100"
        >
          <template #default="{ row }">
            <el-button
              v-if="(row.datasetCount || 0) > 0"
              link
              type="success"
              size="small"
              @click.stop="$emit('view-datasets', row)"
            >
              {{ row.datasetCount || 0 }}
            </el-button>
            <span v-else>{{ row.datasetCount || 0 }}</span>
          </template>
        </el-table-column>
        <el-table-column
          prop="createAt"
          :label="$t('images.uploadTime', '上传时间')"
          width="180"
        />
        <el-table-column
          :label="$t('common.actions', '操作')"
          width="220"
          fixed="right"
        >
          <template #default="{ row }">
            <el-button
              size="small"
              link
              @click.stop="$emit('annotate', row)"
            >
              {{ $t('images.annotate', '标注') }}
            </el-button>
            <el-button
              size="small"
              link
              @click.stop="$emit('generate-questions', row)"
            >
              {{ $t('images.generateQuestions', '生成问题') }}
            </el-button>
            <el-button
              size="small"
              link
              @click.stop="$emit('generate-dataset', row)"
            >
              {{ $t('images.generateDataset', '生成数据集') }}
            </el-button>
            <el-button
              size="small"
              type="danger"
              link
              @click.stop="$emit('delete', row.id)"
            >
              {{ $t('common.delete', '删除') }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="total > pageSize" class="pagination">
        <el-pagination
          :current-page="page"
          :page-size="pageSize"
          layout="prev, pager, next"
          :total="total"
          @current-change="$emit('page-change', $event)"
        />
      </div>

      <el-dialog
        v-model="previewVisible"
        :title="previewImage?.imageName"
        width="70%"
      >
        <div class="preview-container" v-if="previewImage">
          <img
            :src="previewImage.base64 || previewImage.path"
            :alt="previewImage.imageName"
            class="preview-img"
          />
        </div>
      </el-dialog>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';

defineProps({
  images: {
    type: Array,
    default: () => [],
  },
  total: {
    type: Number,
    default: 0,
  },
  page: {
    type: Number,
    default: 1,
  },
  pageSize: {
    type: Number,
    default: 8,
  },
  selectedIds: {
    type: Array,
    default: () => [],
  },
});

defineEmits([
  'page-change',
  'generate-questions',
  'generate-dataset',
  'delete',
  'annotate',
  'update:selected-ids',
  'view-questions',
  'view-datasets',
]);

const previewVisible = ref(false);
const previewImage = ref(null);

const preview = (img) => {
  previewImage.value = img;
  previewVisible.value = true;
};
</script>

<style scoped>
.thumb {
  width: 56px;
  height: 56px;
  border-radius: 4px;
  cursor: pointer;
}

.ellipsis {
  display: inline-block;
  max-width: 260px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.pagination {
  display: flex;
  justify-content: center;
  margin-top: 16px;
}

.preview-container {
  text-align: center;
}

.preview-img {
  max-width: 100%;
  max-height: 70vh;
  object-fit: contain;
}
</style>


