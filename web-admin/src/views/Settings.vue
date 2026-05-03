<template>
  <div class="settings-page">
    <div class="page-header">
      <h1>系统设置</h1>
    </div>
    <el-card>
      <el-form label-width="150px">
        <el-form-item label="AI 提供商">
          <el-select v-model="settings.ai_provider" style="width: 300px">
            <el-option label="Anthropic Claude" value="anthropic" />
            <el-option label="OpenAI GPT" value="openai" />
          </el-select>
        </el-form-item>
        <el-form-item label="API Key">
          <el-input v-model="settings.api_key" type="password" show-password style="width: 400px" />
        </el-form-item>
        <el-form-item label="模型">
          <el-input v-model="settings.model" style="width: 300px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="saveSettings">保存设置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>
<script setup>
import { ref } from 'vue'
const settings = ref({
  ai_provider: 'anthropic',
  api_key: '',
  model: 'claude-sonnet-4-6'
})
const saveSettings = () => {
  console.log('保存设置:', settings.value)
}
</script>
<style scoped>
.settings-page { padding: 20px; }
.page-header { margin-bottom: 20px; }
</style>
