<template>
  <section class="content-grid">
    <div class="section-panel">
      <div class="section-header">
        <div>
          <p class="eyebrow">Reglas automaticas</p>
          <h3>Motor de fraude</h3>
        </div>
        <button class="primary-button" @click="runDetection">Ejecutar deteccion</button>
      </div>

      <p class="status-text" v-if="errorMessage">{{ errorMessage }}</p>

      <div v-if="summary" class="fraud-summary">
        <div>
          <span>Nivel</span>
          <strong>{{ summary.risk_level }}</strong>
        </div>
        <div>
          <span>Evidencias</span>
          <strong>{{ summary.total_alerts }}</strong>
        </div>
        <div>
          <span>Reglas activadas</span>
          <strong>{{ summary.rules_triggered }}</strong>
        </div>
      </div>

      <div class="rule-catalog" v-if="rules.length">
        <article v-for="rule in rules" :key="rule.rule || rule" class="rule-item">
          <strong>{{ rule.name || rule }}</strong>
          <p>{{ rule.description || "" }}</p>
        </article>
      </div>
    </div>

    <div v-if="detectionRules.length" class="content-grid">
      <article v-for="rule in detectionRules" :key="rule.rule" class="section-panel fraud-rule-card">
        <div class="section-header">
          <div>
            <p class="eyebrow">{{ rule.rule }}</p>
            <h3>{{ rule.title }}</h3>
          </div>
          <strong class="rule-count">{{ rule.count }}</strong>
        </div>
        <DataTable :rows="rule.results" />
        <details class="cypher-details">
          <summary>Ver Cypher</summary>
          <pre>{{ rule.cypher }}</pre>
        </details>
      </article>
    </div>

    <div class="section-panel">
      <div class="section-header">
        <div>
          <p class="eyebrow">Consultas demo</p>
          <h3>Investigacion guiada</h3>
        </div>
        <button class="secondary-button" @click="loadQueries">Recargar</button>
      </div>

      <article v-for="query in queries" :key="query.name" class="query-card">
        <div class="section-header query-header">
          <div>
            <h4>{{ query.name }}</h4>
            <p>{{ query.description }}</p>
          </div>
          <button class="primary-button" @click="executeQuery(query)">Execute</button>
        </div>
        <DataTable v-if="query.executed" :rows="query.results" />
        <details class="cypher-details">
          <summary>Ver Cypher</summary>
          <pre>{{ query.cypher }}</pre>
        </details>
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
const summary = ref(null);
const detectionRules = ref([]);
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
    queries.value = data.map((query) => ({ ...query, executed: false }));
  } catch (error) {
    errorMessage.value = formatApiError(error);
  }
}

function executeQuery(query) {
  query.executed = true;
}

async function runDetection() {
  errorMessage.value = "";
  summary.value = null;
  detectionRules.value = [];
  try {
    const { data } = await api.post("/fraud/run-detection/");
    summary.value = data.summary;
    detectionRules.value = data.rules;
  } catch (error) {
    errorMessage.value = formatApiError(error);
  }
}

onMounted(async () => {
  await loadRules();
  await loadQueries();
});
</script>
