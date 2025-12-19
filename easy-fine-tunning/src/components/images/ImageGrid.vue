<template>
  <div>
    <div v-if="!images || !images.length" class="empty">
      <el-empty :description="$t('images.noImages', '还没有图片')" />
    </div>
    <div v-else>
      <el-row :gutter="16">
        <el-col
          v-for="img in images"
          :key="img.id"
          :xs="24"
          :sm="12"
          :md="8"
          :lg="6"
        >
          <el-card class="image-card" shadow="hover">
            <div class="image-wrapper" @click="preview(img)">
              <el-image
                :src="img.base64 || img.path"
                :alt="img.imageName"
                fit="contain"
                class="image"
              />
              <div class="chips">
                <el-tag
                  size="small"
                  :type="(img.questionCount || 0) > 0 ? 'primary' : 'info'"
                  class="chip"
                  :class="{ 'clickable': (img.questionCount || 0) > 0 }"
                  @click.stop="(img.questionCount || 0) > 0 && $emit('view-questions', img)"
                >
                  {{ img.questionCount || 0 }} {{ $t('images.questions', '问题') }}
                </el-tag>
                <el-tag
                  size="small"
                  :type="(img.datasetCount || 0) > 0 ? 'success' : 'info'"
                  class="chip"
                  :class="{ 'clickable': (img.datasetCount || 0) > 0 }"
                  @click.stop="(img.datasetCount || 0) > 0 && $emit('view-datasets', img)"
                >
                  {{ img.datasetCount || 0 }} {{ $t('images.datasets', '数据集') }}
                </el-tag>
              </div>
              <div class="name">
                <el-tooltip :content="img.imageName">
                  <span>{{ img.imageName }}</span>
                </el-tooltip>
              </div>
            </div>
            <div class="actions">
              <el-button
                size="small"
                type="primary"
                @click.stop="$emit('annotate', img)"
              >
                {{ $t('images.annotate', '标注') }}
              </el-button>
              <el-tooltip :content="$t('images.generateQuestions', '生成问题')">
                <el-button
                  circle
                  size="small"
                  @click.stop="$emit('generate-questions', img)"
                >
                  <el-icon><QuestionFilled /></el-icon>
                </el-button>
              </el-tooltip>
              <el-tooltip :content="$t('images.generateDataset', '生成数据集')">
                <el-button
                  circle
                  size="small"
                  @click.stop="$emit('generate-dataset', img)"
                >
                  <el-icon><MagicStick /></el-icon>
                </el-button>
              </el-tooltip>
              <el-tooltip :content="$t('common.delete', '删除')">
                <el-button
                  circle
                  size="small"
                  type="danger"
                  @click.stop="$emit('delete', img.id)"
                >
                  <el-icon><Delete /></el-icon>
                </el-button>
              </el-tooltip>
            </div>
          </el-card>
        </el-col>
      </el-row>

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
import { QuestionFilled, MagicStick, Delete } from '@element-plus/icons-vue';

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
});

const emit = defineEmits(['page-change', 'generate-questions', 'generate-dataset', 'delete', 'annotate', 'view-questions', 'view-datasets']);

const previewVisible = ref(false);
const previewImage = ref(null);

const preview = (img) => {
  previewImage.value = img;
  previewVisible.value = true;
};
</script>

<style scoped>
.image-card {
  margin-bottom: 16px;
}

.image-wrapper {
  position: relative;
  cursor: pointer;
}

.image {
  width: 100%;
  height: 180px;
}

.chips {
  position: absolute;
  top: 8px;
  right: 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.chip {
  align-self: flex-end;
}

.chip.clickable {
  cursor: pointer;
  transition: opacity 0.2s;
}

.chip.clickable:hover {
  opacity: 0.8;
}

.name {
  margin-top: 8px;
  font-size: 13px;
  color: var(--el-text-color-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-top: 8px;
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


