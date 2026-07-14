<template>
  <app-layout page-title="AI安防日报" :no-scroll="true">
    <div class="report-page">
      <div class="report-stats">
        <div class="stat-item">
          <span class="stat-value">{{ workflowStatus && workflowStatus.auto_enabled ? '已开启' : '未开启' }}</span>
          <span class="stat-label">自动日报</span>
        </div>
        <div class="stat-item stat-ai">
          <span class="stat-value">{{ workflowStatus && workflowStatus.ai_configured ? '已配置' : '待配置' }}</span>
          <span class="stat-label">AI服务 · {{ workflowStateLabel }}</span>
        </div>
      </div>

      <div class="filter-section">
        <div class="filter-row filter-time">
          <div class="filter-group">
            <div class="custom-date-picker">
              <div class="date-trigger" @click="toggleDatePicker('start')">
                <span :class="{ 'is-placeholder': !filter.startDate }">{{ filter.startDate || '开始日期' }}</span>
                <i class="el-icon-date"></i>
              </div>
              <div v-if="openDatePicker === 'start'" class="date-dropdown">
                <div class="date-header">
                  <button class="date-nav-btn" @click="showMonthYearPicker === 'start' ? prevYear('start') : prevMonth('start')">
                    <i class="el-icon-arrow-left"></i>
                  </button>
                  <button class="date-title-btn" @click="toggleMonthYearPicker('start')">
                    {{ showMonthYearPicker === 'start' ? startPickerDate.getFullYear() + '年' : getMonthTitle(startPickerDate) }}
                    <i :class="showMonthYearPicker === 'start' ? 'el-icon-arrow-up' : 'el-icon-arrow-down'"></i>
                  </button>
                  <button class="date-nav-btn" @click="showMonthYearPicker === 'start' ? nextYear('start') : nextMonth('start')">
                    <i class="el-icon-arrow-right"></i>
                  </button>
                </div>
                <div v-if="showMonthYearPicker === 'start'" class="month-year-picker">
                  <div class="month-grid">
                    <span
                      v-for="month in 12"
                      :key="month"
                      class="month-item"
                      :class="{ 'is-current': isCurrentMonth(month, 'start') }"
                      @click.stop="selectMonth(month, 'start')"
                    >
                      {{ month }}月
                    </span>
                  </div>
                </div>
                <div v-show="showMonthYearPicker !== 'start'">
                  <div class="date-today-btn" @click="goToToday('start')">
                    <i class="el-icon-time"></i>
                    <span>回到今天</span>
                  </div>
                  <div class="date-weekdays">
                    <span v-for="day in weekdays" :key="day" class="weekday">{{ day }}</span>
                  </div>
                  <div class="date-days">
                    <span
                      v-for="(day, index) in getDaysInMonth(startPickerDate)"
                      :key="index"
                      class="day"
                      :class="{
                        'is-empty': !day.date,
                        'is-today': isToday(day.date),
                        'is-selected': isDateSelected(day.date, 'start')
                      }"
                      @click="selectDate(day.date, 'start')"
                    >
                      {{ day.day }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div class="filter-group">
            <div class="custom-date-picker">
              <div class="date-trigger" @click="toggleDatePicker('end')">
                <span :class="{ 'is-placeholder': !filter.endDate }">{{ filter.endDate || '结束日期' }}</span>
                <i class="el-icon-date"></i>
              </div>
              <div v-if="openDatePicker === 'end'" class="date-dropdown">
                <div class="date-header">
                  <button class="date-nav-btn" @click="showMonthYearPicker === 'end' ? prevYear('end') : prevMonth('end')">
                    <i class="el-icon-arrow-left"></i>
                  </button>
                  <button class="date-title-btn" @click="toggleMonthYearPicker('end')">
                    {{ showMonthYearPicker === 'end' ? endPickerDate.getFullYear() + '年' : getMonthTitle(endPickerDate) }}
                    <i :class="showMonthYearPicker === 'end' ? 'el-icon-arrow-up' : 'el-icon-arrow-down'"></i>
                  </button>
                  <button class="date-nav-btn" @click="showMonthYearPicker === 'end' ? nextYear('end') : nextMonth('end')">
                    <i class="el-icon-arrow-right"></i>
                  </button>
                </div>
                <div v-if="showMonthYearPicker === 'end'" class="month-year-picker">
                  <div class="month-grid">
                    <span
                      v-for="month in 12"
                      :key="month"
                      class="month-item"
                      :class="{ 'is-current': isCurrentMonth(month, 'end') }"
                      @click.stop="selectMonth(month, 'end')"
                    >
                      {{ month }}月
                    </span>
                  </div>
                </div>
                <div v-show="showMonthYearPicker !== 'end'">
                  <div class="date-today-btn" @click="goToToday('end')">
                    <i class="el-icon-time"></i>
                    <span>回到今天</span>
                  </div>
                  <div class="date-weekdays">
                    <span v-for="day in weekdays" :key="day" class="weekday">{{ day }}</span>
                  </div>
                  <div class="date-days">
                    <span
                      v-for="(day, index) in getDaysInMonth(endPickerDate)"
                      :key="index"
                      class="day"
                      :class="{
                        'is-empty': !day.date,
                        'is-today': isToday(day.date),
                        'is-selected': isDateSelected(day.date, 'end')
                      }"
                      @click="selectDate(day.date, 'end')"
                    >
                      {{ day.day }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div class="filter-actions-group">
            <button class="action-btn action-btn-primary" @click="onSearch">
              <i class="el-icon-search"></i>
              <span>查询</span>
            </button>
            <button class="action-btn action-btn-default" @click="onReset">
              <i class="el-icon-refresh"></i>
              <span>重置</span>
            </button>
          </div>
        </div>
        <div class="filter-bottom-row">
          <span v-if="workflowStatus && workflowStatus.auto_enabled" class="workflow-hint">
            <i class="el-icon-info"></i>
            <span>每天 {{ workflowStatus.generate_time }} 自动生成</span>
          </span>
          <span v-else class="workflow-hint"></span>
          <div class="filter-actions-group">
            <button class="action-btn action-btn-accent" @click="showGenerate = true">
              <i class="el-icon-magic-stick"></i>
              <span>AI生成</span>
            </button>
            <button class="action-btn action-btn-default" @click="openApiConfig">
              <i class="el-icon-setting"></i>
              <span>API配置</span>
            </button>
          </div>
        </div>
      </div>

      <div class="report-list-section" ref="listSection">
        <div v-if="loading" class="probe-loading"><i class="el-icon-loading"></i><span>加载中...</span></div>
        <div class="report-list" ref="listContent" :style="{ visibility: !loading || reportList.length ? '' : 'hidden' }">
          <van-cell v-for="item in reportList" :key="item.id" is-link @click="goDetail(item)">
            <template #title>
              <div class="cell-title-row">
                <span class="cell-name">{{ item.report_date }}</span>
                <span class="risk-tag" :class="`risk-${item.risk_level || 'low'}`">
                  {{ riskLabel(item.risk_level) }}风险
                </span>
              </div>
              <div class="cell-label-row">
                <span class="cell-meta">
                  <i class="el-icon-cpu"></i>
                  <span>{{ sourceLabel(item.workflow_source) }}</span>
                </span>
                <span class="cell-meta">
                  <i class="el-icon-circle-check"></i>
                  <span>{{ statusLabel(item.generate_status) }}</span>
                </span>
              </div>
            </template>
            <template #right-icon>
              <span class="cell-actions" @click.stop>
                <button class="cell-action-btn" :disabled="regeneratingId === item.id" @click="onRegenerate(item)">
                  <i :class="regeneratingId === item.id ? 'el-icon-loading' : 'el-icon-refresh'"></i>
                  <span>重新生成</span>
                </button>
                <button class="cell-action-btn cell-action-danger" :disabled="deletingId === item.id" @click="onDelete(item)">
                  <i :class="deletingId === item.id ? 'el-icon-loading' : 'el-icon-delete'"></i>
                  <span>删除</span>
                </button>
              </span>
            </template>
          </van-cell>
          <div v-if="reportList.length === 0 && !loading" class="empty-state">
            <i class="el-icon-document" style="font-size:48px;color:var(--dark-text-muted)"></i>
            <p style="color:var(--dark-text-muted);margin-top:12px">暂无日报数据</p>
          </div>
        </div>
        <div class="pagination-wrapper" v-show="reportList.length > 0">
          <el-pagination
            background
            layout="prev, pager, next"
            :current-page="page"
            :page-size="perPage"
            :total="total"
            @current-change="onPageChange"
          />
        </div>
      </div>
    </div>

    <el-dialog :visible.sync="showGenerate" title="生成AI安防日报" width="500px" top="25vh" append-to-body custom-class="dark-dialog" center>
      <div class="detail-content">
        <div class="detail-row">
          <span class="detail-label">日报日期</span>
          <div class="detail-value" style="flex:1">
            <div class="custom-date-picker">
              <div class="date-trigger" @click="toggleDatePicker('generate')">
                <span :class="{ 'is-placeholder': !generateDate }">{{ generateDate || '选择日期' }}</span>
                <i class="el-icon-date"></i>
              </div>
              <div v-if="openDatePicker === 'generate'" class="date-dropdown">
                <div class="date-header">
                  <button class="date-nav-btn" @click="showMonthYearPicker === 'generate' ? prevYear('generate') : prevMonth('generate')">
                    <i class="el-icon-arrow-left"></i>
                  </button>
                  <button class="date-title-btn" @click="toggleMonthYearPicker('generate')">
                    {{ showMonthYearPicker === 'generate' ? generatePickerDate.getFullYear() + '年' : getMonthTitle(generatePickerDate) }}
                    <i :class="showMonthYearPicker === 'generate' ? 'el-icon-arrow-up' : 'el-icon-arrow-down'"></i>
                  </button>
                  <button class="date-nav-btn" @click="showMonthYearPicker === 'generate' ? nextYear('generate') : nextMonth('generate')">
                    <i class="el-icon-arrow-right"></i>
                  </button>
                </div>
                <div v-if="showMonthYearPicker === 'generate'" class="month-year-picker">
                  <div class="month-grid">
                    <span
                      v-for="month in 12"
                      :key="month"
                      class="month-item"
                      :class="{ 'is-current': isCurrentMonth(month, 'generate') }"
                      @click.stop="selectMonth(month, 'generate')"
                    >
                      {{ month }}月
                    </span>
                  </div>
                </div>
                <div v-show="showMonthYearPicker !== 'generate'">
                  <div class="date-today-btn" @click="goToToday('generate')">
                    <i class="el-icon-time"></i>
                    <span>回到今天</span>
                  </div>
                  <div class="date-weekdays">
                    <span v-for="day in weekdays" :key="day" class="weekday">{{ day }}</span>
                  </div>
                  <div class="date-days">
                    <span
                      v-for="(day, index) in getDaysInMonth(generatePickerDate)"
                      :key="index"
                      class="day"
                      :class="{
                        'is-empty': !day.date,
                        'is-today': isToday(day.date),
                        'is-selected': isDateSelected(day.date, 'generate')
                      }"
                      @click="selectDate(day.date, 'generate')"
                    >
                      {{ day.day }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div slot="footer" class="dialog-footer">
        <button class="action-btn action-btn-default" @click="showGenerate = false">取消</button>
        <button class="action-btn action-btn-primary" @click="onGenerate">确认生成</button>
      </div>
    </el-dialog>

    <el-dialog :visible.sync="showApiConfig" title="配置硅基流动API" width="500px" top="25vh" append-to-body custom-class="dark-dialog" center>
      <div class="detail-content">
        <div class="detail-row">
          <span class="detail-label">API密钥</span>
          <div class="detail-value" style="flex:1">
            <input
              v-model.trim="apiKey"
              type="password"
              class="api-key-input"
              :placeholder="apiKeyPlaceholder"
              autocomplete="new-password"
            />
          </div>
        </div>
      </div>
      <div slot="footer" class="dialog-footer">
        <button class="action-btn action-btn-default" @click="cancelApiConfig">取消</button>
        <button class="action-btn action-btn-primary" :disabled="savingApiKey" @click="saveApiConfig">
          {{ savingApiKey ? '保存中...' : '保存' }}
        </button>
      </div>
    </el-dialog>
  </app-layout>
</template>

<script>
import {
  getReportList,
  generateReport,
  regenerateReport,
  deleteReport,
  getReportWorkflowStatus,
  saveReportApiKey
} from '@/api/property'

export default {
  name: 'ReportListPage',
  data () {
    return {
      reportList: [],
      workflowStatus: null,
      loading: false,
      page: 1,
      perPage: 10,
      total: 0,
      openDatePicker: null,
      showMonthYearPicker: null,
      startPickerDate: new Date(),
      endPickerDate: new Date(),
      generatePickerDate: new Date(),
      weekdays: ['日', '一', '二', '三', '四', '五', '六'],
      filter: {
        startDate: '',
        endDate: ''
      },
      showGenerate: false,
      generateDate: '',
      showApiConfig: false,
      savingApiKey: false,
      apiKey: '',
      regeneratingId: null,
      deletingId: null
    }
  },
  computed: {
    workflowStateLabel () {
      if (!this.workflowStatus || !this.workflowStatus.ai_enabled) return '本地规则兜底'
      return this.workflowStatus.ai_configured ? '硅基流动API' : '硅基流动待配置'
    },
    apiKeyPlaceholder () {
      return this.workflowStatus && this.workflowStatus.ai_configured
        ? '已配置，输入新密钥可替换'
        : '请输入 sk- 开头的密钥'
    }
  },
  created () {
    const yesterday = new Date(Date.now() - 24 * 60 * 60 * 1000)
    this.generateDate = this.formatDate(yesterday)
    this.loadWorkflowStatus()
  },
  mounted () {
    document.addEventListener('click', this.handleClickOutside)
    this.loadData()
  },
  beforeDestroy () {
    document.removeEventListener('click', this.handleClickOutside)
  },
  methods: {
    handleClickOutside (event) {
      if (!event.target.closest('.custom-date-picker')) {
        this.openDatePicker = null
      }
    },
    toggleDatePicker (type) {
      this.openDatePicker = this.openDatePicker === type ? null : type
    },
    prevMonth (type) {
      const date = this.getPickerDate(type)
      const newDate = new Date(date.getFullYear(), date.getMonth() - 1, 1)
      this.setPickerDate(type, newDate)
    },
    nextMonth (type) {
      const date = this.getPickerDate(type)
      const newDate = new Date(date.getFullYear(), date.getMonth() + 1, 1)
      this.setPickerDate(type, newDate)
    },
    toggleMonthYearPicker (type) {
      this.showMonthYearPicker = this.showMonthYearPicker === type ? null : type
    },
    prevYear (type) {
      const date = this.getPickerDate(type)
      const newDate = new Date(date.getFullYear() - 1, date.getMonth(), 1)
      this.setPickerDate(type, newDate)
    },
    nextYear (type) {
      const date = this.getPickerDate(type)
      const newDate = new Date(date.getFullYear() + 1, date.getMonth(), 1)
      this.setPickerDate(type, newDate)
    },
    getPickerDate (type) {
      const map = { start: this.startPickerDate, end: this.endPickerDate, generate: this.generatePickerDate }
      return map[type]
    },
    setPickerDate (type, date) {
      if (type === 'start') this.startPickerDate = date
      else if (type === 'end') this.endPickerDate = date
      else this.generatePickerDate = date
    },
    isCurrentMonth (month, type) {
      const date = this.getPickerDate(type)
      return date.getMonth() + 1 === month
    },
    selectMonth (month, type) {
      const date = this.getPickerDate(type)
      const newDate = new Date(date.getFullYear(), month - 1, 1)
      this.setPickerDate(type, newDate)
      this.showMonthYearPicker = null
    },
    goToToday (type) {
      const today = new Date()
      this.setPickerDate(type, new Date(today.getFullYear(), today.getMonth(), 1))
      const dateStr = this.formatDate(today)
      if (type === 'start') this.filter.startDate = dateStr
      else if (type === 'end') this.filter.endDate = dateStr
      else this.generateDate = dateStr
    },
    getMonthTitle (date) {
      return `${date.getFullYear()}年${date.getMonth() + 1}月`
    },
    getDaysInMonth (date) {
      const year = date.getFullYear()
      const month = date.getMonth()
      const firstDay = new Date(year, month, 1)
      const lastDay = new Date(year, month + 1, 0)
      const days = []
      for (let i = 0; i < firstDay.getDay(); i++) {
        days.push({ date: null, day: '' })
      }
      for (let i = 1; i <= lastDay.getDate(); i++) {
        days.push({ date: new Date(year, month, i), day: i })
      }
      return days
    },
    isToday (date) {
      if (!date) return false
      const today = new Date()
      return date.getFullYear() === today.getFullYear() &&
             date.getMonth() === today.getMonth() &&
             date.getDate() === today.getDate()
    },
    isDateSelected (date, type) {
      if (!date) return false
      const selectedDate = type === 'start' ? this.filter.startDate : type === 'end' ? this.filter.endDate : this.generateDate
      if (!selectedDate) return false
      return this.formatDate(date) === selectedDate
    },
    selectDate (date, type) {
      if (!date) return
      const dateStr = this.formatDate(date)
      if (type === 'start') this.filter.startDate = dateStr
      else if (type === 'end') this.filter.endDate = dateStr
      else this.generateDate = dateStr
      this.openDatePicker = null
    },
    async loadWorkflowStatus () {
      try {
        const res = await getReportWorkflowStatus()
        if (res.code === 0) this.workflowStatus = res.data
      } catch (e) {}
    },
    async loadData () {
      this.loading = true
      try {
        const params = { page: this.page, per_page: this.perPage }
        if (this.filter.startDate) params.start_date = this.filter.startDate
        if (this.filter.endDate) params.end_date = this.filter.endDate
        const res = await getReportList(params)
        if (res.code === 0 && res.data) {
          this.reportList = res.data.items || []
          this.total = res.data.total || 0
        }
      } catch (e) {
        console.error(e)
      } finally {
        this.loading = false
      }
    },
    onSearch () {
      this.page = 1
      this.loadData()
    },
    onReset () {
      this.filter = { startDate: '', endDate: '' }
      this.onSearch()
    },
    onPageChange (newPage) {
      this.page = newPage
      this.loadData()
    },
    goDetail (item) {
      this.$router.push(`/report/detail/${item.id}`)
    },
    async onRegenerate (item) {
      if (this.regeneratingId || this.deletingId) return
      this.regeneratingId = item.id
      try {
        const res = await regenerateReport(item.id)
        if (res.code !== 0) throw new Error(res.message)
        this.$message.success('日报已重新生成')
        this.loadData()
      } catch (e) {
        if (!e.__messageShown) this.$message.error(e.message || '重新生成失败')
      } finally {
        this.regeneratingId = null
      }
    },
    onDelete (item) {
      if (this.regeneratingId || this.deletingId) return
      this.$confirm('删除后不可恢复，确定删除这份日报吗？', '确认删除', {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning',
        customClass: 'dark-dialog'
      }).then(() => this.doDelete(item)).catch(() => {})
    },
    async doDelete (item) {
      this.deletingId = item.id
      try {
        const res = await deleteReport(item.id)
        if (res.code !== 0) throw new Error(res.message)
        this.$message.success('日报已删除')
        this.loadData()
      } catch (e) {
        if (!e.__messageShown) this.$message.error(e.message || '删除日报失败')
      } finally {
        this.deletingId = null
      }
    },
    openApiConfig () {
      this.apiKey = this.workflowStatus && this.workflowStatus.ai_configured ? 'sk-••••••••••••••••' : ''
      this.showApiConfig = true
    },
    cancelApiConfig () {
      this.apiKey = ''
      this.showApiConfig = false
    },
    async saveApiConfig () {
      const apiKey = this.apiKey.trim()
      if (!apiKey || apiKey === 'sk-••••••••••••••••') {
        this.$message.warning('请输入新的硅基流动 API 密钥')
        return
      }
      this.savingApiKey = true
      try {
        await saveReportApiKey(apiKey)
        this.apiKey = ''
        this.showApiConfig = false
        await this.loadWorkflowStatus()
        this.$message.success('API 密钥保存成功，现在可以生成 AI 日报')
      } catch (e) {
        if (!e.__messageShown) this.$message.error(e.message || 'API 密钥保存失败')
      } finally {
        this.savingApiKey = false
      }
    },
    async onGenerate () {
      if (!/^\d{4}-\d{2}-\d{2}$/.test(this.generateDate)) {
        return this.$message.warning('请选择正确日期')
      }
      const existing = this.reportList.find(item => item.report_date === this.generateDate)
      if (existing) {
        this.$message.warning('该日期日报已存在，已打开日报详情')
        this.showGenerate = false
        this.goDetail(existing)
        return
      }
      try {
        const res = await generateReport({ report_date: this.generateDate })
        if (res.code !== 0) throw new Error(res.message)
        this.$message.success('AI安防日报生成成功')
        this.showGenerate = false
        this.onSearch()
      } catch (e) {
        if (!e.__messageShown) this.$message.error(e.message || '生成失败')
      }
    },
    riskLabel (level) {
      return { low: '低', medium: '中', high: '高' }[level] || '低'
    },
    sourceLabel (source) {
      if (source === 'siliconflow') return '硅基流动生成'
      if (source === 'ollama') return '历史Ollama生成'
      return source === 'ai_service' ? 'AI生成' : '本地智能分析'
    },
    statusLabel (status) {
      return status === 'generated' ? '已完成' : '生成中'
    },
    formatDate (date) {
      if (!date) return ''
      const d = date instanceof Date ? date : new Date(date)
      const year = d.getFullYear()
      const month = String(d.getMonth() + 1).padStart(2, '0')
      const day = String(d.getDate()).padStart(2, '0')
      return `${year}-${month}-${day}`
    }
  }
}
</script>

<style scoped>
.report-page {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.report-stats {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
  flex-shrink: 0;
}

.stat-item {
  background: var(--dark-card);
  border-radius: 12px;
  border: 1px solid var(--dark-border);
  padding: 20px;
  text-align: center;
}

.stat-value {
  display: block;
  font-size: 20px;
  font-weight: 700;
  color: var(--dark-text);
}

.stat-label {
  font-size: 12px;
  color: var(--dark-text-secondary);
  margin-top: 4px;
}

.stat-ai .stat-value {
  color: var(--dark-accent-light);
}

.filter-section {
  background: var(--dark-card);
  border-radius: 16px;
  border: 1px solid var(--dark-border);
  padding: 20px;
  margin-bottom: 16px;
  flex-shrink: 0;
}

.filter-row {
  margin-bottom: 12px;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.filter-group {
  min-width: 0;
  width: 100%;
  overflow: visible;
}

.filter-time {
  display: grid;
  grid-template-columns: 1fr 1fr auto;
  gap: 12px;
  align-items: end;
}

.filter-time .filter-group {
  flex: none;
  min-width: 0;
}

.filter-actions-group {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  flex-wrap: wrap;
}

.workflow-hint {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--dark-text-secondary);
  margin-right: auto;
}

.workflow-hint i {
  font-size: 14px;
  color: var(--dark-accent-light);
}

.filter-bottom-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 12px;
}

.custom-date-picker {
  position: relative;
  width: 100%;
  overflow: visible;
}

.date-trigger {
  width: 100%;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--dark-border-field);
  border-radius: 8px;
  color: var(--dark-text);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  box-sizing: border-box;
  height: 36px;
}

