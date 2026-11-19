<script setup lang="ts">
/**
 * Table with head row; scrolls horizontally on narrow screens instead of breaking the page.
 * Navy head, striped rows.
 * Markdown tables inside .prose get the same look from CSS.
 */
defineProps<{ head: string[]; rows: string[][]; caption?: string }>()
</script>

<template>
  <div class="table-scroll" tabindex="0" :aria-label="caption">
    <table class="data-table">
      <caption v-if="caption" class="visually-hidden">{{ caption }}</caption>
      <thead>
        <tr><th v-for="(cell, i) in head" :key="i" scope="col">{{ cell }}</th></tr>
      </thead>
      <tbody>
        <tr v-for="(row, r) in rows" :key="r">
          <td v-for="(cell, c) in row" :key="c">{{ cell }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
