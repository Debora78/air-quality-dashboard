<script setup lang="ts">
// Import dai composables di Vue Router e reattività
import { ref, onMounted, computed } from "vue"; /* 
- ref -> Crea una variabile reattiva
- onMounted -> hook di ciclo di vita(esegue una funzione quando il componente e montato nel DOM)
- computed -> Crea una variabile derivata da altre variabili reattive(si aggiorna automaticamente quando le dipendenze cambinao) */

import { useRoute } from "vue-router"; /*  useRoute è un composable(useApi.ts) di Vue Router che permette di :
- leggere la route attuale(cioè la pagina in cui ti trovi)
- Accedere ai parmetri della URL, come l'id della stazione
- Vedere query string, nome route*/

import { useRouter } from "vue-router"; /* useRouter è un altro composeble(useApi.ts) che da accesso al router(il sistema di navigazione) e permette di :
- Navigare tra le pagine (router.push(..))
- Tornare indietro (router.back())
- Controllare la cronologia, route attiva */

// 1) Prendi l'id dalla route

const route =
  useRoute(); /* Crea una variabile route che permette di leggere la route attutale e con route si accede a:
 - route.params -> parametri dinamici della URL(es. /stations/:id)
 - route.query -> query string(es. ?lang=it)
 - route.name, route.path, ecc*/

const router =
  useRouter(); /*Crea una variabile router che permette di navigare tra le pagine e permette di:
- Fare router.push("/home")per andare a una pagina
- Fare router.back() per tronare indietro
- Accedere alla cronologia, route attiva, ecc.. */

const id = String(
  route.params.id || ""
); /* Salva nella costante id il valore del parametro id presente nell'URL della rotta 
- route.params.id -> è il valore dinamico della URL(es. se la rotta è /station/123 allora route.params.id è 123)
- String() -> converte il valore in stringa(per sicurezza)
- " " -> se route.params.id è undefined usa una stringa vuota*/

// 2) Configurazioni reactive usate nella pagina

const stationPayload = ref<any | null>(null); /*
- stationPayload: intero JSON ricevuto dal backend/proxy per la station
- ref(..) -> rende la variabile reattiva, così la UI si aggiorna quando cambia
- any|null -> può contenere qualsiasi tipo di oggetto oppure null se non è ancora caricato
(null) -> è il valore inizale in attesa della risposta dell'API
*/

const metricsData = ref<Record<string, any[]>>({}); /* 
- metricsData: oggetto reattivo che mappa nomi di metriche (stringhe) a liste di valori (array)
- Record<string, any[]> -> ogni chiave è una metrica, ogni valore è un array di dati associati
- ref(..) -> rende l’oggetto reattivo, così la UI si aggiorna quando i dati cambiano
- ({}) -> inizializzato come oggetto vuoto, in attesa dei dati metrici dal backend
*/

const availableMetrics = ref<string[]>([]); /*
- availableMetrics: lista reattiva di nomi di metriche disponibili per la station (es. "PM2.5", "PM10")
- string[] -> array di stringhe (es. ["temperature", "humidity", ...])
- ref(..) -> rende la lista reattiva, utile per popolare dropdown o filtri dinamici
- ([]) -> inizializzato vuoto, verrà riempito dopo la chiamata API
*/

const selectedMetric = ref<string | null>(null); /*
- selectedMetric: metrica attualmente selezionata dall’utente (es. per visualizzare un grafico)
- string | null -> può essere una stringa (nome metrica) oppure null se nessuna è selezionata
- ref(..) -> reattivo, così la UI può reagire al cambio di selezione
- (null) -> valore iniziale, in attesa che l’utente scelga una metrica
*/

const loading = ref<boolean>(true); /*
- loading: stato reattivo che indica se i dati sono ancora in fase di caricamento
- boolean -> true se il caricamento è in corso, false se completato
- ref(..) -> utile per mostrare spinner o disabilitare elementi della UI durante l’attesa
- (true) -> inizialmente true, verrà impostato a false al termine della chiamata API
*/

