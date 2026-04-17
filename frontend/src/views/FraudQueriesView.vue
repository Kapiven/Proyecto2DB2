<template>
  <section class="content-grid">
    <div class="section-panel">
      <p class="eyebrow">Reglas automáticas</p>
      <h3>Motor heurístico</h3>
      <ul class="plain-list">
        <li v-for="rule in rules" :key="rule">{{ rule }}</li>
      </ul>
      <button class="primary-button" @click="runDetection">Ejecutar detección</button>
      <pre>{{ detectionResult }}</pre>
    </div>

    <div class="section-panel">
      <div class="section-header">
        <div>
          <p class="eyebrow">Cypher</p>
          <h3>Consultas de demostración</h3>
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
import DataTable from "../components/DataTable.vue";

const rules = ref([]);
const queries = ref([]);
const detectionResult = ref("");

async function loadRules() {
  const { data } = await api.get("/fraud/rules/");
  rules.value = data.rules;
}

async function loadQueries() {
  const { data } = await api.get("/analytics/demo-queries/");
  queries.value = data;
}

async function runDetection() {
  const { data } = await api.post("/fraud/detect/");
  detectionResult.value = JSON.stringify(data, null, 2);
}

onMounted(async () => {
  await loadRules();
  await loadQueries();
});
</script>
