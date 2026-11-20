// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },
  modules: ['@nuxt/ui'],
  css: ['~/assets/css/main.css'],
  runtimeConfig: {
    public: {
      // Backend base URL. Overridden in docker-compose.yml for the built app.
      apiBase: process.env.API_BASE_URL || 'http://localhost:8000',
    },
  },
})