const error = ref<string | null>(null); /*
- error: messaggio di errore reattivo, se qualcosa va storto durante il caricamento dei dati
- string | null -> contiene il messaggio di errore oppure null se non ci sono errori
- ref(..) -> permette alla UI di mostrare messaggi di errore dinamicamente
- (null) -> inizialmente null, verrà valorizzato solo in caso di errore
*/

// 3) candidates

const candidates = [
  // - candidates è un array di URL API che si possono usare per recuperare dati relativi a una stazione
  // - ${id} -> è una variabile che rappresenta l'ID della stazione

  `/api/stations/${id}`, //questo URL è preferito perché passa da un proxy Flask che arricchisce la response

  `/api/stations/${id}/days`, // questo è un fallback se il proxy ha endpoint separato specifico per i dati giornalieri
];

// La funzione smartBack() è una navigazione intelligente: se può tornare indietro -> lo fa altrimenti -> porta l'utente alla pagina /station
function smartBack(): void {
  /* 
  - definisce una funzione chiamata smartBack che non restituisce nulla (void)
  - serve per gestire la navigazione intelligente all'indietro */

  if (window.history.length > 1) {
    /* 
    - controlla se la cronologia del browser ha più di una pagina
    - se sì, significa che l'utente è arrivato da un'altra pagina -> puoi tornare indietro */

    router.back(); /* 
    - usa il router di Vue per tornare alla pagina precedente
    - equivalente a premere 
    "indietro" nel browser */
  } else {
    /* 
    - se la cronologia è troppo corta (es. l'utente è arrivato direttamente su questa pagina), allora non puoi tornare indietro */

    router.push("/stations"); /* 
    - in questo caso, porti l'utente alla pagina principale delle stazioni
    - è una destinazione sicura se non c'è una pagina precedente */
  }
}

/*
  4) Helper: normalizza un singolo giorno in un oggetto con campi coerenti
  - Accepta varie denominazioni: date/ts/day; average/avg/mean; min,max; sample_size/samples/count
  - Restituisce sempre { date, min, avg, max, sample_size, raw }
*/

/*La funzione normalizeDay() prende un oggetto  (che rappresenta un giorno di dati) e restituisce un oggetto normalizzato con proprietà coerenti, indipendentemente dai nomi usati nel backend 
 Serve per:
 - Uniformare i dati ricevuti da API diverse
 - Estrarre le informazioni principali con nomi coerenti
 - Gestire backend che usano nomi diversi per le stesse cose*/
function normalizeDay(d: any) {
  return {
    date: d?.date ?? d?.day ?? d?.ts ?? d?.timestamp ?? null /* 
    - Cerca la data del giorno usando vari possibili nome (date, day, ts, timestamp)
    - Se nessuno è presente -> null */,

    min: d?.min ?? d?.min_value ?? d?.minimum ?? null /* 
    - Valore minimo registrato per quel giorno
    - Supporta vari nomi alternativi (min, min_value, minimum) */,

    avg: d?.average ?? d?.avg ?? d?.mean ?? null /* 
    - Valore medio del giorno
    - Accetta average, avg, mean */,

    max: d?.max ?? d?.max_value ?? d?.maximum ?? null /* 
    - Valore massimo del giorno
    - Compatibile con max, max_value, maximum */,

    sample_size: d?.sample_size ?? d?.samples ?? d?.count ?? null,
    /* - Numero di campioni raccolti per quel giorno
       - Supporta sample_size, samples, count */

    raw: d /* 
       - Salva l'oggetto originale ricevuto dal backend
       - Utile per debug o accesso a proprietà non normalizzate */,
  };
}

