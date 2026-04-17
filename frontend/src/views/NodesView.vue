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
  </section>
</template>

<script setup>
import { onMounted, reactive, ref } from "vue";
import api from "../api/client";
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

async function loadNodes() {
  const { data } = await api.get("/nodes/", { params: filters });
  nodes.value = data;
}

async function createNode() {
  await api.post("/nodes/", {
    labels: createForm.labelInput.split(",").map((item) => item.trim()).filter(Boolean),
    properties: JSON.parse(createForm.propertiesInput)
  });
  message.value = "Nodo creado correctamente.";
  await loadNodes();
}

async function updateDynamicLabel() {
  await api.post(`/nodes/${labelForm.baseLabel}/${labelForm.nodeId}/labels/`, {
    label: labelForm.dynamicLabel,
    action: labelForm.action
  });
  message.value = "Etiqueta dinámica actualizada.";
  await loadNodes();
}

onMounted(loadNodes);
</script>
