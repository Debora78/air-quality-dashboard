# backend/app.py
"""
Flask proxy server for Air Quality Dashboard

Espone:
- GET /api/stations          -> proxy a {API_BASE_URL}/stations (ritorna body upstream)
- GET /api/stations/<id>    -> proxy a {API_BASE_URL}/stations/<id>
                               restituisce il JSON upstream arricchito con:
                               "weighted_average_7d": { <metric>: <value|null>, ... }

Weighted average rules:
- consideriamo i giorni forniti dall'upstream (si assume che contengano fino a 10 giorni)
- usiamo al massimo i 7 giorni più recenti con sample_size > 0
- weighted_avg = sum(average * sample_size) / sum(sample_size)
- se non ci sono giorni validi, il valore restituito è null (None in Python)

Il server:
- legge API_BASE_URL e PORT da environment (carica .env se presente)
- applica CORS su /api/* (origine '*' per semplicità in dev)
- risponde con JSON di errore in caso di problemi upstream o interni
"""

# todo Import Tecnici e funzionali
from __future__ import annotations  # -  Serve per: usare le annotazioni di tipo come stringhe che vengono valutate più tardi.
# Utile quando: hai riferimenti a classi che non sono ancora state definite (forward references) o vuoi evitare import circolari.

import os  # accesso a variabili d'ambiente e operazioni sul filesystem (path, join, etc.)
# - os.getenv("API_BASE") per leggere variabili da .env
# - os.path.join() per costruire path compatibili cross-platform

import requests  # libreria HTTP per fare richieste GET/POST verso API esterne - - Usato per: comunicare con https://api.zeroc.green


import logging  # modulo di logging di Python per registrare info, warning, errori e debug - usato per tracciare il comportamento dell’app e diagnosticare problemi.

import time  # funzioni relative al tempo (time(), sleep non bloccante esplicito, timestamp) - ottiene timestamp corrente

from time import sleep  # import esplicito di sleep per pause/backoff nelle retry (anche se non usato esplicitamente, può essere utile in futuro) - sleep(1) per fare una pausa di 1 secondo evitando sovraccarico API


# todo Tipi e Annotazioni
from typing import Any, Dict, List, Optional, Tuple  # tipi per le annotazioni: Any, Dict, List, Optional, Tuple - List[Dict[str, Any]] → lista di dizionari generici - - Optional[float] → valore che può essere float o None - Tuple[str, int] → coppia di stringa e intero

# todo Debug e Stampa
from pprint import pprint  # pretty-print per stampare oggetti Python in modo leggibile (utile in debug)- per controllare la struttura dei dati ricevuti

# todo Flash e CORS
#  ? Flask(è un micro-framework web per Python. Leggero e flessibile per creare API REST e app semplici e scalabili - gestisce: le route(/api/stations), riceve e risponde a richieste HTTP(GET, POST, PUT, DELETE) - permette di costruire API JSON e supporta estensioni come CORS, autenticazione, database, ecc.
# * CORS (Cross-Origin Resource Sharing) è un meccanismo che permette a un'app web di accedere a risorse da un dominio diverso. E' fondamentale quando il frontend e backend sono ospitati su domini diversi (es. localhost:3000 e localhost:5000 in sviluppo). Senza CORS, le richieste tra domini diversi verrebbero bloccate dal browser per motivi di sicurezza. CORS aggiunge instestazioni HTTP che autorizzano il frontend(Nuxt) a comunicare con il backend(Flash) -  evita errori come: Access-Control-Allow-Origin missing .

from flask import Flask, jsonify, request, Response, make_response  # Serve per costruire l'app web: - Flask(istanza dell'app) - jsonify(converte dict in JSON response) - request(gestisce richieste in entrata) - Response(per inoltrare una risposta HTTP ricevuta da API - oggetto risposta HTTP ) - make_response(costruisce risposte HTTP complesse personalizzate con intestazioni)

