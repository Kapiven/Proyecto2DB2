<template>
  <section class="content-grid">
    <div class="section-panel">
      <div class="section-header">
        <div>
          <p class="eyebrow">CRUD de nodos</p>
          <h3>Crear y consultar nodos</h3>
        </div>
        <button class="secondary-button" @click="loadNodes">Cargar nodos</button>
      </div>

      <div class="form-grid">
        <input v-model="filters.label" placeholder="Etiqueta, por ejemplo Cliente" />
        <input v-model="filters.property_name" placeholder="Propiedad a filtrar" />
        <input v-model="filters.property_value" placeholder="Valor" />
        <button class="primary-button" @click="loadNodes">Filtrar</button>
      </div>

      <DataTable :rows="nodes" />
    </div>

    <div class="section-panel">
      <p class="eyebrow">Nuevo nodo</p>
      <h3>Alta rápida</h3>
      <div class="form-grid">
        <input v-model="createForm.labelInput" placeholder="Etiquetas separadas por coma" />
        <div class="properties-grid">
          <div class="property-row" v-for="(row, index) in createForm.propertyRows" :key="index">
            <input v-model="row.key" placeholder="Propiedad" />
            <input v-model="row.value" placeholder="Valor" />
          </div>
          <button type="button" class="secondary-button small" @click="createForm.propertyRows.push({ key: '', value: '' })">
            Agregar propiedad
          </button>
        </div>
        <button class="primary-button" @click="createNode">Crear nodo</button>
      </div>
    </div>

    <div class="section-panel">
      <p class="eyebrow">Etiquetas dinámicas</p>
      <h3>Asignar o remover labels</h3>
      <div class="form-grid">
        <input v-model="labelForm.baseLabel" placeholder="Etiqueta base" />
        <input v-model="labelForm.nodeId" placeholder="ID del nodo" />
        <input v-model="labelForm.dynamicLabel" placeholder="Etiqueta dinámica" />
        <select v-model="labelForm.action">
          <option value="add">Agregar</option>
          <option value="remove">Remover</option>
        </select>
        <button class="secondary-button" @click="updateDynamicLabel">Aplicar</button>
      </div>
      <p class="status-text">{{ message }}</p>
    </div>

    <div class="section-panel">
      <p class="eyebrow">Operaciones en lote</p>
      <h3>Propiedades y borrado masivo</h3>
      <div class="form-grid">
        <input v-model="batchForm.label" placeholder="Etiqueta" />
        <input v-model="batchForm.nodeIdsInput" placeholder="IDs separados por coma" />
        <div class="properties-grid">
          <div class="property-row" v-for="(row, index) in batchForm.propertyRows" :key="index">
            <input v-model="row.key" placeholder="Propiedad" />
            <input v-model="row.value" placeholder="Valor" />
          </div>
          <button type="button" class="secondary-button small" @click="batchForm.propertyRows.push({ key: '', value: '' })">
            Agregar propiedad
          </button>
        </div>
        <button class="primary-button" @click="batchUpdateProperties">Actualizar propiedades</button>
      </div>
      <div class="form-grid">
        <input v-model="batchRemoveForm.label" placeholder="Etiqueta" />
        <input v-model="batchRemoveForm.nodeIdsInput" placeholder="IDs separados por coma" />
        <input v-model="batchRemoveForm.propertyNamesInput" placeholder="Propiedades separadas por coma" />
        <button class="secondary-button" @click="batchRemoveProperties">Eliminar propiedades</button>
      </div>
      <div class="form-grid">
        <input v-model="batchDeleteForm.label" placeholder="Etiqueta" />
        <input v-model="batchDeleteForm.nodeIdsInput" placeholder="IDs separados por coma" />
        <button class="secondary-button" @click="batchDeleteNodes">Eliminar nodos</button>
      </div>
      <p class="status-text">{{ batchMessage }}</p>
    </div>
  </section>
</template>

<script setup>
import { onMounted, reactive, ref } from "vue";
import api from "../api/client";
import { formatApiError } from "../utils/apiError";
import DataTable from "../components/DataTable.vue";

