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
          <div v-if="isAdmin" class="filter-actions-group">
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
              <span v-if="isAdmin" class="cell-actions" @click.stop>
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
    <div class="dark-card">
      <van-list v-model="loading" :finished="finished" finished-text="没有更多了" @load="loadData">
        <van-cell v-for="item in reportList" :key="item.id" is-link @click="goDetail(item)">
          <template #title>{{ item.report_date }}</template>
          <template #label>
            <div>状态: {{ item.generate_status }}</div>
          </template>
        </van-cell>
      </van-list>
    </div>
    <van-dialog v-model="showGenerate" title="生成日报" show-cancel-button @confirm="onGenerate">
      <van-field v-model="generateDate" label="日期" placeholder="YYYY-MM-DD" />
    </van-dialog>
  </app-layout>
</template>

<script>
import { getReportList, generateReport } from '@/api/property'

export default {
  name: 'ReportListPage',
  data () {
    return {
      reportList: [],
      loading: false,
      finished: false,
      page: 1,
      startDate: '',
      endDate: '',
      showGenerate: false,
      generateDate: ''
    }
  },
  computed: {
    isAdmin () {
      return this.$store.getters['user/isAdmin']
    },
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
    if (this.isAdmin) this.loadWorkflowStatus()
  },
  mounted () {
    document.addEventListener('click', this.handleClickOutside)
    this.loadData()
  },
  beforeDestroy () {
    document.removeEventListener('click', this.handleClickOutside)
  },
  methods: {
    async loadData () {
      try {
        const params = { page: this.page, per_page: 20 }
        if (this.startDate) params.start_date = this.startDate
        if (this.endDate) params.end_date = this.endDate
        const res = await getReportList(params)
        if (res.code === 0 && res.data) {
          const items = res.data.items || []
          if (this.page === 1) this.reportList = items
          else this.reportList.push(...items)
          this.finished = this.reportList.length >= res.data.total
          this.page++
        }
      } catch (e) { this.finished = true }
      this.loading = false
    },
    goDetail (item) { this.$router.push(`/report/detail/${item.id}`) },
    async onGenerate () {
      if (!this.generateDate) return this.$message.warning('请输入日期')
      try {
        await generateReport({ report_date: this.generateDate })
        this.$message.success('日报生成成功')
        this.page = 1; this.finished = false; this.loadData()
      } catch (e) { this.$message.error('生成失败') }
    }
  }
}
</script>

<style scoped>
.dark-card {
  background: var(--dark-card);
  border-radius: 16px;
  border: 1px solid var(--dark-border);
  padding: 20px;
  margin-bottom: 16px;
}
</style>
