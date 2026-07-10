<template>
  <div class="dashboard-page">
    <div class="dashboard-bg">
      <div class="bg-orb bg-orb-1"></div>
      <div class="bg-orb bg-orb-2"></div>
    </div>

    <aside class="sidebar">
      <div class="sidebar-brand">
        <div class="brand-icon">
          <van-icon name="shield-o" size="20" :style="{ color: 'var(--dark-accent-light)' }" />
        </div>
        <span class="brand-text">安防系统</span>
      </div>

      <nav class="sidebar-nav">
        <div
          v-for="item in navItems"
          :key="item.path"
          class="nav-item"
          :class="{ 'nav-item-active': isActive(item.path) }"
          @click="$router.push(item.path)"
        >
          <div class="nav-icon-wrap">
            <van-icon :name="item.icon" size="20" />
          </div>
          <span class="nav-label">{{ item.label }}</span>
        </div>
      </nav>

      <div class="sidebar-footer">
        <div class="sidebar-status">
          <span class="status-dot"></span>
          <span class="status-text">运行中</span>
        </div>
      </div>
    </aside>

    <main class="main-area">
      <header class="main-header">
        <div class="header-left">
          <h1 class="header-title">安防总览</h1>
          <span class="header-subtitle">{{ currentDate }}</span>
        </div>
        <div class="header-right">
          <span class="header-time">{{ currentTime }}</span>
        </div>
      </header>

      <div class="main-content">
        <section class="stats-grid">
          <div
            class="stat-card stat-card-wide stat-card-primary"
            @click="$router.push('/face-management')"
          >
            <div class="stat-card-glow"></div>
            <div class="stat-card-inner">
              <div class="stat-icon-wrap stat-icon-indigo">
                <van-icon name="friends-o" size="22" />
              </div>
              <div class="stat-info">
                <span class="stat-value">{{ stats.passCount }}</span>
                <span class="stat-label">今日通行</span>
              </div>
              <van-icon name="arrow" class="stat-arrow" size="14" />
            </div>
          </div>

          <div
            class="stat-card stat-card-danger"
            @click="$router.push('/alarm-center')"
          >
            <div class="stat-card-glow"></div>
            <div class="stat-card-inner">
              <div class="stat-icon-wrap stat-icon-rose">
                <van-icon name="warning-o" size="22" />
              </div>
              <div class="stat-info">
                <span class="stat-value">{{ stats.alarmCount }}</span>
                <span class="stat-label">待处理告警</span>
              </div>
              <van-icon name="arrow" class="stat-arrow" size="14" />
            </div>
          </div>

          <div class="stat-card stat-card-success">
            <div class="stat-card-glow"></div>
            <div class="stat-card-inner">
              <div class="stat-icon-wrap stat-icon-emerald">
                <van-icon name="shield-o" size="22" />
              </div>
              <div class="stat-info">
                <span class="stat-value">{{ stats.onlineDevices }}</span>
                <span class="stat-label">在线设备</span>
              </div>
            </div>
          </div>

          <div class="stat-card" :class="stats.zoneStatus === '正常' ? 'stat-card-success' : 'stat-card-danger'">
            <div class="stat-card-glow"></div>
            <div class="stat-card-inner">
              <div class="stat-icon-wrap" :class="stats.zoneStatus === '正常' ? 'stat-icon-emerald' : 'stat-icon-rose'">
                <van-icon name="eye-o" size="22" />
              </div>
              <div class="stat-info">
                <span class="stat-value">{{ stats.zoneStatus }}</span>
                <span class="stat-label">禁区状态</span>
              </div>
            </div>
          </div>
        </section>

        <section class="section-block">
          <div class="section-header">
            <h2 class="section-title">最近告警</h2>
            <span class="section-more" @click="$router.push('/alarm-center')">查看全部</span>
          </div>
          <div class="alarm-list">
            <div
              v-for="alarm in recentAlarms"
              :key="alarm.id"
              class="alarm-item"
            >
              <div class="alarm-dot" :class="alarm.level === 'high' ? 'alarm-dot-high' : 'alarm-dot-low'"></div>
              <div class="alarm-body">
                <span class="alarm-title">{{ alarm.title }}</span>
                <span class="alarm-meta">{{ alarm.location }} · {{ alarm.time }}</span>
              </div>
              <span class="alarm-badge" :class="alarm.level === 'high' ? 'badge-high' : 'badge-low'">
                {{ alarm.level === 'high' ? '高危' : '一般' }}
              </span>
            </div>
            <div v-if="!recentAlarms.length" class="alarm-empty">
              <van-icon name="checked" size="28" :style="{ color: 'var(--dark-text-dim)' }" />
              <span>暂无告警</span>
            </div>
          </div>
        </section>
      </div>
    </main>
  </div>
</template>

<script>
import { getDashboardStats, getRecentAlarms } from '@/api/dashboard'

