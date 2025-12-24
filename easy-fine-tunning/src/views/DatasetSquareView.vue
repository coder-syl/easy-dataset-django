<template>
  <div class="dataset-square-view">
    <!-- Hero header -->
    <div class="hero">
      <div class="hero-inner">
        <div class="hero-icon">📚</div>
        <h1 class="hero-title">{{ $t('datasetSquare.title') }}</h1>
        <p class="hero-sub">{{ $t('datasetSquare.subtitle') }}</p>

        <div class="hero-search">
          <DatasetSearchBar v-model="query" :sites="sites" @search="onSearch" />
        </div>
      </div>
    </div>

    <div class="container-card">
      <el-card>
        <DatasetSiteList :sites="sites" :query="query" :loading="loading" />
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { fetchSites } from "@/api/datasetSquare";
import DatasetSearchBar from "@/components/dataset-square/DatasetSearchBar.vue";
import DatasetSiteList from "@/components/dataset-square/DatasetSiteList.vue";

const sites = ref([]);
const query = ref("");
const loading = ref(true);

async function loadSites() {
  loading.value = true;
  try {
    const resp = await fetchSites();
    sites.value = resp || [];
  } catch (e) {
    console.error("加载站点失败", e);
    sites.value = [];
  } finally {
    // 保持短暂的骨架效果
    setTimeout(() => {
      loading.value = false;
    }, 300);
  }
}

function onSearch(q) {
  // 记录历史搜索或统计（可扩展）
  console.log("搜索:", q);
}

onMounted(() => {
  loadSites();
});
</script>

<style scoped>
.dataset-square-view {
  padding: 20px;
}
.hero{
  background: linear-gradient(135deg,#3b82f6 0%, #60a5fa 60%);
  color: white;
  padding: 56px 20px;
  border-radius: 8px;
  margin-bottom: 20px;
}
.hero-inner{
  max-width: 1100px;
  margin: 0 auto;
  text-align: center;
}
.hero-icon{
  font-size: 36px;
  margin-bottom: 12px;
}
.hero-title{
  margin: 0;
  font-size: 32px;
  font-weight: 700;
  margin-bottom: 8px;
}
.hero-sub{
  margin: 0;
  margin-bottom: 18px;
  opacity: 0.95;
}
.hero-search{
  max-width: 800px;
  margin: 0 auto;
}
.container-card{
  max-width: 1200px;
  margin: 0 auto;
}
</style>