/*
  5) Questa funzione extractMetricsMap() prende un oggetto payload(tipicamente ricevuto da un'API) e restituisce una mappa di metriche dove ogni chiave è il nome della metrica(es. "PM205") e ogni valore è un array di oggetti normalizzati(giorni) tramite normalizeDay
*/
function extractMetricsMap(payload: any): Record<string, any[]> {
  const out: Record<string, any[]> = {}; /* 
   - Inizializza un oggetto vuoto out che conterrà il risultato finale
   - Ogni chiave sarà una metrica(string), ogni valore un array di oggetti(any[]) */

  if (!payload || typeof payload !== "object") return out; /* 
   - Se payload è null, undefined o non è un oggetto -> ritorna subito l'oggetto vuoto
   - Protezione contro input malformati */

  // Se payload.metrics è un array (forma vista nell'upstream)
  if (Array.isArray(payload.metrics)) {
    /* 
    - Verifica se payload.metrics è un array
    - E' la forma attesa dal backend upstream (es. [{name: "PM2.5", data_points:[...]}, ...]) */

    for (const m of payload.metrics) {
      /* 
      - Itera su ogni metrica m presente nell'array */

      const name = m?.name ?? m?.metric ?? "unknown"; /* 
       - Estrai il nome della metrica (es. "PM2.5", "PM10", "NO2")
       - Usa m.name oppure m.metric, altrimenti assegna "unknown" come fallback */

      const rawPoints = Array.isArray(m?.data_points) /* 
        - Controlla se m.data_point esiste ed è un array
        - Usa l'operatore opzionale ?. per evitare errori se m è null o undefined
        - Se è vero, allora rawPoints = m.data_points */
        ? m.data_points /* Se la condizione precedente è vera -> assegna m.data_points a rawPoints */
        : Array.isArray(
            m?.days
          ) /* Se m.data_points non è un array, controlla se m.days è un array
        - E' una seconda possibilità per trovare i dati giornalieri */
        ? m.days /* Se m.days è un array -> assegna m.days a rawPoints */
        : []; /* Se nessuna delle due proprietà è un array, assegna un array vuoto ([])
        - Evita errori e garantisce che rawPoints sia sempre un array */

      out[name] =
        rawPoints.map(
          normalizeDay
        ); /* Applica la funzione normalizeDay a ogni elemento dell'array rawPoints
      - Crea un nuovo array di oggetti normalizzati(con proprietà coerenti come date, min, avg, ecc..)
      - Salva questo array sotto la chiave name nell'oggetto out */
    }
    return out; /* Restituisce l'oggetto out, che è una mappa di metriche con i relativi dati giornalieri normalizzati 
    - Il tipo restituito è Record<sring, any[]>, cioè:
      {
        "PM2.5": [ { date, min, avg, max, ... }, ... ],
        "NO2": [ { date, min, avg, max, ... }, ... ],
         ...
      }*/
  }

  /* Questo codice è un fallback intelligente: se il payload non ha una struttura con metrics, prova a cercare direttamente una lista di giorni sotto alcune chiavi comuni (days, data, resutls, ecc..) */
  const tryKeys = [
    /* La costante tryKeys definisce un array di chiavi comuni che potrebbero contenere dati giornalieri
  - Serve per cercare in modo flessibile dentro payload, anche se la struttura non è standard */
    "days",
    "measurements",
    "data",
    "values",
    "history",
    "results",
  ];

  for (const k of tryKeys) {
    /* Itera su ogni chiave k dell'array tryKeys
  - Per ogni chiave, controlla se payload[k] è un array valido di oggetti */

    if (
      /* Verifica se payload[k] sia un array
          - L'array non sia vuoto
          - Il primo elemento dell'array sia un oggetto(quindi contiene dati strutturati)
          - Se tutte queste condizioni sono vere, si presume che payload contenga dati giornalieri */
      Array.isArray(payload[k]) &&
      payload[k].length &&
      typeof payload[k][0] === "object"
    ) {
      out["default"] = payload[k].map(normalizeDay); /* 
      - Applica normalizeDay a ogni elemento dell'array payload[k]
      - Salva il risultato sotto la chiave "default" nell'oggetto out
      - Questo crea una metrica generica "default" con i dati normalizzati */

      return out; /* Restituisce subito l'oggetto out con i dati trovati
      - Evita di continuare il ciclo una volta trovata una chiave valida */
    }
  }

  /* Questo codice cerca dati giornalieri all’interno del, anche se non sono sotto chiavi convenzionali.
  - È una strategia di recupero intelligente per gestire formati API non uniformi. */
  for (const k of Object.keys(payload)) {
    /* 
    - Itera su tutte le chiavi dirette dell'oggetto payload
    - Per ogni chiave k, esamina il valore associato payload */

    const v = payload[k]; /* 
    - Estrae il valore v associato alla chiave k
    - v può essere un array, un oggetto, o altro */

    if (Array.isArray(v) && v.length && typeof v[0] === "object") {
      /* - Controlla se v è un array non vuoto di oggetti */

      const sample = v[0];
      if ("average" in sample || "min" in sample || "max" in sample) {
        /* 
        - Prende il primo elemento (sample) e verifica se contiene almeno una delle proprietà chiave: "average", "min", "max" 
        - Se sì, presume che v sia una lista di metriche giornaliere */

        out[k] =
          v.map(
            normalizeDay
          ); /* - Applica normalizeDay a ogni elemento e salva il risultato sotto la chiave k in out */

        return out; /* Ritorna out  -> non continua a cercare */
      }
    }
    // annidamento: se v è un oggetto prova a cercare dati annidati dentro data_points o days
    if (v && typeof v === "object") {
      /* 
      - Controlla se v è un oggetto valido */

      const nested = Array.isArray(v?.data_points) /* 
      - Controlla se v.data_points esiste ed è un array
      - Usa ?. per evitare errori se v è null o undefined
      - Se è vero, assegn v.data_points a nested */
        ? v.data_points /* - Se la condizione precedente è vera ->nested = v.data_poins */
        : Array.isArray(
            v?.days
          ) /* - Se data_points non è un array, controlla se v.days è un array */
        ? v.days /* Se v.days è un array ->nested = v.days */
        : null; /* Se nessuna delle due proprietà è un array -> nested = null */

      if (nested) {
        /* - Verifica se nested contiene un array valido
        - Se sì, significa che ha trovato dati metrici annidati
         */
        out[k] =
          nested.map(
            normalizeDay
          ); /* - Applica normalizeDay a ogni elemento dell'array nested
        - Salva il risultato sotto la chiave k nell'oggetto out */

        return out; /* - Ritorna subito l'oggetto out con i dati normalizzati
        - Interrompe la ricerca: ha trovato ciò che cercava */
      }
    }
  }

  return out; /*fallback definitivo: se non è stato trovato nulla di utile, restituisce comunque l'oggetto out, che sarà vuoto ({})   */
}

