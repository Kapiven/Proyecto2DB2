<template>
  <section class="content-grid">
    <div class="section-panel">
      <p class="eyebrow">Bootstrap</p>
      <h3>Preparar índices en Neo4j</h3>
      <button class="primary-button" @click="bootstrap">Inicializar esquema</button>
    </div>

    <div class="section-panel">
      <p class="eyebrow">Carga por CSV</p>
      <h3>Importación manual</h3>
      <div class="form-grid">
        <select v-model="entityType">
          <option v-for="option in options" :key="option" :value="option">{{ option }}</option>
        </select>
        <input type="file" @change="onFileChange" />
        <button class="secondary-button" @click="uploadCSV">Subir CSV</button>
      </div>
    </div>

    <div class="section-panel">
      <p class="eyebrow">Generación masiva</p>
      <h3>Datos falsos conectados</h3>
      <div class="form-grid">
        <input v-model.number="generator.total_clientes" type="number" />
        <input v-model.number="generator.cuentas_por_cliente" type="number" />
        <input v-model.number="generator.transacciones_por_cuenta" type="number" />
        <button class="primary-button" @click="generateFakeData">Generar más de 5000 nodos</button>
      </div>
    </div>

    <div class="section-panel">
      <h3>Resultado</h3>
      <p class="status-text" v-if="statusMessage">{{ statusMessage }}</p>
      <pre>{{ statusMessage }}</pre>
    </div>
  </section>
</template>

<script setup>
import { reactive, ref } from "vue";
import api from "../api/client";
import { formatApiError } from "../utils/apiError";

const options = [
  "Cliente",
  "Cuenta",
  "Tarjeta",
  "Transaccion",
  "Dispositivo",
  "Ubicacion",
  "Comercio",
  "Banco",
  "Alerta",
  "TIENE_CUENTA",
  "USA_DISPOSITIVO",
  "TIENE_TARJETA",
  "ORIGINA",
  "DESTINADA_A",
  "UTILIZA_DISPOSITIVO",
  "DESDE_UBICACION",
  "EN_COMERCIO",
  "UTILIZA_TARJETA",
  "GENERA_ALERTA",
  "PERTENECE_A",
  "LOCALIZADO_EN",
  "REMITE",
  "INTERACTUA",
];
const entityType = ref("Cliente");
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
  } catch (error) {
    statusMessage.value = formatApiError(error);
  }
}

async function uploadCSV() {
  statusMessage.value = "";
  try {
    const formData = new FormData();
    formData.append("entity_type", entityType.value);
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
