import axios from 'axios'
import { ElMessage } from 'element-plus'
import { getToken, removeToken } from '@/utils/auth'
import router from '@/router'

// 创建 axios 实例
const request = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
request.interceptors.request.use(
  (config) => {
    // 添加认证 Token
    const token = getToken()
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  (response) => {
    const data = response.data
    if (data.code !== 200) {
      ElMessage.error(data.message || '请求失败')
      return Promise.reject(new Error(data.message))
    }
    return data.data
  },
  (error) => {
    const { response } = error

    if (response) {
      // 处理 401 错误
      if (response.status === 401) {
        removeToken()
        router.push('/login')
        ElMessage.error('登录已过期，请重新登录')
        return Promise.reject(error)
      }

      // 处理其他错误
      const message = response.data?.message || `请求错误: ${response.status}`
      ElMessage.error(message)
    } else {
      ElMessage.error('网络错误，请检查网络连接')
    }

    return Promise.reject(error)
  }
)

// 认证 API
export const authApi = {
  login: (data) => request.post('/auth/login', data),
  getCurrentUser: () => request.get('/auth/me'),
  refreshToken: () => request.post('/auth/refresh')
}

// 股票 API
export const stockApi = {
  getList: (params) => request.get('/stocks', { params }),
  getByCode: (code) => request.get(`/stocks/${code}`),
  create: (data) => request.post('/stocks', data),
  update: (code, data) => request.put(`/stocks/${code}`, data),
  delete: (code) => request.delete(`/stocks/${code}`),
  bulkImport: (data) => request.post('/stocks/bulk', data),
  getHistory: (code, params) => request.get(`/stocks/${code}/history`, { params })
}

// 策略 API
export const strategyApi = {
  getList: (params) => request.get('/strategies', { params }),
  getById: (id) => request.get(`/strategies/${id}`),
  create: (data) => request.post('/strategies', data),
  update: (id, data) => request.put(`/strategies/${id}`, data),
  delete: (id) => request.delete(`/strategies/${id}`),
  duplicate: (id) => request.post(`/strategies/${id}/duplicate`),
  generateWithAI: (data) => request.post('/strategies/generate', data)
}

// 筛选 API
export const screeningApi = {
  getResults: (params) => request.get('/screening-results', { params }),
  getResultById: (id) => request.get(`/screening-results/${id}`),
  deleteResult: (id) => request.delete(`/screening-results/${id}`),
  execute: (data) => request.post('/screening/execute', data),
  analyzeWithAI: (id, data) => request.post(`/screening-results/${id}/analyze`, data)
}

// 配置 API
export const configApi = {
  getStatistics: () => request.get('/statistics'),
  getConfigs: () => request.get('/configs'),
  getConfig: (key) => request.get(`/configs/${key}`),
  setConfig: (data) => request.post('/configs', data),
  deleteConfig: (key) => request.delete(`/configs/${key}`)
}

// AI API
export const aiApi = {
  getSuggestions: (params) => request.get('/ai-suggestions', { params }),
  rateSuggestion: (id, data) => request.post(`/ai-suggestions/${id}/rate`, data)
}

export default request