/*
  6) Questa funzione asincrona serve per recuperare i dettagli di una stazione da uno o più endpoint API, normalizzare i dati metrici e aggiornare le variabili reattive per la UI
*/
async function fetchStationDetails() {
  loading.value = true; /* loading -> indica che il caricamento è in corso */

  error.value = null; /* error -> azzerato, nessun errore al momento */

  stationPayload.value =
    null; /* stationPayload ->svuotato, in attesa di nuovi dati */

  metricsData.value = {}; //azzerato per ripartire da zero
  availableMetrics.value = []; //azzerato per ripartire da zero
  selectedMetric.value = null; //azzerato per ripartire da zero

  for (const ep of candidates) {
    /*
    - Itera su ogni URL candidato 
    (/api/stations/${id}, /api/stations/${id}/days, ecc..)
    - Prova a recuperare i dati da ciascun endpoint finché ne trova uno valido */

    try {
      const res = await fetch(ep, {
        headers: { Accept: "application/json" },
      }); /* - Effettua la richiesta HTTP GET all'endpoint ep
      - Chiede esplicitamente una risposta in formato JSON */

      if (!res.ok) {
        console.warn(
          `[fetchStationDetails] status ${res.status} from ${ep}`
        ); /* - se la risposta ha status 404, 500, ecc.. ->logga un warning */

        continue; /* - Passa al prossimo endpoint (continue) */
      }

      // Parso il JSON ricevuto
      const json =
        await res.json(); /* - Converte la risposta in un oggetto JSON */

      console.debug(
        "[fetchStationDetails] payload from",
        ep,
        json
      ); /* - Logga il payload ricevuto per debug */

      const mm =
        extractMetricsMap(
          json
        ); /* - Usa la funzione extractMetricsMap per ottenere una mappa di metriche normalizzate */

      if (!mm || Object.keys(mm).length === 0) {
        /* Se mm è vuoto -> Logga un warnig */
        console.warn(
          "[fetchStationDetails] no metrics found in payload from",
          ep
        );

        stationPayload.value =
          json; /* - Salva comunque il payload nel caso contenga altri dati utili (es. weighted_average_7d) */

        continue; /* - Passa al prossimo endpoint */
      }

      // Popola reactive refs con i dati normalizzati
      metricsData.value =
        mm; /* - 'metricsData è una variabile reattiva creata con ref()(useApi.ts) - Serve per memorizzare i dati delle metriche (es. PM205, NO2, ecc..) che verranno mostrati nella UI
      - 'mm' è il risultato della funzione extractMetricsMap(json) - contiene una mappa di metriche con i dati giornalieri già normalizzati */

      availableMetrics.value =
        Object.keys(
          mm
        ); /* - 'availabeMetrics' è una variabile reattiva che contiene la lista dei nomi delle metriche disponibili - Serve per popolare la UI: ad es. un menù a tendina o dei pulsanti per scegliere la metrica da visualizzare */

      stationPayload.value =
        json; /* - 'stationPayload' è una variabile reattiva che serve per memorizzare il payload completo ricevuto dall'API(contiene tutti i dati, non solo le metriche) - 'json' è il risultato della chiamata API in formato JSON, usato come oggetto tipizzato in TypeScript  */

      selectedMetric.value = availableMetrics.value.includes(
        "PM2.5"
      ) /* Se  "PM2.5" è disponibile, la selzione come metrica attiva */
        ? "PM2.5"
        : availableMetrics.value[0] ??
          null; /* Se non è disponibile sceglie la prima metrica disponibile o null se non ce ne sono */

      loading.value =
        false; /* Caricamento terminato(serve per aggiornare la UI) */

      return; // abbiamo trovato dati validi: esci dalla funzione
    } catch (e: any) {
      /* Intercetta un errore generato dal blocco 'try'
    'e' è l'oggetto errore (di tipo 'any')
    - evita che l'app si blocchi se una chiamata fallisce */

      console.error(
        "[fetchStationDetails] error fetching",
        ep,
        e
      ); /* Stampa l'errore nella console per aiutare il debug
      - Mostra quale endpoint ('ep') ha fallito e il dettaglio dell'errore ('e') */

      continue; /*  Salta il resto del ciclo corrente e passa subito alla prossima iterazione */
    }
  }

  // Se siamo qui significa che nessun candidate ha restituito dati utili
  error.value =
    "Nessun dato giornaliero trovato per questa stazione (controlla il backend/proxy).";
  loading.value =
    false; /*  Il caricamento è finito: l'app ha completato la richiesta e può mostrare i dati(o un messaggio di errore, se non ha trovato nulla) */
}

