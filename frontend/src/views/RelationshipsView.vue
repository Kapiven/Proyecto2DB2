<template>
  <section class="content-grid">
    <div class="section-panel">
      <div class="section-header">
        <div>
          <p class="eyebrow">CRUD de relaciones</p>
          <h3>Explorar y crear enlaces</h3>
        </div>
        <button class="secondary-button" @click="loadRelationships">Refrescar</button>
      </div>
      <DataTable :rows="relationships" />
    </div>

    <div class="section-panel">
      <p class="eyebrow">Nueva relación</p>
      <h3>Alta manual</h3>
      <div class="form-grid">
        <input v-model="form.relationship_type" placeholder="Tipo de relación" />
        <input v-model="form.start_label" placeholder="Etiqueta origen" />
        <input v-model="form.start_node_id" placeholder="ID nodo origen" />
        <input v-model="form.end_label" placeholder="Etiqueta destino" />
        <input v-model="form.end_node_id" placeholder="ID nodo destino" />
        <div class="properties-grid">
          <div class="property-row" v-for="(row, index) in form.propertyRows" :key="index">
            <input v-model="row.key" placeholder="Propiedad" />
            <input v-model="row.value" placeholder="Valor" />
          </div>
          <button type="button" class="secondary-button small" @click="form.propertyRows.push({ key: '', value: '' })">
            Agregar propiedad
          </button>
        </div>
        <button class="primary-button" @click="createRelationship">Crear relación</button>
      </div>
      <p v-if="createMessage" class="status-text">{{ createMessage }}</p>
    </div>

    <div class="section-panel">
      <p class="eyebrow">Operaciones en lote</p>
      <h3>Propiedades y borrado masivo</h3>
      <div class="form-grid">
        <input v-model="batchForm.relationshipIdsInput" placeholder="IDs de relaciones separadas por coma" />
        <div class="properties-grid">
          <div class="property-row" v-for="(row, index) in batchForm.propertyRows" :key="index">
            <input v-model="row.key" placeholder="Propiedad" />
            <input v-model="row.value" placeholder="Valor" />
          </div>
          <button type="button" class="secondary-button small" @click="batchForm.propertyRows.push({ key: '', value: '' })">
            Agregar propiedad
          </button>
        </div>
        <button class="primary-button" @click="batchUpdateProperties">Actualizar propiedades en relaciones</button>
      </div>
      <div class="form-grid">
        <input v-model="batchRemoveForm.relationshipIdsInput" placeholder="IDs de relaciones separadas por coma" />
        <input v-model="batchRemoveForm.propertyNamesInput" placeholder="Propiedades separadas por coma" />
        <button class="secondary-button" @click="batchRemoveProperties">Eliminar propiedades en relaciones</button>
      </div>
      <div class="form-grid">
        <input v-model="batchDeleteForm.relationshipIdsInput" placeholder="IDs de relaciones separadas por coma" />
        <button class="secondary-button" @click="batchDeleteRelationships">Eliminar relaciones</button>
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

const relationships = ref([]);
const createMessage = ref("");
const batchMessage = ref("");
const form = reactive({
  relationship_type: "TIENE_CUENTA",
  start_label: "Cliente",
  start_node_id: "CLI-MANUAL-1",
  end_label: "Cuenta",
  end_node_id: "CUE-MANUAL-1",
  propertyRows: [
    { key: "fecha_asignacion", value: "2026-01-01" },
    { key: "tipo_relacion", value: "Titular" },
    { key: "es_principal", value: "true" }
  ]
});
const batchForm = reactive({
  relationshipIdsInput: "12345,12346",
  propertyRows: [
    { key: "tipo_relacion", value: "Titular" },
    { key: "es_principal", value: "true" }
  ]
});
const batchRemoveForm = reactive({
  relationshipIdsInput: "12345,12346",
  propertyNamesInput: "score_riesgo,prioridad"
});
const batchDeleteForm = reactive({
  relationshipIdsInput: "12345,12346"
});

async function loadRelationships() {
  message.value = "";
  try {
    const { data } = await api.get("/relationships/");
    relationships.value = data;
  } catch (error) {
    message.value = formatApiError(error);
  }
}

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

async function createRelationship() {
  createMessage.value = "";
  try {
    await api.post("/relationships/", {
      relationship_type: form.relationship_type,
      start_label: form.start_label,
      start_node_id: form.start_node_id,
      end_label: form.end_label,
      end_node_id: form.end_node_id,
      properties: collectProperties(form.propertyRows)
    });
    createMessage.value = "✓ Relación creada correctamente.";
    setTimeout(() => { createMessage.value = ""; }, 3000);
    await loadRelationships();
  } catch (error) {
    createMessage.value = formatApiError(error);
  }
}

async function batchUpdateProperties() {
  batchMessage.value = "";
  try {
    const relationship_ids = parseCsv(batchForm.relationshipIdsInput);
    const properties = collectProperties(batchForm.propertyRows);
    await api.post("/relationships/properties/batch/", {
      relationship_ids,
      properties
    });
    batchMessage.value = "✓ Propiedades actualizadas en lote.";
    setTimeout(() => { batchMessage.value = ""; }, 3000);
    await loadRelationships();
  } catch (error) {
    batchMessage.value = formatApiError(error);
  }
}

async function batchRemoveProperties() {
  batchMessage.value = "";
  try {
    const relationship_ids = parseCsv(batchRemoveForm.relationshipIdsInput);
    const property_names = parseCsv(batchRemoveForm.propertyNamesInput);
    await api.delete("/relationships/properties/batch/", { data: {
      relationship_ids,
      property_names
    }});
    batchMessage.value = "✓ Propiedades eliminadas en lote.";
    setTimeout(() => { batchMessage.value = ""; }, 3000);
    await loadRelationships();
  } catch (error) {
    batchMessage.value = formatApiError(error);
  }
}

async function batchDeleteRelationships() {
  batchMessage.value = "";
  try {
    const relationship_ids = parseCsv(batchDeleteForm.relationshipIdsInput);
    await api.post("/relationships/delete/", {
      relationship_ids
    });
    batchMessage.value = "✓ Relaciones eliminadas en lote.";
    setTimeout(() => { batchMessage.value = ""; }, 3000);
    await loadRelationships();
  } catch (error) {
    batchMessage.value = formatApiError(error);
  }
}

onMounted(loadRelationships);
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
