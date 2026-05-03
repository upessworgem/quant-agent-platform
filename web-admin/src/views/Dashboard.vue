<template>
  <div class="dashboard">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">数据仪表盘</h1>
        <p class="page-subtitle">实时监控股票筛选系统运行状态</p>
      </div>
      <div class="header-actions">
        <el-button type="primary" :icon="Refresh" @click="refreshData" :loading="loading">
          刷新数据
        </el-button>
        <el-button type="success" :icon="TrendCharts" @click="quickScreen">
          快速筛选
        </el-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stat-cards">
      <el-col :xs="24" :sm="12" :lg="6">
        <div class="stat-card" @click="$router.push('/stocks')">
          <div class="card-icon blue">
            <el-icon><TrendCharts /></el-icon>
          </div>
          <div class="card-info">
            <div class="card-label">股票总数</div>
            <div class="card-value">{{ formatNumber(statistics.stocks_count) }}</div>
            <div class="card-trend up">
              <el-icon><ArrowUp /></el-icon>
              <span>+2.5%</span>
            </div>
          </div>
        </div>
      </el-col>

      <el-col :xs="24" :sm="12" :lg="6">
        <div class="stat-card" @click="$router.push('/strategies')">
          <div class="card-icon purple">
            <el-icon><SetUp /></el-icon>
          </div>
          <div class="card-info">
            <div class="card-label">策略数量</div>
            <div class="card-value">{{ formatNumber(statistics.strategies_count) }}</div>
            <div class="card-trend up">
              <el-icon><ArrowUp /></el-icon>
              <span>+1</span>
            </div>
          </div>
        </div>
      </el-col>

      <el-col :xs="24" :sm="12" :lg="6">
        <div class="stat-card" @click="$router.push('/results')">
          <div class="card-icon green">
            <el-icon><Document /></el-icon>
          </div>
          <div class="card-info">
            <div class="card-label">筛选次数</div>
            <div class="card-value">{{ formatNumber(statistics.screening_results_count) }}</div>
            <div class="card-trend up">
              <el-icon><ArrowUp /></el-icon>
              <span>+12.8%</span>
            </div>
          </div>
        </div>
      </el-col>

      <el-col :xs="24" :sm="12" :lg="6">
        <div class="stat-card" @click="$router.push('/ai-assistant')">
          <div class="card-icon orange">
            <el-icon><MagicStick /></el-icon>
          </div>
          <div class="card-info">
            <div class="card-label">AI 建议</div>
            <div class="card-value">{{ formatNumber(statistics.ai_suggestions_count) }}</div>
            <div class="card-trend neutral">
              <span>今日 +3</span>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <el-row :gutter="20" class="chart-row">
      <el-col :xs="24" :lg="16">
        <div class="chart-card">
          <div class="chart-header">
            <h3>筛选趋势</h3>
            <el-radio-group v-model="trendPeriod" size="small">
              <el-radio-button label="week">本周</el-radio-button>
              <el-radio-button label="month">本月</el-radio-button>
              <el-radio-button label="year">全年</el-radio-button>
            </el-radio-group>
          </div>
          <v-chart class="chart" :option="trendChartOption" autoresize />
        </div>
      </el-col>

      <el-col :xs="24" :lg="8">
        <div class="chart-card">
          <div class="chart-header">
            <h3>策略使用分布</h3>
          </div>
          <v-chart class="chart" :option="pieChartOption" autoresize />
        </div>
      </el-col>
    </el-row>

    <!-- 最近活动与热门股票 -->
    <el-row :gutter="20" class="bottom-row">
      <el-col :xs="24" :lg="12">
        <div class="list-card">
          <div class="card-header">
            <h3>最近筛选记录</h3>
            <el-button type="primary" link @click="$router.push('/results')">
              查看全部
            </el-button>
          </div>
          <el-timeline class="activity-timeline">
            <el-timeline-item
              v-for="(item, index) in recentActivities"
              :key="index"
              :type="item.type"
              :icon="item.icon"
              :timestamp="item.time"
            >
              <div class="activity-item">
                <div class="activity-title">{{ item.title }}</div>
                <div class="activity-desc">{{ item.description }}</div>
                <div class="activity-stats" v-if="item.stats">
                  <el-tag size="small" type="success">匹配 {{ item.stats.matched }} 只</el-tag>
                  <el-tag size="small" type="info">筛选 {{ item.stats.total }} 只</el-tag>
                </div>
              </div>
            </el-timeline-item>
          </el-timeline>
        </div>
      </el-col>

      <el-col :xs="24" :lg="12">
        <div class="list-card">
          <div class="card-header">
            <h3>今日热门筛选条件</h3>
            <el-button type="primary" link @click="$router.push('/strategies')">
              创建策略
            </el-button>
          </div>
          <div class="hot-conditions">
            <div
              v-for="(item, index) in hotConditions"
              :key="index"
              class="hot-item"
              @click="applyCondition(item)"
            >
              <div class="hot-rank" :class="{ top: index < 3 }">{{ index + 1 }}</div>
              <div class="hot-info">
                <div class="hot-name">{{ item.name }}</div>
                <div class="hot-desc">{{ item.description }}</div>
              </div>
              <div class="hot-usage">
                <el-progress
                  :percentage="item.usage"
                  :color="getProgressColor(index)"
                  :stroke-width="8"
                  :show-text="false"
                />
                <span class="usage-count">{{ item.count }} 次使用</span>
              </div>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- AI 快速入口 -->
    <div class="ai-section">
      <div class="ai-card" @click="$router.push('/ai-assistant')">
        <div class="ai-content">
          <el-icon class="ai-icon"><MagicStick /></el-icon>
          <div class="ai-text">
            <h3>AI 智能助手</h3>
            <p>用自然语言描述你的选股需求，AI 自动生成策略</p>
          </div>
        </div>
        <el-button type="primary" size="large" round>
          立即体验 <el-icon class="btn-icon"><ArrowRight /></el-icon>
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, PieChart } from 'echarts/charts'
import {
  GridComponent, TooltipComponent, LegendComponent,
  TitleComponent, ToolboxComponent
} from 'echarts/components'
import VChart from 'vue-echarts'
import { useAppStore } from '@/store'
import { configApi } from '@/api/request'
import {
  Refresh, TrendCharts, SetUp, Document, MagicStick,
  ArrowUp, ArrowRight, SuccessFilled, InfoFilled, WarningFilled
} from '@element-plus/icons-vue'