.date-trigger:hover {
  background: rgba(255, 255, 255, 0.06);
  border-color: var(--dark-accent-light);
}

.date-trigger i {
  font-size: 14px;
  color: var(--dark-text-secondary);
}

.date-trigger span.is-placeholder {
  color: var(--dark-text-secondary);
}

.date-dropdown {
  position: fixed;
  top: auto;
  left: auto;
  right: auto;
  width: 280px;
  background: #0a0a0a;
  border: 1px solid var(--dark-border-field);
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.5);
  z-index: 1000;
  padding: 12px;
}

.date-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.date-nav-btn {
  width: 28px;
  height: 28px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--dark-border-field);
  border-radius: 6px;
  color: var(--dark-text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.date-nav-btn:hover {
  background: rgba(255, 255, 255, 0.08);
  color: var(--dark-text);
}

.date-title-btn {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--dark-border-field);
  border-radius: 6px;
  padding: 4px 10px;
  font-size: 14px;
  font-weight: 500;
  color: var(--dark-text);
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
  transition: all 0.2s;
}

.date-title-btn:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: var(--dark-accent-light);
}

.date-title-btn i {
  font-size: 12px;
  color: var(--dark-text-secondary);
}

.month-year-picker {
  margin-bottom: 8px;
}

.month-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 6px;
}

