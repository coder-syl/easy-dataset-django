<template>
  <el-card class="site-card ed-card" :body-style="{ padding: '10px 14px' }" shadow="hover">
    <div class="card-layout">
      <div class="thumb" ref="imgWrap">
        <img
          v-if="currentSrc"
          ref="imgEl"
          class="thumb-img"
          :src="currentSrc"
          :alt="site.name"
          @error="onImgError"
        />
        <div v-else class="thumb-placeholder">
          <i class="el-icon-picture" style="font-size:36px;color:#cbdaf7;"></i>
        </div>
      </div>

      <div class="card-body">
        <div class="card-title-row">
          <h3 class="card-title ed-title">{{ site.name }}</h3>
          <i class="el-icon-link card-external" @click="openLink" title="Open"></i>
        </div>

        <p class="card-desc">{{ site.description }}</p>

        <div class="card-footer">
          <div class="card-tags">
            <span v-for="(l, i) in visibleTags" :key="i" class="ed-tag">{{ l }}</span>
            <span v-if="extraTagsCount > 0" class="ed-tag">+{{ extraTagsCount }}</span>
          </div>
          <button class="ed-btn" @click="openLink">查看数据集</button>
        </div>
      </div>
    </div>
  </el-card>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from "vue";
import { getPlatformImageFromLink } from "@/utils/platform";

const props = defineProps({
  site: { type: Object, required: true },
});

const imageError = ref(false);
function onImgError() {
  imageError.value = true;
  currentSrc.value = '/imgs/default-dataset.png';
}

const platformImg = computed(() => getPlatformImageFromLink(props.site.link) || '');
const preferredSrc = computed(() => (props.site.image && props.site.image.trim()) || platformImg.value || '/imgs/default-dataset.png');

// lazy loading
const imgEl = ref(null);
const imgWrap = ref(null);
const currentSrc = ref('');
let observer = null;

function loadImage() {
  if (currentSrc.value) return;
  currentSrc.value = preferredSrc.value;
}

onMounted(() => {
  // IntersectionObserver for lazy load
  try {
    observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          loadImage();
          if (observer) {
            observer.disconnect();
            observer = null;
          }
        }
      });
    }, { rootMargin: '200px' });
    if (imgWrap.value) observer.observe(imgWrap.value);
  } catch (e) {
    // fallback: load immediately
    loadImage();
  }
});

onUnmounted(() => {
  if (observer) observer.disconnect();
});

function openLink() {
  window.open(props.site.link, "_blank");
}

// 标签显示限制（最多2个，其余显示 +N）
const visibleTags = computed(() => (props.site.labels || []).slice(0, 2));
const extraTagsCount = computed(() => Math.max(0, (props.site.labels || []).length - visibleTags.value.length));
</script>

<style scoped>
.site-inner {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}
.site-image-wrap{
  width:160px;
  height:100px;
  flex: 0 0 160px;
  display:flex;
  align-items:center;
  justify-content:center;
  background:#fbfdff;
  border-radius:8px;
  border:1px solid rgba(43,79,162,0.06);
}
.site-image {
  width: 160px;
  height: 100px;
  object-fit: cover;
  border-radius: 6px;
}
.site-image-placeholder{
  width:100%;
  height:100%;
  display:flex;
  align-items:center;
  justify-content:center;
  color:#2b65ff;
}
.site-body {
  flex: 1;
}
.site-head{
  display:flex;
  justify-content:space-between;
  align-items:center;
  gap:12px;
  margin-bottom:6px;
}
.site-title{
  font-size:18px;
  font-weight:700;
  color:#222;
}
.desc {
  color: #666;
  margin: 6px 0;
  max-height: 48px;
  overflow: hidden;
}
.tags {
  margin-top: 8px;
}
.site-actions {
  display: flex;
  align-items: center;
}
.site-card{
  border-radius:10px;
  display:flex;
  flex-direction:column;
  height:100%;
}
.card-layout{
  display:flex;
  flex-direction:column;
  flex:1;
}
.thumb{
  width:100%;
  height:160px;
  overflow:hidden;
  border-radius:8px;
  background:linear-gradient(180deg, rgba(0,0,0,0.02), rgba(0,0,0,0.04));
  display:flex;
  align-items:center;
  justify-content:center;
}
.thumb-img{
  width:100%;
  height:100%;
  object-fit:cover;
  border-radius:8px;
  box-shadow: inset 0 -30px 40px rgba(0,0,0,0.15);
}
.thumb-placeholder{
  width:100%;
  height:100%;
  display:flex;
  align-items:center;
  justify-content:center;
}
.card-body{
  padding:14px 6px 6px 6px;
  display:flex;
  flex-direction:column;
  flex:1;
}
.card-title-row{
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:8px;
}
.card-title{
  margin:0;
  font-size:18px;
  font-weight:800;
  color:#0f172a;
}
.card-external{
  color:#3b82f6;
  font-size:18px;
  cursor:pointer;
}
.card-desc{
  color:#6b7280;
  margin:8px 0 12px 0;
  line-height:1.6;
  max-height:72px;
  overflow:hidden;
}
.card-footer{
  display:flex;
  align-items:center;
  justify-content:space-between;
  margin-top:auto;
  gap:12px;
}
.card-tags{
  display:flex;
  gap:8px;
  align-items:center;
  flex:1;
  min-width:0;
  overflow:hidden;
}
.card-tags ::v-deep .el-tag{
  white-space:nowrap;
  text-overflow:ellipsis;
  overflow:hidden;
}
.view-btn{
  flex:0 0 auto;
  border-radius:8px;
}
.view-btn.outline{
  background:#fff;
  color:#2563eb;
  border:1px solid #cfe0ff;
  box-shadow:none;
}
.view-btn.outline:hover{
  background:#f6fbff;
}
</style>


