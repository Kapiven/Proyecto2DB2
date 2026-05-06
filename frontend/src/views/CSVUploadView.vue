<template>
  <section class="content-grid">
    <div class="section-panel">
      <p class="eyebrow">Bootstrap</p>
      <h3>Preparar indices en Neo4j</h3>
      <button class="primary-button" @click="bootstrap">Inicializar esquema</button>
    </div>

    <div class="section-panel">
      <p class="eyebrow">Carga por CSV</p>
      <h3>Importacion unificada</h3>
      <div class="form-grid">
        <input type="file" accept=".csv,text/csv" @change="onFileChange" />
        <button class="secondary-button" @click="uploadCSV">Subir CSV</button>
      </div>
    </div>

    <div class="section-panel">
      <p class="eyebrow">Generacion masiva</p>
      <h3>Datos falsos conectados</h3>
      <div class="form-grid">
        <input v-model.number="generator.total_clientes" type="number" />
        <input v-model.number="generator.cuentas_por_cliente" type="number" />
        <input v-model.number="generator.transacciones_por_cuenta" type="number" />
        <button class="primary-button" @click="generateFakeData">Generar mas de 5000 nodos</button>
      </div>
    </div>

    <div class="section-panel">
      <h3>Resultado</h3>
      <p class="status-text" v-if="statusMessage">{{ statusMessage }}</p>
      <pre v-if="statusMessage">{{ statusMessage }}</pre>
      <p v-else style="color: #888;">La respuesta aparecerá aquí...</p>
    </div>
  </section>
</template>

<script setup>
import { reactive, ref } from "vue";
import api from "../api/client";
import { formatApiError } from "../utils/apiError";

const selectedFile = ref(null);
const statusMessage = ref("");
const generator = reactive({
  total_clientes: 1000,
  cuentas_por_cliente: 1,
  transacciones_por_cuenta: 4
});

function onFileChange(event) {
  selectedFile.value = event.target.files[0];
}

async function bootstrap() {
  statusMessage.value = "";
  try {
    const { data } = await api.post("/schema/bootstrap/");
    statusMessage.value = JSON.stringify(data, null, 2);
    console.log("Bootstrap result:", data);
  } catch (error) {
    statusMessage.value = formatApiError(error);
    console.error("Bootstrap error:", error);
  }
}

async function uploadCSV() {
  statusMessage.value = "";
  try {
    if (!selectedFile.value) {
      statusMessage.value = "Selecciona un archivo CSV unificado antes de subirlo.";
      return;
    }
    const formData = new FormData();
    formData.append("file", selectedFile.value);
    const { data } = await api.post("/upload/csv/", formData);
    statusMessage.value = JSON.stringify(data, null, 2);
  } catch (error) {
    statusMessage.value = formatApiError(error);
  }
}

async function generateFakeData() {
  statusMessage.value = "";
  try {
    const { data } = await api.post("/generate/fake-data/", generator);
    statusMessage.value = JSON.stringify(data, null, 2);
  } catch (error) {
    statusMessage.value = formatApiError(error);
  }
}
</script>
