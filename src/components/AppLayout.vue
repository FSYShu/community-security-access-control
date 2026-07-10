<template>
  <div class="app-layout">
    <div class="layout-bg">
      <div class="bg-orb bg-orb-1"></div>
      <div class="bg-orb bg-orb-2"></div>
    </div>

    <div v-if="sidebarOpen" class="sidebar-overlay" @click="sidebarOpen = false"></div>

    <aside class="sidebar" :class="{ 'is-open': sidebarOpen }">
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
          @click="$router.push(item.path); sidebarOpen = false"
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

      <main class="main-area" :class="{ 'no-scroll': noScroll }">
      <header class="main-header">
        <div class="header-left">
          <button class="header-menu-btn" @click="sidebarOpen = !sidebarOpen">
            <i :class="sidebarOpen ? 'el-icon-close' : 'el-icon-s-unfold'"></i>
          </button>
          <button v-if="showBack" class="header-back" @click="$router.back()">
            <i class="el-icon-arrow-left"></i>
            <span>返回</span>
          </button>
          <h1 class="header-title">{{ pageTitle }}</h1>
        </div>
        <div class="header-right">
          <div class="header-datetime-mobile">
            <div class="header-status-mobile">
              <span class="status-dot"></span>
              <span class="status-text-mobile">运行中</span>
            </div>
            <div class="header-time-row">
              <span class="header-date-mobile">{{ currentDate }}</span>
              <span class="header-time-mobile">{{ currentTime }}</span>
            </div>
          </div>
        </div>
      </header>

      <div class="main-content" :class="{ 'no-scroll': noScroll }">
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
    },
    noScroll: {
      type: Boolean,
      default: false
    }
  },
  data () {
    return {
      currentTime: '',
      currentDate: '',
      timeTimer: null,
      sidebarOpen: false,
      navItems: [
        { label: '安防总览', icon: 'el-icon-monitor', path: '/dashboard' },
        { label: '人脸管理', icon: 'el-icon-user', path: '/face-management' },
        { label: '门禁管理', icon: 'el-icon-lock', path: '/access-control' },
        { label: '禁区检测', icon: 'el-icon-warning-outline', path: '/danger-zone' },
        { label: '实时监控', icon: 'el-icon-view', path: '/video-monitor' },
        { label: '历史回放', icon: 'el-icon-video-play', path: '/video-monitor/playback' },
        { label: '告警中心', icon: 'el-icon-bell', path: '/alarm-center' },
        { label: '安防日报', icon: 'el-icon-document', path: '/report' },
        { label: '通行日志', icon: 'el-icon-notebook-2', path: '/property-admin/pass-logs' },
        { label: '告警日志', icon: 'el-icon-tickets', path: '/property-admin/alarm-logs' }
      ]
    }
  },
  computed: {
    showBack () {
      const navPaths = this.navItems.map(item => item.path)
      return !navPaths.includes(this.$route.path)
    }
  },
  mounted () {
    this.updateTime()
    this.timeTimer = setInterval(this.updateTime, 1000)
    this.checkWidth()
    window.addEventListener('resize', this.checkWidth)
  },
  beforeDestroy () {
    if (this.timeTimer) {
      clearInterval(this.timeTimer)
    }
    window.removeEventListener('resize', this.checkWidth)
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
      return this.$route.path === path
    },
    checkWidth () {
      if (window.innerWidth <= 768) {
        this.sidebarOpen = false
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

.app-layout {
  position: relative;
  min-height: 100vh;
  background: var(--dark-bg);
  color: var(--dark-text);
}

.layout-bg {
  position: fixed;
  inset: 0;
  z-index: 0;
  overflow: hidden;
  pointer-events: none;
}

.bg-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(120px);
  animation: float-orb 20s ease-in-out infinite;
}

.bg-orb-1 {
  width: 400px;
  height: 400px;
  background: rgba(99, 102, 241, 0.06);
  top: -100px;
  right: -100px;
}

.bg-orb-2 {
  width: 300px;
  height: 300px;
  background: rgba(16, 185, 129, 0.04);
  bottom: -80px;
  left: 20%;
  animation-delay: -7s;
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
  color: var(--dark-text);
  letter-spacing: -0.01em;
}

.sidebar-nav {
  flex: 1;
  overflow-y: auto;
  padding: 0 10px;
  display: flex;
  flex-direction: column;
  gap: 2px;
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

.sidebar-overlay {
  display: none;
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 15;
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

.main-area.no-scroll {
  height: 100vh;
  min-height: 100vh;
  overflow: hidden;
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

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-menu-btn {
  display: none;
  width: 36px;
  height: 36px;
  border: none;
  background: rgba(255, 255, 255, 0.06);
  border-radius: 8px;
  color: var(--dark-text-secondary);
  font-size: 18px;
  cursor: pointer;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: background 0.2s, color 0.2s;
}

.header-menu-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: var(--dark-text);
}

.header-right {
  display: none;
  align-items: center;
  gap: 16px;
}

.header-datetime-mobile {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.header-status-mobile {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 2px;
}

.status-text-mobile {
  font-size: 11px;
  color: var(--dark-text-secondary);
}

.header-time-row {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.header-date-mobile {
  font-size: 16px;
  font-weight: 600;
  color: var(--dark-text-secondary);
  font-variant-numeric: tabular-nums;
}

.header-time-mobile {
  font-size: 16px;
  font-weight: 600;
  color: var(--dark-text-secondary);
  font-variant-numeric: tabular-nums;
  letter-spacing: 0.03em;
}

.header-title {
  font-size: 22px;
  font-weight: 600;
  letter-spacing: -0.02em;
  margin: 0;
  color: var(--dark-text);
}

.header-back {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 6px 12px;
  border: none;
  background: rgba(255, 255, 255, 0.06);
  border-radius: 8px;
  color: var(--dark-text-secondary);
  cursor: pointer;
  font-size: 13px;
  transition: background 0.2s, color 0.2s;
  flex-shrink: 0;
}

.header-back:hover {
  background: rgba(255, 255, 255, 0.1);
  color: var(--dark-text);
}

.header-back i {
  font-size: 14px;
}

.main-content {
  padding: 24px 28px 40px;
  flex: 1;
  overflow: auto;
}

.main-content.no-scroll {
  overflow: hidden;
  padding-bottom: 24px;
}

@media (max-width: 768px) {
  .sidebar {
    transform: translateX(-100%);
    transition: transform 0.3s ease;
  }

  .sidebar.is-open {
    transform: translateX(0);
  }

  .sidebar-overlay {
    display: block;
  }

  .sidebar-footer {
    display: none;
  }

  .header-menu-btn {
    display: flex;
  }

  .header-right {
    display: flex;
  }

  .main-area {
    margin-left: 0;
  }

  .main-header {
    padding: 12px 16px;
  }

  .header-title {
    font-size: 16px;
  }

  .main-content {
    padding: 16px 16px 32px;
  }
}
</style>
