// https://nuxt.com/docs/api/configuration/nuxt-config
// frontend/nuxt.config.ts
export default defineNuxtConfig({
  // base config minimal
  runtimeConfig: {
    public: {
      // ENDPOINT del backend; in produzione verrà sostituito con l'URL reale
      apiBase:
        import.meta.env.NUXT_PUBLIC_API_BASE || "http://localhost:5000/api",
    },
  },
});