export default {
  name: 'DashboardPage',
  data () {
    return {
      currentTime: '',
      currentDate: '',
      timeTimer: null,
      stats: {
        passCount: 0,
        alarmCount: 0,
        onlineDevices: 0,
        zoneStatus: '正常'
      },
      recentAlarms: [],
      navItems: [
        { label: '安防总览', icon: 'home-o', path: '/dashboard' },
        { label: '人脸管理', icon: 'friends-o', path: '/face-management' },
        { label: '门禁权限', icon: 'shield-o', path: '/access-control' },
        { label: '禁区检测', icon: 'warning-o', path: '/danger-zone' },
        { label: '视频监控', icon: 'eye-o', path: '/video-monitor' },
        { label: '告警中心', icon: 'bell', path: '/alarm-center' },
        { label: '安防日报', icon: 'notes-o', path: '/report' },
        { label: '通行日志', icon: 'orders-o', path: '/property-admin/pass-logs' },
        { label: '告警日志', icon: 'records', path: '/property-admin/alarm-logs' },
        { label: '人脸测试', icon: 'scan', path: '/property-admin/face-test' }
      ]
    }
  },
  mounted () {
    this.updateTime()
    this.timeTimer = setInterval(this.updateTime, 1000)
    this.loadDashboardStats()
    this.loadRecentAlarms()
  },
  beforeDestroy () {
    if (this.timeTimer) {
      clearInterval(this.timeTimer)
    }
  },
  methods: {
    updateTime () {
      const now = new Date()
      const h = String(now.getHours()).padStart(2, '0')
      const m = String(now.getMinutes()).padStart(2, '0')
      const s = String(now.getSeconds()).padStart(2, '0')
      this.currentTime = `${h}:${m}:${s}`
      const month = now.getMonth() + 1
      const day = now.getDate()
      const weekDays = ['日', '一', '二', '三', '四', '五', '六']
      const weekDay = weekDays[now.getDay()]
      this.currentDate = `${month}月${day}日 周${weekDay}`
    },
    isActive (path) {
      return this.$route.path === path
    },
    async loadDashboardStats () {
      try {
        const res = await getDashboardStats()
        if (res.data) {
          this.stats = { ...this.stats, ...res.data }
        }
      } catch (e) {
        // 接口未就绪时使用默认值
      }
    },
    async loadRecentAlarms () {
      try {
        const res = await getRecentAlarms({ limit: 5 })
        if (res.data) {
          this.recentAlarms = res.data.list || []
        }
      } catch (e) {
        // 接口未就绪时使用空列表
      }
    }
  }
}
</script>

<style scoped>
@keyframes breathe {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

@keyframes float-orb {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(30px, -20px) scale(1.05); }
  66% { transform: translate(-20px, 15px) scale(0.95); }
}

@keyframes shimmer {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(200%); }
}

.dashboard-page {
  display: flex;
  min-height: 100vh;
  background: var(--dark-bg);
  color: var(--dark-text);
  position: relative;
  overflow-x: hidden;
}

.dashboard-bg {
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
}

.bg-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(120px);
  opacity: 0.12;
}

.bg-orb-1 {
  width: 400px;
  height: 400px;
  background: var(--dark-accent);
  top: -100px;
  right: -80px;
  animation: float-orb 20s ease-in-out infinite;
}

.bg-orb-2 {
  width: 300px;
  height: 300px;
  background: var(--dark-purple);
  bottom: 10%;
  left: 60px;
  animation: float-orb 25s ease-in-out infinite reverse;
}

.sidebar {
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  width: 200px;
  z-index: 20;
  display: flex;
  flex-direction: column;
  background: var(--dark-bg-sidebar);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border-right: 1px solid var(--dark-border);
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 20px 20px 24px;
}

.brand-icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: rgba(99, 102, 241, 0.15);
  display: flex;
  align-items: center;
  justify-content: center;
}

.brand-text {
  font-size: 15px;
  font-weight: 600;
  letter-spacing: -0.01em;
  color: var(--dark-text);
}

.sidebar-nav {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 0 10px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: 10px;
  cursor: pointer;
  transition: background 0.15s ease, color 0.15s ease;
  color: var(--dark-text-secondary);
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.04);
  color: var(--dark-text);
}

.nav-item-active {
  background: rgba(99, 102, 241, 0.1);
  color: var(--dark-text);
}

.nav-item-active .nav-icon-wrap {
  color: var(--dark-accent-light);
}

.nav-icon-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  flex-shrink: 0;
}

.nav-label {
  font-size: 13px;
  font-weight: 500;
  letter-spacing: -0.01em;
}

.sidebar-footer {
  padding: 16px 20px;
  border-top: 1px solid var(--dark-border-light);
}

.sidebar-status {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--dark-success);
  animation: breathe 3s ease-in-out infinite;
  box-shadow: 0 0 8px rgba(16, 185, 129, 0.5);
}

.status-text {
  font-size: 12px;
  color: var(--dark-text-secondary);
}

