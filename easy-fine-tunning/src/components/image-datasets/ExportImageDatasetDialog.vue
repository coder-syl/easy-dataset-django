<template>
  <el-dialog
    v-model="dialogVisible"
    :title="$t('imageDatasets.exportTitle', '导出图像数据集')"
    width="600px"
    @close="handleClose"
  >
    <el-form label-width="140px">
      <!-- 导出格式选择 -->
      <el-form-item :label="$t('imageDatasets.exportFormat', '导出格式')">
        <el-radio-group v-model="formatType">
          <el-radio value="raw">{{ $t('imageDatasets.rawFormat', '原始格式') }}</el-radio>
          <el-radio value="sharegpt">ShareGPT (OpenAI)</el-radio>
          <el-radio value="alpaca">Alpaca</el-radio>
        </el-radio-group>
      </el-form-item>

      <!-- 图片导出选项 -->
      <el-form-item>
        <el-checkbox v-model="exportImages">
          {{ $t('imageDatasets.exportImagesOption', '导出图片文件') }}
        </el-checkbox>
        <div class="form-tip">
          {{ $t('imageDatasets.exportImagesDesc', '将所有图片打包成 ZIP 压缩包一起下载') }}
        </div>
      </el-form-item>

      <!-- 图片路径选项 -->
      <el-form-item>
        <el-checkbox v-model="includeImagePath">
          {{ $t('imageDatasets.includeImagePath', '在数据集中包含图片路径') }}
        </el-checkbox>
        <div class="form-tip">
          {{ $t('imageDatasets.includeImagePathDesc', '在问题或答案中添加图片路径（格式：/images/图片名称）') }}
        </div>
      </el-form-item>

      <!-- 系统提示词 -->
      <el-form-item :label="$t('imageDatasets.systemPrompt', '系统提示词（可选）')">
        <el-input
          v-model="systemPrompt"
          type="textarea"
          :rows="3"
          :placeholder="$t('imageDatasets.systemPromptPlaceholder', '输入系统提示词...')"
        />
      </el-form-item>

      <!-- 仅导出已确认 -->
      <el-form-item>
        <el-checkbox v-model="confirmedOnly">
          {{ $t('imageDatasets.confirmedOnly', '仅导出已确认的数据集') }}
        </el-checkbox>
      </el-form-item>

      <!-- 提示信息 -->
      <el-alert
        :title="$t('imageDatasets.exportTip', '标签格式的答案将自动解析为文本（逗号分隔）')"
        type="info"
        :closable="false"
        style="margin-top: 16px"
      />
    </el-form>

    <template #footer>
      <el-button @click="handleClose">{{ $t('common.cancel', '取消') }}</el-button>
      <el-button type="primary" @click="handleExport">{{ $t('common.export', '导出') }}</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch, computed } from 'vue';

const props = defineProps({
  open: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['update:open', 'export', 'close']);

const dialogVisible = computed({
  get: () => props.open,
  set: (val) => emit('update:open', val)
});

const formatType = ref('raw');
const exportImages = ref(false);
const includeImagePath = ref(true);
const systemPrompt = ref('');
const confirmedOnly = ref(false);

watch(
  () => props.open,
  (val) => {
    if (!val) {
      // 重置表单
      formatType.value = 'raw';
      exportImages.value = false;
      includeImagePath.value = true;
      systemPrompt.value = '';
      confirmedOnly.value = false;
    }
  }
);

const handleExport = () => {
  emit('export', {
    formatType: formatType.value,
    exportImages: exportImages.value,
    includeImagePath: includeImagePath.value,
    systemPrompt: systemPrompt.value,
    confirmedOnly: confirmedOnly.value
  });
};

const handleClose = () => {
  dialogVisible.value = false;
  emit('close');
};
</script>

<style scoped>
.form-tip {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 4px;
  margin-left: 24px;
}
</style>

