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
from __future__ import annotations  # abilita l'uso di annotation come stringhe valutate in seguito; utile per tipi forward e per migliorare le annotazioni senza import circolari
import os  # accesso a variabili d'ambiente e operazioni sul filesystem (path, join, etc.)
import requests  # libreria HTTP per fare richieste GET/POST verso API esterne
import logging  # modulo di logging di Python per registrare info, warning, errori e debug
import time  # funzioni relative al tempo (time(), sleep non bloccante esplicito, timestamp)
from time import sleep  # import esplicito di sleep per pause/backoff nelle retry
from typing import Tuple  # tipo generico Tuple per annotazioni (nota: import duplicato più sotto)
from typing import Any, Dict, List, Optional, Tuple  # tipi per le annotazioni: Any, Dict, List, Optional, Tuple
from pprint import pprint  # pretty-print per stampare oggetti Python in modo leggibile (utile in debug)
from flask import make_response  # helper Flask per costruire manualmente Response con corpo e intestazioni
from flask import Flask, jsonify, request, Response  # Flask core: app, helper JSON, oggetto request e tipo Response
from flask_cors import CORS  # estensione per abilitare Cross Origin Resource Sharing (CORS)
from dotenv import load_dotenv  # carica variabili d'ambiente da file .env in sviluppo
from requests.adapters import HTTPAdapter, Retry  # componenti di requests per configurare retry e adapter di sessione


# sessione requests con retry per ridurre l'impatto di errori temporanei upstream
session = requests.Session()
retries = Retry(
    total=2,
    backoff_factor=0.5,
    status_forcelist=[429, 502, 503, 504],
    allowed_methods=["GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS"]
)
adapter = HTTPAdapter(max_retries=retries)
session.mount("https://", adapter)
session.mount("http://", adapter)
# Load .env if present
load_dotenv()

API_BASE = os.getenv("API_BASE_URL", "https://api.zeroc.green/v1")
PORT = int(os.getenv("PORT", 5000))
TIMEOUT = int(os.getenv("TIMEOUT", 20))

# Basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backend")

app = Flask(__name__)
# Allow cross-origin requests to /api/* (development convenience)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# DEBUG TEMPORANEO: stampa tutte le route registrate (rimuovere dopo debug)
pprint([rule.rule for rule in app.url_map.iter_rules()])

# Logger semplice per i messaggi di debug
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def _safe_float(val: Any) -> Optional[float]:
    try:
        if val is None:
            return None
        return float(val)
    except (ValueError, TypeError):
        return None


def compute_weighted_average(days: List[Dict[str, Any]]) -> Optional[float]:
    """
    Calcola la media ponderata sui giorni forniti.

    - days: lista di dict che contengono almeno 'average' e 'sample_size' per giorno
      (possono anche contenere 'date', 'min', 'max', ecc.)
    - Si selezionano i giorni più recenti con sample_size > 0 fino a un massimo di 7 giorni utili.
      Si assume che l'array fornito dall'upstream sia ordinato dal più recente al meno recente.
      Se non lo fosse, questa funzione può essere adattata ricevendo giorni già ordinati.
    - Ritorna valore float arrotondato a 6 decimali oppure None se non ci sono giorni validi.
    """
    if not days:
        return None

    weighted_sum = 0.0
    total_samples = 0
    considered = 0

    for day in days:
        if considered >= 7:
            break
        # estrai sample_size e average in modo robusto
        sample_size = day.get("sample_size", 0) or 0
        avg = _safe_float(day.get("average"))
        if not sample_size or avg is None:
            # ignoriamo giorni senza campioni o senza average
            continue
        weighted_sum += avg * int(sample_size)
        total_samples += int(sample_size)
        considered += 1

    if total_samples == 0:
        return None

    result = weighted_sum / total_samples
    # arrotondamento per stabilità e leggibilità in UI
    return round(result, 6)

# Compatibilità sviluppo: registriamo la stessa route sia con il prefisso /api
# che senza prefisso perché il dev server (devProxy) durante lo sviluppo può
# inoltrare le richieste rimuovendo il prefisso /api. Mantenere entrambe evita
# 404 locali e permette di testare l'app senza modificare la configurazione
# del proxy. Rimuovere la route senza /api quando la configurazione di proxy
# sarà allineata o in produzione.


@app.route("/api/stations", methods=["GET"])
@app.route("/stations", methods=["GET"])
def get_stations():
    """
    Proxy semplice per l'elenco stazioni:
    - inoltra la GET a {API_BASE}/stations
    - ritorna esattamente il body upstream con lo stesso status e content-type quando possibile
    - in caso di errore upstream ritorna JSON con message e detail e status 502/appropriato
    """
   # costruzione upstream con trailing slash
    upstream = f"{API_BASE.rstrip('/')}/stations/"
    headers = {"Accept": "application/json"}
    try:
        r = session.get(upstream, headers=headers, timeout=TIMEOUT, allow_redirects=True)
        r.raise_for_status()
        # mantiene content-type e body originali quando è JSON o altro
        content_type = r.headers.get("Content-Type", "application/json")
        return Response(r.content, status=r.status_code, content_type=content_type)
    except requests.exceptions.Timeout:
        logger.error("Network timeout contacting upstream /stations")
        return jsonify({"message": "Upstream timeout", "detail": "Timeout contacting upstream service"}), 504
    except requests.exceptions.HTTPError as e:
        status = getattr(e.response, "status_code", 502)
        try:
            detail = e.response.json()
        except Exception:
            detail = e.response.text or str(e)
        logger.error("Upstream HTTP error on /stations: %s", detail)
        return jsonify({"message": "Upstream returned error", "detail": detail}), status
    except requests.exceptions.RequestException as e:
        logger.error("Network error contacting upstream /stations: %s", str(e))
        return jsonify({"message": "Errore contattando il servizio upstream", "detail": str(e)}), 502