const nodes = ref([]);
const message = ref("");
const filters = reactive({ label: "", property_name: "", property_value: "" });
const createForm = reactive({
  labelInput: "Cliente,RiesgoBajo",
  propertyRows: [
    { key: "id", value: "CLI-MANUAL-1" },
    { key: "nombre", value: "Cliente Manual" },
    { key: "edad", value: "29" },
    { key: "genero", value: "F" },
    { key: "email", value: "manual@example.com" }
  ]
});
const labelForm = reactive({
  baseLabel: "Cliente",
  nodeId: "CLI-MANUAL-1",
  dynamicLabel: "RiesgoBajo",
  action: "add"
});
const batchForm = reactive({
  label: "Cliente",
  nodeIdsInput: "CLI-MANUAL-1,CLI-MANUAL-2",
  propertyRows: [
    { key: "riesgo", value: "0.55" },
    { key: "nivel_riesgo", value: "Medio" }
  ]
});
const batchRemoveForm = reactive({
  label: "Cliente",
  nodeIdsInput: "CLI-MANUAL-1,CLI-MANUAL-2",
  propertyNamesInput: "telefono,email"
});
const batchDeleteForm = reactive({
  label: "Cliente",
  nodeIdsInput: "CLI-MANUAL-1,CLI-MANUAL-2"
});
const batchMessage = ref("");

function collectProperties(rows) {
  return rows.reduce((result, { key, value }) => {
    const trimmedKey = key?.trim();
    if (trimmedKey) {
      result[trimmedKey] = parseSimpleValue(value);
    }
    return result;
  }, {});
}

function parseCsv(value) {
  return String(value)
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function parseSimpleValue(value) {
  if (value === null || value === undefined) return value;
  const text = String(value).trim();
  if (text === "") return "";
  if (/^(true|false)$/i.test(text)) return text.toLowerCase() === "true";
  if (!Number.isNaN(Number(text)) && text !== "") return Number(text);
  return text;
}

async function loadNodes() {
  message.value = "";
  try {
    const { data } = await api.get("/nodes/", { params: filters });
    nodes.value = data;
  } catch (error) {
    message.value = formatApiError(error);
  }
}

async function createNode() {
  try {
    await api.post("/nodes/", {
      labels: createForm.labelInput.split(",").map((item) => item.trim()).filter(Boolean),
      properties: collectProperties(createForm.propertyRows)
    });
    message.value = "Nodo creado correctamente.";
    await loadNodes();
  } catch (error) {
    message.value = formatApiError(error);
  }
}

async function updateDynamicLabel() {
  try {
    await api.post(`/nodes/${labelForm.baseLabel}/${labelForm.nodeId}/labels/`, {
      label: labelForm.dynamicLabel,
      action: labelForm.action
    });
    message.value = "Etiqueta dinámica actualizada.";
    await loadNodes();
  } catch (error) {
    message.value = formatApiError(error);
  }
}

async function batchUpdateProperties() {
  try {
    const node_ids = parseCsv(batchForm.nodeIdsInput);
    const properties = collectProperties(batchForm.propertyRows);
    await api.post("/nodes/properties/batch/", {
      label: batchForm.label,
      node_ids,
      properties
    });
    batchMessage.value = "Propiedades actualizadas en lote.";
    await loadNodes();
  } catch (error) {
    batchMessage.value = formatApiError(error);
  }
}

async function batchRemoveProperties() {
  try {
    const node_ids = parseCsv(batchRemoveForm.nodeIdsInput);
    const property_names = parseCsv(batchRemoveForm.propertyNamesInput);
    await api.delete("/nodes/properties/batch/", { data: {
      label: batchRemoveForm.label,
      node_ids,
      property_names
    }});
    batchMessage.value = "Propiedades eliminadas en lote.";
    await loadNodes();
  } catch (error) {
    batchMessage.value = formatApiError(error);
  }
}

async function batchDeleteNodes() {
  try {
    const node_ids = parseCsv(batchDeleteForm.nodeIdsInput);
    await api.post("/nodes/delete/", {
      label: batchDeleteForm.label,
      node_ids
    });
    batchMessage.value = "Nodos eliminados en lote.";
    await loadNodes();
  } catch (error) {
    batchMessage.value = formatApiError(error);
  }
}

onMounted(loadNodes);
</script>

<style scoped>
.properties-grid {
  display: grid;
  gap: 12px;
}
.property-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
.property-row input {
  width: 100%;
}
button.small {
  width: fit-content;
  padding: 10px 14px;
  font-size: 13px;
}
</style>
