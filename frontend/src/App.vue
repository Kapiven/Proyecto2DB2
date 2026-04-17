<template>
  <div class="app-shell">
    <aside class="sidebar">
      <div class="brand-block">
        <p class="eyebrow">Neo4j + Django + Vue</p>
        <h1>Fraud Graph Monitor</h1>
        <p class="brand-copy">
          Plataforma de detección de fraude con foco en riesgo, trazabilidad y análisis de relaciones complejas.
        </p>
      </div>

      <nav class="nav-links">
        <RouterLink v-for="item in links" :key="item.to" :to="item.to" class="nav-link">
          {{ item.label }}
        </RouterLink>
      </nav>
    </aside>

    <main class="main-panel">
      <header class="topbar">
        <div>
          <p class="eyebrow">Centro operativo</p>
          <h2>Monitoreo de fraude sobre grafo conectado</h2>
        </div>
      </header>
      <RouterView />
    </main>
  </div>
</template>

<script setup>
const links = [
  { to: "/", label: "Dashboard" },
  { to: "/nodes", label: "CRUD Nodos" },
  { to: "/relationships", label: "CRUD Relaciones" },
  { to: "/csv", label: "Carga CSV" },
  { to: "/fraud", label: "Consultas Fraude" },
  { to: "/gds", label: "Ejecución GDS" },
  { to: "/graph", label: "Visualización" }
];
</script>
