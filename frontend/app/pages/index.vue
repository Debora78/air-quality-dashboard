<template>
  <!-- Pagina principale con la lista delle stazioni.
       Mostra stato di caricamento / errore / tabella con i risultati.
       I link usano NuxtLink per navigazione client-side verso /station/:id -->
  <div class="page-container">
    <h1>Stazioni</h1>

    <!-- Se stiamo caricando, mostriamo un messaggio di caricamento (v-if è una direttiva di Vue.js che usa per controllare il comportamento del DOM in  base allo stato dell'applicazione )
     todo Le direttive iniziano cone v- e servono per: - legare dati(es. v-model) - gestore eventi(es. v-onclick) - controllare la visibilità(es. v-if, v-show)-->
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

            <!-- NuxtLink per navigazione senza ricaricare la pagina, sostituisce <a href=".." 
             
            todo class="action-lind"(aggiunge la classe CSS action-link per stilizzare il link)
            * :to=""(Binding dinamico: costruisce l'URL in base a s.id. Se s.id = 42, il link sarà /station/42)
            todo :aria-label=""(etichetta per l'accessibilità. Se s.name = "Firenze", sarà:"Apri dettagli stazione Firenze". Se s.name è vuoto, usa s.id) -->
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
/*Importa 2 funzioni dalla libreria Vue:
 - ref()- Crea una variabile reattiva(cioè che Vue controlla per aggiornare il DOM quando cambia)
 - onMounted()- Esegue una funzione quando il componente è stato montato nel DOM(cioè visibile a schermo)
- Questa riga importa una funzione personalizzata chiamata useApi: che si trova nel file useApi.ts dentro la cartella composables */
import { ref, onMounted } from "vue";
import { useApi } from "../../composables/useApi";

/*
In TypeScript, un'interfaccia(interface)serve per descrivere la forma di un oggetto: quali proprietà ha, che tipo id dati contiene, e se sono obbligatore o facoltative
*/
interface Station {
  //Definisce un'interfaccia chiamata Station(Gli oggetti che la usano devono rispettare questa struttura)
  id: string; //id è una stringa che identifica univocamente la stazione(es. st123)

  //Proprietà facoltativa (grazie al ?)
  name?: string; //name è il nome della stazione(es. "firenze SMN")- se non presente non dà errore

  address?: string; // address è l'indirizzo della stazione,(solo la parte "addressOnly" dopo normalizzazione - separato dalla città)
  city?: string; // città estratta dalla stringa raw(ricevi un file JSON con dati grezzi)

  [k: string]: any /* L'oggetto può avere qualunque proprietà aggiuntiva con: 
  - una chiave di tipo stringa(k:string)
  - un valore di qualsiasi tipo(any) */;
}

/* STATO LOCALE
   - api: istanza del composable che astrae le chiamate al backend
   - loading: true mentre attendiamo la risposta
   - error: messaggio di errore da mostrare in UI (null se tutto ok)
   - stations: ref che conterrà un array di Station (inizialmente vuoto)
*/
const api = useApi(); // chiama la funzione useApi() che è importata da composables/useApi

/* ref(in Vue3 e Nuxt3) è una funzione della composition API che serve a creare variabili reattive */
const loading = ref<boolean>(true); //Crea una variabile reattiva chiamata loading, inizialmente impostata su true(serve per mostrare un messaggio di caricamento mentre i dati arrivano)

const error = ref<string | null>(null); //Crea una variabile reattiva chiamata error, inizialmente null - può contenere una stringa(es. "Errore rete") oppure null se non c'è errore - serve per gestire e mostrare gli errori delle chiamate API

const stations = ref<Station[]>([]); //Crea una variabile reattiva chiamata stations, inizalmente un array vuoto - il tipo è
// Station[], cioè un array di oggetti che seguono l'interfaccia Station - serve per memorizzare l'elenco delle stazioni ricevute dal backend

/*
  FUNZIONE splitAddress
  La funzione accetta una stringa oppure undefined
*/
function splitAddress(raw: string | undefined) {
  // Normalizziamo input: se raw è undefined, usa ""(stringa vuota) - applica .trim() per rimuovere spazi all'inizio e alla fine
  const s = (raw ?? "").trim();

  /* Controlla se la stringa è vuota: se s è vuoto(cioè false), la funzione esce subito e restituisce un oggetto con 2 stringhe */
  if (!s) return { addressOnly: "", city: "" };

  // Prova a dividere una stringa di indirizzo in due parti: - addressOnly ->la parte dell'indirizzo(es. "Via, n°, ecc") e city ->la città
  const byComma = s
    .split(",") //divide la stringa s in un array, separando dove trova la virgola

    .map((p) => p.trim()) //rinuove gli spazi da ogni parte

    .filter(Boolean); //Elimina eventuali elementi vuoti(es. ""), se ci sono

  if (byComma.length > 1) {
    //Controlla se ci sono almento 2 elementi(length > 1) cioè se la virgola ha effettivamente separato qualcosa - se sì, si presume che l'ultima parte sia la città

    const city = byComma[byComma.length - 1]; //prende l'ultimo elemento dell'array come città

    const addressOnly = byComma.slice(0, -1).join(", "); //prende tutti gli elementi tranne l'ultimo(slice(0, -1))cioè l'indirizzo - li unisce di nuovo con una virgola (se ci fossero più virgole)

    return { addressOnly, city }; //restituisce l'oggetto con le due parti separate
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
  //s.split(/\s+/)->divide la stringa in base agli spazi(\s+ vuol dire "uno o più spazi")

  const tokens = s.split(/\s+/).filter(Boolean); //.filter(Boolean)->rimuove eventuali elementi vuoti(es. se ci sono doppi spazi)
  if (tokens.length <= 1) return { addressOnly: s, city: "" }; //se c'è solo una parola, si restituisce tutto come addressOnly e city resta vuota

  // costruiamo possibili estrazioni quando non ci sono separatori chiari come virgole o trattini
  const lastTwo = tokens.slice(-2).join(" "); //Prende le ultime 2 parole e le unisce(testando se le ultime 2 parole formano una città composta)

  const penultimate = tokens[tokens.length - 2]?.toLowerCase() ?? ""; //Prende la penultima parola , in minuscolo - se non esiste(es. stringa troppo corta), usa ""

  const commonPrefixes = ["san", "santa", "monte", "porto", "colle"]; //Elenco di prefissi comuni nei nomi di città italiane - serve per capire se la penultima parola è un prefisso noto -> se sì è possibile che le ultime 2 parole siano una città

  // se la penultima parola è un prefisso comune, proviamo a prendere 3 parole per la città
  if (commonPrefixes.includes(penultimate) && tokens.length >= 3) {
    //Se la penultima parola(penultimate) è un predisso comune - ci sono almeno 3 parole nella stringa(tokens.length >= 3) - se entrambe le condizioni sono vere, è probabile che le ultime 3 parole siano una città composta

    const maybeCity = tokens.slice(-3).join(" "); //Prende le ultime 3 parole e le unisce in una stringa(es. "Via Roma 12 San Gimignano" ->maybeCity = "San Gimingnano")

    const addressOnly = tokens.slice(0, -3).join(" "); //Prende tutte le parole tranne le ultime 3 ->cioè la parte dell'indirizzo (es. "Via Roma 12 San Gimignano" -> "Via Roma")
    return { addressOnly: addressOnly || s, city: maybeCity };
  }

  // fallback: consideriamo le ultime 2 parole come città plausibile, escludendo eventuali numeri dalla città
  const isNumeric = (str: string) => /^\d+$/.test(str); // funzione per riconoscere numeri

  const lastTwoTokens = tokens.slice(-2); // prendiamo le ultime 2 parole

  const cityTokens = lastTwoTokens.filter((t) => !isNumeric(t)); // escludiamo i numeri dalla città
  const city = cityTokens.join(" "); // uniamo le parole rimanenti per formare la città

  // calcoliamo quante parole sono state usate per la città (escludendo i numeri)
  const addressOnly = tokens
    .slice(0, tokens.length - cityTokens.length)
    .join(" "); // il resto è l’indirizzo

  return { addressOnly: addressOnly || s, city };
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
  // Pulisce eventuali errori precedenti
  error.value = null;

  try {
    // payload può essere:
    // - direttamente un array: [ { id, name, ... }, ... ]
    // - oppure un wrapper: { stations: [ ... ], meta: {...} }
    // - o qualsiasi altra struttura: per questo normalizziamo dopo
    const payload =
      typeof api.getStations === "function" //Verifica se api.getStations esiste ed è una funzione
        ? // se sì, significa che  il composable è presente, e lo usa (gestisce baseUrl, token, ecc.)

          await api.getStations() //Chiama direttamente la funzione
        : // se non esiste usa fallback a fetch standard
          await fetch("/api/stations").then((r) => {
            //Fa una chiamata HTTP all'endopoint(/api/stations)

            if (!r.ok) throw new Error(`HTTP ${r.status}`); //se la risposta è OK(r.ok), lancia un errore con il codice HTTP
            return r.json(); // Atrimenti converte la risposta in JSON
          });

    // DEBUG: log del payload grezzo per ispezionare la forma della risposta
    // Rimuovi o commenta questi console.log in produzione
    console.log("[index] raw payload", payload);

    // NORMALIZZAZIONE INIZIALE:

    // - Altrimenti, se payload.stations è presente e è un array lo usiamo
    // - Se nessuna delle due condizioni è vera, assegniamo array vuoto
    const rawArray: any[] = Array.isArray(payload) // Se payload è un array lo assegna a rawArray
      ? payload //lo usiamo direttamente
      : Array.isArray(payload?.stations) //Se playload non è un array, controlla se ha una proprietà stations che è un array
      ? payload.stations //se sì, usa payload.stations come array
      : []; //se nessuna condizione è vera usa un array vuoto evitando errori se la risposta è malformata

    // Mappatura dell'array
    stations.value = rawArray.map((item) => {
      //Per ogni elemento dell'array(item), crea una nuova versione normalizzata(cioè semplificare i dati, correggere le incoerenze e standardizzare la struttura)

      const rawAddr: string | undefined = item.address ?? item.indirizzo ?? ""; //cerca l'indirizzo item.address(formato inglese) - item.indirizzo(formato italiano) - se non trova nulla usa la stringa vuota

      const { addressOnly, city } = splitAddress(rawAddr); // Usa la funzione splitAddress() per dividere: - addressOnly: solo la via - city: solo la città

      //COSTRUZIONE OGGETTO NORMALIZZATO
      const normalized: Station = {
        ...item, //Copia tutti i dati originali(id, name, indirizzo, city) - spreed operator(serve per copiare tutte le proprietà di un oggetto dentro un altro evitando di scrivere le proprietà manualmente)

        address: addressOnly || rawAddr || "", // Se address è valido, lo usa - altrimenti usa rawAddr(stringa che viene ricevuta da ciascun oggetto item nel payload che può trovarsi in item.address o item.indirizzo)

        city: city || "", // Se la variabile city contiene una città valida viene usata - se city è undefined, null o stringa vuota usa di default stringa vuota
      };
      return normalized; //Restituisce un oggetto chiamato normalized che rappresenta una stazione normalizzata
    });

    // DEBUG: conferma che stations.value ora è un array e contiene campi address/city
    console.log("[index] stations normalized", stations.value); //Stampa in console il messaggio "stations normalized" con il contenuto di stations.value - [index] è un'etichetta per sapere da quale file o componente arriva il log
  } catch (e: any) {
    // In caso qualcosa nel try fallisce

    console.error("[index] load error", e); //stampa l'errore in console

    error.value = e?.message ?? String(e); //Salva il messaggio di errore in error.vale, che può essere mostrato nella UI - se  e.message non esiste, converte l'errore in stringa

    stations.value = []; //Svuota la lista delle stazioni per evitare di mostrare dati vecchi o errati se il caricamento è fallito
  } finally {
    //Viene eseguito sempre, sia se il try ha successo, sia se c'è un errore

    loading.value = false; //Serve per chiudere il caricamento e nascondere lo spinner(elemento grafico che indica che il caricamnto)
  }
}

/* CARICAMENTO INIZIALE
   - onMounted è un hook(gancio)cioè una funzione speciale che permette di agganciare  un momento preciso del ciclo di vita di un componente o di un'applicazione ed eseguire codice personalizzato.
*/
onMounted(() => loadList()); //Quando il componente viene montato(cioè appare sullo schermo)esegui la funzione loadList()
</script>
