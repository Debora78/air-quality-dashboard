<template>
    <header>
      <h1>La mia app</h1>
    </header>
  
    <!-- Punto di render delle pagine; :key forza remount quando cambia la route -->
    <NuxtPage :key="$route.fullPath" />
  
    <footer>
      <small>Footer</small>
    </footer>
  </template>
  
  <script setup>
  // Log per verificare che il layout venga renderizzato
  console.log('[layout default] render');
  </script>
  
  <style scoped>
  header, footer { padding: 0.5rem; background: #f6f6f6; }
  </style>