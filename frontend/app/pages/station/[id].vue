<script setup lang="ts">
// Import dai composables di Vue Router e reattività
import { ref, onMounted, computed } from "vue";
import { useRoute } from "vue-router";
import { useRouter } from "vue-router";

/*
  1) Prendi l'id dalla route
  - useRoute() fornisce i params; lo castiamo a stringa per sicurezza.
*/
const route = useRoute();
const router = useRouter();
const id = String(route.params.id || "");

/*
  2) Configurazioni reactive usate nella pagina
  - stationPayload: intero JSON ricevuto dal backend/proxy per la station
  - metricsData: mappa name -> array di punti giornalieri normalizzati
  - availableMetrics: lista di nomi metriche disponibili (es. "PM2.5", "PM10")
  - selectedMetric: metrica corrente mostrata nella tabella
  - loading / error: stato di UI
*/
const stationPayload = ref<any | null>(null);
const metricsData = ref<Record<string, any[]>>({});
const availableMetrics = ref<string[]>([]);
const selectedMetric = ref<string | null>(null);
const loading = ref<boolean>(true);
const error = ref<string | null>(null);

/*
  3) candidates
  - Qui definiamo i possibili endpoint da provare. Primo tentativo sempre il proxy che
    hai implementato ("/api/stations/:id"). Se usi axios con base che include "/api",
    sostituisci con ['/stations/${id}'] per evitare doppio /api.
  - Manteniamo solo poche voci per velocità: il proxy e un fallback /days se esposto.
*/
const candidates = [
  `/api/stations/${id}`, // preferito: il proxy Flask che arricchisce la response
  `/api/stations/${id}/days`, // fallback se il proxy ha endpoint specifico per giorni
];

function smartBack(): void {
  if (window.history.length > 1) {
    router.back();
  } else {
    router.push("/stations");
  }
}

/*
  4) Helper: normalizza un singolo giorno in un oggetto con campi coerenti
  - Accepta varie denominazioni: date/ts/day; average/avg/mean; min,max; sample_size/samples/count
  - Restituisce sempre { date, min, avg, max, sample_size, raw }
*/
function normalizeDay(d: any) {
  return {
    date: d?.date ?? d?.day ?? d?.ts ?? d?.timestamp ?? null,
    min: d?.min ?? d?.min_value ?? d?.minimum ?? null,
    avg: d?.average ?? d?.avg ?? d?.mean ?? null,
    max: d?.max ?? d?.max_value ?? d?.maximum ?? null,
    sample_size: d?.sample_size ?? d?.samples ?? d?.count ?? null,
    raw: d,
  };
}

/*
  5) Helper: trova e ritorna l'array di giorni all'interno della response JSON
  - Gestisce la shape vista dall'upstream: metrics -> [ { name, data_points: [...] }, ... ]
  - Se trova un array di giorni lo normalizza e lo restituisce come mappa name -> array
*/
function extractMetricsMap(payload: any): Record<string, any[]> {
  const out: Record<string, any[]> = {};

  if (!payload || typeof payload !== "object") return out;

  // Se payload.metrics è un array (forma vista nell'upstream)
  if (Array.isArray(payload.metrics)) {
    for (const m of payload.metrics) {
      // nome della metrica (es. "PM2.5", "PM10", "NO2")
      const name = m?.name ?? m?.metric ?? "unknown";
      // i punti giornalieri possono essere in data_points oppure days nella stessa struttura
      const rawPoints = Array.isArray(m?.data_points)
        ? m.data_points
        : Array.isArray(m?.days)
        ? m.days
        : [];
      out[name] = rawPoints.map(normalizeDay);
    }
    return out;
  }

  // Fallback: se payload contiene direttamente una lista di giorni sotto alcune chiavi comuni
  const tryKeys = [
    "days",
    "measurements",
    "data",
    "values",
    "history",
    "results",
  ];
  for (const k of tryKeys) {
    if (
      Array.isArray(payload[k]) &&
      payload[k].length &&
      typeof payload[k][0] === "object"
    ) {
      out["default"] = payload[k].map(normalizeDay);
      return out;
    }
  }

  // Fallback profondo: cerca dentro le proprietà per trovare una lista di oggetti con 'average' o 'min'
  for (const k of Object.keys(payload)) {
    const v = payload[k];
    if (Array.isArray(v) && v.length && typeof v[0] === "object") {
      const sample = v[0];
      if ("average" in sample || "min" in sample || "max" in sample) {
        out[k] = v.map(normalizeDay);
        return out;
      }
    }
    // annidamento: se v è un oggetto prova a leggere v.data_points o v.days
    if (v && typeof v === "object") {
      const nested = Array.isArray(v?.data_points)
        ? v.data_points
        : Array.isArray(v?.days)
        ? v.days
        : null;
      if (nested) {
        out[k] = nested.map(normalizeDay);
        return out;
      }
    }
  }

  return out;
}

