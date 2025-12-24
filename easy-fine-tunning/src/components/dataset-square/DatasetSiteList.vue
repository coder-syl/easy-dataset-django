<template>
  <div class="site-list">
    <el-tabs v-model="activeCategory" type="card" @tab-click="onTabClick">
      <el-tab-pane v-for="(label, key) in categories" :key="key" :label="label" :name="label" />
    </el-tabs>

    <div class="results-info" style="margin:12px 0;">
      <span v-if="!loading">{{ $t('datasetSquare.foundResources', { count: filteredSites.length }) }}</span>
      <el-tag v-if="!loading" type="info" style="margin-left:8px">{{ filteredSites.length }}</el-tag>
    </div>

    <div v-if="loading" class="skeleton-grid">
      <div v-for="n in 8" :key="n" class="skeleton-card"></div>
    </div>

    <el-row v-else :gutter="24" justify="start">
      <el-col :xs="24" :sm="12" :md="6" :lg="6" v-for="(site, idx) in filteredSites" :key="idx">
        <div class="card-wrap">
          <DatasetSiteCard :site="site" />
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed } from "vue";
import DatasetSiteCard from "./DatasetSiteCard.vue";
const props = defineProps({
  sites: { type: Array, default: () => [] },
  query: { type: String, default: "" },
  loading: { type: Boolean, default: false },
});
const categories = {
  ALL: "全部",
  POPULAR: "热门推荐",
  CHINESE: "中文资源",
  ENGLISH: "英文资源",
  RESEARCH: "研究数据",
  MULTIMODAL: "多模态",
};
const activeCategory = ref(categories.ALL);

function onTabClick(tab) {
  activeCategory.value = tab.name;
}

const filteredSites = computed(() => {
  let list = props.sites || [];
  const q = props.query ? props.query.trim().toLowerCase() : "";
  if (activeCategory.value && activeCategory.value !== categories.ALL) {
    list = list.filter((s) => (s.labels || []).some((l) => l.toLowerCase().includes(activeCategory.value.toLowerCase())));
  }
  if (q) {
    list = list.filter((s) => (s.name || "").toLowerCase().includes(q) || (s.description || "").toLowerCase().includes(q));
  }
  return list;
});
</script>

<style scoped>
.results-info {
  display: flex;
  align-items: center;
  justify-content: flex-start;
}
.skeleton-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 16px;
}
.skeleton-card {
  height: 180px;
  border-radius: 8px;
  background: linear-gradient(90deg, #f6f6f6 0%, #ededed 50%, #f6f6f6 100%);
  background-size: 200% 100%;
  animation: shimmer 1.2s linear infinite;
}
@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
.card-wrap{
  height:100%;
  display:flex;
}
.card-wrap > *{
  flex:1;
}
</style>


