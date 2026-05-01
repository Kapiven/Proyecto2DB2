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
        <textarea v-model="form.propertiesInput" rows="8" placeholder='{"fecha_asignacion":"2026-01-01","tipo_relacion":"Titular","es_principal":true}'></textarea>
        <button class="primary-button" @click="createRelationship">Crear relación</button>
      </div>
      <p class="status-text">{{ message }}</p>
    </div>

    <div class="section-panel">
      <p class="eyebrow">Operaciones en lote</p>
      <h3>Propiedades y borrado masivo</h3>
      <div class="form-grid">
        <textarea v-model="batchForm.relationshipIdsInput" rows="4" placeholder='["12345","12346"]'></textarea>
        <textarea v-model="batchForm.propertiesInput" rows="6" placeholder='{"tipo_relacion":"Titular","es_principal":true}'></textarea>
        <button class="primary-button" @click="batchUpdateProperties">Actualizar propiedades en relaciones</button>
      </div>
      <div class="form-grid">
        <textarea v-model="batchRemoveForm.relationshipIdsInput" rows="4" placeholder='["12345","12346"]'></textarea>
        <textarea v-model="batchRemoveForm.propertyNamesInput" rows="4" placeholder='["score_riesgo","prioridad"]'></textarea>
        <button class="secondary-button" @click="batchRemoveProperties">Eliminar propiedades en relaciones</button>
      </div>
      <div class="form-grid">
        <textarea v-model="batchDeleteForm.relationshipIdsInput" rows="4" placeholder='["12345","12346"]'></textarea>
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
const message = ref("");
const batchMessage = ref("");
const form = reactive({
  relationship_type: "TIENE_CUENTA",
  start_label: "Cliente",
  start_node_id: "CLI-MANUAL-1",
  end_label: "Cuenta",
  end_node_id: "CUE-MANUAL-1",
  propertiesInput: '{\n  "fecha_asignacion": "2026-01-01",\n  "tipo_relacion": "Titular",\n  "es_principal": true\n}'
});
const batchForm = reactive({
  relationshipIdsInput: '["12345","12346"]',
  propertiesInput: '{\n  "tipo_relacion": "Titular",\n  "es_principal": true\n}'
});
const batchRemoveForm = reactive({
  relationshipIdsInput: '["12345","12346"]',
  propertyNamesInput: '["score_riesgo","prioridad"]'
});
const batchDeleteForm = reactive({
  relationshipIdsInput: '["12345","12346"]'
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

async function createRelationship() {
  try {
    await api.post("/relationships/", {
      relationship_type: form.relationship_type,
      start_label: form.start_label,
      start_node_id: form.start_node_id,
      end_label: form.end_label,
      end_node_id: form.end_node_id,
      properties: JSON.parse(form.propertiesInput)
    });
    message.value = "Relación creada correctamente.";
    await loadRelationships();
  } catch (error) {
    message.value = formatApiError(error);
  }
}

function parseJsonInput(value) {
  try {
    return JSON.parse(value);
  } catch (error) {
    throw new Error("JSON inválido. Revisar el formato de entrada.");
  }
}

async function batchUpdateProperties() {
  try {
    const relationship_ids = parseJsonInput(batchForm.relationshipIdsInput);
    const properties = parseJsonInput(batchForm.propertiesInput);
    await api.post("/relationships/properties/batch/", {
      relationship_ids,
      properties
    });
    batchMessage.value = "Propiedades actualizadas en lote.";
    await loadRelationships();
  } catch (error) {
    batchMessage.value = formatApiError(error);
  }
}

async function batchRemoveProperties() {
  try {
    const relationship_ids = parseJsonInput(batchRemoveForm.relationshipIdsInput);
    const property_names = parseJsonInput(batchRemoveForm.propertyNamesInput);
    await api.delete("/relationships/properties/batch/", { data: {
      relationship_ids,
      property_names
    }});
    batchMessage.value = "Propiedades eliminadas en lote.";
    await loadRelationships();
  } catch (error) {
    batchMessage.value = formatApiError(error);
  }
}

async function batchDeleteRelationships() {
  try {
    const relationship_ids = parseJsonInput(batchDeleteForm.relationshipIdsInput);
    await api.post("/relationships/delete/", {
      relationship_ids
    });
    batchMessage.value = "Relaciones eliminadas en lote.";
    await loadRelationships();
  } catch (error) {
    batchMessage.value = formatApiError(error);
  }
}

onMounted(loadRelationships);
</script>
