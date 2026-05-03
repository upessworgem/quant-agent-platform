import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { configApi } from '@/api/request'

export const useAppStore = defineStore('app', () => {
  // 侧边栏折叠状态
  const sidebarCollapsed = ref(false)

  // 系统统计
  const statistics = ref({
    stocks_count: 0,
    strategies_count: 0,
    screening_results_count: 0,
    historical_data_count: 0,
    ai_suggestions_count: 0
  })

  // 系统配置
  const systemConfig = ref({
    ai_provider: 'anthropic',
    api_key: '',
    model: 'claude-sonnet-4-6'
  })

  // 计算属性
  const hasAIConfig = computed(() => {
    return !!systemConfig.value.api_key
  })

  // 方法
  const toggleSidebar = () => {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  const fetchStatistics = async () => {
    try {
      const data = await configApi.getStatistics()
      statistics.value = data
      return data
    } catch (error) {
      console.error('获取统计信息失败:', error)
      return null
    }
  }

  return {
    sidebarCollapsed,
    statistics,
    systemConfig,
    hasAIConfig,
    toggleSidebar,
    fetchStatistics
  }
})

export const useStockStore = defineStore('stock', () => {
  const stockList = ref([])
  const total = ref(0)
  const loading = ref(false)

  return {
    stockList,
    total,
    loading
  }
})

export const useStrategyStore = defineStore('strategy', () => {
  const strategyList = ref([])
  const currentStrategy = ref(null)
  const loading = ref(false)

  return {
    strategyList,
    currentStrategy,
    loading
  }
})
