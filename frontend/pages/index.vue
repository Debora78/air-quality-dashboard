<template>
    <div>
      <h1>Stazioni</h1>
      <div v-if="loading">Caricamento...</div>
      <div v-else-if="error" class="error">{{ error }}</div>
      <div v-else>
        <table>
          <thead><tr><th>Id</th><th>Nome</th><th>Azioni</th></tr></thead>
          <tbody>
            <tr v-for="s in stations" :key="s.id">
              <td>{{ s.id }}</td>
              <td>{{ s.name || s.id }}</td>
              <td><NuxtLink :to="`/station/${s.id}`">Apri</NuxtLink></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </template>
  
  <script setup lang="ts">
  import { ref, onMounted } from 'vue'
  import { useApi } from '~/composables/useApi'
  
  const stations = ref([])
  const loading = ref(true)
  const error = ref<string | null>(null)
  const api = useApi()
  
  onMounted(async () => {
    try {
      const data = await api.getStations()
      stations.value = Array.isArray(data) ? data : (data.stations || [])
    } catch (e: any) {
      error.value = e?.message || 'Errore caricamento stazioni'
    } finally {
      loading.value = false
    }
  })
  </script>