use([
  CanvasRenderer,
  LineChart,
  PieChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  TitleComponent,
  ToolboxComponent
])

const router = useRouter()
const appStore = useAppStore()

const loading = ref(false)
const trendPeriod = ref('week')
const statistics = computed(() => appStore.statistics)

// 趋势图配置
const trendChartOption = computed(() => ({
  tooltip: {
    trigger: 'axis',
    backgroundColor: 'rgba(255,255,255,0.95)',
    borderColor: '#eee',
    borderWidth: 1,
    textStyle: { color: '#333' }
  },
  grid: {
    left: '3%',
    right: '4%',
    bottom: '3%',
    top: '10%',
    containLabel: true
  },
  xAxis: {
    type: 'category',
    boundaryGap: false,
    data: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'],
    axisLine: { lineStyle: { color: '#ddd' } },
    axisLabel: { color: '#666' }
  },
  yAxis: {
    type: 'value',
    axisLine: { show: false },
    axisTick: { show: false },
    splitLine: { lineStyle: { color: '#f0f0f0' } },
    axisLabel: { color: '#666' }
  },
  series: [
    {
      name: '筛选次数',
      type: 'line',
      smooth: true,
      symbol: 'circle',
      symbolSize: 8,
      sampling: 'average',
      itemStyle: { color: '#409EFF' },
      lineStyle: { width: 3 },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(64,158,255,0.3)' },
            { offset: 1, color: 'rgba(64,158,255,0.05)' }
          ]
        }
      },
      data: [12, 18, 25, 32, 28, 35, 42]
    },
    {
      name: '匹配股票',
      type: 'line',
      smooth: true,
      symbol: 'circle',
      symbolSize: 8,
      itemStyle: { color: '#67C23A' },
      lineStyle: { width: 3 },
      data: [8, 12, 18, 22, 20, 25, 30]
    }
  ]
}))

