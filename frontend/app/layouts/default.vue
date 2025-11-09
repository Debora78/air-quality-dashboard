<template>
  <header>
    <h1>Air Quality Dashboard</h1>
  </header>

  <!-- Inserisce la pagina attiva(es. index.vue)nel layout - è gestito automaticamente da Nuxt -->
  <NuxtPage :key="$route.fullPath" />

  <footer>
    <small>Footer</small>
  </footer>
</template>

<script setup>
// Log per verificare che il layout venga renderizzato
console.log("[layout default] render");
</script>
