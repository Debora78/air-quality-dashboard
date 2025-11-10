/* Questo file è stato creato per centralizzare la configurazione delle chiamate API per mantenere codice pulito e riutilizzabile evitando di scrivere fetch o axios in ogni componente   */

//Import di axios per effettuare le chiamate HTTP verso il backend.
import axios from "axios";

// Crea una variabile booleana DEBUG che sarà true solo se hai definito VITE_DEBUG_API=true nel tuo .env. Ti permette di attivare o disattivare il debug in modo controllato, senza modificare il codice..

//? import.meta.env permette di accedere alle variabili d'ambiente in Vite/Nuxt e contiene tutte le variabili definite nei file .env

const DEBUG = !!import.meta.env?.VITE_DEBUG_API;

//todo VITE_DEBUG_API è una variabile che può essere definita nel file .env e serve per attivare o disattivare il debug delle chiamate API
//* ? è l'optional chaining controlla se import.meta.env esiste prima di legere VITE_DEBUG_API ed evita errori se l'ambiente non è definito
// !! Serve per convertire il valore in booleano: Se VITE_DEBUG_API è "true" -> DEBUG sarà true - Se non esiste o è "false" -> DEBUG sarà false

// base URL del backend (prende NUXT_PUBLIC_API_BASE (dichiarata nel .env frontend usando Nuxt) o VITE_API_BASE(se si usa vite senza Nuxt), altrimenti fallback(se le due precedenti non sono definite))
const base =
  (import.meta.env?.NUXT_PUBLIC_API_BASE as string) ||
  (import.meta.env?.VITE_API_BASE as string) ||
  "http://127.0.0.1:5000/api";

// Creiamo un'istanza axios con baseURL e timeout; usare `http.get('/path')` nelle chiamate.
const http = axios.create({
  //Crea una nuova istanza di Axios
  baseURL: base, // baseURL per tutte le richieste(usa la costante base dichiarata sopra(const base =))
  timeout: 5000, // timeout di 5 secondi per evitare attese indefinite(se il server non risponde entro 5 secondi Axios interrompe la richiesta )
});