.month-item {
  text-align: center;
  padding: 8px 0;
  font-size: 13px;
  color: var(--dark-text-secondary);
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid var(--dark-border-light);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s;
}

.month-item:hover {
  background: rgba(99, 102, 241, 0.1);
  border-color: rgba(99, 102, 241, 0.3);
  color: var(--dark-text);
}

.month-item.is-current {
  background: rgba(99, 102, 241, 0.15);
  border-color: var(--dark-accent);
  color: var(--dark-accent-light);
  font-weight: 500;
}

.date-today-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 6px 0;
  margin-bottom: 8px;
  background: rgba(99, 102, 241, 0.08);
  border: 1px solid rgba(99, 102, 241, 0.2);
  border-radius: 6px;
  color: var(--dark-accent-light);
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.date-today-btn:hover {
  background: rgba(99, 102, 241, 0.15);
  border-color: var(--dark-accent-light);
}

.date-today-btn i {
  font-size: 13px;
}

.date-weekdays {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 2px;
  margin-bottom: 4px;
}

.weekday {
  text-align: center;
  font-size: 12px;
  color: var(--dark-text-secondary);
  aspect-ratio: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.date-days {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 2px;
}

.day {
  aspect-ratio: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  color: var(--dark-text-secondary);
  cursor: pointer;
  border-radius: 4px;
  transition: all 0.15s;
}

.day:hover:not(.is-empty) {
  background: rgba(99, 102, 241, 0.1);
  color: var(--dark-text);
}

.day.is-empty {
  cursor: default;
}

.day.is-today {
  color: var(--dark-accent-light);
  font-weight: 500;
}

.day.is-selected {
  background: var(--dark-accent);
  color: #fff;
  font-weight: 500;
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid;
  box-sizing: border-box;
  height: 36px;
}

.action-btn i {
  font-size: 14px;
}

.action-btn-primary {
  background: var(--dark-accent);
  border-color: var(--dark-accent);
  color: #fff;
}

.action-btn-primary:hover {
  background: var(--dark-accent-light);
  border-color: var(--dark-accent-light);
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.3);
}

