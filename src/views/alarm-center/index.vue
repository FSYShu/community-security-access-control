<template>
  <app-layout page-title="告警中心">
    <div class="alarm-page">
      <div class="alarm-stats">
        <div class="stat-card dark-card">
          <div class="stat-value">{{ stats.total }}</div>
          <div class="stat-label">总告警</div>
        </div>
        <div class="stat-card dark-card">
          <div class="stat-value stat-pending">{{ stats.pending }}</div>
          <div class="stat-label">待处理</div>
        </div>
        <div class="stat-card dark-card">
          <div class="stat-value stat-handled">{{ stats.handled }}</div>
          <div class="stat-label">已处理</div>
        </div>
        <div class="stat-card dark-card">
          <div class="stat-value stat-today">{{ stats.today_count }}</div>
          <div class="stat-label">今日告警</div>
        </div>
      </div>

      <div class="alarm-filter dark-card">
        <div class="filter-row">
          <el-select v-model="filterStatus" placeholder="处置状态" size="small" clearable @change="onFilterChange">
            <el-option label="待处理" value="pending" />
            <el-option label="已处理" value="handled" />
          </el-select>
          <el-select v-model="filterLevel" placeholder="告警级别" size="small" clearable @change="onFilterChange">
            <el-option label="低" value="low" />
            <el-option label="中" value="medium" />
            <el-option label="高" value="high" />
          </el-select>
          <el-select v-model="filterType" placeholder="告警类型" size="small" clearable @change="onFilterChange">
            <el-option label="禁区入侵" value="danger_zone_intrusion" />
          </el-select>
          <button class="action-btn export-btn" @click="onExport">
            <i class="el-icon-download"></i>
            <span>导出</span>
          </button>
        </div>
      </div>

      <div class="alarm-list">
        <van-pull-refresh v-model="refreshing" @refresh="onRefresh">
          <van-list v-model="loading" :finished="finished" finished-text="没有更多了" @load="loadAlarms">
            <div v-for="alarm in alarmList" :key="alarm.id" class="alarm-card dark-card" @click="openDetail(alarm)">
              <div class="alarm-card-header">
                <div class="alarm-type-badge" :class="'badge-' + alarm.alarm_level">
                  {{ levelMap[alarm.alarm_level] || alarm.alarm_level }}
                </div>
                <span class="alarm-desc">{{ alarm.alarm_description }}</span>
                <span class="alarm-status-tag" :class="alarm.handle_status === 'handled' ? 'tag-handled' : 'tag-pending'">
                  {{ alarm.handle_status === 'handled' ? '已处理' : '待处理' }}
                </span>
              </div>
              <div class="alarm-card-body">
                <div class="alarm-meta">
                  <i class="el-icon-time"></i>
                  <span>{{ alarm.alarm_time }}</span>
                </div>
                <div class="alarm-meta">
                  <i class="el-icon-warning-outline"></i>
                  <span>{{ typeMap[alarm.alarm_type] || alarm.alarm_type }}</span>
                </div>
              </div>
            </div>
          </van-list>
          <div v-if="!loading && alarmList.length === 0" class="empty-state">
            <i class="el-icon-bell empty-icon"></i>
            <p>暂无告警记录</p>
          </div>
        </van-pull-refresh>
      </div>

      <el-dialog :visible.sync="showDetailDialog" title="告警详情" width="500px" append-to-body custom-class="dark-dialog">
        <div v-if="currentAlarm" class="alarm-detail">
          <div class="detail-row">
            <span class="detail-label">告警ID</span>
            <span class="detail-value">{{ currentAlarm.id }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">告警类型</span>
            <span class="detail-value">{{ typeMap[currentAlarm.alarm_type] || currentAlarm.alarm_type }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">告警级别</span>
            <span class="detail-value">
              <span class="alarm-type-badge" :class="'badge-' + currentAlarm.alarm_level">
                {{ levelMap[currentAlarm.alarm_level] || currentAlarm.alarm_level }}
              </span>
            </span>
          </div>
          <div class="detail-row">
            <span class="detail-label">告警描述</span>
            <span class="detail-value">{{ currentAlarm.alarm_description }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">告警时间</span>
            <span class="detail-value">{{ currentAlarm.alarm_time }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">处置状态</span>
            <span class="detail-value">
              <span class="alarm-status-tag" :class="currentAlarm.handle_status === 'handled' ? 'tag-handled' : 'tag-pending'">
                {{ currentAlarm.handle_status === 'handled' ? '已处理' : '待处理' }}
              </span>
            </span>
          </div>
          <div v-if="currentAlarm.handle_status === 'handled'" class="detail-row">
            <span class="detail-label">处置时间</span>
            <span class="detail-value">{{ currentAlarm.handle_time }}</span>
          </div>
          <div v-if="currentAlarm.handle_status === 'handled'" class="detail-row">
            <span class="detail-label">处置备注</span>
            <span class="detail-value">{{ currentAlarm.handle_remark }}</span>
          </div>
        </div>
        <div v-if="currentAlarm && currentAlarm.handle_status === 'pending'" slot="footer">
          <el-button size="small" @click="showDetailDialog = false">关闭</el-button>
          <el-button size="small" type="primary" @click="openHandleDialog">处置</el-button>
        </div>
      </el-dialog>

      <el-dialog :visible.sync="showHandleDialog" title="处置告警" width="400px" :close-on-click-modal="false" append-to-body custom-class="dark-dialog">
        <div class="form-grid">
          <div class="form-item">
            <label class="form-label">处置备注 <span class="required">*</span></label>
            <el-input v-model="handleRemark" type="textarea" :rows="3" placeholder="请输入处置备注" size="small" />
          </div>
        </div>
        <div slot="footer">
          <el-button size="small" @click="showHandleDialog = false">取消</el-button>
          <el-button size="small" type="primary" @click="submitHandle">确认处置</el-button>
        </div>
      </el-dialog>
    </div>
  </app-layout>
</template>

<script>
import { getAlarmList, getAlarmDetail, handleAlarm, exportAlarmLog, getAlarmStats } from '@/api/alarm'

export default {
  name: 'AlarmCenterPage',
  data () {
    return {
      alarmList: [],
      loading: false,
      finished: false,
      refreshing: false,
      page: 1,
      perPage: 20,
      filterStatus: '',
      filterLevel: '',
      filterType: '',
      stats: {
        total: 0,
        pending: 0,
        handled: 0,
        today_count: 0
      },
      showDetailDialog: false,
      currentAlarm: null,
      showHandleDialog: false,
      handleRemark: '',
      levelMap: { low: '低', medium: '中', high: '高' },
      typeMap: { danger_zone_intrusion: '禁区入侵' }
    }
  },
  created () {
    this.fetchStats()
  },
  methods: {
    async fetchStats () {
      try {
        const res = await getAlarmStats()
        if (res.code === 0 && res.data) {
          this.stats = res.data
        }
      } catch (e) {
        console.error('Failed to fetch alarm stats:', e)
      }
    },
    async loadAlarms () {
      try {
        const params = {
          page: this.page,
          per_page: this.perPage
        }
        if (this.filterStatus) params.handle_status = this.filterStatus
        if (this.filterLevel) params.alarm_level = this.filterLevel
        if (this.filterType) params.alarm_type = this.filterType

        const res = await getAlarmList(params)
        if (res.code === 0 && res.data) {
          const items = res.data.items || []
          if (this.page === 1) {
            this.alarmList = items
          } else {
            this.alarmList = this.alarmList.concat(items)
          }
          const total = res.data.total || 0
          if (this.alarmList.length >= total) {
            this.finished = true
          } else {
            this.page++
          }
        } else {
          this.finished = true
        }
      } catch (e) {
        console.error('Failed to load alarms:', e)
        this.finished = true
      } finally {
        this.loading = false
      }
    },
    onRefresh () {
      this.page = 1
      this.finished = false
      this.loading = true
      this.loadAlarms().then(function () {
        this.refreshing = false
        this.fetchStats()
      }.bind(this))
    },
    onFilterChange () {
      this.page = 1
      this.alarmList = []
      this.finished = false
      this.loading = true
      this.loadAlarms()
    },
    async openDetail (alarm) {
      try {
        const res = await getAlarmDetail(alarm.id)
        if (res.code === 0 && res.data) {
          this.currentAlarm = res.data
          this.showDetailDialog = true
        }
      } catch (e) {
        console.error('Failed to get alarm detail:', e)
      }
    },
    openHandleDialog () {
      this.handleRemark = ''
      this.showHandleDialog = true
    },
    async submitHandle () {
      if (!this.handleRemark.trim()) {
        this.$message.warning('请输入处置备注')
        return
      }
      try {
        const res = await handleAlarm(this.currentAlarm.id, {
          handle_remark: this.handleRemark.trim()
        })
        if (res.code === 0) {
          this.$message.success('处置成功')
          this.showHandleDialog = false
          this.showDetailDialog = false
          this.onRefresh()
        }
      } catch (e) {
        console.error('Handle alarm failed:', e)
      }
    },
    async onExport () {
      try {
        const params = {}
        if (this.filterStatus) params.handle_status = this.filterStatus
        if (this.filterLevel) params.alarm_level = this.filterLevel
        if (this.filterType) params.alarm_type = this.filterType

        const res = await exportAlarmLog(params)
        const blob = new Blob([res], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
        const url = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.download = 'alarm_log.xlsx'
        link.click()
        window.URL.revokeObjectURL(url)
        this.$message.success('导出成功')
      } catch (e) {
        console.error('Export failed:', e)
        this.$message.error('导出失败')
      }
    }
  }
}
</script>

<style scoped>
.alarm-page {
  height: calc(100vh - 120px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.alarm-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}

.stat-card {
  padding: 16px;
  text-align: center;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--dark-text);
}

.stat-pending {
  color: var(--dark-danger);
}

.stat-handled {
  color: var(--dark-success);
}

.stat-today {
  color: var(--dark-accent-light);
}

.stat-label {
  font-size: 12px;
  color: var(--dark-text-secondary);
  margin-top: 4px;
}

.alarm-filter {
  padding: 12px 16px;
  margin-bottom: 12px;
}

.filter-row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 7px 14px;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  transition: background 0.2s, color 0.2s;
  border: 1px solid var(--dark-border-field);
  background: rgba(255, 255, 255, 0.04);
  color: var(--dark-text-secondary);
}

.export-btn:hover {
  color: var(--dark-accent-light);
  border-color: var(--dark-accent);
}

.alarm-list {
  flex: 1;
  overflow-y: auto;
}

.alarm-card {
  padding: 14px 16px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: border-color 0.2s;
}

.alarm-card:hover {
  border-color: var(--dark-accent);
}

.alarm-card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.alarm-type-badge {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 500;
  flex-shrink: 0;
}

.badge-low {
  background: rgba(59, 130, 246, 0.12);
  color: var(--dark-info);
}

.badge-medium {
  background: rgba(251, 191, 36, 0.12);
  color: var(--dark-warning);
}

.badge-high {
  background: rgba(239, 68, 68, 0.12);
  color: var(--dark-danger);
}

.alarm-desc {
  font-size: 13px;
  color: var(--dark-text);
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.alarm-status-tag {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 500;
  flex-shrink: 0;
}

.tag-pending {
  background: rgba(239, 68, 68, 0.12);
  color: var(--dark-danger);
}

.tag-handled {
  background: rgba(16, 185, 129, 0.12);
  color: var(--dark-success);
}

.alarm-card-body {
  display: flex;
  align-items: center;
  gap: 16px;
}

.alarm-meta {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--dark-text-secondary);
}

.alarm-meta i {
  font-size: 13px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: var(--dark-text-muted);
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 12px;
}

.alarm-detail {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.detail-row {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.detail-label {
  font-size: 13px;
  color: var(--dark-text-secondary);
  min-width: 70px;
  flex-shrink: 0;
}

.detail-value {
  font-size: 13px;
  color: var(--dark-text);
  word-break: break-all;
}

.form-grid {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-label {
  font-size: 13px;
  color: var(--dark-text-secondary);
  font-weight: 500;
}

.required {
  color: var(--dark-danger);
}
</style>
