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
  </section>
</template>

<script setup>
import { onMounted, reactive, ref } from "vue";
import api from "../api/client";
import DataTable from "../components/DataTable.vue";

const relationships = ref([]);
const message = ref("");
const form = reactive({
  relationship_type: "TIENE_CUENTA",
  start_label: "Cliente",
  start_node_id: "CLI-MANUAL-1",
  end_label: "Cuenta",
  end_node_id: "CUE-MANUAL-1",
  propertiesInput: '{\n  "fecha_asignacion": "2026-01-01",\n  "tipo_relacion": "Titular",\n  "es_principal": true\n}'
});

async function loadRelationships() {
  const { data } = await api.get("/relationships/");
  relationships.value = data;
}

async function createRelationship() {
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
}

onMounted(loadRelationships);
</script>