from flask_cors import CORS  # estensione per abilitare Cross Origin Resource Sharing (CORS)- evita errori CORS in sviluppo quando frontend e backend sono su domini diversi(porte differenti)

# todo Ambiente e Configurazione
from dotenv import load_dotenv  # carica variabili d'ambiente da file .env in sviluppo - tenere segreti e configurazioni fuori dal codice sorgente(es. API_BASE_URL, TIMEOUT)

# todo Retry e Gestione rete
from requests.adapters import HTTPAdapter, Retry  # componenti di requests per configurare retry(ripete la richiesta fino a un max di tentativi dichiarati) e adapter di sessione in caso di errori di rete ed evita crash se l'API esterna è temporaneamente non raggiungibile - Retry(per definire politiche di retry) - HTTPAdapter(per collegare la politica di retry alla sessione requests)


# L'oggetto Session mantiene connessioni aperte(più veloce), intestazioni comuni e configurazioni condivise(come i retry) - riutilizza le connessioni
session = requests.Session() # crea un oggetto session salvandolo nella variabile session
retries = Retry( # creo l'oggetto retry con parametri salvato nella variabile retries
    total=2, # n° massimo di tentativi (incluso il primo)
    backoff_factor=0.5, # tempo di attesa tra i tentativi (0.5s, 1s, 2s, ecc.)
    status_forcelist=[429, 502, 503, 504], # codici di stato HTTP che attivano il retry(es. 429 Too Many Requests, 502 Bad Gateway, 503 Service Unavailable, 504 Gateway Timeout(il server non ha ricevuto risposta in tempo da un altro server))
    allowed_methods=["GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS"] # metodi HTTP che possono essere ritentati
)
# HTTPAdapter gestisce le connessioni e applica la logica di retry che è stata definita quando ho creato l'oggetto retries
adapter = HTTPAdapter(max_retries=retries)# creo un oggetto adapter con la politica di retry
session.mount("https://", adapter)# collega l'adapter alla sessione per richieste HTTPS
session.mount("http://", adapter)# collega l'adapter alla sessione per richieste HTTP


# Load .env if present (carica variabili d'ambiente da file .env in sviluppo)
load_dotenv()

# la funzione os.getenv() legge le variabili d'ambiente e se non esiste usa il valore di default(secondo argomento)
API_BASE = os.getenv("API_BASE_URL", "https://api.zeroc.green/v1")
PORT = int(os.getenv("PORT", 5000)) # cerca la variabile PORT, se non esiste usa 5000
TIMEOUT = int(os.getenv("TIMEOUT", 20)) # cerca la variabile TIMEOUT, se non esiste usa 20 secondi

# Basic logging(utilizzato per tracciare il comportamento dell'app e diagnosticare problemi anche in ambienti di produzione)
logging.basicConfig(level=logging.INFO)#mostra solo i messaggi importanti: INFO, WARNING, ERROR, CRITICAL e ignora DEBUG
logger = logging.getLogger("backend")# creo l'oggetto logger con nome "backend" salvandolo nella variabile logger


app = Flask(__name__) # crea l'istanza dell'app Flask salvandola nella variabile app e __name__ indica dove si trova il modulo principale dell'app nel contesto di esecuzione corrente
# Allow cross-origin requests to /api/* (development convenience)
CORS(app, resources={r"/api/*": {"origins": "*"}})# abilita CORS per tutte le route che iniziano con /api/ permettendo richieste da qualsiasi origine (utile in sviluppo quando frontend e backend sono su domini/porte diverse)- r = raw string per evitare problemi con caratteri speciali(legge la stringa così com'è senza interpretare escape sequences)

# DEBUG TEMPORANEO: stampa tutte le route registrate (rimuovere dopo debug)
pprint([rule.rule for rule in app.url_map.iter_rules()])