// 饼图配置
const pieChartOption = computed(() => ({
  tooltip: {
    trigger: 'item',
    formatter: '{b}: {c} ({d}%)'
  },
  legend: {
    orient: 'vertical',
    right: '5%',
    top: 'center',
    textStyle: { color: '#666' }
  },
  series: [
    {
      name: '策略类型',
      type: 'pie',
      radius: ['40%', '70%'],
      center: ['35%', '50%'],
      avoidLabelOverlap: false,
      itemStyle: {
        borderRadius: 10,
        borderColor: '#fff',
        borderWidth: 2
      },
      label: { show: false },
      emphasis: {
        label: {
          show: true,
          fontSize: 14,
          fontWeight: 'bold'
        }
      },
      labelLine: { show: false },
      data: [
        { value: 35, name: '动量策略', itemStyle: { color: '#409EFF' } },
        { value: 25, name: '价值投资', itemStyle: { color: '#67C23A' } },
        { value: 20, name: '突破策略', itemStyle: { color: '#E6A23C' } },
        { value: 15, name: 'AI生成', itemStyle: { color: '#9B59B6' } },
        { value: 5, name: '自定义', itemStyle: { color: '#909399' } }
      ]
    }
  ]
}))

// 最近活动
const recentActivities = [
  {
    title: '执行高换手策略',
    description: '筛选出换手率大于15%的股票',
    time: '10分钟前',
    type: 'primary',
    icon: SuccessFilled,
    stats: { matched: 12, total: 5274 }
  },
  {
    title: 'AI 生成新策略',
    description: '科技板块放量突破策略',
    time: '1小时前',
    type: 'success',
    icon: MagicStick
  },
  {
    title: '更新股票数据',
    description: '同步最新行情数据',
    time: '2小时前',
    type: 'warning',
    icon: InfoFilled
  },
  {
    title: '策略回测完成',
    description: '动量策略近30天回测',
    time: '昨天',
    type: 'info',
    icon: TrendCharts
  }
]

// 热门条件
const hotConditions = [
  { name: '换手率 > 15%', description: '高活跃度股票', usage: 95, count: 328 },
  { name: '量比 > 1.5', description: '放量上涨', usage: 88, count: 286 },
  { name: '筹码集中度 < 20%', description: '筹码集中', usage: 72, count: 234 },
  { name: '连续上涨', description: '2日以上连涨', usage: 65, count: 198 },
  { name: '突破新高', description: '创近期新高', usage: 45, count: 156 }
]

const formatNumber = (num) => {
  return num?.toLocaleString() || '0'
}

const getProgressColor = (index) => {
  const colors = ['#F56C6C', '#E6A23C', '#409EFF', '#67C23A', '#909399']
  return colors[index] || '#909399'
}

const refreshData = async () => {
  loading.value = true
  await appStore.fetchStatistics()
  loading.value = false
}

const quickScreen = () => {
  router.push('/screening')
}

const applyCondition = (item) => {
  router.push({
    path: '/strategies',
    query: { condition: item.name }
  })
}

onMounted(() => {
  appStore.fetchStatistics()
})
</script>