.action-btn-default {
  background: rgba(255, 255, 255, 0.04);
  border-color: var(--dark-border-field);
  color: var(--dark-text);
}

.action-btn-default:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: var(--dark-text-secondary);
}

.action-btn-accent {
  background: rgba(99, 102, 241, 0.1);
  border-color: rgba(99, 102, 241, 0.3);
  color: var(--dark-accent-light);
}

.action-btn-accent:hover {
  background: rgba(99, 102, 241, 0.2);
  border-color: var(--dark-accent-light);
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.2);
}

.report-list-section {
  position: relative;
  background: var(--dark-card);
  border-radius: 16px;
  border: 1px solid var(--dark-border);
  padding: 20px;
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.probe-loading {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: var(--dark-text-secondary);
  font-size: 14px;
}

.probe-loading i {
  font-size: 18px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.report-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.pagination-wrapper {
  padding-top: 16px;
  display: flex;
  justify-content: center;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
  min-height: 200px;
}

.cell-title-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

::v-deep .van-cell__title {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

.cell-name {
  flex: 1;
  min-width: 0;
  font-size: 15px;
  color: var(--dark-text);
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.risk-tag {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0 6px;
  height: 22px;
  border-radius: 4px;
  font-size: 12px;
  border: 1px solid;
}

.risk-low {
  color: #38c78f;
  border-color: rgba(56, 199, 143, 0.3);
  background: rgba(56, 199, 143, 0.08);
}

.risk-medium {
  color: #e8a84e;
  border-color: rgba(232, 168, 78, 0.3);
  background: rgba(232, 168, 78, 0.08);
}

.risk-high {
  color: #ef5b5b;
  border-color: rgba(239, 91, 91, 0.3);
  background: rgba(239, 91, 91, 0.08);
}

.cell-label-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 6px;
}

.cell-meta {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--dark-text-secondary);
}

.cell-meta i {
  font-size: 14px;
}

::v-deep .van-cell__right-icon {
  display: flex;
  align-items: center;
}

.cell-actions {
  display: inline-flex;
  align-items: center;
  gap: 10px;
}

.cell-action-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--dark-border-field);
  border-radius: 6px;
  color: var(--dark-text-secondary);
  cursor: pointer;
  transition: all 0.2s;
  font-size: 12px;
  white-space: nowrap;
}