/*
  7) Utility computed: righe da mostrare in tabella per la metrica selezionata
  - Restituisce array vuoto se non ci sono dati
*/
const selectedMetricRows = computed(() => {
  /* La costante selectMetricRows salva il risultato della funzione computed() che calcola automaticamente quando cambiano i dati da cui dipende*/

  if (!selectedMetric.value)
    return []; /* Se non è stata selezionata alcuna metrica valida restituisce un array vuoto */

  return (
    metricsData.value[selectedMetric.value] ?? []
  ); /* Cerca i dati associati alla metrica selezionata (es. "PM2.5") 
  - si li trova -> li restituisce (es. un array di righe mostrate in tabella)
  - se non trova nullaa(cioè il valore è undefined o null) -> restituisce l'array vuoto grazie all'operatore ?? */
});

/*
  8) Mostrare media pesata se il backend la fornisce in stationPayload.weighted_average_7d
  - weightedMap: mappa metric -> valore (o null)
*/
const weightedMap = computed(() => {
  /* Crea una computed che legge da stationPayload.value.weighted_average_7d (weightedMap contiene una mappa del tipo {"PM2.5":12.3, "NO2":8.7,} dove ogni chiave è una metrica e il valore è la media pesata degli ultimi 7 giorni)*/
  return (
    stationPayload.value?.weighted_average_7d ?? null
  ); /* Se il backend fornisce questa proprietà -> la restituisce
  Se non esiste -> restituisce null */
});

