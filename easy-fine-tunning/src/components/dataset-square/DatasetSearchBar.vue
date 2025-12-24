<template>
  <div class="ds-search-bar" ref="root">
    <el-input
      v-model="query"
      :placeholder="$t('datasetSquare.searchPlaceholder')"
      clearable
      @clear="onClear"
      @keyup.enter.native="onSubmit"
      @keydown.native="onKeyDown"
      @input="onInput"
    >
      <template #prefix>
        <el-icon><i class="el-icon-search"></i></el-icon>
      </template>
    </el-input>

    <transition name="fade">
      <div v-if="showSuggestions && suggestions.length" class="suggestions">
        <ul>
          <li
            v-for="(s, i) in suggestions"
            :key="i"
            @click="onSuggestionClick(s)"
            :class="{ selected: i === selectedIndex }"
          >
            <div class="suggestion-left">
              <img
                v-if="!imgErrorMap[i] && (s.image || platformNameFrom(s.link))"
                :src="s.image ? s.image : (platformImageFrom(s.link) || '/imgs/default-dataset.png')"
                alt=""
                @error="() => onSuggestionImgError(i)"
              />
              <div v-else class="suggestion-fallback">{{ platformNameFrom(s.link) }}</div>
            </div>
            <div class="suggestion-body">
              <div class="s-name">{{ s.name }}</div>
              <div class="s-desc">{{ s.description }}</div>
            </div>
            <div class="s-action">→</div>
          </li>
        </ul>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, watch, computed } from "vue";
import { getPlatformNameFromLink, getPlatformImageFromLink } from "@/utils/platform";
const emit = defineEmits(["update:query", "search"]);
const props = defineProps({
  modelValue: { type: String, default: "" },
  sites: { type: Array, default: () => [] },
});

const query = ref(props.modelValue);
const showSuggestions = ref(false);

watch(
  () => props.modelValue,
  (v) => {
    query.value = v;
  }
);

watch(query, (val) => {
  emit("update:query", val);
  showSuggestions.value = !!val;
});

function onInput(val) {
  // already handled by v-model/watch
}

function onSubmit() {
  emit("search", query.value);
  showSuggestions.value = false;
  saveRecentSearch(query.value);
}

function onClear() {
  emit("update:query", "");
  emit("search", "");
  showSuggestions.value = false;
}

const suggestions = computed(() => {
  const q = (query.value || "").trim().toLowerCase();
  if (!q) return props.sites.slice(0, 5);
  return (props.sites || [])
    .filter((s) => (s.name || "").toLowerCase().includes(q) || (s.description || "").toLowerCase().includes(q))
    .slice(0, 5);
});

function buildSearchUrl(site, q) {
  if (!q) return site.link;
  const encoded = encodeURIComponent(q);
  if (site.link.includes("huggingface.co")) {
    return `${site.link}?sort=trending&search=${encoded}`;
  } else if (site.link.includes("kaggle.com")) {
    return `${site.link}?search=${encoded}`;
  } else if (site.link.includes("datasetsearch.research.google.com")) {
    return `${site.link}/search?query=${encoded}&src=0`;
  } else if (site.link.includes("paperswithcode.com")) {
    return `${site.link}?q=${encoded}`;
  } else if (site.link.includes("modelscope.cn")) {
    return `${site.link}?query=${encoded}`;
  } else {
    return `${site.link}${site.link.includes("?") ? "&" : "?"}search=${encoded}`;
  }
}

function onSuggestionClick(site) {
  if (!site) return;
  const url = buildSearchUrl(site, query.value);
  saveRecentSearch(query.value);
  window.open(url, "_blank");
  showSuggestions.value = false;
  emit("search", query.value);
}

// 最近搜索存储
function saveRecentSearch(q) {
  if (!q || !q.trim()) return;
  try {
    const key = "recentDatasetSearches";
    const existing = JSON.parse(localStorage.getItem(key) || "[]");
    const updated = [q, ...existing.filter((s) => s !== q)].slice(0, 5);
    localStorage.setItem(key, JSON.stringify(updated));
  } catch (e) {
    // ignore
  }
}

// 键盘导航
const selectedIndex = ref(-1);
function onKeyDown(e) {
  if (!suggestions.value || suggestions.value.length === 0) return;
  if (e.key === "ArrowDown") {
    selectedIndex.value = Math.min(selectedIndex.value + 1, suggestions.value.length - 1);
    e.preventDefault();
  } else if (e.key === "ArrowUp") {
    selectedIndex.value = Math.max(selectedIndex.value - 1, 0);
    e.preventDefault();
  } else if (e.key === "Enter") {
    if (selectedIndex.value >= 0 && selectedIndex.value < suggestions.value.length) {
      onSuggestionClick(suggestions.value[selectedIndex.value]);
      e.preventDefault();
    } else {
      onSubmit();
    }
  } else if (e.key === "Escape") {
    showSuggestions.value = false;
    selectedIndex.value = -1;
  }
}

// 图片错误映射，用于显示来源平台占位
const imgErrorMap = ref({});
function onSuggestionImgError(index) {
  imgErrorMap.value = { ...imgErrorMap.value, [index]: true };
}

const platformNameFrom = getPlatformNameFromLink;
const platformImageFrom = getPlatformImageFromLink;
</script>
 
<style scoped>
.ds-search-bar {
  position: relative;
  margin-bottom: 18px;
}
.suggestions {
  position: absolute;
  z-index: 2000;
  left: 0;
  right: 0;
  background: white;
  border: 1px solid #eee;
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.08);
  border-radius: 8px;
  margin-top: 8px;
  max-height: 320px;
  overflow: auto;
}
.suggestions ul {
  list-style: none;
  margin: 0;
  padding: 8px 0;
}
.suggestions li {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  cursor: pointer;
}
.suggestion-left img {
  width: 56px;
  height: 40px;
  object-fit: cover;
  border-radius: 6px;
}
.s-name {
  font-weight: 600;
}
.s-desc {
  font-size: 12px;
  color: #666;
  max-width: 420px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.s-action {
  margin-left: auto;
  color: #999;
}
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
.suggestions li.selected {
  background: #f0f6ff;
}
</style>


