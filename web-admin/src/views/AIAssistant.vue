<template>
  <div class="ai-page">
    <div class="page-header">
      <h1>AI 助手</h1>
      <p class="subtitle">用自然语言描述你的选股需求，AI 自动生成策略</p>
    </div>
    <el-card class="ai-card">
      <div class="input-section">
        <el-input
          v-model="userInput"
          type="textarea"
          :rows="4"
          placeholder="例如：找出近期放量突破、换手率大于20%的科技类股票"
        />
        <el-button type="primary" size="large" @click="generateStrategy" :loading="loading">
          <el-icon><MagicStick /></el-icon> 生成策略
        </el-button>
      </div>
    </el-card>
  </div>
</template>
<script setup>
import { ref } from 'vue'
import { MagicStick } from '@element-plus/icons-vue'
const userInput = ref('')
const loading = ref(false)
const generateStrategy = () => {
  loading.value = true
  setTimeout(() => loading.value = false, 2000)
}
</script>
<style scoped>
.ai-page { padding: 20px; }
.page-header { margin-bottom: 20px; }
.subtitle { color: #666; margin-top: 8px; }
.ai-card { padding: 40px; }
.input-section { display: flex; flex-direction: column; gap: 20px; max-width: 800px; margin: 0 auto; }
</style>
