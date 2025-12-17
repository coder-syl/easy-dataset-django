<template>
  <div class="star-rating">
    <el-rate
      v-model="localValue"
      :max="5"
      :allow-half="true"
      :disabled="readOnly"
      @change="handleChange"
    />
    <span v-if="showLabel && localValue > 0" class="rating-label">
      {{ getLabelText(localValue) }}
    </span>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';

const props = defineProps({
  modelValue: {
    type: Number,
    default: 0
  },
  readOnly: {
    type: Boolean,
    default: false
  },
  showLabel: {
    type: Boolean,
    default: true
  }
});

const emit = defineEmits(['update:model-value']);

const { t } = useI18n();

const localValue = ref(props.modelValue);

watch(
  () => props.modelValue,
  (newVal) => {
    localValue.value = newVal;
  }
);

const handleChange = (value) => {
  emit('update:model-value', value);
};

const getLabelText = (value) => {
  const labels = {
    0.5: t('rating.veryPoor', '很差'),
    1: t('rating.poor', '差'),
    1.5: t('rating.belowAverage', '偏差'),
    2: t('rating.fair', '一般'),
    2.5: t('rating.average', '中等'),
    3: t('rating.good', '良好'),
    3.5: t('rating.veryGood', '很好'),
    4: t('rating.excellent', '优秀'),
    4.5: t('rating.outstanding', '杰出'),
    5: t('rating.perfect', '完美')
  };
  return labels[value] || '';
};
</script>

<style scoped>
.star-rating {
  display: flex;
  align-items: center;
  gap: 12px;
}

.rating-label {
  font-size: 14px;
  color: var(--el-text-color-regular);
}
</style>

