<template>
  <section class="content-grid">
    <div class="section-panel">
      <div class="section-header">
        <div>
          <p class="eyebrow">Grafo</p>
          <h3>Visualización básica</h3>
        </div>
        <button class="secondary-button" @click="loadGraph">Actualizar</button>
      </div>
      <svg viewBox="0 0 900 600" class="graph-canvas">
        <line
          v-for="edge in positionedEdges"
          :key="edge.id"
          :x1="edge.source.x"
          :y1="edge.source.y"
          :x2="edge.target.x"
          :y2="edge.target.y"
          stroke="rgba(162, 179, 255, 0.4)"
          stroke-width="1.4"
        />
        <g v-for="node in positionedNodes" :key="node.id">
          <circle :cx="node.x" :cy="node.y" r="15" :fill="colorByType(node.tipo)" />
          <text :x="node.x + 18" :y="node.y + 4" fill="#eef2ff" font-size="11">{{ node.nombre }}</text>
        </g>
      </svg>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import api from "../api/client";

const snapshot = ref({ nodes: [], relationships: [] });

async function loadGraph() {
  const { data } = await api.get("/analytics/graph-snapshot/");
  snapshot.value = data;
}

const positionedNodes = computed(() => {
  const radius = 220;
  const centerX = 420;
  const centerY = 280;
  return snapshot.value.nodes.map((node, index, array) => {
    const angle = (index / Math.max(array.length, 1)) * Math.PI * 2;
    return { ...node, x: centerX + radius * Math.cos(angle), y: centerY + radius * Math.sin(angle) };
  });
});

const positionedEdges = computed(() => {
  const nodeMap = Object.fromEntries(positionedNodes.value.map((node) => [node.id, node]));
  return snapshot.value.relationships
    .map((edge) => ({ ...edge, source: nodeMap[edge.source], target: nodeMap[edge.target] }))
    .filter((edge) => edge.source && edge.target);
});

function colorByType(type) {
  const palette = {
    Cliente: "#73e0a9",
    Cuenta: "#8ad8ff",
    Tarjeta: "#ffd166",
    Transaccion: "#ff7a7a",
    Dispositivo: "#b89bff",
    Ubicacion: "#ffb26b",
    Comercio: "#f28f8f",
    Banco: "#78c8b0",
    Alerta: "#ff4d6d"
  };
  return palette[type] || "#d9e1ff";
}

onMounted(loadGraph);
</script>
