<template>
  <section class="content-grid">
    <div class="section-panel">
      <p class="eyebrow">Reglas automaticas</p>
      <h3>Motor heuristico</h3>
      <p class="status-text" v-if="errorMessage">{{ errorMessage }}</p>
      <ul class="plain-list">
        <li v-for="rule in rules" :key="rule">{{ rule }}</li>
      </ul>
      <button class="primary-button" @click="runDetection">Ejecutar deteccion real</button>
      <article v-if="detectionResult" class="fraud-report">
        {{ detectionResult }}
      </article>
    </div>

    <div class="section-panel">
      <div class="section-header">
        <div>
          <p class="eyebrow">Cypher</p>
          <h3>Consultas de demostracion</h3>
        </div>
        <button class="secondary-button" @click="loadQueries">Recargar</button>
      </div>
      <article v-for="query in queries" :key="query.name" class="query-card">
        <h4>{{ query.name }}</h4>
        <pre>{{ query.cypher }}</pre>
        <DataTable :rows="query.results" />
      </article>
    </div>
  </section>
</template>

<script setup>
import { onMounted, ref } from "vue";
import api from "../api/client";
import { formatApiError } from "../utils/apiError";
import DataTable from "../components/DataTable.vue";

const rules = ref([]);
const queries = ref([]);
const detectionResult = ref("");
const errorMessage = ref("");

async function loadRules() {
  errorMessage.value = "";
  try {
    const { data } = await api.get("/fraud/rules/");
    rules.value = data.rules;
  } catch (error) {
    errorMessage.value = formatApiError(error);
  }
}

async function loadQueries() {
  errorMessage.value = "";
  try {
    const { data } = await api.get("/analytics/demo-queries/");
    queries.value = data;
  } catch (error) {
    errorMessage.value = formatApiError(error);
  }
}

async function runDetection() {
  errorMessage.value = "";
  detectionResult.value = "";
  try {
    const { data } = await api.post("/fraud/detect/?report=text", null, {
      responseType: "text"
    });
    detectionResult.value = data;
  } catch (error) {
    errorMessage.value = formatApiError(error);
  }
}

onMounted(async () => {
  await loadRules();
  await loadQueries();
});
</script>
