<template>
  <!-- Pagina principale con la lista delle stazioni.
       Mostra stato di caricamento / errore / tabella con i risultati.
       I link usano NuxtLink per navigazione client-side verso /station/:id -->
  <div class="page-container">
    <h1>Stazioni</h1>

    <!-- Se stiamo caricando, mostriamo un messaggio di caricamento -->
    <div v-if="loading" class="loading">Caricamento...</div>

    <!-- Se è presente un errore, lo mostriamo -->
    <div v-else-if="error" class="error">{{ error }}</div>

    <!-- Altrimenti mostriamo la tabella delle stazioni -->
    <div v-else class="table-card">
      <table class="stations" aria-describedby="stations-table-caption">
        <caption id="stations-table-caption" class="table-caption"></caption>
        <thead>
          <tr>
            <th scope="col">Id</th>
            <th scope="col">Nome</th>
            <th scope="col">Indirizzo</th>
            <th scope="col">Città</th>
            <th scope="col">Azioni</th>
          </tr>
        </thead>

        <!--
          v-for itera sull'array `stations`.
          :key con s.id permette a Vue di ottimizzare il rendering
        -->
        <tbody>
          <tr v-for="s in stations" :key="s.id">
            <td class="cell-id" title="Id">{{ s.id }}</td>
            <!-- Se name non esiste, mostriamo l'id come fallback -->
            <td>{{ s.name || s.id }}</td>
            <td class="cell-address">{{ s.address || "N/A" }}</td>
            <td class="cell-city">{{ s.city || "N/A" }}</td>

            <!-- NuxtLink per navigazione senza ricaricare la pagina -->
            <td>
              <NuxtLink
                class="action-link"
                :to="`/station/${s.id}`"
                :aria-label="`Apri dettagli stazione ${s.name || s.id}`"
              >
                Apri
              </NuxtLink>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
// IMPORT
// - ref, onMounted: reactive state e lifecycle hook di Vue
// - useApi: composable (se presente) per centralizzare le chiamate API
import { ref, onMounted } from "vue";
import { useApi } from "../../composables/useApi";

/*
  TIPIZZAZIONE (consigliata)
  - Definiamo qui una interfaccia minima Station per migliorare il controllo dei tipi.
  - Adattala ai campi reali restituiti dal backend.
*/
interface Station {
  id: string;
  name?: string;
  address?: string; // indirizzo (solo la parte "addressOnly" dopo normalizzazione)
  city?: string; // città estratta dalla stringa raw
  [k: string]: any;

  // aggiungi altri campi reali qui se li conosci
}

/* STATO LOCALE
   - api: istanza del composable che astrae le chiamate al backend
   - loading: true mentre attendiamo la risposta
   - error: messaggio di errore da mostrare in UI (null se tutto ok)
   - stations: ref che conterrà un array di Station (inizialmente vuoto)
*/
const api = useApi();
const loading = ref<boolean>(true);
const error = ref<string | null>(null);
const stations = ref<Station[]>([]);

/*
  FUNZIONE splitAddress
  - Divide una stringa di indirizzo in due parti: addressOnly e city
  - Usa la virgola come separatore
  - Split address più robusto:
    * - prova separatori ("," e " - ")
    * - se non ci sono, usa euristica sulle ultime parole
    * - gestisce input undefined/null
    * - restituisce sempre { addressOnly, city } dove i valori sono stringhe (possibilmente vuote)
*/
function splitAddress(raw: string | undefined) {
  // Normalizziamo input: convertiamo undefined/null in stringa vuota e rimuoviamo spazi esterni
  const s = (raw ?? "").trim();
  if (!s) return { addressOnly: "", city: "" };

  // prova con virgola (es. "Via X, Città")
  const byComma = s
    .split(",")
    .map((p) => p.trim())
    .filter(Boolean);
  if (byComma.length > 1) {
    const city = byComma[byComma.length - 1];
    const addressOnly = byComma.slice(0, -1).join(", ");
    return { addressOnly, city };
  }

  // prova con trattino " - " (altro formato comune)
  const byDash = s
    .split(" - ")
    .map((p) => p.trim())
    .filter(Boolean);
  if (byDash.length > 1) {
    const city = byDash[byDash.length - 1];
    const addressOnly = byDash.slice(0, -1).join(", ");
    return { addressOnly, city };
  }

  // Se non ci sono separatori chiari, tentiamo un'euristica:
  // prendiamo le ultime 1-3 parole come possibile città, privilegiando prefissi comuni (San, Santa, Monte, ecc.)
  const tokens = s.split(/\s+/).filter(Boolean);
  if (tokens.length <= 1) return { addressOnly: s, city: "" };

  // costruiamo possibili estrazioni
  const lastTwo = tokens.slice(-2).join(" ");
  const penultimate = tokens[tokens.length - 2]?.toLowerCase() ?? "";
  const commonPrefixes = ["san", "santa", "monte", "porto", "colle"];

  // se la penultima parola è un prefisso comune, proviamo a prendere 3 parole per la città
  if (commonPrefixes.includes(penultimate) && tokens.length >= 3) {
    const maybeCity = tokens.slice(-3).join(" ");
    const addressOnly = tokens.slice(0, -3).join(" ");
    return { addressOnly: addressOnly || s, city: maybeCity };
  }

  // fallback: consideriamo le ultime 2 parole come città plausibile
  const addressOnly = tokens.slice(0, -2).join(" ");
  return { addressOnly: addressOnly || s, city: lastTwo };
}