.main-area {
  margin-left: 200px;
  flex: 1;
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.main-header {
  position: sticky;
  top: 0;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 28px;
  background: var(--dark-bg-header);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border-bottom: 1px solid var(--dark-border);
}

.header-title {
  font-size: 22px;
  font-weight: 600;
  letter-spacing: -0.02em;
  margin: 0;
  color: var(--dark-text);
}

.header-subtitle {
  font-size: 13px;
  color: var(--dark-text-secondary);
  margin-top: 2px;
  display: block;
}

.header-time {
  font-size: 32px;
  font-weight: 600;
  letter-spacing: 0.05em;
  color: var(--dark-text-secondary);
  font-variant-numeric: tabular-nums;
}

.main-content {
  padding: 24px 28px 40px;
  flex: 1;
}

.stats-grid {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr;
  gap: 14px;
}

.stat-card {
  position: relative;
  border-radius: 16px;
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  border: 1px solid var(--dark-border);
  background: var(--dark-card);
}

.stat-card:active {
  transform: scale(0.97);
}

.stat-card-wide {
  grid-column: span 1;
}

.stat-card-glow {
  position: absolute;
  top: -20px;
  right: -20px;
  width: 80px;
  height: 80px;
  border-radius: 50%;
  filter: blur(40px);
  opacity: 0.2;
  pointer-events: none;
}

.stat-card-primary .stat-card-glow {
  background: var(--dark-accent);
}

.stat-card-danger .stat-card-glow {
  background: var(--dark-danger);
}

.stat-card-success .stat-card-glow {
  background: var(--dark-success);
}

.stat-card-inner {
  position: relative;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 14px;
  overflow: hidden;
}

.stat-card-inner::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 50%;
  height: 100%;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(255, 255, 255, 0.03),
    transparent
  );
  animation: shimmer 6s ease-in-out infinite;
  pointer-events: none;
}

.stat-icon-wrap {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-icon-indigo {
  background: rgba(99, 102, 241, 0.15);
  color: var(--dark-accent-light);
}

.stat-icon-rose {
  background: rgba(239, 68, 68, 0.15);
  color: var(--dark-danger-light);
}

.stat-icon-emerald {
  background: rgba(16, 185, 129, 0.15);
  color: var(--dark-success-light);
}

.stat-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  letter-spacing: -0.02em;
  line-height: 1.2;
  color: var(--dark-text);
}

.stat-label {
  font-size: 12px;
  color: var(--dark-text-secondary);
  line-height: 1.2;
}

.stat-arrow {
  margin-left: auto;
  color: var(--dark-text-dim);
  flex-shrink: 0;
}

.section-block {
  margin-top: 24px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  letter-spacing: -0.01em;
  color: var(--dark-text);
}

.section-more {
  font-size: 12px;
  color: var(--dark-accent);
  cursor: pointer;
}

.alarm-list {
  border-radius: 16px;
  background: var(--dark-card);
  border: 1px solid var(--dark-border);
  overflow: hidden;
}

.alarm-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 20px;
  border-bottom: 1px solid var(--dark-border-light);
  cursor: pointer;
  transition: background 0.15s ease;
}

.alarm-item:last-child {
  border-bottom: none;
}

.alarm-item:active {
  background: rgba(255, 255, 255, 0.03);
}

.alarm-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.alarm-dot-high {
  background: var(--dark-danger);
  box-shadow: 0 0 8px rgba(239, 68, 68, 0.4);
  animation: breathe 2s ease-in-out infinite;
}

.alarm-dot-low {
  background: #F59E0B;
}

.alarm-body {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
  flex: 1;
}

.alarm-title {
  font-size: 14px;
  color: var(--dark-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.alarm-meta {
  font-size: 11px;
  color: var(--dark-text-muted);
}

.alarm-badge {
  font-size: 10px;
  padding: 2px 8px;
  border-radius: 6px;
  flex-shrink: 0;
  font-weight: 500;
}

.badge-high {
  background: rgba(239, 68, 68, 0.15);
  color: var(--dark-danger-light);
}

.badge-low {
  background: rgba(245, 158, 11, 0.15);
  color: var(--dark-warning);
}

.alarm-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 32px 16px;
  color: var(--dark-text-dim);
  font-size: 13px;
}

@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    bottom: 0;
    top: auto;
    left: 0;
    right: 0;
    width: 100%;
    height: 64px;
    flex-direction: row;
    border-right: none;
    border-top: 1px solid var(--dark-border);
  }

  .sidebar-brand,
  .sidebar-footer {
    display: none;
  }

  .sidebar-nav {
    flex-direction: row;
    justify-content: space-around;
    align-items: center;
    padding: 0 8px;
    gap: 0;
  }

  .nav-item {
    flex-direction: column;
    gap: 2px;
    padding: 6px 4px;
    border-radius: 8px;
  }

  .nav-label {
    font-size: 10px;
  }

  .main-area {
    margin-left: 0;
    padding-bottom: 64px;
  }

  .stats-grid {
    grid-template-columns: 1fr 1fr;
  }

  .main-header {
    padding: 16px 16px;
  }

  .main-content {
    padding: 16px 16px 32px;
  }

  .header-time {
    font-size: 24px;
  }
}
</style>
