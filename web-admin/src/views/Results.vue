<template>
  <div class="results-page">
    <div class="page-header">
      <h1>历史结果</h1>
    </div>
    <el-card>
      <el-table :data="results" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="strategy_name" label="策略" />
        <el-table-column prop="matched_count" label="匹配数" width="100" />
        <el-table-column prop="executed_at" label="执行时间" />
      </el-table>
    </el-card>
  </div>
</template>
<script setup>
import { ref } from 'vue'
const results = ref([])
</script>
<style scoped>
.results-page { padding: 20px; }
.page-header { margin-bottom: 20px; }
</style>