# Logger semplice per i messaggi di debug
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def _safe_float(val: Any) -> Optional[float]: # funzione che prende un valore di qualsiasi tipo(val: Any) e tenta di convertirlo in float (-> Optional[float] indica che può restituire float o None)
    try:
        if val is None: 
            return None
        return float(val) # tenta di convertire val in float
    except (ValueError, TypeError): # cattura eccezioni se la conversione fallisce invece di far crashare l'app
        return None


def compute_weighted_average(days: List[Dict[str, Any]]) -> Optional[float]: # spiegata nel docstring sotto
    # docstring della funzione(spiega cosa fa la funzione, i parametri e il valore di ritorno) è una stringa speciale racchiusa tra triple virgolette che viene letta e interpretata da Python.
    """
    Calcola la media ponderata sui giorni forniti.

    - days: lista di dict che contengono almeno 'average' e 'sample_size' per giorno
      (possono anche contenere 'date', 'min', 'max', ecc.)
    - Si selezionano i giorni più recenti con sample_size > 0 fino a un massimo di 7 giorni utili.
      Si assume che l'array fornito dall'upstream sia ordinato dal più recente al meno recente.
      Se non lo fosse, questa funzione può essere adattata ricevendo giorni già ordinati.
    - Ritorna valore float arrotondato a 6 decimali oppure None se non ci sono giorni validi.
    """
    if not days: # se la lista days è vuota o None
        return None # ritorna None e termina la funzione

    # inizializzazione delle variabil
    weighted_sum = 0.0 # somma pesata degli average * sample_size
    total_samples = 0 # somma dei campioni validi
    considered = 0 # contatore dei giorni validi (massimo 7)

    # itera sui giorni forniti
    for day in days:
        if considered >= 7:
            break
        
        # estrai sample_size e average in modo robusto
        sample_size = day.get("sample_size", 0) or 0 # prende sample_size(se manca usa 0)
        
        avg = _safe_float(day.get("average")) # prende average e tenta di convertirlo in float in modo sicuro(usando la funzione _safe_float)
        
        # scarta i dati non validi
        if not sample_size or avg is None:  # ignoriamo giorni senza campioni o senza average
            continue
        
        # calcolo somma pesata e totale campioni   
        weighted_sum += avg * int(sample_size) #Aggiunge il contributo del giorno alla somma totale
        
        total_samples += int(sample_size) #Aggiunge il numero di campioni del giorno al totale
        
        considered += 1 # incrementa il contatore dei giorni validi
        
        
    # calcolo finale
    if total_samples == 0: # se non ci sono campioni validi
        return None # ritorna None

    # Risultato arrotondato a 6 decimali
    result = weighted_sum / total_samples # calcola la media pesata
   
    return round(result, 6)  # arrotondamento per stabilità e leggibilità in UI


# Duplichiamo la route che entrambe accettano richeiste HTTP di tipo GET di cui una ha il prefisso /api e l'altra no
#todo Si è registrato una route con prefisso /api e una senza per compatibilità in sviluppo poiché il devProxy può rimuovere il prefisso /api e se il backend ha solo la route con /api/stations, la richiesta a /stations darà 404 not found. Invece registrando entrambe le route si evita questo problema.
@app.route("/api/stations", methods=["GET"])
@app.route("/stations", methods=["GET"])

# * Proxy è un intermediario tra due sistemi che comunicano tra loro - ad esempio tra un client (browser) e un server (come il backend Flask). Proxy riceve una richiesta da un client, la inostra al server giusto, riceve la risposta e la rimanda al client.