.cell-action-btn i {
  font-size: 13px;
}

.cell-action-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.08);
  color: var(--dark-text);
  border-color: var(--dark-text-secondary);
}

.cell-action-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.cell-action-danger:hover:not(:disabled) {
  background: rgba(239, 68, 68, 0.1);
  border-color: rgba(239, 68, 68, 0.3);
  color: #f87171;
}

.detail-content {
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

.api-key-input {
  width: 100%;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--dark-border-field);
  border-radius: 8px;
  color: var(--dark-text);
  font-size: 13px;
  box-sizing: border-box;
  height: 36px;
  outline: none;
  transition: all 0.2s;
}

.api-key-input:focus {
  border-color: var(--dark-accent-light);
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.15);
}

.api-key-input::placeholder {
  color: var(--dark-text-secondary);
}

@media (max-width: 1024px) {
  .report-page {
    height: auto;
    min-height: calc(100vh - 120px);
  }

  .report-stats {
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  }

  .stat-item {
    padding: 16px;
  }

  .stat-value {
    font-size: 18px;
  }

  .filter-section {
    padding: 16px;
  }

  .filter-row {
    gap: 10px;
  }

  .filter-time {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
  }

  .filter-time .filter-group {
    flex: 1 1 calc(50% - 5px);
    min-width: 0;
  }

  .filter-actions-group {
    flex: 1 1 100%;
    gap: 8px;
  }

  .filter-bottom-row {
    flex-wrap: wrap;
    gap: 10px;
  }

  .filter-bottom-row .filter-actions-group {
    flex: 0 0 auto;
  }

  .action-btn {
    flex: 1;
    padding: 8px 14px;
    font-size: 12px;
  }

  .report-list-section {
    padding: 16px;
  }
}

