import { createRouter, createWebHistory } from 'vue-router'
import Layout from '@/components/Layout.vue'
import { getToken } from '@/utils/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { title: '登录', requiresAuth: false }
  },
  {
    path: '/',
    component: Layout,
    redirect: '/dashboard',
    meta: { requiresAuth: true },
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: { title: '仪表盘', icon: 'Odometer' }
      },
      {
        path: 'stocks',
        name: 'Stocks',
        component: () => import('@/views/Stocks.vue'),
        meta: { title: '股票管理', icon: 'TrendCharts' }
      },
      {
        path: 'strategies',
        name: 'Strategies',
        component: () => import('@/views/Strategies.vue'),
        meta: { title: '策略管理', icon: 'SetUp' }
      },
      {
        path: 'screening',
        name: 'Screening',
        component: () => import('@/views/Screening.vue'),
        meta: { title: '筛选执行', icon: 'Search' }
      },
      {
        path: 'ai-assistant',
        name: 'AIAssistant',
        component: () => import('@/views/AIAssistant.vue'),
        meta: { title: 'AI 助手', icon: 'MagicStick' }
      },
      {
        path: 'results',
        name: 'Results',
        component: () => import('@/views/Results.vue'),
        meta: { title: '历史结果', icon: 'Document' }
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('@/views/Settings.vue'),
        meta: { title: '系统设置', icon: 'Setting' }
      }
    ]
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/login'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  // 设置页面标题
  document.title = to.meta.title
    ? `${to.meta.title} - 股票智能筛选系统`
    : '股票智能筛选系统'

  const requiresAuth = to.matched.some(record => record.meta.requiresAuth !== false)
  const token = getToken()

  if (requiresAuth && !token) {
    // 需要认证但没有 Token，跳转到登录页
    next({ path: '/login', query: { redirect: to.fullPath } })
  } else if (to.path === '/login' && token) {
    // 已登录访问登录页，跳转到首页
    next({ path: '/' })
  } else {
    next()
  }
})

export default router