/*
  6) Funzione principale: prova i candidates in ordine fino a trovare una response valida
  - Per ogni candidate: fa fetch, se ok estrae metricsMap e popola reactive refs.
  - Se nessuno dei candidates ritorna dati utili imposta error.
*/
async function fetchStationDetails() {
  loading.value = true;
  error.value = null;
  stationPayload.value = null;
  metricsData.value = {};
  availableMetrics.value = [];
  selectedMetric.value = null;

  for (const ep of candidates) {
    try {
      // Effettua la richiesta; usare fetch garantisce che l'URL sia relativo al dev server corrente.
      // Se usi axios con base diversa, sostituisci con http.get(ep) coerentemente.
      const res = await fetch(ep, { headers: { Accept: "application/json" } });
      // Se la risposta non è OK (404/500...) proseguiamo al candidato successivo
      if (!res.ok) {
        console.warn(`[fetchStationDetails] status ${res.status} from ${ep}`);
        continue;
      }
      // Parso il JSON ricevuto
      const json = await res.json();
      console.debug("[fetchStationDetails] payload from", ep, json);

      // Estrai le metriche con i punti giornalieri
      const mm = extractMetricsMap(json);

      // Se non trovi metriche utili passa al candidate successivo
      if (!mm || Object.keys(mm).length === 0) {
        console.warn(
          "[fetchStationDetails] no metrics found in payload from",
          ep
        );
        // ma registriamo stationPayload nel caso contenga weighted_average_7d utili
        stationPayload.value = json;
        continue;
      }

      // Popola reactive refs con i dati normalizzati
      metricsData.value = mm;
      availableMetrics.value = Object.keys(mm);
      stationPayload.value = json;
      // seleziona di default PM2.5 se presente, altrimenti la prima metrica disponibile
      selectedMetric.value = availableMetrics.value.includes("PM2.5")
        ? "PM2.5"
        : availableMetrics.value[0] ?? null;
      loading.value = false;
      return; // abbiamo trovato dati validi: esci dalla funzione
    } catch (e: any) {
      // Log di debug ma non interrompiamo il ciclo: proviamo il prossimo candidate
      console.error("[fetchStationDetails] error fetching", ep, e);
      continue;
    }
  }

  // Se siamo qui significa che nessun candidate ha restituito dati utili
  error.value =
    "Nessun dato giornaliero trovato per questa stazione (controlla il backend/proxy).";
  loading.value = false;
}

/*
  7) Utility computed: righe da mostrare in tabella per la metrica selezionata
  - Restituisce array vuoto se non ci sono dati
*/
const selectedMetricRows = computed(() => {
  if (!selectedMetric.value) return [];
  return metricsData.value[selectedMetric.value] ?? [];
});

/*
  8) Mostrare media pesata se il backend la fornisce in stationPayload.weighted_average_7d
  - weightedMap: mappa metric -> valore (o null)
*/
const weightedMap = computed(() => {
  return stationPayload.value?.weighted_average_7d ?? null;
});

// Esegui il fetch al mount del componente
onMounted(() => {
  fetchStationDetails();
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