<style scoped lang="scss">
.dashboard {
  padding-bottom: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 24px 32px;
  border-radius: 16px;
  color: #fff;

  .page-title {
    font-size: 28px;
    font-weight: 600;
    margin-bottom: 8px;
  }

  .page-subtitle {
    font-size: 14px;
    opacity: 0.9;
  }

  .header-actions {
    display: flex;
    gap: 12px;
  }
}

.stat-cards {
  margin-bottom: 20px;

  .stat-card {
    background: #fff;
    border-radius: 12px;
    padding: 24px;
    display: flex;
    align-items: center;
    box-shadow: 0 2px 12px rgba(0,0,0,0.08);
    cursor: pointer;
    transition: all 0.3s;

    &:hover {
      transform: translateY(-4px);
      box-shadow: 0 8px 24px rgba(0,0,0,0.12);
    }

    .card-icon {
      width: 64px;
      height: 64px;
      border-radius: 16px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 32px;
      margin-right: 20px;

      &.blue {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: #fff;
      }

      &.purple {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: #fff;
      }

      &.green {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        color: #fff;
      }

      &.orange {
        background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
        color: #fff;
      }
    }

    .card-info {
      flex: 1;

      .card-label {
        font-size: 14px;
        color: #999;
        margin-bottom: 8px;
      }

      .card-value {
        font-size: 32px;
        font-weight: 700;
        color: #333;
        margin-bottom: 8px;
      }

      .card-trend {
        display: flex;
        align-items: center;
        gap: 4px;
        font-size: 13px;

        &.up {
          color: #67C23A;
        }

        &.down {
          color: #F56C6C;
        }

        &.neutral {
          color: #909399;
        }
      }
    }
  }
}

.chart-row {
  margin-bottom: 20px;
}

.chart-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.08);

  .chart-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;

    h3 {
      font-size: 16px;
      font-weight: 600;
      color: #333;
    }
  }

  .chart {
    height: 320px;
  }
}

.bottom-row {
  margin-bottom: 20px;
}

.list-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.08);
  height: 100%;

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;

    h3 {
      font-size: 16px;
      font-weight: 600;
      color: #333;
    }
  }
}

.activity-timeline {
  padding-left: 8px;

  .activity-item {
    .activity-title {
      font-weight: 500;
      color: #333;
      margin-bottom: 4px;
    }

    .activity-desc {
      font-size: 13px;
      color: #999;
      margin-bottom: 8px;
    }

    .activity-stats {
      display: flex;
      gap: 8px;
    }
  }
}

.hot-conditions {
  .hot-item {
    display: flex;
    align-items: center;
    padding: 16px;
    border-radius: 8px;
    cursor: pointer;
    transition: background 0.3s;

    &:hover {
      background: #f5f7fa;
    }

    .hot-rank {
      width: 28px;
      height: 28px;
      border-radius: 50%;
      background: #f0f2f5;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 600;
      color: #666;
      margin-right: 16px;

      &.top {
        background: #409EFF;
        color: #fff;
      }
    }

    .hot-info {
      flex: 1;

      .hot-name {
        font-weight: 500;
        color: #333;
        margin-bottom: 4px;
      }

      .hot-desc {
        font-size: 12px;
        color: #999;
      }
    }

    .hot-usage {
      width: 120px;

      .usage-count {
        font-size: 12px;
        color: #999;
        margin-top: 4px;
        display: block;
      }
    }
  }
}

.ai-section {
  .ai-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 16px;
    padding: 32px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    cursor: pointer;
    transition: transform 0.3s;

    &:hover {
      transform: translateY(-4px);
    }

    .ai-content {
      display: flex;
      align-items: center;
      gap: 20px;
      color: #fff;

      .ai-icon {
        font-size: 48px;
        opacity: 0.9;
      }

      .ai-text {
        h3 {
          font-size: 20px;
          font-weight: 600;
          margin-bottom: 8px;
        }

        p {
          font-size: 14px;
          opacity: 0.9;
        }
      }
    }

    .btn-icon {
      margin-left: 8px;
    }
  }
}
</style>
