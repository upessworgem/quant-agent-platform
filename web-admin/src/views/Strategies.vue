<template>
  <div class="strategies-page">
    <div class="page-header">
      <h1>策略管理</h1>
      <el-button type="primary" @click="showCreateDialog = true">
        <el-icon><Plus /></el-icon> 新建策略
      </el-button>
    </div>
    <el-card>
      <el-empty description="策略列表加载中..." />
    </el-card>
  </div>
</template>
<script setup>
import { ref } from 'vue'
import { Plus } from '@element-plus/icons-vue'
const showCreateDialog = ref(false)
</script>
<style scoped>
.strategies-page { padding: 20px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
</style>