@media (max-width: 600px) {
  .filter-row {
    grid-template-columns: 1fr;
  }

  .filter-time .filter-group {
    flex: 1 1 100%;
  }

  .action-btn {
    min-width: 80px;
  }
}
</style>

<style>
.el-pagination.is-background .btn-prev,
.el-pagination.is-background .btn-next,
.el-pagination.is-background .el-pager li {
  background: rgba(255, 255, 255, 0.04) !important;
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
  color: var(--dark-text-secondary) !important;
}

.el-pagination.is-background .btn-prev:hover,
.el-pagination.is-background .btn-next:hover,
.el-pagination.is-background .el-pager li:hover {
  background: rgba(255, 255, 255, 0.08) !important;
  color: var(--dark-text) !important;
}

.el-pagination.is-background .el-pager li.active {
  background: var(--dark-accent) !important;
  border-color: var(--dark-accent) !important;
  color: #fff !important;
}

.el-pagination.is-background .btn-prev:disabled,
.el-pagination.is-background .btn-next:disabled {
  background: rgba(255, 255, 255, 0.02) !important;
  color: var(--dark-text-dim) !important;
}

.dark-dialog {
  background: #0A0A0A !important;
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 16px;
}

.dark-dialog .el-dialog__header {
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  padding: 16px 20px;
}