// Al montaggio del componente, esegui il fetch dei dettagli della stazione
onMounted(() => {
  /* Quando il componente viene montato(mostrato nella UI)*/
  fetchStationDetails(); /*  chiama la funzione(fetchStationDetails()) per recuperare i dati della stazione  */
});
</script>

<template>
  <div class="station-detail-details">
    <!-- Stato di caricamento / errore -->
    <div v-if="loading">Caricamento dati stazione...</div>
    <div v-if="error" class="error-details">{{ error }}</div>

    <!-- Bottone Indietro: posizionato subito dopo loading/error -->
    <button
      class="btn-back"
      @click="smartBack"
      aria-label="Vai indietro"
      title="Torna indietro"
    >
      <svg
        class="btn-back__icon"
        viewBox="0 0 24 24"
        fill="none"
        aria-hidden="true"
      >
        <path
          d="M15 18l-6-6 6-6"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        />
      </svg>
      <span class="btn-back__text">Indietro</span>
    </button>

    <!-- Contenuto principale -->
    <div v-if="!loading && !error">
      <!-- Titolo stazione (nome/address se disponibili) -->
      <h1>
        {{
          stationPayload?.name ??
          stationPayload?.station?.name ??
          "Dettaglio stazione"
        }}
      </h1>
      <p v-if="stationPayload?.address">{{ stationPayload.address }}</p>

      <!-- Media pesata (fornita dal backend) -->
      <div v-if="weightedMap" class="weighted-summary-details">
        <h3>Media pesata ultimi 7 giorni</h3>
        <div
          v-for="(v, k) in weightedMap"
          :key="k"
          class="weighted-row-details"
        >
          <strong>{{ k }}:</strong>
          <span>{{ v !== null ? Number(v).toFixed(2) : "N/D" }}</span>
        </div>
      </div>

      <!-- Selezione metrica -->
      <div v-if="availableMetrics.length" class="metric-select-details">
        <label for="metric">Metrica:</label>
        <select id="metric" v-model="selectedMetric">
          <option v-for="m in availableMetrics" :key="m" :value="m">
            {{ m }}
          </option>
        </select>
      </div>

      <!-- Tabella giornaliera per la metrica selezionata -->
      <div v-if="selectedMetric">
        <h2>{{ selectedMetric }} - ultimi valori giornalieri</h2>

        <table class="days-table-details" v-if="selectedMetricRows.length">
          <thead>
            <tr>
              <th>Data</th>
              <th>Min</th>
              <th>Avg</th>
              <th>Max</th>
              <th>Samples</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(d, idx) in selectedMetricRows" :key="idx">
              <!-- Data: se presente, mostriamo la stringa così com'è -->
              <td>{{ d.date ?? "-" }}</td>

              <!-- Valori numerici: se null mostriamo N/D, altrimenti formatto con 2 decimali -->
              <td>
                {{
                  d.min !== null && d.min !== undefined
                    ? Number(d.min).toFixed(2)
                    : "N/D"
                }}
              </td>
              <td>
                {{
                  d.avg !== null && d.avg !== undefined
                    ? Number(d.avg).toFixed(2)
                    : "N/D"
                }}
              </td>
              <td>
                {{
                  d.max !== null && d.max !== undefined
                    ? Number(d.max).toFixed(2)
                    : "N/D"
                }}
              </td>
              <td>{{ d.sample_size ?? "-" }}</td>
            </tr>
          </tbody>
        </table>

        <!-- Messaggio se la metrica non ha righe -->
        <div v-else>
          <p>Nessun dato giornaliero trovato per questa metrica.</p>
        </div>
      </div>

      <!-- Se non ci sono metriche disponibili -->
      <div v-else-if="!availableMetrics.length">
        <p>Nessuna metrica disponibile per questa stazione.</p>
        <pre style="max-height: 200px; overflow: auto">{{
          JSON.stringify(stationPayload, null, 2)
        }}</pre>
      </div>
    </div>
  </div>
</template>