#Questa funzione è un proxy: inoltra la richiesta al servizio upstream e ritorna la risposta
def get_stations():
    """
    Proxy semplice per l'elenco stazioni:
    - inoltra la GET a {API_BASE}/stations
    - ritorna esattamente il body upstream con lo stesso status e content-type quando possibile
    - in caso di errore upstream ritorna JSON con message e detail e status 502/appropriato
    """
   # costruzione upstream(fonte esterna da cui si ricevono i dati)(f" è una f-string che permette di inserire variabili direttamente nella stringa) 
    upstream = f"{API_BASE.rstrip('/')}/stations/" # il metodo rstrip('/') rimuove lo slash final da API_BASE per evitare doppio slash nell'URL finale quando aggiunge /stations/(es. https://api.zeroc.green//stations/)
    
    # headers è un dizionario che contiene le intestazioni HTTP da inviare con la richiesta(Le intestazioni sono informazioni aggiuntive che il client(backend) manda al server per specificare come vuole comunicare)
    headers = {"Accept": "application/json"}# "Accept" (è un'intestazione standar HTTP)- "application/json" indica che il client vuole ricevere la risposta in formato JSON
    
    try:
        # r è una variabile che contiene la risposta HTTP ricevuta dall'upstream usata come abbreviazione di "response"
        # - Invia una richiesta GET all’URL upstream
        # - Usa intestazioni (Accept: application/json)
        # - Imposta un timeout massimo (TIMEOUT)
        # - Permette i redirect (allow_redirects=True)
        r = session.get(upstream, headers=headers, timeout=TIMEOUT, allow_redirects=True)

        
        r.raise_for_status() # Solleva eccezione in caso di status code >= 400 gestendo gli errori nel blocco except

        
        content_type = r.headers.get("Content-Type", "application/json") # Recupera il tipo di contenuto dalla risposta upstream, se non presente usa "application/json" come default
        
        return Response(r.content, status=r.status_code, content_type=content_type) # Restituisce la risposta originale al client - Mantiene il corpo (r.content), lo status e il content-type
    
    
    
    except requests.exceptions.Timeout:
        logger.error("Network timeout contacting upstream /stations") # Registra un errore nel log: timeout di rete
        
        return jsonify({"message": "Upstream timeout", "detail": "Timeout contacting upstream service"}), 504 # Ritorna JSON di errore con status 504 (Gateway Timeout) - usa lo status originale dell'errore
    
    
    except requests.exceptions.HTTPError as e:
        status = getattr(e.response, "status_code", 502) # getattr(e.response è l'oggetto, "status_code" è il nome dell'attributo come stringa, 502 è il valore di default) è la funzione built-in di Python che recupera l'attributo di un oggetto in modo sicuro e dinamico evitando errori se l'attributo non esiste.
        
        
        try: # prova a leggere il dettaglio dell'errore come JSON
            detail = e.response.json()# la variabile detail viene usata per catturare e descrivere il contenuto dell'errore che arriva da l'upstream, quando qualcosa va storto nella richiesta HTTP.
            
        except Exception:
            detail = e.response.text or str(e)# e il  fallisce (es. perché la risposta non è JSON), prova a leggere il testo grezzo - Se anche quello non c’è, usa la stringa dell’eccezione come fallback
            
        logger.error("Upstream HTTP error on /stations: %s", detail) # Registra l'errore HTTP nel log con il dettaglio
        
        return jsonify({"message": "Upstream returned error", "detail": detail}), status # Restituisce un JSON al client con: - message: messaggio generico - detail: dettaglio specifico dell'errore - status: codice di stato HTTP originale dell'errore
    
    except requests.exceptions.RequestException as e:
        logger.error("Network error contacting upstream /stations: %s", str(e)) # Registra errori di rete generici nel log(es. DNS, connessione rifiutata, ecc.)
        
        return jsonify({"message": "Errore contattando il servizio upstream", "detail": str(e)}), 502 # Ritorna JSON con messaggio e dettaglio dell'errore con status 502 (Bad Gateway)


# Duplichiamo la route che entrambe accettano richeiste HTTP di tipo GET di cui una ha il prefisso /api e l'altra no
#todo Si è registrato una route con prefisso /api e una senza per compatibilità in sviluppo poiché il devProxy può rimuovere il prefisso /api e se il backend ha solo la route con /api/stations, la richiesta a /stations darà 404 not found. Invece registrando entrambe le route si evita questo problema.

