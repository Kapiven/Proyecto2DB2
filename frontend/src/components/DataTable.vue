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
            <template v-if="isArray(row[column])">
              <div class="array-cell">
                <span v-for="(item, itemIndex) in row[column]" :key="itemIndex">
                  {{ formatValue(item) }}<span v-if="itemIndex < row[column].length - 1">, </span>
                </span>
              </div>
            </template>
            <template v-else-if="isObject(row[column])">
              <div class="object-cell">
                <div v-for="(value, key) in row[column]" :key="key" class="object-field">
                  <span class="object-key">{{ key }}:</span>
                  <span class="object-value">{{ formatValue(value) }}</span>
                </div>
              </div>
            </template>
            <template v-else>
              <span>{{ row[column] }}</span>
            </template>
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

function isObject(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function isArray(value) {
  return Array.isArray(value);
}

function formatValue(value) {
  if (value === null || value === undefined) {
    return "";
  }
  return typeof value === "object" ? JSON.stringify(value) : value;
}
</script>

<style scoped>
.array-cell,
.object-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.object-field {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}
.object-key {
  font-weight: 700;
  color: var(--accent-strong);
}
.object-value {
  color: var(--text);
}
</style>