# Compatibilità sviluppo: duplichiamo la route del dettaglio per lo stesso motivo
# spiegato sopra. La seconda decorator risponde a /stations/<id> quando il devProxy
# rimuove il prefisso /api.

@app.route("/api/stations/<station_id>", methods=["GET"])
@app.route("/stations/<station_id>", methods=["GET"])
def get_station_detail(station_id: str):
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
        # Solleva eccezione in caso di status code 4xx/5xx
        r.raise_for_status()
        # Parsifica il corpo della risposta come JSON; può sollevare ValueError se non è JSON valido
        data = r.json()
    except requests.exceptions.Timeout:
        # Gestione timeout di rete: log e ritorno 504 (Gateway Timeout)
        logger.error("Network timeout contacting upstream /stations/%s", station_id)
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
        logger.error("Upstream HTTP error on /stations/%s: %s", station_id, detail)
        return jsonify({"message": "Upstream returned error", "detail": detail}), status
    except requests.exceptions.RequestException as e:
        # Gestione di altri errori della libreria requests (DNS, connessione rifiutata, ecc.)
        logger.error("Network error contacting upstream /stations/%s: %s", station_id, str(e))
        return jsonify({"message": "Errore contattando il servizio upstream", "detail": str(e)}), 502
    except ValueError as e:
        # Gestione di JSON non valido ricevuto dall'upstream
        logger.error("Invalid JSON from upstream for station %s: %s", station_id, str(e))
        return jsonify({"message": "Invalid JSON from upstream", "detail": str(e)}), 502

    # Inizializziamo un contenitore che mappa nome_metrica -> lista di giorni (ogni giorno è dict)
    metrics_container: Dict[str, List[Dict[str, Any]]] = {}

    # Se il payload upstream è un oggetto/dizionario (forma attesa)
    if isinstance(data, dict):
        # Caso tipico: data["metrics"] è una LISTA di oggetti del tipo { name, data_points: [...] }
        if "metrics" in data and isinstance(data["metrics"], list):
            # Iteriamo ogni elemento della lista metrics
            for m in data["metrics"]:
                # Determiniamo il nome della metrica con vari fallback (name, metric, 'unknown')
                name = m.get("name") or m.get("metric") or "unknown"
                # Estraiamo i punti giornalieri: preferiamo data_points poi days poi una lista vuota
                points = m.get("data_points") or m.get("days") or []
                # Se points è una lista la consideriamo valide e la aggiungiamo al container
                if isinstance(points, list):
                    metrics_container[name] = points
        else:
            # Fallback generale: cerchiamo in tutto l'oggetto chiavi che contengono liste di dict plausibili
            for k, v in data.items():
                # Se v è una lista e il primo elemento è un dict, potrebbe essere una serie giornaliera
                if isinstance(v, list) and v and isinstance(v[0], dict):
                    sample = v[0]
                    # Consideriamo questa lista se il sample contiene chiavi tipiche: average o sample_size o min+max
                    if "average" in sample or "sample_size" in sample or ("min" in sample and "max" in sample):
                        metrics_container[k] = v
                # Se v è un oggetto/dizionario che al suo interno contiene data_points o days, lo importiamo
                if v and isinstance(v, dict):
                    nested = v.get("data_points") or v.get("days")
                    if isinstance(nested, list):
                        metrics_container[k] = nested

    # Ora calcoliamo la media pesata (weighted average) per ciascuna metrica trovata
    weighted_map: Dict[str, Optional[float]] = {}
    for metric_name, days in metrics_container.items():
        try:
            # compute_weighted_average è la funzione che implementa la logica di pesatura su 7 giorni
            wa = compute_weighted_average(days)
        except Exception as e:
            # In caso di errore nel calcolo non vogliamo rompere la response: logghiamo e impostiamo None
            logger.exception("Error computing weighted average for %s: %s", metric_name, e)
            wa = None
        # Salviamo il risultato (float o None) nella mappa finale
        weighted_map[metric_name] = wa

    # Infine costruiamo la risposta: non modifichiamo i campi upstream, aggiungiamo solo weighted_average_7d
    if isinstance(data, dict):
        # Aggiungiamo una nuova chiave al dict esistente con la mappa delle medie pesate
        data["weighted_average_7d"] = weighted_map
        # Restituiamo il dict aggiornato con lo stesso status code ottenuto dall'upstream
        return jsonify(data), r.status_code
    else:
        # Se l'upstream ha restituito qualcosa che non è un dict (es. lista), wrappiamo il contenuto
        return jsonify({
            "data": data,
            "weighted_average_7d": weighted_map
        }), r.status_code


if __name__ == "__main__":
    logger.info("Starting backend proxy on port %s (API_BASE=%s)", PORT, API_BASE)
    # debug=True tiene il reload in sviluppo; disattivare in produzione
    app.run(host="0.0.0.0", port=PORT, debug=True)
    
""" - Uso di Response per /api/stations: mantiene esattamente il body e content-type dell'upstream; utile se upstream ritorna payload con struttura particolare o headers importanti. Nel dettaglio stazione si usa jsonify perché modifichiamo il JSON.
- compute_weighted_average: più robusta verso input non validi (conversione sicura, ignorare giorni senza average o sample_size).
- Logging per capire velocemente errori in sviluppo.
- CORS abilitato su /api/* (utile in sviluppo; in produzione limitare origini).
- Timeout configurabile per richieste upstream."""