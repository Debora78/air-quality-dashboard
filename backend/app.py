# backend/app.py
"""
Flask proxy server:
- espone /api/stations e /api/stations/<id>
- inoltra le richieste all'API upstream (https://api.zeroc.green/v1/...)
- aggiunge per ogni metrica il campo 'weighted_average_7d' (media ponderata sugli ultimi 7 giorni)
- gestisce errori in modo semplice restituendo JSON con message e status
"""

import os
import requests
from flask import Flask, jsonify, request
from dotenv import load_dotenv

# Carica variabili d'ambiente dal file .env (se presente)
load_dotenv()

API_BASE = os.getenv("API_BASE_URL", "https://api.zeroc.green/v1")
PORT = int(os.getenv("PORT", 5000))
TIMEOUT = 10  # timeout per le chiamate HTTP

app = Flask(__name__)

def compute_weighted_average(days):
    """
    Calcola la media ponderata per una lista di giorni.
    Input:
      days: lista di dict, ognuno con almeno 'average' e 'sample_size'
    Regole:
      - considera solo fino agli ultimi 7 giorni (partendo dal più recente nell'input)
      - ignora i giorni con sample_size == 0
      - se non ci sono giorni validi restituisce None
    Restituisce:
      float arrotondato a 6 decimali o None
    """
    if not days:
        return None

    # assume che l'upstream fornisca gli ultimi 10 giorni in ordine dal più recente al meno recente
    # prendiamo i primi 7 elementi utili (fino a 7 giorni con sample_size > 0)
    weighted_sum = 0.0
    total_samples = 0

    count_considered = 0
    for day in days:
        if count_considered >= 7:
            break
        # estrai sample_size e average in modo robusto
        sample_size = day.get("sample_size", 0) or 0
        average = day.get("average", None)
        # skip if no samples or average missing
        if sample_size == 0 or average is None:
            # non incrementiamo count_considered qui: la definizione richiede "ultimi 7 giorni disponibili dentro i 10"
            # quindi conto i giorni utili (con sample_size > 0) fino a 7
            continue
        # ora considero questo giorno valido
        weighted_sum += average * sample_size
        total_samples += sample_size
        count_considered += 1

    if total_samples == 0:
        return None

    weighted_avg = weighted_sum / total_samples
    # arrotondo per stabilità nella UI
    return round(weighted_avg, 6)

@app.route("/api/stations", methods=["GET"])
def get_stations():
    """
    Proxy per GET /v1/stations
    Inoltra la risposta upstream così com'è. Gestisce errori semplici.
    """
    upstream = f"{API_BASE}/stations"
    try:
        resp = requests.get(upstream, timeout=TIMEOUT)
        resp.raise_for_status()
        # ritorniamo esattamente il body upstream, senza modifiche
        return jsonify(resp.json()), resp.status_code
    except requests.exceptions.RequestException as e:
        # errore di rete o upstream non raggiungibile
        return jsonify({"message": "Errore contattando il servizio upstream", "detail": str(e)}), 502
    #get_station_detail: fa da proxy, individua le "metriche" nella risposta upstream e aggiunge il campo root weighted_average_7d che mappa ogni metrica al valore calcolato.
@app.route("/api/stations/<station_id>", methods=["GET"])
def get_station_detail(station_id):
    """
    Proxy per GET /v1/stations/<id>
    Richiama l'upstream e aggiunge, per ogni metrica presente nella risposta, il campo
    'weighted_average_7d' con la media ponderata calcolata sui giorni forniti dall'upstream.
    """
    upstream = f"{API_BASE}/stations/{station_id}"
    try:
        resp = requests.get(upstream, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()

        # Presupposto sul formato: 'data' contiene forse un dict con chiavi che includono le metriche.
        # Esempio ipotetico:
        # data = {
        #   "id": "...",
        #   "metrics": {
        #     "pm10": [{ "date": "...", "min": ..., "average": ..., "max": ..., "sample_size": ... }, ...],
        #     "pm2_5": [ ... ],
        #   }
        # }
        # Se la struttura differisce, l'implementazione nel README deve documentare l'assunzione.
        # Cerchiamo una chiave 'metrics' o, come fallback, analizziamo tutte le chiavi che hanno liste di giorni.

        metrics_container = None
        if isinstance(data, dict) and "metrics" in data and isinstance(data["metrics"], dict):
            metrics_container = data["metrics"]
        else:
            # fallback: trova le chiavi che contengono liste di dict con 'average' e 'sample_size'
            metrics_container = {}
            for k, v in list(data.items()):
                if isinstance(v, list) and v and isinstance(v[0], dict) and "average" in v[0]:
                    metrics_container[k] = v

        # calcola weighted_average per ogni metrica trovata
        weighted_map = {}
        for metric_name, days in metrics_container.items():
            # assumiamo che 'days' siano ordinati dal più recente al più vecchio; se non lo sono, bisognerebbe ordinarli per data
            
            weighted = compute_weighted_average(days)
            # compute_weighted_average: prende i giorni forniti (assume più recente primo), ignora giorni con sample_size==0, conta fino a 7 giorni validi e calcola Σ(average*sample_size) / Σ(sample_size). Se Σ=0 restituisce None (null in JSON).
            weighted_map[metric_name] = weighted

        # Aggiungiamo un campo esplicito nella risposta upstream
        # Non modifichiamo gli altri campi, ma aggiungiamo 'weighted_average_7d' a root o sotto 'metrics_summary'
        data["weighted_average_7d"] = weighted_map

        return jsonify(data), resp.status_code
        #- gestione errori: si intercettano eccezioni di rete e http error, e si ritornano JSON con message e detail per il frontend.

    except requests.exceptions.HTTPError as e:
        # l'upstream ha restituito 4xx/5xx
        code = getattr(e.response, "status_code", 502)
        try:
            detail = e.response.json()
        except Exception:
            detail = str(e)
        return jsonify({"message": "Upstream returned error", "detail": detail}), code
    except requests.exceptions.RequestException as e:
        return jsonify({"message": "Errore contattando il servizio upstream", "detail": str(e)}), 502
    except Exception as e:
        # fallback generico
        return jsonify({"message": "Errore interno server", "detail": str(e)}), 500

if __name__ == "__main__":
    # avvio in sviluppo: host 0.0.0.0 per accesso da altri dispositivi in LAN (facoltativo)
    app.run(host="0.0.0.0", port=PORT, debug=True)