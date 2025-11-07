<template>
  <header>
    <h1>Air Quality Dashboard</h1>
  </header>

  <!-- Punto di render delle pagine; :key forza remount quando cambia la route -->
  <NuxtPage :key="$route.fullPath" />

  <footer>
    <small>Footer</small>
  </footer>
</template>

<script setup>
// Log per verificare che il layout venga renderizzato
console.log("[layout default] render");
</script>