.dark-dialog .el-dialog__title {
  color: #EDEDEF;
  font-weight: 600;
}

.dark-dialog .el-dialog__headerbtn .el-dialog__close {
  color: #8A8F98;
}

.dark-dialog .el-dialog__body {
  padding: 20px;
}

.dark-dialog .el-dialog__footer {
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  padding: 12px 20px;
}

.dark-dialog .detail-content {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.dark-dialog .detail-row {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.dark-dialog .detail-label {
  font-size: 13px;
  color: var(--dark-text-secondary);
  min-width: 70px;
  flex-shrink: 0;
  line-height: 36px;
}

.dark-dialog .detail-value {
  font-size: 13px;
  color: var(--dark-text);
  word-break: break-all;
  flex: 1;
}

.dark-dialog .api-key-input {
  width: 100%;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--dark-border-field);
  border-radius: 8px;
  color: var(--dark-text);
  font-size: 13px;
  box-sizing: border-box;
  height: 36px;
  outline: none;
  transition: all 0.2s;
}

.dark-dialog .api-key-input:focus {
  border-color: var(--dark-accent-light);
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.15);
}

.dark-dialog .api-key-input::placeholder {
  color: var(--dark-text-secondary);
}

.dark-dialog .dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.dark-dialog .dialog-footer .action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid;
  box-sizing: border-box;
  height: 36px;
}

.dark-dialog .dialog-footer .action-btn-primary {
  background: var(--dark-accent);
  border-color: var(--dark-accent);
  color: #fff;
}

.dark-dialog .dialog-footer .action-btn-primary:hover {
  background: var(--dark-accent-light);
  border-color: var(--dark-accent-light);
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.3);
}

.dark-dialog .dialog-footer .action-btn-default {
  background: rgba(255, 255, 255, 0.04);
  border-color: var(--dark-border-field);
  color: var(--dark-text);
}

.dark-dialog .dialog-footer .action-btn-default:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: var(--dark-text-secondary);
}

.dark-dialog .dialog-footer .action-btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