#?FLUSSO FRONTEND-BACKEND:
#*È la rotta @app.route("/stations/<station_id>, methods=["GET"]) che Flask intercetta quando il frontend invia una richiesta HTTP, tipicamente in seguito al click dell’utente. Il parametro dinamico <station_id> viene estratto dalla URL e passato alla funzione <get_station_detail>, che restituisce i dati richiesti. Il frontend riceve la risposta e mostra il dettaglio della stazione corrispondente.
#? FLUSSO COMPLETO:
# - L’utente clicca su una stazione nel frontend
# - Il frontend invia una richiesta HTTP a /stations/A123
# - Flask intercetta la rotta /stations/<station_id>
# - Chiama get_station_detail("A123")
# - La funzione costruisce l’URL upstream, ottiene i dati, li elabora
# - Restituisce un JSON al frontend
# - Il frontend mostra il dettaglio della stazione



@app.route("/api/stations/<station_id>", methods=["GET"])
@app.route("/stations/<station_id>", methods=["GET"])
def get_station_detail(station_id: str):# def get_station_detail è il nome della funzione, (station_id è il parametro di input che rappresenta l'ID della stazione da recuperare, : str indica il tipo(una stringa)
    """
    Proxy per dettaglio stazione:
    - richiama upstream /stations/<id>
    - estrae metrics[*].data_points (forma upstream reale) e calcola weighted_average_7d per ciascuna metrica
    - ritorna JSON arricchito con weighted_average_7d
    """
    # Costruzione dell'URL upstream senza trailing slash per evitare redirect indesiderati
    upstream = f"{API_BASE.rstrip('/')}/stations/{station_id}"
    # Header che chiedono al server upstream di restituire JSON quando possibile
    headers = {"Accept": "application/json"}

    # Blocco try/except per gestire errori di rete e parsing JSON in modo robusto
    try:
        # Richiesta HTTP verso l'upstream usando la sessione (con retry configurati altrove)
        r = session.get(upstream, headers=headers, timeout=TIMEOUT, allow_redirects=True)
        
        
        r.raise_for_status() # Solleva eccezione in caso di status code >= 400
        
        data = r.json() # serve per estrarre i dati JSON dalla risposta HTTP, solo dopo aver verificato che la risposta sia valida.
        
    except requests.exceptions.Timeout:
        # Gestione timeout di rete: log e ritorno 504 (Gateway Timeout)
        logger.error("Network timeout contacting upstream /stations/%s", station_id) # %s è un segnaposto per inserire la variabile station_id nel messaggio di log
        
        return jsonify({"message": "Upstream timeout", "detail": "Timeout contacting upstream service"}), 504
    
    except requests.exceptions.HTTPError as e:
        # Gestione errori HTTP ritornati dall'upstream (es. 404, 500)
        status = getattr(e.response, "status_code", 502)  # fallback 502 se non disponibile
        try:
            # Proviamo a restituire il JSON di dettaglio se presente nella risposta di errore
            detail = e.response.json()
            
        except Exception:
            # Se non è JSON, prendiamo il testo grezzo o la rappresentazione dell'eccezione
            detail = e.response.text or str(e)
            
        logger.error("Upstream HTTP error on /stations/%s: %s", station_id, detail) # %s: %s sono segnaposto per inserire variabili che saranno sostituiti con station_id e detail nel messaggio di log(valori dopo la virgola)
        
        return jsonify({"message": "Upstream returned error", "detail": detail}), status
    
    except requests.exceptions.RequestException as e:
        # Gestione di altri errori della libreria requests (DNS, connessione rifiutata, ecc.)
        logger.error("Network error contacting upstream /stations/%s: %s", station_id, str(e))
        
        return jsonify({"message": "Errore contattando il servizio upstream", "detail": str(e)}), 502
    
    except ValueError as e:
        # Gestione di JSON non valido ricevuto dall'upstream
        logger.error("Invalid JSON from upstream for station %s: %s", station_id, str(e))
        
        return jsonify({"message": "Invalid JSON from upstream", "detail": str(e)}), 502

    # Inizializziamo un contenitore chiamato metrics_container che raccoglie le metriche disponibili, associando ogni nome alla metria della sua lista di punti giornalieri
    metrics_container: Dict[str, List[Dict[str, Any]]] = {} #crea un dizionario vuoto dove le chiavi sono stringhe (nomi delle metriche) e i valori sono liste di dizionari (punti giornalieri)

    if isinstance(data, dict): # controlla se data è un dizionario e se non lo è salta l'elaborazione
       
        if "metrics" in data and isinstance(data["metrics"], list): # controlla se esiste la chiave "metrics" e se è una lista
           
            for m in data["metrics"]:  # Iteriamo ogni elemento della lista metrics 
                
                name = m.get("name") or m.get("metric") or "unknown" # prova a prendere il valore della chiave "name", se non esiste prova "metric", altrimenti usa "unknown" come nome di default(chiave  e valore sono dati dal json upstream)
                
                points = m.get("data_points") or m.get("days") or [] # prova a prendere il valore della chiave "data_points", se non esiste prova "days", altrimenti usa una lista vuota come default
                
                if isinstance(points, list): #Verifica che points sia effettivamente una lista prima di aggiungerla al contenitore
                    metrics_container[name] = points # Se points è una lista valida, la salva nel dizionario metrics_container. La chiave è "name" (il nome della metrica, es. PM10) e il valore "points" (la lista di punti giornalieri)
        else:

            for k, v in data.items(): # k è la chiave(es. PM10) e v è il valore associato (può essere una lista di dict o un dict) - data.items() restituisce tutte le coppie chiave-valore del dizionario data
                
                if isinstance(v, list) and v and isinstance(v[0], dict): # Verifica che v sia una lista, che non sia vuota e che il primo elemento sia un dizionario
                    sample = v[0] # v è la lista di misurazioni - sample è il primo elemento di quella lista usato per capire se contiene dati utili(es. average, sample_size, min, max)
                    
                    if "average" in sample or "sample_size" in sample or ("min" in sample and "max" in sample): # Se questo dizionario (v) contiene "average"(valore medio), oppure "sample_size"(quanti campioni sono stati raccolti - proprietà di ogni singola misurazione), oppure sia "min" che "max"(valori minimi e massimi) allora considera v come una lista di metriche valide e lo salva in metrics_container
                        
                        metrics_container[k] = v # in metrics_container viene salvato v con chiave k (nome della metrica)
                        
               
                if v and isinstance(v, dict): # Se v esiste (quindi non è None o vuoto) ed è un dizionario(escludendo liste o altri tipi di dati)
                    nested = v.get("data_points") or v.get("days") # cerca all'interno di v una delle due chiavi: "data_points" ( lista di misurazioni)o "days" (alternativa usata da alcune API) e se trova una delle due, la salva in nested
                    
                    if isinstance(nested, list): # Verifica che nested sia effettivamente una lista e se sì è una lista di dati giornalieri validi
                        
                        metrics_container[k] = nested # Salva la lista nested nel dizionario metrics_container con chiave k (cioè il nome della metrica)

    # Ora calcoliamo la media pesata (weighted average) per ciascuna metrica trovata
    weighted_map: Dict[str, Optional[float]] = {} #Crea un dizionario vuoto, le chiavi sono stringhe(nomi delle metriche), i valori sono float(media pesata) o None se il calcolo fallisce
    
    for metric_name, days in metrics_container.items(): #itera ogni metrica nel metrics_container - metric_name è il nome della metrica - days è la lista dei dati giornalieri associati
        
        try:
           
            wa = compute_weighted_average(days) # Prova a calcolare la media pesata usando la funzione compute_weighted_average e passa la lista days come input
            
        except Exception as e: # - Se la funzione compute_weighted_average(days) genera un errore (es. dati mancanti, tipo errato…), si entra qui

           
            logger.exception("Error computing weighted average for %s: %s", metric_name, e) # Registra l’errore nel log con un messaggio dettagliato - Include il nome della metrica (metric_name) e l’eccezione (e) utile per il debug senza interrompere il programma
            
            wa = None # Imposta "wa" a None  per indicare che non è stato possibile calcolare la media
            
        weighted_map[metric_name] = wa # Salva comunque un valore nella mappa finale weighted_map anche se è None, così il dizionario resta completo e coerente
        

    # Restituire al client una risposta JSON che include i dati originali ricevuti dall’upstream (es. da un’API esterna)e aggiunge la media pesata calcolata (weighted_map) sotto la chiave "weighted_average_7d"
    
    if isinstance(data, dict): #Se data è un dizionario (es. {"metrics":[...], "location": "Montecatini"}) 
        
       
        data["weighted_average_7d"] = weighted_map # aggiunge una nuova chiave "weighted_average_7d" con il valore weighted_map
       
        return jsonify(data), r.status_code # restituisce il dizionario aggiornato come JSON (jsonify(data) converte il dizionario Python data in formato JSON che il formato standard delle API REST), r.stutus_code mantiene lo stesso status code della risposta originale ricevuto dalla risposta upstream(r) ad es: 200->OK, 404-> Not found, ecc..
    
    else:
        #Se la risposta ricevuta dall’upstream (es. da un’API esterna) non è un dizionario,allora la wrappiamo (cioè la incapsuliamo) in un nuovo dizionari
        return jsonify({ #crea un nuovo dizionario con 2 chiavi: 
                        # "data" -> contiene i dati originali(es. la lista ricevuta) - "weoghted_average_7d" -> contiene la mappa delle medie pesate - converte tutto in JSON con "jsonify(...)"

            "data": data,
            "weighted_average_7d": weighted_map
        }), r.status_code # restituisce la risposta con lo stesso status code ricevuto da "r.status_code"


