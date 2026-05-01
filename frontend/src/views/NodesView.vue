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
        <textarea v-model="createForm.propertiesInput" rows="10" placeholder='{"id":"CLI-MANUAL-1","nombre":"Ana"}'></textarea>
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
        <textarea v-model="batchForm.nodeIdsInput" rows="4" placeholder='["CLI-00000","CLI-00001"]'></textarea>
        <textarea v-model="batchForm.propertiesInput" rows="8" placeholder='{"riesgo": 0.55, "nivel_riesgo": "Medio"}'></textarea>
        <button class="primary-button" @click="batchUpdateProperties">Actualizar propiedades</button>
      </div>
      <div class="form-grid">
        <input v-model="batchRemoveForm.label" placeholder="Etiqueta" />
        <textarea v-model="batchRemoveForm.nodeIdsInput" rows="4" placeholder='["CLI-00000","CLI-00001"]'></textarea>
        <textarea v-model="batchRemoveForm.propertyNamesInput" rows="4" placeholder='["telefono","email"]'></textarea>
        <button class="secondary-button" @click="batchRemoveProperties">Eliminar propiedades</button>
      </div>
      <div class="form-grid">
        <input v-model="batchDeleteForm.label" placeholder="Etiqueta" />
        <textarea v-model="batchDeleteForm.nodeIdsInput" rows="4" placeholder='["CLI-00000","CLI-00001"]'></textarea>
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
  propertiesInput:
    '{\n  "id": "CLI-MANUAL-1",\n  "nombre": "Cliente Manual",\n  "edad": 29,\n  "genero": "F",\n  "riesgo": 0.22,\n  "nivel_riesgo": "Bajo",\n  "fecha_registro": "2026-01-10",\n  "email": "manual@example.com",\n  "telefono": "5555-5555"\n}'
});
const labelForm = reactive({
  baseLabel: "Cliente",
  nodeId: "CLI-MANUAL-1",
  dynamicLabel: "RiesgoBajo",
  action: "add"
});
const batchForm = reactive({
  label: "Cliente",
  nodeIdsInput: '["CLI-MANUAL-1","CLI-MANUAL-2"]',
  propertiesInput: '{\n  "riesgo": 0.55,\n  "nivel_riesgo": "Medio"\n}'
});
const batchRemoveForm = reactive({
  label: "Cliente",
  nodeIdsInput: '["CLI-MANUAL-1","CLI-MANUAL-2"]',
  propertyNamesInput: '["telefono","email"]'
});
const batchDeleteForm = reactive({
  label: "Cliente",
  nodeIdsInput: '["CLI-MANUAL-1","CLI-MANUAL-2"]'
});
const batchMessage = ref("");

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
      properties: JSON.parse(createForm.propertiesInput)
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

function parseJsonInput(value) {
  try {
    return JSON.parse(value);
  } catch (error) {
    throw new Error("JSON inválido. Revisar el formato de entrada.");
  }
}

async function batchUpdateProperties() {
  try {
    const node_ids = parseJsonInput(batchForm.nodeIdsInput);
    const properties = parseJsonInput(batchForm.propertiesInput);
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
    const node_ids = parseJsonInput(batchRemoveForm.nodeIdsInput);
    const property_names = parseJsonInput(batchRemoveForm.propertyNamesInput);
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
    const node_ids = parseJsonInput(batchDeleteForm.nodeIdsInput);
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
