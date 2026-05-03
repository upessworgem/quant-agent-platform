<template>
  <div class="stocks-page">
    <div class="page-header">
      <h1>股票管理</h1>
      <el-button type="primary" @click="refreshData" :loading="loading">
        <el-icon><Refresh /></el-icon> 刷新
      </el-button>
    </div>
    <el-card class="table-card">
      <el-table :data="stocks" v-loading="loading" stripe>
        <el-table-column prop="code" label="股票代码" width="120" />
        <el-table-column prop="name" label="股票名称" />
        <el-table-column prop="exchange" label="交易所" width="100" />
        <el-table-column prop="industry" label="行业" />
      </el-table>
    </el-card>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
const loading = ref(false)
const stocks = ref([])
const refreshData = async () => {
  loading.value = true
  stocks.value = []
  loading.value = false
}
onMounted(() => refreshData())
</script>
<style scoped>
.stocks-page { padding: 20px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
</style>
