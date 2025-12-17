import { defineStore } from 'pinia';

const THEME_KEY = 'app-theme';
const LOCALE_KEY = 'app-locale';

export const useAppStore = defineStore('app', {
  state: () => ({
    isDark: false,
    locale: 'zh',
  }),
  actions: {
    loadPrefs() {
      const savedTheme = localStorage.getItem(THEME_KEY);
      const savedLocale = localStorage.getItem(LOCALE_KEY);
      if (savedTheme) this.isDark = savedTheme === 'dark';
      if (savedLocale) this.locale = savedLocale;
    },
    setDark(value) {
      this.isDark = value;
      localStorage.setItem(THEME_KEY, value ? 'dark' : 'light');
      this.applyTheme();
    },
    applyTheme() {
      const html = document.documentElement;
      html.classList.toggle('dark', this.isDark);
      html.setAttribute('data-theme', this.isDark ? 'dark' : 'light');
    },
    setLocale(locale) {
      this.locale = locale;
      localStorage.setItem(LOCALE_KEY, locale);
    },
  },
});

