<template>
  <section class="content-grid">
    <div class="hero-panel">
      <p class="eyebrow">Visión general</p>
      <h3>Estado del grafo de fraude</h3>
      <p>
        Esta vista resume el tamaño del grafo, el volumen transaccional y la carga operativa de alertas.
      </p>
      <button class="primary-button" @click="loadDashboard">Actualizar KPIs</button>
    </div>

    <p class="status-text" v-if="statusMessage">{{ statusMessage }}</p>
    <div class="kpi-grid">
      <KpiCard label="Total nodos" :value="dashboard.total_nodos || 0" />
      <KpiCard label="Total relaciones" :value="dashboard.total_relaciones || 0" />
      <KpiCard label="Transacciones" :value="dashboard.total_transacciones || 0" />
      <KpiCard label="Sospechosas" :value="dashboard.transacciones_sospechosas || 0" />
      <KpiCard label="Alertas" :value="dashboard.total_alertas || 0" />
    </div>

    <div class="section-panel">
      <div class="section-header">
        <div>
          <p class="eyebrow">Agregaciones</p>
          <h3>Resumen analítico</h3>
        </div>
        <button class="secondary-button" @click="loadAggregations">Refrescar</button>
      </div>

      <div class="aggregation-grid">
        <article v-for="(rows, key) in aggregations" :key="key" class="aggregation-card">
          <h4>{{ key }}</h4>
          <DataTable :rows="rows.slice(0, 5)" />
        </article>
      </div>
    </div>
  </section>
</template>

<script setup>
import { onMounted, ref } from "vue";
import api from "../api/client";
import { formatApiError } from "../utils/apiError";
import KpiCard from "../components/KpiCard.vue";
import DataTable from "../components/DataTable.vue";

const dashboard = ref({});
const aggregations = ref({});
const statusMessage = ref("");

async function loadDashboard() {
  statusMessage.value = "";
  try {
    const { data } = await api.get("/dashboard/");
    dashboard.value = data;
  } catch (error) {
    statusMessage.value = formatApiError(error);
  }
}

async function loadAggregations() {
  statusMessage.value = "";
  try {
    const { data } = await api.get("/analytics/aggregations/");
    aggregations.value = data;
  } catch (error) {
    statusMessage.value = formatApiError(error);
  }
}

onMounted(async () => {
  await loadDashboard();
  await loadAggregations();
});
</script>
