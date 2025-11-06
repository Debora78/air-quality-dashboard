### Air Quality Dashboard (Flask proxy) - Backend
# Panoramica
Proxy Flask che interroga l’API upstream (api.zeroc.green), applica retry/backoff, salva l’ultimo payload valido in cache in memoria e normalizza il payload per il frontend. Espone endpoint come /api/stations/<station_id>.
# Tecnologie
- Python 3.10+
- Flask
- requests
- python-dotenv
- gunicorn (opzionale, produzione)
# Requisiti
- Python 3.10+
- pip
- (consigliato) virtualenv / venv
# Installazione e setup
- Entra nella cartella backend: cd backend
- Crea e attiva virtualenv: python -m venv .venv

### SISTEMI OPERATIVI
## Passi comuni
- Apri un terminale e posizionati nella cartella del backend: cd backend
- Crea l'ambiente virtuale (comando identico su tutte le piattaforme): python -m venv .venv
- Crea il file .env nella cartella backend con almeno queste variabili: API_BASE=https://api.zeroc.green/v1
FLASK_ENV=development
FLASK_APP=app.py
TIMEOUT=10
CACHE_TTL=3600
- Dopo l'attivazione dell'ambiente, installa le dipendenze: pip install -r requirements.txt
- Avvio (da eseguire dopo l'attivazione): flask run --host=127.0.0.1 --port=5000
oppure
python app.py

## Windows — PowerShell (raccomandato se usi la shell di sistema)
- Apri PowerShell e vai nella cartella backend: cd backend
- Se non l'hai già fatto, crea l'ambiente: python -m venv .venv
- Attiva l'ambiente: ..venv\Scripts\Activate.ps1
- Se PowerShell blocca l'esecuzione di script, abilita temporaneamente: Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass ..venv\Scripts\Activate.ps1
- Installa dipendenze e avvia: pip install -r requirements.txt
flask run --host=127.0.0.1 --port=5000
- Disattiva: deactivate

## Windows — Command Prompt (CMD)
- Apri CMD e vai in backend: cd backend
- Crea l'ambiente: python -m venv .venv
- Attiva l'ambiente: ..venv\Scripts\activate.bat
- Installa dipendenze e avvia: pip install -r requirements.txt
flask run --host=127.0.0.1 --port=5000
- Disattiva: deactivate

## Windows — Git Bash (se preferisci bash su Windows)
Nota: Git Bash fornisce una shell tipo Unix; l'attivazione del venv può richiedere comandi differenti rispetto a PowerShell/CMD. Procedura consigliata:
- Apri Git Bash e vai in backend: cd /c/percorsodeltuorepo/backend  (o usa il percorso Windows convertito)
- Crea l'ambiente (stesso comando): python -m venv .venv
- Prova ad attivare il venv in modalità bash: source .venv/bin/activate
- Se source non funziona o l'attivazione non attiva correttamente il PATH, apri PowerShell/CMD e usa i comandi di attivazione riportati sopra.
- Poi: pip install -r requirements.txt
flask run --host=127.0.0.1 --port=5000
- Disattiva: deactivate

## Windows — WSL (Windows Subsystem for Linux, se lo usi)
- Apri la tua distribuzione WSL (es. Ubuntu) e posizionati nella cartella del progetto (es. /mnt/c/…): cd /mnt/c/Users/TuoUtente/path/to/repo/backend
- Crea e attiva il venv come su Linux: python3 -m venv .venv
source .venv/bin/activate
- Installa dipendenze e avvia: pip install -r requirements.txt
flask run --host=127.0.0.1 --port=5000
- Disattiva: deactivate

## macOS (bash / zsh / fish)
- Apri Terminal.app (o iTerm2) e vai nella cartella backend: cd backend
- Crea l'ambiente: python3 -m venv .venv
- Attiva l'ambiente
    - bash / zsh: source .venv/bin/activate
    - fish: source .venv/bin/activate.fish
- Installa dipendenze: pip install -r requirements.txt
- Avvia: flask run --host=127.0.0.1 --port=5000
oppure
python app.py
- Disattiva: deactivate
Nota macOS: se il sistema ha sia python che python3, usa python3 per creare il venv; verifica la versione con python3 --version.

## Linux (bash / zsh / fish)
- Apri terminale e vai in backend: cd backend
- Crea l'ambiente: python3 -m venv .venv
- Attiva l'ambiente
    - bash / zsh: source .venv/bin/activate
    - fish: source .venv/bin/activate.fish
- Installa dipendenze e avvia: pip install -r requirements.txt
flask run --host=127.0.0.1 --port=5000
- Disattiva: deactivate

## Suggerimenti pratici
- Se usi macOS o Linux, preferisci python3 per chiarezza; su Windows spesso python è sufficiente.
- WSL fornisce esperienza Linux completa su Windows ed è l’opzione migliore se vuoi usare bash in modo nativo.
- Se Git Bash non attiva correttamente il venv, apri PowerShell/CMD per l’attivazione e poi torna a Git Bash per lavorare (dopo l’attivazione i PATH possono comunque non propagarsi).
- Dopo attivazione, i comandi pip install, flask run e python app.py sono gli stessi su tutte le piattaforme.
Se vuoi, aggiorno il file backend/README.md sostituendo la sezione di setup con questa versione pronta da incollare. Vuoi che lo faccia?


## Note pratiche e consigli
- Se usi Git Bash regolarmente e source .venv/bin/activate non funziona, preferisci PowerShell o CMD per attivare il venv; lo sviluppo continuerà normalmente dopo l'attivazione.
- WSL offre l'esperienza Linux completa su Windows ed è la scelta migliore se vuoi usare comandi bash nativi senza problemi di compatibilità.
- Dopo l'attivazione, i comandi pip install, flask run e python app.py sono identici su tutte le piattaforme.
- Non committare .env; usa file locali o secret manager in produzione.
- In produzione preferisci process manager (es. gunicorn su Linux/WSL) e un reverse proxy (nginx).

## Suggerimenti pratici
- Se usi macOS o Linux, preferisci python3 per chiarezza; su Windows spesso python è sufficiente.
- WSL fornisce esperienza Linux completa su Windows ed è l’opzione migliore se vuoi usare bash in modo nativo.
- Se Git Bash non attiva correttamente il venv, apri PowerShell/CMD per l’attivazione e poi torna a Git Bash per lavorare (dopo l’attivazione i PATH possono comunque non propagarsi).
- Dopo attivazione, i comandi pip install, flask run e python app.py sono gli stessi su tutte le piattaforme.