/*
  FUNZIONE loadList
  - Recupera i dati dalla API o dal composable api.getStations
  - Normalizza il payload per garantire che stations.value sia sempre un array
  - Arricchisce ogni record con fields address (addressOnly) e city (estratta)
  - Gestisce gli errori impostando error.value e svuotando stations se necessario
*/
async function loadList() {
  // segnaliamo inizio caricamento
  loading.value = true;
  error.value = null;

  try {
    // payload può essere:
    // - direttamente un array: [ { id, name, ... }, ... ]
    // - oppure un wrapper: { stations: [ ... ], meta: {...} }
    // - o qualsiasi altra struttura: per questo normalizziamo dopo
    const payload =
      typeof api.getStations === "function"
        ? // se il composable è presente, lo usiamo (gestisce baseUrl, token, ecc.)
          await api.getStations()
        : // altrimenti fallback a fetch standard
          await fetch("/api/stations").then((r) => {
            // se la risposta non è ok lanciamo un errore per essere gestito dal catch
            if (!r.ok) throw new Error(`HTTP ${r.status}`);
            return r.json();
          });

    // DEBUG: log del payload grezzo per ispezionare la forma della risposta
    // Rimuovi o commenta questi console.log in produzione
    console.log("[index] raw payload", payload);

    // NORMALIZZAZIONE INIZIALE:
    // - Se payload è un array lo usiamo direttamente
    // - Altrimenti, se payload.stations è presente e è un array lo usiamo
    // - Se nessuna delle due condizioni è vera, assegniamo array vuoto
    const rawArray: any[] = Array.isArray(payload)
      ? payload
      : Array.isArray(payload?.stations)
      ? payload.stations
      : [];

    // Normalizza e arricchisci con address/city
    // - cerchiamo sia item.address sia item.indirizzo per tollerare API italiane
    stations.value = rawArray.map((item) => {
      const rawAddr: string | undefined = item.address ?? item.indirizzo ?? "";
      // estraiamo addressOnly e city dalla stringa raw
      const { addressOnly, city } = splitAddress(rawAddr);
      const normalized: Station = {
        ...item,
        // address contiene la parte "indirizzo" (senza città)
        address: addressOnly || rawAddr || "",
        // city contiene la città estratta (se trovata), altrimenti stringa vuota
        city: city || "",
      };
      return normalized;
    });

    // DEBUG: conferma che stations.value ora è un array e contiene campi address/city
    console.log("[index] stations normalized", stations.value);
  } catch (e: any) {
    // In caso di errore:
    // - logghiamo l'errore per il debug
    // - mostriamo un messaggio in UI
    // - assicuriamoci che stations sia un array (svuotato)
    console.error("[index] load error", e);
    error.value = e?.message ?? String(e);
    stations.value = [];
  } finally {
    // Fine del caricamento, sempre
    loading.value = false;
  }
}

/* CARICAMENTO INIZIALE
   - All'onMounted chiamiamo loadList per popolare la tabella appena la pagina viene montata.
*/
onMounted(() => loadList());
</script>
