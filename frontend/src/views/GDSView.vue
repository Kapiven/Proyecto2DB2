<template>
  <section class="content-grid">
    <div class="section-panel">
      <p class="eyebrow">Graph Data Science</p>
      <h3>Gestión del grafo proyectado</h3>
      <div class="form-grid">
        <button class="primary-button" @click="projectGraph">Project Graph</button>
        <button class="secondary-button" @click="checkGraphExists">Verificar proyección</button>
        <button class="secondary-button" @click="dropGraph">Eliminar proyección</button>
      </div>
      <pre>{{ JSON.stringify(graphStatus, null, 2) }}</pre>
    </div>

    <div class="section-panel">
      <p class="eyebrow">Algoritmos</p>
      <h3>Ejecución GDS</h3>
      <div class="form-grid">
        <button class="primary-button" @click="runPageRank">Run PageRank</button>
        <button class="primary-button" @click="runLouvain">Run Louvain</button>
        <button class="primary-button" @click="runSimilarity">Run Similarity</button>
      </div>
    </div>

    <div class="section-panel">
      <p class="eyebrow">Ruta mínima</p>
      <h3>Shortest Path entre clientes</h3>
      <div class="form-grid">
        <input v-model="sourceId" placeholder="source_id para shortest path" />
        <input v-model="targetId" placeholder="target_id para shortest path" />
        <button class="primary-button" @click="runShortestPath">Shortest Path</button>
      </div>
    </div>

    <div class="section-panel">
      <div class="section-header">
        <div>
          <p class="eyebrow">Resultados</p>
          <h3>Salida lista para el frontend</h3>
        </div>
      </div>
      <p v-if="errorMessage" class="status-text">{{ errorMessage }}</p>
      <pre v-if="resultMeta">{{ JSON.stringify(resultMeta, null, 2) }}</pre>
      <DataTable v-if="resultRows.length" :rows="resultRows" />
    </div>
  </section>
</template>

<script setup>
import { ref } from "vue";
import api from "../api/client";
import DataTable from "../components/DataTable.vue";

const sourceId = ref("");
const targetId = ref("");
const graphStatus = ref({});
const resultMeta = ref(null);
const resultRows = ref([]);
const errorMessage = ref("");

function setResult(data) {
  resultMeta.value = {
    algorithm: data.algorithm || null,
    graphName: data.graphName || null,
    total: Array.isArray(data.results) ? data.results.length : null
  };
  resultRows.value = Array.isArray(data.results) ? data.results : [];
}

function setError(error) {
  errorMessage.value = error?.response?.data?.detail || error.message || "Ocurrió un error al ejecutar GDS.";
}

async function checkGraphExists() {
  errorMessage.value = "";
  try {
    const { data } = await api.post("/gds/exists/");
    graphStatus.value = data;
  } catch (error) {
    setError(error);
  }
}

async function projectGraph() {
  errorMessage.value = "";
  try {
    const { data } = await api.post("/gds/project/");
    graphStatus.value = data;
  } catch (error) {
    setError(error);
  }
}

async function dropGraph() {
  errorMessage.value = "";
  try {
    const { data } = await api.delete("/gds/drop/");
    graphStatus.value = data;
  } catch (error) {
    setError(error);
  }
}

async function runPageRank() {
  errorMessage.value = "";
  try {
    const { data } = await api.post("/gds/pagerank/");
    setResult(data);
  } catch (error) {
    setError(error);
  }
}

async function runLouvain() {
  errorMessage.value = "";
  try {
    const { data } = await api.post("/gds/louvain/");
    setResult(data);
  } catch (error) {
    setError(error);
  }
}

async function runSimilarity() {
  errorMessage.value = "";
  try {
    const { data } = await api.post("/gds/similarity/");
    setResult(data);
  } catch (error) {
    setError(error);
  }
}

async function runShortestPath() {
  errorMessage.value = "";
  try {
    const { data } = await api.post("/gds/shortest-path/", {
      source_id: sourceId.value,
      target_id: targetId.value
    });
    setResult(data);
  } catch (error) {
    setError(error);
  }
}
</script>
