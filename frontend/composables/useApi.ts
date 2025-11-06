// Import di axios per effettuare le chiamate HTTP verso il backend.
import axios from "axios";

// Flag di debug globale: true se VITE_DEBUG_API è impostato nell'env.
const DEBUG = !!import.meta.env?.VITE_DEBUG_API;

// base URL del backend (prende NUXT_PUBLIC_API_BASE o VITE_API_BASE, altrimenti fallback)
const base =
  (import.meta.env?.NUXT_PUBLIC_API_BASE as string) ||
  (import.meta.env?.VITE_API_BASE as string) ||
  "http://127.0.0.1:5000/api";

// Creiamo un'istanza axios con baseURL e timeout; usare `http.get('/path')` nelle chiamate.
const http = axios.create({
  baseURL: base, // baseURL per tutte le richieste
  timeout: 5000, // timeout di 5 secondi per evitare attese indefinite
});

// Export del composable useApi
export const useApi = () => {
  // Log iniziale che mostra il base quando DEBUG è attivo
  if (DEBUG) console.debug("[useApi] base API:", base);

  // ---------- getStations ----------
  // Funzione per ottenere la lista di tutte le stations e normalizzare la risposta.
  const getStations = async (): Promise<{ stations: any[] }> => {
    // Log diagnostico dell'endpoint chiamato
    if (DEBUG) console.debug("[useApi] getStations -> GET", "/stations");

    try {
      // Eseguiamo la richiesta GET verso /stations usando l'istanza http
      const res = await http.get("/stations");
      // Estrarre il payload dalla risposta axios
      const payload = res.data;

      // Se il backend ritorna direttamente un array -> normalizziamo in { stations: [...] }
      if (Array.isArray(payload)) return { stations: payload };

      // Se il backend ritorna { stations: [...] } -> estraiamo stations
      if (
        payload &&
        typeof payload === "object" &&
        Array.isArray((payload as any).stations)
      ) {
        return { stations: (payload as any).stations };
      }

      // Se il backend ritorna { data: [...] } -> estraiamo data come stations
      if (
        payload &&
        typeof payload === "object" &&
        Array.isArray((payload as any).data)
      ) {
        return { stations: (payload as any).data };
      }

      // Fallback: nessuna station trovata -> ritorniamo array vuoto in shape coerente
      return { stations: [] };
    } catch (err: any) {
      // In caso di errore network/logico logghiamo in DEBUG lo stato o il messaggio
      if (DEBUG)
        console.debug(
          "[useApi] getStations failed:",
          err?.response?.status ?? err?.code ?? err?.message
        );
      // Ritorniamo comunque la stessa shape per semplicità del caller
      return { stations: [] };
    }
  };

  // ---------- getStationMeasurements ----------
  // Funzione che prova più endpoint per ottenere le misurazioni di una station, poi fallback su getStations.
  const getStationMeasurements = async (id: string): Promise<any[]> => {
    // Se id non fornito, ritorniamo subito array vuoto per evitare chiamate inutili
    if (!id) return [];

    // Lista di endpoint relativi da provare in ordine di preferenza
    const endpoints = [
      // prima prova il proxy locale
      `/api/stations/${id}`, // preferito: il proxy restituisce il JSON arricchito
      `/api/stations/${id}/measurements`,
      `/api/stations/${id}/days`,
      // poi prova gli endpoint relativi all'upstream (se necessario)
      `/stations/${id}/measurements`,
      `/stations/${id}/days`,
      `/stations/${id}/timeseries`,
      `/v1/stations/${id}/measurements`,
      `/v1/stations/${id}`,
      `/measurements?station_id=${id}`,
      `/measurements?stationId=${id}`,
      `/measurements?station=${id}`,
    ];

    // Helper che normalizza varie forme di payload e restituisce il primo array utile trovato
    const extractArray = (payload: any): any[] | null => {
      // Se payload è falsy, non c'è nulla da fare
      if (!payload) return null;
      // Se payload è già un array lo usiamo direttamente
      if (Array.isArray(payload)) return payload;
      // Se payload contiene data che è un array -> usalo
      if (Array.isArray(payload?.data)) return payload.data;
      // Se payload contiene measurements che è un array -> usalo
      if (Array.isArray(payload?.measurements)) return payload.measurements;
      // Se payload contiene result che è un array -> usalo
      if (Array.isArray(payload?.result)) return payload.result;

      // Ricerca ricorsiva del primo array di oggetti nella struttura
      const findArray = (obj: any): any[] | null => {
        // Se non è oggetto o è null, torniamo null
        if (!obj || typeof obj !== "object") return null;
        // Se è array e il primo elemento è oggetto, consideriamolo valido
        if (Array.isArray(obj) && obj.length && typeof obj[0] === "object")
          return obj;
        // Altrimenti esploriamo ricorsivamente le proprietà
        for (const k of Object.keys(obj)) {
          try {
            const f = findArray(obj[k]);
            if (f) return f;
          } catch {
            // Ignoriamo errori interni alla ricerca
          }
        }
        // Nessun array trovato in questo ramo
        return null;
      };

      // Avviamo la ricerca ricorsiva e ritorniamo il risultato
      return findArray(payload);
    };

    // Proviamo ogni endpoint fino a trovare dati utili
    for (const ep of endpoints) {
      try {
        // Log diagnostico che indica quale endpoint stiamo provando
        if (DEBUG) console.debug("[useApi] trying", `${base}${ep}`);
        // Eseguiamo la richiesta con l'istanza http (baseURL già applicata)
        const res = await http.get(ep);
        // Proviamo ad estrarre un array utile dalla risposta
        const arr = extractArray(res.data);
        // Se troviamo un array non vuoto lo restituiamo subito
        if (Array.isArray(arr) && arr.length) {
          if (DEBUG)
            console.debug(
              "[useApi] getStationMeasurements success on",
              ep,
              "len",
              arr.length
            );
          return arr;
        }
        // Se la risposta è OK ma non contiene un array utile logghiamo in DEBUG
        if (DEBUG)
          console.debug(
            "[useApi] ok but no array on",
            ep,
            "status",
            res.status
          );
      } catch (err: any) {
        // In caso di errore logghiamo (timeout, 404, ecc.) e passiamo al successivo endpoint
        if (DEBUG)
          console.debug(
            "[useApi] endpoint failed",
            ep,
            err?.response?.status ?? err?.code ?? err?.message
          );
      }
    }

    // Se nessun endpoint ha restituito dati utili, eseguiamo il fallback: scarichiamo tutte le stations
    try {
      if (DEBUG)
        console.debug("[useApi] fallback -> getStations and filter by id:", id);
      // getStations è definita sopra e ritorna { stations: [...] }
      const allWrapper = await getStations();
      // Normalizziamo le possibili forme di allWrapper in un array list
      const list: any[] = Array.isArray(allWrapper)
        ? allWrapper
        : Array.isArray((allWrapper as any)?.stations)
        ? (allWrapper as any).stations
        : Array.isArray((allWrapper as any)?.data)
        ? (allWrapper as any).data
        : [];

      // Cerchiamo la station con l'id richiesto
      const found = list.find((s: any) => s?.id === id) ?? null;
      // Se non troviamo la station, non ci sono misurazioni disponibili
      if (!found) return [];
      // Proviamo a restituire proprietà comunemente usate per misurazioni
      if (Array.isArray(found.days)) return found.days;
      if (Array.isArray(found.measurements)) return found.measurements;
      if (Array.isArray(found.data)) return found.data;
      if (Array.isArray(found.timeseries)) return found.timeseries;
      // Nessuna proprietà contenente array trovata: ritorniamo array vuoto
      return [];
    } catch (e: any) {
      // In caso di errore durante il fallback logghiamo e ritorniamo array vuoto
      if (DEBUG)
        console.debug("[useApi] fallback getStations failed:", e?.message ?? e);
      return [];
    }
  };

  // ---------- getStation ----------
  // Funzione che prova /stations/:id e poi fallback su getStations.
  const getStation = async (id: string): Promise<any | null> => {
    // Se id non fornito ritorniamo null
    if (!id) return null;

    // Proviamo prima l'endpoint specifico
    try {
      // Log dell'URL provato
      if (DEBUG) console.debug("[useApi] try GET", `/stations/${id}`);
      // Richiesta GET con l'istanza http
      const res = await http.get(`/stations/${id}`);
      // Estraiamo il payload
      const data = res.data;

      // Log della risposta grezza per debug
      if (DEBUG) console.debug("[useApi] getStation raw response:", data);

      // 1) Se il payload è direttamente l'oggetto station e l'id coincide -> restituiscilo
      if (data && typeof data === "object" && data.id === id) return data;

      // 2) Se il payload è wrapper comune { station: {...} } o { data: {...} } -> controlla e restituisci
      if (data && typeof data === "object") {
        if (data.station && data.station.id === id) return data.station;
        if (data.data && data.data.id === id) return data.data;
      }

      // 3) Se il payload è un array -> cerchiamo l'elemento con matching id
      if (Array.isArray(data)) {
        const found = data.find((s: any) => s?.id === id) ?? null;
        if (found) return found;
      }

      // 4) Se payload contiene { stations: [...] } -> cerchiamo dentro quell'array
      if (data && Array.isArray((data as any).stations)) {
        const found =
          (data as any).stations.find((s: any) => s?.id === id) ?? null;
        if (found) return found;
      }

      // Se non troviamo nulla nella risposta diretta procediamo al fallback
    } catch (err: any) {
      // In caso di errore sulla chiamata diretta logghiamo lo stato/messaggio in DEBUG
      if (DEBUG)
        console.debug(
          "[useApi] getStation direct request failed:",
          err?.response?.status ?? err?.code ?? err?.message
        );
      // Non rilanciamo: vogliamo provare il fallback
    }

    // Fallback: scarichiamo la lista completa e filtriamo lato client
    try {
      if (DEBUG)
        console.debug("[useApi] fallback -> getStations and filter by id:", id);
      const all = await getStations();

      // Normalizziamo all in un array list
      const list: Array<any> = Array.isArray(all)
        ? all
        : Array.isArray((all as any)?.stations)
        ? (all as any).stations
        : Array.isArray((all as any)?.data)
        ? (all as any).data
        : [];

      // Log della lunghezza della lista ottenuta
      if (DEBUG) console.debug("[useApi] list length:", list.length);

      // Cerchiamo la station con l'id richiesto
      const found = list.find((s: any) => s?.id === id) ?? null;

      // Log del risultato della ricerca
      if (DEBUG) console.debug("[useApi] getStation found:", found);

      // Ritorniamo l'elemento trovato (o null se non esiste)
      return found;
    } catch (e: any) {
      // In caso di errore nel fallback logghiamo e ritorniamo null
      if (DEBUG)
        console.debug("[useApi] fallback getStations failed:", e?.message ?? e);
      return null;
    }
  };

  // Esportiamo le funzioni pubbliche del composable
  return { getStations, getStation, getStationMeasurements };
};
