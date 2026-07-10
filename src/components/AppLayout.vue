<template>
  <div class="app-layout">
    <div class="layout-bg">
      <div class="bg-orb bg-orb-1"></div>
      <div class="bg-orb bg-orb-2"></div>
    </div>

    <aside class="sidebar">
      <div class="sidebar-brand">
        <div class="brand-icon">
          <i class="el-icon-lock brand-el-icon" :style="{ color: 'var(--dark-accent-light)' }"></i>
        </div>
        <span class="brand-text">社区安防门禁系统后台</span>
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
            <i :class="item.icon"></i>
          </div>
          <span class="nav-label">{{ item.label }}</span>
        </div>
      </nav>

      <div class="sidebar-footer">
        <div class="sidebar-datetime">
          <span class="sidebar-date">{{ currentDate }}</span>
          <span class="sidebar-time">{{ currentTime }}</span>
        </div>
        <div class="sidebar-status">
          <span class="status-dot"></span>
          <span class="status-text">运行中</span>
        </div>
      </div>
    </aside>

    <main class="main-area">
      <header class="main-header">
        <div class="header-left">
          <h1 class="header-title">{{ pageTitle }}</h1>
        </div>
      </header>

      <div class="main-content">
        <slot></slot>
      </div>
    </main>
  </div>
</template>

<script>
export default {
  name: 'AppLayout',
  props: {
    pageTitle: {
      type: String,
      default: ''
    }
  },
  data () {
    return {
      currentTime: '',
      currentDate: '',
      timeTimer: null,
      navItems: [
        { label: '安防总览', icon: 'el-icon-monitor', path: '/dashboard' },
        { label: '人脸管理', icon: 'el-icon-user', path: '/face-management' },
        { label: '门禁权限', icon: 'el-icon-lock', path: '/access-control' },
        { label: '禁区检测', icon: 'el-icon-warning-outline', path: '/danger-zone' },
        { label: '视频监控', icon: 'el-icon-view', path: '/video-monitor' },
        { label: '告警中心', icon: 'el-icon-bell', path: '/alarm-center' },
        { label: '安防日报', icon: 'el-icon-document', path: '/report' },
        { label: '通行日志', icon: 'el-icon-notebook-2', path: '/property-admin/pass-logs' },
        { label: '告警日志', icon: 'el-icon-tickets', path: '/property-admin/alarm-logs' }
      ]
    }
  },
  mounted () {
    this.updateTime()
    this.timeTimer = setInterval(this.updateTime, 1000)
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
      const year = now.getFullYear()
      const month = now.getMonth() + 1
      const day = now.getDate()
      const weekDays = ['日', '一', '二', '三', '四', '五', '六']
      const weekDay = weekDays[now.getDay()]
      this.currentDate = `${year}年${month}月${day}日 周${weekDay}`
    },
    isActive (path) {
      return this.$route.path === path || this.$route.path.startsWith(path + '/')
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

.app-layout {
  display: flex;
  min-height: 100vh;
  background: var(--dark-bg);
  color: var(--dark-text);
  position: relative;
  overflow-x: hidden;
}

.layout-bg {
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
  width: 260px;
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

.brand-el-icon {
  font-size: 20px;
}

.brand-text {
  font-size: 15px;
  font-weight: 600;
  letter-spacing: -0.01em;
  color: #EDEDEF;
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
  font-size: 18px;
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

.sidebar-datetime {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  margin-bottom: 12px;
}

.sidebar-date {
  font-size: 14px;
  color: var(--dark-text-secondary);
}

.sidebar-time {
  font-size: 28px;
  font-weight: 600;
  letter-spacing: 0.05em;
  color: var(--dark-text-secondary);
  font-variant-numeric: tabular-nums;
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
  margin-left: 260px;
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

.main-content {
  padding: 24px 28px 40px;
  flex: 1;
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

  .main-header {
    padding: 16px 16px;
  }

  .main-content {
    padding: 16px 16px 32px;
  }
}
</style>
