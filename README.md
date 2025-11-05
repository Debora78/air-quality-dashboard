# Air Quality Dashboard

Stack:
- Backend: Python 3.11, Flask
- Frontend: Nuxt 3, Node 18+

## Struttura
- backend/: Flask proxy e calcolo media ponderata
- frontend/: Nuxt 3 app (lista stazioni, dettaglio stazione)

## Variabili d'ambiente
- backend/.env:
  - API_BASE_URL (default https://api.zeroc.green/v1)
  - PORT (default 5000)
- frontend: NUXT_PUBLIC_API_BASE (es. http://localhost:5000/api)

## Avvio locale

### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# modificare .env se necessario
python app.py