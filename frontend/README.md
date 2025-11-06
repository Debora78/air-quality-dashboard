### Air Quality Dashboard - Frontend
# Panoramica
Interfaccia utente sviluppata con Vue 3 (Composition API) e TypeScript. Utilizza Vite per sviluppo e build. Consuma l’API esposta dal backend (VITE_API_BASE).
# Tecnologie
- Vue 3 (Composition API)
- TypeScript
- Vite
- Vue Router
- Pinia (opzionale)
- Axios o fetch (per chiamate)
- Tailwind CSS o CSS custom (opzionale)
# Requisiti
- Node.js v16+ (consigliato v18)
- npm / yarn / pnpm
# Installazione e esecuzione (sviluppo)
- Spostati nella cartella frontend: cd frontend
- Installa dipendenze: npm install (oppure yarn install / pnpm install)
- Configura variabili d’ambiente:
- Crea .env.local (non committarlo) e aggiungi: VITE_API_BASE=http://127.0.0.1:5000/api VITE_APP_TITLE="Air Quality Dashboard"
- Avvia il dev server: npm run dev
- Build produzione: npm run build
- Anteprima build (locale): npm run preview
# Comandi utili
- npm run dev — sviluppo (HMR)
- npm run build — build produzione
- npm run preview — serve build localmente
- npm run lint — linting (se configurato)
- npm run test — test (se configurato)
# Struttura proposta
- src/
- components/ — componenti riutilizzabili
- pages/ — pagine (stations list, station detail)
- composables/ — composables / hooks
- router/ — Vue Router
- store/ — Pinia / Vuex (opzionale)
- assets/, styles/
# Buone pratiche
- Imposta VITE_API_BASE per puntare al proxy backend in sviluppo.
- Usa DevTools → Network per confrontare payload con backend.
- Mostra un badge o banner quando i dati sono da cache o l’upstream è offline.
Dipendenze suggerite (esempi)
- vue, vue-router, vite, typescript, axios, pinia, tailwindcss (se usato)
- Dev: @vitejs/plugin-vue, vite-plugin-checker, eslint, prettier
Debug
- Controlla console e Network in DevTools.
- Se il backend restituisce 502/5xx, mostra messaggio user-friendly nel UI.







