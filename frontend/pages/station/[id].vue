<template>
    <div>
      <NuxtLink to="/">← Torna</NuxtLink>
      <h1>Dettaglio stazione: {{ stationId }}</h1>
  
      <div v-if="loading">Caricamento...</div>
      <div v-else-if="error" class="error">{{ error }}</div>
      <div v-else>
        <!-- evidenzia la media pesata per metrica -->
        <div v-if="weightedKeys.length">
          <h2>Media pesata ultimi 7 giorni</h2>
          <div v-for="k in weightedKeys" :key="k" class="badge">
            <strong>{{ k }}</strong>: {{ weightedMap[k] ?? 'N/A' }}
          </div>
        </div>
  
        <!-- tabella giorni (ultimi 10) per metrica selezionata -->
        <div v-if="metricsList.length">
          <h2>Metriche</h2>
          <select v-model="selectedMetric">
            <option v-for="m in metricsList" :key="m" :value="m">{{ m }}</option>
          </select>
  
          <table>
            <thead><tr><th>Data</th><th>Min</th><th>Avg</th><th>Max</th><th>Sample size</th></tr></thead>
            <tbody>
              <tr v-for="d in currentDays" :key="d.date">
                <td>{{ d.date }}</td>
                <td>{{ d.min }}</td>
                <td>{{ d.average }}</td>
                <td>{{ d.max }}</td>
                <td>{{ d.sample_size }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </template>
  
  <script setup lang="ts">
  import { ref, computed, onMounted } from 'vue'
  import { useRoute } from 'vue-router'
  import { useApi } from '~/composables/useApi'
  
  const route = useRoute()
  const stationId = route.params.id as string
  const api = useApi()
  
  const loading = ref(true)
  const error = ref<string | null>(null)
  const stationData = ref<any>(null)
  
  const weightedMap = ref<Record<string, any>>({})
  const metricsList = ref<string[]>([])
  const selectedMetric = ref<string | null>(null)
  
  onMounted(async () => {
    try {
      const data = await api.getStation(stationId)
      stationData.value = data
  
      // weighted_average_7d come aggiunto dal backend
      if (data && data.weighted_average_7d) {
        weightedMap.value = data.weighted_average_7d
      }
  
      // estraiamo metriche: cerca sotto 'metrics' o fallback su chiavi che contengono liste
      let metrics = {}
      if (data.metrics) metrics = data.metrics
      else {
        for (const k in data) {
          if (Array.isArray(data[k]) && data[k].length && data[k][0].average !== undefined) {
            metrics[k] = data[k]
          }
        }
      }
      metricsList.value = Object.keys(metrics)
      selectedMetric.value = metricsList.value[0] || null
  
      // salva le serie in stationData per uso nella tabella
      stationData.value.metrics = metrics
    } catch (e: any) {
      error.value = e?.message || 'Errore caricamento dettaglio'
    } finally {
      loading.value = false
    }
  })
  
  const weightedKeys = computed(() => Object.keys(weightedMap.value))
  
  const currentDays = computed(() => {
    if (!selectedMetric.value || !stationData.value || !stationData.value.metrics) return []
    return stationData.value.metrics[selectedMetric.value] || []
  })
  </script>
  
  <style scoped>
  /* stili minimi per leggibilità */
  table { width: 100%; border-collapse: collapse; margin-top: 1rem;}
  th, td { padding: 8px; border: 1px solid #ddd; text-align: left;}
  .badge { display: inline-block; margin-right: 10px; padding: 6px; background: #eef; border-radius: 6px; }
  .error { color: red; }
  </style>