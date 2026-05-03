<template>
  <el-container class="layout-container">
    <!-- 侧边栏 -->
    <el-aside :width="sidebarCollapsed ? '64px' : '220px'" class="sidebar">
      <div class="logo">
        <el-icon class="logo-icon"><TrendCharts /></el-icon>
        <span v-show="!sidebarCollapsed" class="logo-text">智能选股</span>
      </div>

      <el-menu
        :default-active="$route.path"
        :collapse="sidebarCollapsed"
        :collapse-transition="false"
        router
        background-color="#001529"
        text-color="#a6adb4"
        active-text-color="#409EFF"
        class="sidebar-menu"
      >
        <el-menu-item v-for="route in menuRoutes" :key="route.path" :index="route.path">
          <el-icon>
            <component :is="route.meta.icon" />
          </el-icon>
          <template #title>{{ route.meta.title }}</template>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <!-- 顶部导航 -->
      <el-header class="header">
        <div class="header-left">
          <el-icon class="collapse-btn" @click="toggleSidebar">
            <Fold v-if="!sidebarCollapsed" />
            <Expand v-else />
          </el-icon>
          <breadcrumb />
        </div>
        <div class="header-right">
          <el-tooltip content="刷新数据">
            <el-icon class="header-icon" @click="refreshData"><Refresh /></el-icon>
          </el-tooltip>
          <el-tooltip content="全屏">
            <el-icon class="header-icon" @click="toggleFullscreen"><FullScreen /></el-icon>
          </el-tooltip>
          <el-dropdown>
            <span class="user-info">
              <el-avatar :size="32" src="https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png" />
              <span class="username">管理员</span>
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="$router.push('/settings')">系统设置</el-dropdown-item>
                <el-dropdown-item divided @click="handleLogout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <!-- 主内容区 -->
      <el-main class="main-content">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAppStore } from '@/store'
import { removeToken, getUser } from '@/utils/auth'
import { ElMessageBox } from 'element-plus'
import Breadcrumb from './Breadcrumb.vue'

const route = useRoute()
const router = useRouter()
const appStore = useAppStore()

const sidebarCollapsed = computed(() => appStore.sidebarCollapsed)

const menuRoutes = computed(() => {
  const layoutRoute = router.getRoutes().find(r => r.path === '/')
  return layoutRoute?.children.filter(r => r.meta) || []
})

const toggleSidebar = () => {
  appStore.toggleSidebar()
}

const refreshData = () => {
  window.location.reload()
}

const toggleFullscreen = () => {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen()
  } else {
    document.exitFullscreen()
  }
}

const handleLogout = async () => {
  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    removeToken()
    router.push('/login')
  } catch {
    // 用户取消
  }
}
</script>

<style scoped lang="scss">
.layout-container {
  height: 100vh;
}

.sidebar {
  background: #001529;
  transition: width 0.3s;
  box-shadow: 2px 0 8px rgba(0,0,0,0.15);

  .logo {
    height: 64px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #002140;
    color: #fff;

    .logo-icon {
      font-size: 32px;
      color: #409EFF;
    }

    .logo-text {
      font-size: 18px;
      font-weight: 600;
      margin-left: 12px;
      white-space: nowrap;
    }
  }

  .sidebar-menu {
    border-right: none;

    :deep(.el-menu-item) {
      height: 50px;
      line-height: 50px;

      &:hover {
        background: #1890ff !important;
        color: #fff !important;
      }

      &.is-active {
        background: #1890ff !important;
      }
    }
  }
}

.header {
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 1px 4px rgba(0,0,0,0.1);

  .header-left {
    display: flex;
    align-items: center;

    .collapse-btn {
      font-size: 20px;
      cursor: pointer;
      margin-right: 16px;
      color: #666;

      &:hover {
        color: #409EFF;
      }
    }
  }

  .header-right {
    display: flex;
    align-items: center;
    gap: 20px;

    .header-icon {
      font-size: 20px;
      cursor: pointer;
      color: #666;

      &:hover {
        color: #409EFF;
      }
    }

    .user-info {
      display: flex;
      align-items: center;
      cursor: pointer;

      .username {
        margin: 0 8px;
        color: #333;
      }
    }
  }
}

.main-content {
  background: #f0f2f5;
  padding: 20px;
  overflow-y: auto;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
