<template>
  <!-- - Inizia il blocco visivo del componente- Tutto ciò che è HTML o Vue -->
  <!--
    App root: qui NON deve esserci la lista delle stazioni.
    Il contenuto delle singole pagine viene renderizzato tramite <NuxtPage />
    che funge da placeholder per pages/*.vue oppure per i layout.
  -->
  <header>
    <!-- Header globale: metti qui markup/brand statico (non logica di pagina) -->
    <h1>Air Quality Dashboard</h1>
  </header>

  <!--
    Punto di render per la pagina attiva.
    :key="$route.fullPath" forza il remount quando cambia la route
    utile in fase di debug per assicurarsi che il componente venga rimontato.
  -->
  <!-- <NuxtPage/> è un componente speciale di Nuxt 3 - serve come placeholder per la pagina attiva -->
  <!-- todo :key è una binding dinamica cioè collega un attributo HTML a una variabile o espressione che può cambiare, in Vue si scrive con : e rende il tamplate reattivo e intelligente -->
  <!-- "$route.fullPath" è una proprietà dell'oggetto $route in Nuxt(che usa Vue Router) e rappresenta l'intero URL corrente, inclusi path, parametri e query string
    Contiene:
    - path: solo il percorso (/stations)
    - params: parametri dinamici (/stations/:id)
    - query: parametri nella query string (?id=3)
    - fullPath: tutto insieme (/stations?id=3)
    -->
  <NuxtPage :key="$route.fullPath" />

  <footer>
    <!-- Footer globale -->
    <small>© 2025</small>
  </footer>
</template>

<!-- script setup Serve per gestire dati, eventi, logica del componente attivando il linguaggio typescript-->
<script setup lang="ts">
/*
  Questo file è il wrapper globale dell'app Nuxt.
  - Non importare qui componenti di pagina (es. lista stazioni).
  - Metti solo markup globale, provider o wrapper comuni se necessario.
  - Per debug temporaneo lasciamo un console.log per verificare che il file venga renderizzato.
*/
/* console.log("[app] render"); */
</script>
