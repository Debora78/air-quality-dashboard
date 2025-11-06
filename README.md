# Air Quality Dashboard

## STRUTTURA DEL PROGETTO
air-quality-dashboard/
├─ backend/
│  ├─ app.py
│  ├─ requirements.txt
│  └─ .env.example
├─ frontend/
│  ├─ nuxt.config.ts
│  ├─ package.json
│  └─ (cartella Nuxt standard: pages, components, composables, assets, etc.)
├─ README.md
└─ .gitignore


## Breve descrizione
# Dashboard web per visualizzare dati sulla qualità dell’aria e condizioni meteo (PM10, PM2.5, NO2, SO2, O3, pioggia, vento, pressione). Frontend in Vue 3 + TypeScript; backend proxy in Flask che normalizza e protegge le chiamate all’API upstream (api.zeroc.green).
# Sommario
• 	Struttura del repository
• 	/frontend — codice dell’interfaccia (Vue 3, Vite, TypeScript)
• 	/backend — proxy API (Flask, Python)
# Requisiti globali
• 	Git
• 	Node.js v16+ (consigliato v18)
• 	npm / yarn / pnpm
• 	Python 3.10+
• 	pip
# Flusso dati
- Frontend → Backend (/api/...) → Upstream (https://api.zeroc.green/v1/...)
- Il backend applica retry, cache in memoria e fallback per stabilità.
# Quick start (panoramica)
- Clona il repository: git clone <repo-url>
- Apri due terminali:
- Terminale A: backend
- Terminale B: frontend
- Segui i README nelle rispettive cartelle:
- /backend/README.md
- /frontend/README.md
# Variabili d’ambiente (nota)
- Variabili specifiche sono descritte in ciascun README (frontend e backend). Non committare file .env in Git.
# Contribuire
- Apri issue per bug/feature.
- Segui convenzioni di codice e linters del progetto.
- Per deploy/prod, considera: usare Redis per cache persistente, gunicorn + nginx per il backend, e hosting statico (Netlify/Vercel) per il frontend.



