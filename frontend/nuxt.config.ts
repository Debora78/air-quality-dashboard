// Import dell'helper per definire la configurazione in Nuxt 4
import { defineNuxtConfig } from "nuxt/config";
import tsconfigPaths from "vite-tsconfig-paths";
import { resolve } from "path";

// Esporta la configurazione principale di Nuxt
export default defineNuxtConfig({
  // Aggiunge file CSS globali che verranno inclusi in ogni pagina.
  css: ["~/assets/css/station.css"],

  // Configurazioni specifiche per Vite (dev server)
  vite: {
    plugins: [tsconfigPaths()],
    resolve: {
      alias: {
        // Assicura che l'alias '~' e '@' puntino alla root del progetto come stringhe
        "~": resolve(process.cwd(), "."),
        "@": resolve(process.cwd(), "."),
      },
    },

    server: {
      proxy: {
        // In sviluppo inoltra tutte le richieste a /api verso il backend locale
        "/api": {
          target: "http://127.0.0.1:5000",
          changeOrigin: true,
          secure: false,
        },
      },
    },
  },

  // Configurazione Nitro per il devProxy: assicura che Nitro inoltri /api in dev
  nitro: {
    devProxy: {
      "/api": {
        target: "http://127.0.0.1:5000",
        changeOrigin: true,
        secure: false,
      },
    },
  },
});
