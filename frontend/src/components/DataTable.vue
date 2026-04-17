<template>
  <div class="table-shell">
    <table>
      <thead>
        <tr>
          <th v-for="column in columns" :key="column">{{ column }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(row, index) in rows" :key="index">
          <td v-for="column in columns" :key="column">
            <pre>{{ stringify(row[column]) }}</pre>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  rows: {
    type: Array,
    default: () => []
  }
});

const columns = computed(() => {
  const first = props.rows[0] || {};
  return Object.keys(first);
});

function stringify(value) {
  return typeof value === "object" ? JSON.stringify(value, null, 2) : value;
}
</script>