// Export del composable useApi
export const useApi = () => {
  //todo esporta la funzione composable chiamata useApi() - Serve per raggruppare tutte le funzioni che fanno chiamate Api(ogni componente può importarla e usare la funzione API in modo pulito)
  // Se la variabile DEBUG è attiva (cioè VITE_DEBUG_API=true nel .env ), allora stampa nel terminale:[useApi] base API: http://localhost:5000/api(ciò aiuta a verificare che l'URL del backend sia corretto durante lo sviluppo)
  if (DEBUG) console.debug("[useApi] base API:", base);

  //? ---------- getStations ----------
  // Funzione per ottenere la lista di tutte le stations e normalizzare la risposta.
  //todo const getStation = async(): dichiaro una funzione asincrona
  //* : Promise<{stations: any[]}> : Con TypeScrip dichiaro il tipo di dato che la funzione restituirà cioè getStation() restituirà una Promise che contiene un oggetto con una proprietà stations, che è un array
  //Promise in JS e TS è un tipo di dato speciale che rappresenta il risultato futuro di un'operazione asincrona e può avere 3 stadi: 1) pending - in attesa: l'operazione non è ancora finita - 2) fulfilled - completata con successo: restituisce il risultato - 3) rejected - fallita: c'è stato un errore
  const getStations = async (): Promise<{ stations: any[] }> => {
    // Questo è un log di debug che viene eseguito solo se DEBUG è true - Serve per monitorare le chiamate API durante lo sviluppo
    if (DEBUG) console.debug("[useApi] getStations -> GET", "/stations");

    try {
      // Eseguiamo la richiesta GET all'endpoint  /stations usando l'istanza Axios http
      const res = await http.get("/stations"); //* await: aspetta che arrivi la risposta prima di proseguire
      //*res è l'oggetto risposta completo di Axios

      // Estrae solo il contenuto della risposta (cioè il JSON restituito dal backend)
      // res.data è quello che il backend ha inviato con return jsonify() in Flask
      const payload = res.data;

      // Controlla se payload è direttamente un array
      // return {station: payload} incapsula l'oggetto {station[..]} per uniformare il formato così il frontend riceve sempre un oggetto con la proprietà stations
      if (Array.isArray(payload)) return { stations: payload };

      //* payload && - Verifica che payload esista e non sia null o undefined e se payload è falsy(cioè null, undefined, false, 0, ecc), il blocco if si ferma subito
      //* typeof payload === "object" && - Verifica che payload sia un oggetto escludendo tipi coem string, number, boolean e serve per assicurarsi che payload abbia proprietà come stations
      //* Array.isArray((payload as any).stations) - Controlla se la proprietà stations dentro payload è un array e usando payload as any si evitano errori di tipo in TypeScript

      if (
        payload &&
        typeof payload === "object" &&
        Array.isArray((payload as any).stations)
      ) {
        return { stations: (payload as any).stations }; //stations: è l'array - payload as any è la risposta di qualsiasi tipo - .stations è la proprietà dell'oggetto JSON che contiene l'array di stazioni(all'interno ogni stazione avrà id, nome ecc...)
      }

      // .data contiene i dati recuperati dalla richiesta ricevuta da Flask i quali poi vengono convertiti in JSON con jsonify(data) per poterli inviare al frontend
      if (
        payload &&
        typeof payload === "object" &&
        Array.isArray((payload as any).data)
      ) {
        return { stations: (payload as any).data };
      }

      // Fallback: Se nessuna condizione precedente è soddisfatta (nessun array valido trovato), restituisci comunque: {stations: []}
      return { stations: [] };
    } catch (err: any) {
      // In caso di errore network/logico logghiamo in DEBUG lo stato o il messaggio
      //*se err esiste, prova a leggere err.response
      //*se response esiste, prova a leggere response.status
      //*se qualcuno di questi è undefined, non dà errore: restituisce undefined(Evita errori tipo: Cannot read property 'status' of undefined)
      if (DEBUG)
        console.debug(
          "[useApi] getStations failed:",
          err?.response?.status ?? err?.code ?? err?.message
        ); //*??(Nullish coalescing):se il valore di sinistra è null o undefined, usa quello a destra
      // Ritorniamo comunque la stessa shape per semplicità del caller
      return { stations: [] };
    }
  };

  //todo ---------- getStationMeasurements ----------
  // Funzione che prova più endpoint per ottenere le misurazioni di una station, poi fallback su getStations.
  //*Funzione asincrona(async)-> usa await per chiamare HTTP
  //*Accetta un parametro id(stringa)->identificativo della stazione
  //*Restituisce una Promise che risolve in un array gerarchico(any[]) - Potrebbe essere un array di misurazioni, giorni, serie temporali, ecc..
  const getStationMeasurements = async (id: string): Promise<any[]> => {
    //* Se id è vuoto, nullo o undefined -> ritorniamo subito array vuoto per evitare chiamate inutili o errate
    if (!id) return [];

    // Lista di endpoint relativi da provare in ordine di preferenza
    const endpoints = [
      // prima prova il proxy locale
      `/api/stations/${id}`, // preferito: il proxy restituisce il JSON arricchito
      `/api/stations/${id}/measurements`,
      `/api/stations/${id}/days`,
      // poi prova gli endpoint relativi all'upstream ad es. uun server esterno(se necessario)
      `/stations/${id}/measurements`,
      `/stations/${id}/days`,
      `/stations/${id}/timeseries`,
      `/v1/stations/${id}/measurements`,
      `/v1/stations/${id}`,
      `/measurements?station_id=${id}`,
      `/measurements?stationId=${id}`,
      `/measurements?station=${id}`,
    ];

    // Questa funzione extractArray è un Helper Intelligente che serve a interpretare le risposte JSON ricevute dagli endpoint dichiarati sopra
    //*Funzione che accetta un payload(cioè la risposta JSON ricevuta) che restituisce: - un array (any[]) se trova dati utili - null se non trova nulla
    const extractArray = (payload: any): any[] | null => {
      //todo Se payload è falsy(null, undefined,false, ecc..) -> ritorna null
      if (!payload) return null;

      //todo Se payload è già un array -> lo restituisce direttamente
      if (Array.isArray(payload)) return payload;

      //todo Se payload contiene data che è un array -> lo restituisce
      if (Array.isArray(payload?.data)) return payload.data;

      //todo Se payload contiene measurements che è un array -> lo restituisce
      if (Array.isArray(payload?.measurements)) return payload.measurements;

      //todo Se payload contiene result che è un array -> lo restituisce
      if (Array.isArray(payload?.result)) return payload.result;

      // Questa costante findArray è una funzione ricorsiva che serve per scandagliare un oggetto JSON complesso e trovare il primo array di oggetti al suo interno.
      //*Accetta un parametro obj di tipo any(può essere qualsiasi cosa) ->Restituisce - un array(any[])se lo trova - null se non trova nulla
      const findArray = (obj: any): any[] | null => {
        //todo Se obj è null, undefined, false, ecc OPPURE non è un oggetto(es. stringa, numero)->Ritorna null subito
        if (!obj || typeof obj !== "object") return null;

        //todo Se obj è array e ha almeno un elemento obj.length, il primo elemento è un oggetto(typeof objj[0]==="object")-> lo considera valido
        if (Array.isArray(obj) && obj.length && typeof obj[0] === "object")
          return obj; //todo restituisce obj

        //*Altrimenti scorre tutte le proprietà dell'oggetto
        //*Per ciascuna proprietà chiama ricorsivamente findArray
        //*Se trova un array valido in una proprietà annidata -> lo restituisce
        for (const k of Object.keys(obj)) {
          //Il try catch serve per evitare il crash se una proprietà è malformata
          try {
            const f = findArray(obj[k]);
            if (f) return f;
          } catch {
            // Ignoriamo errori interni alla ricerca
          }
        }
        // Se nessuna proprietà contiene un array valido -> ritorna null
        return null;
      };

      // Avviamo la ricerca ricorsiva e se payload è già un array -> lo restituisce
      return findArray(payload);
    };

    // Scorre tutti gli endpoints definiti prima (/api/sations/${id}, ecc) - ogni ep è una stringa con il path relativo
    for (const ep of endpoints) {
      try {
        // Prova a eseguire la richiesta HTTP e se fallisce (es. 404, timeout) passa al catch
        //*Se DEBUG è attivo, stampa quale endpoint sta provando - base è la base URL(es. http://localhost:3000), ep è il path
        if (DEBUG) console.debug("[useApi] trying", `${base}${ep}`);

        //todo Eseguiamo la richiesta HTTP usando Axios - res.data sarà il contenuto JSON ricevuto
        const res = await http.get(ep);

        //todo Usa la funzione extractArray per cercare un array utile nella risposta(può essere in .data, .measurements, .result, ecc..)
        const arr = extractArray(res.data);

        //todo Se arr è un array e non è vuoto
        if (Array.isArray(arr) && arr.length) {
          if (DEBUG)
            //todo Logga il successo
            console.debug(
              "[useApi] getStationMeasurements success on",
              ep,
              "len",
              arr.length
            );
          return arr; //todo ritorna l'array -> fine funzione
        }
        //*Se la chiamata è andata a buon fine (200 OK) ma non c'è un array utile:
        if (DEBUG)
          //todo Logga che l'endpoint ha risposto ma non ha fornito dati utili
          console.debug(
            "[useApi] ok but no array on",
            ep,
            "status",
            res.status
          );
      } catch (err: any) {
        //*Se la chiamata fallisce(es. 404, timeout, errore di rete)
        if (DEBUG)
          //todo Logga l'errore e passa al prossimo endpoint
          console.debug(
            "[useApi] endpoint failed",
            ep,
            err?.response?.status ?? err?.code ?? err?.message
          );
      }
    }

    //*Questo è il fallback finale della funzione getStationMeasurements.
    //* Serve per gestire il caso in cui nessuno degli endpoint provati prima ha restituito dati utili.
    //todo Se tutti gli endpoint hanno fallito si attiva il try
    try {
      if (DEBUG)
        //*Se DEBUG è attivo,

        //*stampa che si sta eseguendo il fallback con getStations()
        console.debug("[useApi] fallback -> getStations and filter by id:", id);

      //todo Chiama la funzione getStations() che restituisce tutte le stazioni e il risultato è salvato in allWrapper(può avere varie forme(oggetto con .stations, .data, o anche un array diretto))
      const allWrapper = await getStations();

      //todo Si cerca di estrarre un array di stazioni da allWrapper, qualunque sia la sua forma
      //*Se Array.isArray(allWrapper) è vero
      const list: any[] = Array.isArray(allWrapper)
        ? allWrapper //*restituisce allWrapper
        : //todo Accedi a .station solo se allWrapper esiste
        Array.isArray((allWrapper as any)?.stations)
        ? //*Se station è un array, restituiscilo
          (allWrapper as any).stations
        : //todo Usa Array.isArray(..)per verificare che data sia effettivamente un array
        Array.isArray((allWrapper as any)?.data)
        ? (allWrapper as any).data //*Se è un array restituiscilo
        : //todo Altrimenti restituisci array vuoto se non ci sono dati utili
          [];

      // Scorre l’array list (che contiene le stazioni ricevute dall'API tramite getStations()), per ogni elemento s, controlla se s?id (id di ogni singola stazione dentro list) è uguale a id(id  passato alla funzione getStationMeasurements(id)->cioè quello selezionato dall'utente)
      const found = list.find((s: any) => s?.id === id) ?? null;

      //todo Se found è null(cioè la stazione con quell'id non è stata trovata),
      if (!found) return []; //*la funzione ritorna un array vuoto

      //todo controlla le proprietà più comuni che potrebbero contenere misurazioni:
      //*days -> Misurazioni aggregate per giorno
      if (Array.isArray(found.days)) return found.days;

      //*measurements -> Misurazioni dettagliate
      if (Array.isArray(found.measurements)) return found.measurements;

      //*data -> Generico contenitore di dati
      if (Array.isArray(found.data)) return found.data;

      //*timeseries -> Serie temporali
      if (Array.isArray(found.timeseries)) return found.timeseries;

      //* Nessuna proprietà utile
      return []; //*array vuoto
    } catch (e: any) {
      // In caso di errore durante il fallback catturo l'errore
      if (DEBUG)
        //*Se DEBUG è attivo -> Logga l'errore
        console.debug("[useApi] fallback getStations failed:", e?.message ?? e);
      return []; //*Ritorna comunque un array vuoto
    }
  };

  //todo ---------- getStation(id) ----------
  // Funzione asincrona chiamata getStation, riceve un parametro id(stringa), Restituisce una Promise che può contenere un oggetto qualsiasi(any) oppure null
  const getStation = async (id: string): Promise<any | null> => {
    if (!id) return null; //*Se id non è stato fornito (è undefined, null o stringa vuota)  -> ritorn null evitando chiamate inutili

    // Proviamo prima l'endpoint specifico
    try {
      //todo Se DEBUG è attivo
      if (DEBUG) console.debug("[useApi] try GET", `/stations/${id}`); //*Stampa l'URL della richiesta

      //todo Fa una richiesta HTTP GET all'endpoint /stations/{id}
      const res = await http.get(`/stations/${id}`); //*Salva la risposta nella costante res

      //todo Estrae il corpo della risposta(data) che può essere un oggetto, un array o un wrapper
      const data = res.data;

      //*Se DEBUG è attivo -> stampa la risposta ricevuta
      if (DEBUG) console.debug("[useApi] getStation raw response:", data);

      //todo CASO 1 - OGGETTO DIRETTO
      //*Se data è un oggetto e ha un id uguale a quello cercato
      if (data && typeof data === "object" && data.id === id) return data; //* Restituisci l'oggetto

      //todo CASO 2 - WRAPPER { station: {...} } o { data: {...} }
      //* Se data esiste e il tipo di data è un oggetto
      if (data && typeof data === "object") {
        //*Se l'oggetto data contiene una proprietà chiamata station - confronta l'id della stazione ricevuta(data.station.id) con l'id che si sta cercando (id -> quello selezionato dall'utente)
        if (data.station && data.station.id === id) return data.station; //*restituisce direttamente l'oggetto station

        //*Se l'oggetto data contiene una proprietà chiamata data e l'id dentro data.data è uguale all'id che si sta cercando -> Restituisce data.data(tutto l'oggetto data)
        if (data.data && data.data.id === id) return data.data;
      }

      //todo CASO 3 - DATA è UN ARRAY
      if (Array.isArray(data)) {
        //*Se data è un array

        //*sa .find() per cercare il primo elemento s nell'array dove s?.id(id stazione corrente) === id(id selezionato dall'utente)
        //*Se lo trova lo assegna alla costante found
        //*Se non lo trova found = null(grazie a ??null)
        const found = data.find((s: any) => s?.id === id) ?? null;

        if (found) return found; //*Se found non è null -> Restituisce la stazione trovata
      }

      //todo DATA.STATION è un array { stations: [...] }
      //*Se data esiste (non è null o undefined), data.stations è un array
      if (data && Array.isArray((data as any).stations)) {
        //*Usa .find() per cercare la prima stazione s dentro data.stations dove s.id === id
        //*Se la trova la assegna alla costante found
        const found =
          (data as any).stations.find((s: any) => s?.id === id) ?? null; //*Se non la trova ->found = null(grazie a ??null)

        //*found non è null -> Restituisce la stazione giusta
        if (found) return found;
      }

      //* Se la chiamata diretta a /statons/:id fallisce(es. errore di rete, 404)
    } catch (err: any) {
      if (DEBUG)
        //*Se DEBUG è attivo

        //*Logga l'errore e non interrompe la funzione
        console.debug(
          "[useApi] getStation direct request failed:",
          err?.response?.status ?? err?.code ?? err?.message
        );
      //* -> prosegue con il fallback
    }

    // Fallback: scarica la lista completa delle stazioni e cerca quella giusta
    try {
      //*gestione di eventuali errori

      if (DEBUG)
        //*Se DEBUG è attivo

        //*Stampa un messaggio che indica che si sta eseguendo il fallback
        console.debug("[useApi] fallback -> getStations and filter by id:", id);

      //todo chiam la funzione getStations() per ottenere tutte le stazioni disponibili(await attende la risposta)
      const all = await getStations();

      //*Verifica in che formato è la risposta all
      //*Estrae l'array di stazioni in list da una delle seguenti forme:
      const list: Array<any> = Array.isArray(all)
        ? all //*è un array-> lo usa
        : Array.isArray((all as any)?.stations)
        ? (all as any).stations //*all.station è un array-> lo usa
        : Array.isArray((all as any)?.data)
        ? (all as any).data //*all.data è un array-> lo usa
        : []; //*nessuna delle precedenti-> usa array vuoto

      //todo Log della lunghezza della lista ottenuta
      //*Se DEBUG è attivo -> stampa quanti elementi contiene list
      if (DEBUG) console.debug("[useApi] list length:", list.length);

      //todo Ricerca la station con l'id richiesto
      //*Cerca la prima stazione in list dove s.id === id
      //*Se la trova -> assegna alla costante found
      //*Se non la trova -> found = null
      const found = list.find((s: any) => s?.id === id) ?? null;

      //todo  Log del risultato della ricerca
      //*Se DEBUG è attivo -> stampa la stazione trovata(o null)
      if (DEBUG) console.debug("[useApi] getStation found:", found);

      //todo Ritorniamo l'elemento trovato (o null se non esiste)
      return found; //*Restituisce la stazione trovata oppure null se non la trova
    } catch (e: any) {
      // * Se la chiamata a getStation() fallisce
      if (DEBUG)
        //*Se DEBUG è attivo

        //*Logga l'errore
        console.debug("[useApi] fallback getStations failed:", e?.message ?? e);

      return null; //*Restituisce null
    }
  };

  //todo Esportiamo le funzioni pubbliche del composable
  //*getStations() -> tutte le stazioni
  //*getStation() -> una stazione specifica
  //*getStationMeasurements(id) -> misurazioni associate

  return { getStations, getStation, getStationMeasurements };
};
