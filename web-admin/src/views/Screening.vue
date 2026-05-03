<template>
  <div class="screening-page">
    <div class="page-header">
      <h1>筛选执行</h1>
    </div>
    <el-card>
      <el-steps :active="1" simple>
        <el-step title="选择策略" :icon="SetUp" />
        <el-step title="执行筛选" :icon="Search" />
        <el-step title="查看结果" :icon="Document" />
      </el-steps>
    </el-card>
  </div>
</template>
<script setup>
import { SetUp, Search, Document } from '@element-plus/icons-vue'
</script>
<style scoped>
.screening-page { padding: 20px; }
.page-header { margin-bottom: 20px; }
</style>
