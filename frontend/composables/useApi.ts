// frontend/composables/useApi.ts

// Import di axios per effettuare le chiamate HTTP verso il backend.
// axios è una libreria HTTP promise-based semplice da usare lato client.
import axios from "axios";

// Esportiamo una factory function (composable) chiamata useApi.
// Questa funzione restituisce un oggetto con metodi per chiamare l'API backend.
// Pattern comune in Vue/Nuxt per raggruppare la logica di comunicazione con l'API.
export const useApi = () => {
  // Leggiamo l'endpoint base per le chiamate API.
  // import.meta.env è l'oggetto Vite che contiene le variabili d'ambiente
  // disponibili lato client. Qui cerchiamo la variabile NUXT_PUBLIC_API_BASE.
  //
  // Ordine dei fallback:
  // 1) import.meta.env.NUXT_PUBLIC_API_BASE (impostata nel file .env o dall'ambiente)
  // 2) stringa hardcoded 'http://localhost:5000/api' come fallback sicuro in sviluppo
  //
  // Usiamo l'accesso diretto a import.meta.env perché evita l'uso di alias
  // come '#app' o '#imports' che talvolta generano errori in editor/TS se i tipi
  // non sono configurati.
  const base =
    import.meta.env?.NUXT_PUBLIC_API_BASE || "http://localhost:5000/api";

  // Metodo per ottenere la lista delle stazioni.
  // - Chiamiamo GET /stations sull'endpoint base.
  // - axios restituisce un oggetto response; la proprietà .data contiene il payload JSON.
  // - Il metodo ritorna direttamente response.data così il caller riceve i dati già parsati.
  const getStations = async () => {
    const res = await axios.get(`${base}/stations`);
    return res.data;
  };

  // Metodo per ottenere il dettaglio di una singola stazione.
  // - id è passato come stringa e inserito nell'URL.
  // - Ritorniamo response.data con la struttura JSON fornita dal backend.
  const getStation = async (id: string) => {
    const res = await axios.get(`${base}/stations/${id}`);
    return res.data;
  };

  // Restituiamo i metodi pubblici del composable.
  // In Vue/Nuxt i composables solitamente espongono funzioni o refs reattivi.
  return { getStations, getStation };
};
// useApi: composable che fornisce funzioni per chiamare l'API backend. Usa l'endpoint definito in runtimeConfig.public.apiBase, con fallback a variabili d'ambiente o localhost. Espone getStations e getStation per ottenere dati dalle rispettive rotte API.
