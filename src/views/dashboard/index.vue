<template>
  <app-layout page-title="安防总览">
    <section class="stats-grid">
      <div
        class="stat-card stat-card-wide stat-card-primary"
        @click="$router.push('/property-admin/pass-logs')"
      >
        <div class="stat-card-glow"></div>
        <div class="stat-card-inner">
          <div class="stat-icon-wrap stat-icon-indigo">
            <i class="el-icon-user" style="font-size:22px"></i>
          </div>
          <div class="stat-info">
            <span class="stat-value">{{ stats.passCount }}</span>
            <span class="stat-label">今日通行</span>
          </div>
          <i class="el-icon-arrow-right stat-arrow" style="font-size:14px"></i>
        </div>
      </div>

      <div
        class="stat-card stat-card-danger"
        @click="$router.push('/alarm-center')"
      >
        <div class="stat-card-glow"></div>
        <div class="stat-card-inner">
          <div class="stat-icon-wrap stat-icon-rose">
            <i class="el-icon-warning-outline" style="font-size:22px"></i>
          </div>
          <div class="stat-info">
            <span class="stat-value">{{ stats.alarmCount }}</span>
            <span class="stat-label">待处理告警</span>
          </div>
          <i class="el-icon-arrow-right stat-arrow" style="font-size:14px"></i>
        </div>
      </div>

      <div class="stat-card stat-card-success" @click="$router.push('/access-control')">
        <div class="stat-card-glow"></div>
        <div class="stat-card-inner">
          <div class="stat-icon-wrap stat-icon-emerald">
            <i class="el-icon-lock" style="font-size:22px"></i>
          </div>
          <div class="stat-info">
            <span class="stat-value">{{ stats.onlineDevices }}</span>
            <span class="stat-label">在线设备</span>
          </div>
          <i class="el-icon-arrow-right stat-arrow" style="font-size:14px"></i>
        </div>
      </div>

      <div class="stat-card" :class="stats.zoneStatus === '正常' ? 'stat-card-success' : 'stat-card-danger'">
        <div class="stat-card-glow"></div>
        <div class="stat-card-inner">
          <div class="stat-icon-wrap" :class="stats.zoneStatus === '正常' ? 'stat-icon-emerald' : 'stat-icon-rose'">
            <i class="el-icon-view" style="font-size:22px"></i>
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
          <i class="el-icon-circle-check" style="font-size:28px;color:var(--dark-text-dim)"></i>
          <span>暂无告警</span>
        </div>
      </div>
    </section>
  </app-layout>
</template>

<script>
import { getDashboardStats, getRecentAlarms } from '@/api/dashboard'

export default {
  name: 'DashboardPage',
  data () {
    return {
      stats: {
        passCount: 0,
        alarmCount: 0,
        onlineDevices: 0,
        zoneStatus: '正常'
      },
      recentAlarms: []
    }
  },
  mounted () {
    this.loadDashboardStats()
    this.loadRecentAlarms()
  },
  methods: {
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

@keyframes shimmer {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(200%); }
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

@media (max-width: 1024px) {
  .stats-grid {
    grid-template-columns: 1fr 1fr;
  }
}
</style>
