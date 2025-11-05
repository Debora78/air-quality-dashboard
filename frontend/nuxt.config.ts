// https://nuxt.com/docs/api/configuration/nuxt-config
// frontend/nuxt.config.ts
export default defineNuxtConfig({
  compatibilityDate: "2025-11-05",

  // base config minimal
  runtimeConfig: {
    public: {
      // ENDPOINT del backend; in produzione verrà sostituito con l'URL reale
      apiBase:
        import.meta.env.NUXT_PUBLIC_API_BASE || "http://localhost:5000/api",
    },
  },
});
// nuxt.config.ts: Configurazione principale di Nuxt. Definisce runtimeConfig con apiBase pubblico, che punta all'endpoint del backend. Usa variabile d'ambiente NUXT_PUBLIC_API_BASE se definita, altrimenti localhost per sviluppo locale.