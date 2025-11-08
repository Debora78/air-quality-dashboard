<template>
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
  <NuxtPage :key="$route.fullPath" />

  <footer>
    <!-- Footer globale -->
    <small>© 2025</small>
  </footer>
</template>

<script setup lang="ts">
/*
  Questo file è il wrapper globale dell'app Nuxt.
  - Non importare qui componenti di pagina (es. lista stazioni).
  - Metti solo markup globale, provider o wrapper comuni se necessario.
  - Per debug temporaneo lasciamo un console.log per verificare che il file venga renderizzato.
*/
/* console.log("[app] render"); */
</script>
