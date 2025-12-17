import { createApp } from 'vue';
import { createPinia } from 'pinia';
import { VueQueryPlugin, QueryClient } from '@tanstack/vue-query';
import ElementPlus from 'element-plus';
import 'element-plus/dist/index.css';
import 'element-plus/theme-chalk/dark/css-vars.css';
import router from './router';
import i18n from './i18n';
import { useAppStore } from './stores/app';
import App from './App.vue';
import './style.css';

const app = createApp(App);

const pinia = createPinia();
const queryClient = new QueryClient();

app.use(pinia);
app.use(router);
app.use(i18n);
app.use(VueQueryPlugin, { queryClient });
app.use(ElementPlus);

const appStore = useAppStore();
appStore.applyTheme();
i18n.global.locale.value = appStore.locale;

app.mount('#app');