if __name__ == "__main__": # se si esegue direttamente il file (python app.py e parte il server Flash) __name__ sarà __main__ e il blocco di codice viene eseguito( invece se viene importato da un altro ad es. import app non parte da solo) __name__ sarà "app"(cioè il nome del file) e il blocco di codice non viene eseguito
    
    logger.info("Starting backend proxy on port %s (API_BASE=%s)", PORT, API_BASE) #Scrive un messaggio nel "log" per dire che l'app sta partendo - mostra la porta su cui gira il server(PORT) - l'API_BASE -> l'indirizzo dell'API esterna da cui prende i dati
    
   
    app.run(host="0.0.0.0", port=PORT, debug=True) # Aviva il server Flash con questi parametri: - host="0.0.0.0"->accetta connessioni da qualsiasi IP, non solo da localhost,           - port=PORT->usa la porta specificata (es. 5000, 8080),       - debug=True->attiva il debug mode: Ricarica automatica del server quando modichi il codice, mostra errori dettagliati in caso di crash(in produzione è da disattivare per motivi di sicurezza)
    
""" - Uso di Response per /api/stations: mantiene esattamente il body e content-type dell'upstream; utile se upstream ritorna payload con struttura particolare o headers importanti. Nel dettaglio stazione si usa jsonify perché modifichiamo il JSON.
- compute_weighted_average: più robusta verso input non validi (conversione sicura, ignorare giorni senza average o sample_size).
- Logging per capire velocemente errori in sviluppo.
- CORS abilitato su /api/* (utile in sviluppo; in produzione limitare origini).
- Timeout configurabile per richieste upstream."""