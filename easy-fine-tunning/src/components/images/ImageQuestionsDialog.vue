<template>
  <el-dialog
    v-model="localOpen"
    :title="$t('images.imageQuestions', '图片问题')"
    width="800px"
    @close="handleClose"
  >
    <div v-loading="loading" class="dialog-content">
      <div v-if="questions.length === 0" class="empty">
        <el-empty :description="$t('images.noQuestions', '该图片还没有问题')" />
      </div>
      <div v-else>
        <el-table :data="questions" border>
          <el-table-column
            :label="$t('datasets.question', '问题')"
            min-width="300"
            show-overflow-tooltip
          >
            <template #default="{ row }">
              {{ row.question }}
            </template>
          </el-table-column>
          <el-table-column
            :label="$t('common.label', '标签')"
            width="150"
          >
            <template #default="{ row }">
              <el-tag v-if="row.label" size="small" type="primary" effect="plain">
                {{ row.label }}
              </el-tag>
              <span v-else class="no-tag">{{ $t('datasets.noTag', '无标签') }}</span>
            </template>
          </el-table-column>
          <el-table-column
            :label="$t('datasets.answerCount', '答案数')"
            width="100"
          >
            <template #default="{ row }">
              {{ row.datasetCount || row.dataset_count || 0 }}
            </template>
          </el-table-column>
          <el-table-column
            :label="$t('common.actions', '操作')"
            width="150"
            fixed="right"
          >
            <template #default="{ row }">
              <el-button
                size="small"
                link
                @click="handleEditQuestion(row)"
              >
                {{ $t('common.edit', '编辑') }}
              </el-button>
              <el-button
                size="small"
                link
                type="danger"
                @click="handleDeleteQuestion(row)"
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
import { ElMessage, ElMessageBox } from 'element-plus';
import { fetchQuestions, deleteQuestion } from '@/api/question';

const props = defineProps({
  open: { type: Boolean, default: false },
  projectId: { type: [String, Number], required: true },
  image: { type: Object, default: null },
});

const emit = defineEmits(['update:open', 'success', 'edit']);

const { t } = useI18n();

const localOpen = ref(props.open);
watch(() => props.open, val => { localOpen.value = val; });
watch(localOpen, val => emit('update:open', val));

const loading = ref(false);
const questions = ref([]);

watch(() => props.image, async (newImage) => {
  if (newImage && localOpen.value) {
    await fetchQuestionsData();
  }
}, { immediate: false });

watch(localOpen, async (val) => {
  if (val && props.image) {
    await fetchQuestionsData();
  }
});

const fetchQuestionsData = async () => {
  if (!props.image?.id) return;
  
  try {
    loading.value = true;
    const response = await fetchQuestions(props.projectId, {
      imageId: props.image.id,
    });
    
    // 处理响应数据
    let data = response;
    if (data && typeof data === 'object' && !Array.isArray(data) && 'data' in data) {
      questions.value = Array.isArray(data.data) ? data.data : [];
    } else if (Array.isArray(data)) {
      questions.value = data;
    } else {
      questions.value = [];
    }
  } catch (e) {
    console.error('获取问题列表失败:', e);
    ElMessage.error(t('common.fetchError', '获取失败'));
    questions.value = [];
  } finally {
    loading.value = false;
  }
};

const handleEditQuestion = (question) => {
  // 触发编辑事件，由父组件处理
  emit('edit', question);
  handleClose();
};

const handleDeleteQuestion = async (question) => {
  try {
    await ElMessageBox.confirm(
      t('questions.deleteConfirm', '确定要删除这个问题吗？'),
      t('common.confirmDelete', '确认删除'),
      { type: 'warning' },
    );
    await deleteQuestion(props.projectId, question.id);
    ElMessage.success(t('questions.deleteSuccess', '删除成功'));
    await fetchQuestionsData();
    emit('success');
  } catch (e) {
    if (e !== 'cancel') {
      console.error('删除问题失败:', e);
      ElMessage.error(t('questions.deleteFailed', '删除失败'));
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

.no-tag {
  color: var(--el-text-color-placeholder);
  font-size: 12px;
}
</style>

