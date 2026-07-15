<template>
  <app-layout page-title="历史通行日志" :no-scroll="true">
    <div class="pass-log-page">
      <div class="log-stats">
        <div class="stat-item">
          <span class="stat-value">{{ stats.total === null ? '--' : stats.total }}</span>
          <span class="stat-label">总通行</span>
        </div>
        <div class="stat-item stat-today">
          <span class="stat-value">{{ stats.today === null ? '--' : stats.today }}</span>
          <span class="stat-label">今日通行</span>
        </div>
      </div>

      <div class="filter-section">
        <div class="filter-row filter-time">
          <div class="filter-group">
            <div class="custom-select">
              <div class="select-trigger" @click="toggleSelect('gate')">
                <span :class="{ 'is-placeholder': filter.gateId === 0 }">{{ getSelectText('gate', filter.gateId) }}</span>
                <i class="el-icon-arrow-down" :class="{ 'is-open': openSelect === 'gate' }"></i>
              </div>
              <div v-if="openSelect === 'gate'" class="select-dropdown">
                <div
                  v-for="opt in gateOptions"
                  :key="opt.value"
                  class="select-option"
                  :class="{ 'is-selected': filter.gateId === opt.value }"
                  @click="selectOption('gate', opt.value)"
                >
                  {{ opt.text }}
                </div>
              </div>
            </div>
          </div>
          <div class="filter-group">
            <div class="custom-date-picker">
              <div class="date-trigger" @click="toggleDatePicker('start')">
                <span :class="{ 'is-placeholder': !filter.startTime }">{{ filter.startTime || '开始时间' }}</span>
                <i class="el-icon-date"></i>
              </div>
              <div v-if="openDatePicker === 'start'" class="date-dropdown">
                <div class="date-header">
                  <button class="date-nav-btn" @click="showMonthYearPicker === 'start' ? prevYear('start') : prevMonth('start')">
                    <i class="el-icon-arrow-left"></i>
                  </button>
                  <button
                    class="date-title-btn"
                    @click="toggleMonthYearPicker('start')"
                  >
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
                <span :class="{ 'is-placeholder': !filter.endTime }">{{ filter.endTime || '结束时间' }}</span>
                <i class="el-icon-date"></i>
              </div>
              <div v-if="openDatePicker === 'end'" class="date-dropdown">
                <div class="date-header">
                  <button class="date-nav-btn" @click="showMonthYearPicker === 'end' ? prevYear('end') : prevMonth('end')">
                    <i class="el-icon-arrow-left"></i>
                  </button>
                  <button
                    class="date-title-btn"
                    @click="toggleMonthYearPicker('end')"
                  >
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
      </div>

      <div class="log-list-section" ref="listSection">
        <div v-if="!perPageReady" class="probe-loading"><i class="el-icon-loading"></i><span>加载中...</span></div>
        <div class="log-list" ref="listContent" :style="{ visibility: perPageReady ? '' : 'hidden' }">
          <van-cell v-for="item in logList" :key="item.id" is-link @click="showLogDetail(item)">
            <template #title>
              <div class="cell-title-row">

                <span class="cell-name">{{ item.person_name || '未知' }}</span>
                <span class="type-tag" :class="getLevelClass(item.gate_level)">{{ getLevelText(item.gate_level) }}</span>
              </div>
              <div class="cell-label-row">
                <span class="cell-meta">
                  <i class="el-icon-place"></i>
                  <span>{{ item.gate_name }}</span>
                </span>
                <span class="cell-meta">
                  <i class="el-icon-time"></i>
                  <span>{{ formatTime(item.pass_time) }}</span>
                </span>
              </div>
            </template>
            <template #right-icon>
              <span class="cell-status">
                <span class="status-dot" :class="item.pass_result === 'pass' ? 'dot-pass' : 'dot-deny'"></span>
                <span class="status-label">{{ item.pass_result === 'pass' ? '放行' : '拒绝' }}</span>
              </span>
            </template>
          </van-cell>
          <div v-if="logList.length === 0 && !loading" class="empty-state">
            <i class="el-icon-document" style="font-size:48px;color:var(--dark-text-muted)"></i>
            <p style="color:var(--dark-text-muted);margin-top:12px">暂无通行记录</p>
          </div>
        </div>
        <div class="pagination-wrapper" v-show="perPageReady">
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

    <el-dialog :visible.sync="showDetail" title="通行详情" width="500px" append-to-body custom-class="dark-dialog">
      <div v-if="currentLog" class="detail-content">
        <div class="detail-row">
          <span class="detail-label">人员姓名</span>
          <span class="detail-value">{{ currentLog.person_name || '未知' }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">门禁终端</span>
          <span class="detail-value">{{ currentLog.gate_name }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">终端层级</span>
          <span class="detail-value">{{ getLevelText(currentLog.gate_level) }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">通行结果</span>
          <span class="detail-value">{{ currentLog.pass_result === 'pass' ? '放行' : '拒绝' }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">通行时间</span>
          <span class="detail-value">{{ formatTime(currentLog.pass_time) }}</span>
        </div>
        <div v-if="currentLog.capture_image_path" class="detail-image">
          <h4>抓拍图片</h4>
          <img :src="getImageUrl(currentLog.capture_image_path)" alt="抓拍图片" />
        </div>
      </div>
    </el-dialog>
  </app-layout>
</template>

<script>
import { getPassLogs, getGateList } from '@/api/property'

export default {
  name: 'PassLogListPage',
  data () {
    return {
      logList: [],
      loading: false,
      page: 1,
      perPage: 10,
      total: 0,
      openSelect: null,
      openDatePicker: null,
      showMonthYearPicker: null,
      startPickerDate: new Date(),
      endPickerDate: new Date(),
      weekdays: ['日', '一', '二', '三', '四', '五', '六'],
      showDetail: false,
      currentLog: null,
      stats: {
        total: null,
        today: null
      },
      filter: {
        gateId: 0,
        startTime: '',
        endTime: ''
      },
      gateOptions: [
        { text: '全部终端', value: 0 }
      ],
      perPageReady: false
    }
  },
  mounted () {
    this.loadGateOptions()
    document.addEventListener('click', this.handleClickOutside)
    window.addEventListener('resize', this.handleResize)
    if (window.ResizeObserver && this.$refs.listContent) {
      this._resizeObserver = new ResizeObserver(this.handleResize)
      this._resizeObserver.observe(this.$refs.listContent)
    }
    this.initData()
  },
  beforeDestroy () {
    document.removeEventListener('click', this.handleClickOutside)
    window.removeEventListener('resize', this.handleResize)
    if (this._resizeObserver) {
      this._resizeObserver.disconnect()
      this._resizeObserver = null
    }
  },
  methods: {
    handleClickOutside (event) {
      if (!event.target.closest('.custom-select') && !event.target.closest('.custom-date-picker')) {
        this.openSelect = null
        this.openDatePicker = null
      }
    },
    initData () {
      this.perPageReady = false

      this.perPage = 2
      this.loadData()
      this.loadStats()
    },
    calcPerPage () {
      const content = this.$refs.listContent
      if (!content || content.clientHeight <= 0) return false
      const cells = content.querySelectorAll('.van-cell')
      if (!cells.length) return false
      let totalH = 0
      for (let i = 0; i < cells.length; i++) totalH += cells[i].offsetHeight
      const avgCellH = totalH / cells.length
      const newPerPage = Math.max(5, Math.round(content.clientHeight / avgCellH))
      if (newPerPage > this.perPage) {
        this.perPage = newPerPage
        return true
      }
      return false
    },
    handleResize () {
      clearTimeout(this._resizeTimer)
      this._resizeTimer = setTimeout(() => {
        requestAnimationFrame(() => {
          this.calcPerPage()
          this.loadData()
          this.loadStats()
        })
      }, 200)
    },
    toggleDatePicker (type) {
      this.openDatePicker = this.openDatePicker === type ? null : type
    },
    prevMonth (type) {
      const date = type === 'start' ? this.startPickerDate : this.endPickerDate
      const newDate = new Date(date.getFullYear(), date.getMonth() - 1, 1)
      if (type === 'start') {
        this.startPickerDate = newDate
      } else {
        this.endPickerDate = newDate
      }
    },
    nextMonth (type) {
      const date = type === 'start' ? this.startPickerDate : this.endPickerDate
      const newDate = new Date(date.getFullYear(), date.getMonth() + 1, 1)
      if (type === 'start') {
        this.startPickerDate = newDate
      } else {
        this.endPickerDate = newDate
      }
    },
    toggleMonthYearPicker (type) {
      this.showMonthYearPicker = this.showMonthYearPicker === type ? null : type
    },
    prevYear (type) {
      const date = type === 'start' ? this.startPickerDate : this.endPickerDate
      const newDate = new Date(date.getFullYear() - 1, date.getMonth(), 1)
      if (type === 'start') {
        this.startPickerDate = newDate
      } else {
        this.endPickerDate = newDate
      }
    },
    nextYear (type) {
      const date = type === 'start' ? this.startPickerDate : this.endPickerDate
      const newDate = new Date(date.getFullYear() + 1, date.getMonth(), 1)
      if (type === 'start') {
        this.startPickerDate = newDate
      } else {
        this.endPickerDate = newDate
      }
    },
    isCurrentMonth (month, type) {
      const date = type === 'start' ? this.startPickerDate : this.endPickerDate
      return date.getMonth() + 1 === month
    },
    selectMonth (month, type) {
      const date = type === 'start' ? this.startPickerDate : this.endPickerDate
      const newDate = new Date(date.getFullYear(), month - 1, 1)
      if (type === 'start') {
        this.startPickerDate = newDate
      } else {
        this.endPickerDate = newDate
      }
      this.showMonthYearPicker = null
    },
    goToToday (type) {
      const today = new Date()
      if (type === 'start') {
        this.startPickerDate = new Date(today.getFullYear(), today.getMonth(), 1)
      } else {
        this.endPickerDate = new Date(today.getFullYear(), today.getMonth(), 1)
      }
      const year = today.getFullYear()
      const month = String(today.getMonth() + 1).padStart(2, '0')
      const day = String(today.getDate()).padStart(2, '0')
      const dateStr = `${year}-${month}-${day}`
      if (type === 'start') {
        this.filter.startTime = dateStr
      } else {
        this.filter.endTime = dateStr
      }
    },
    getMonthTitle (date) {
      const year = date.getFullYear()
      const month = date.getMonth() + 1
      return `${year}年${month}月`
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
        days.push({
          date: new Date(year, month, i),
          day: i
        })
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
      const selectedDate = type === 'start' ? this.filter.startTime : this.filter.endTime
      if (!selectedDate) return false
      const year = date.getFullYear()
      const month = String(date.getMonth() + 1).padStart(2, '0')
      const day = String(date.getDate()).padStart(2, '0')
      return `${year}-${month}-${day}` === selectedDate
    },
    selectDate (date, type) {
      if (!date) return
      const year = date.getFullYear()
      const month = String(date.getMonth() + 1).padStart(2, '0')
      const day = String(date.getDate()).padStart(2, '0')
      const dateStr = `${year}-${month}-${day}`
      if (type === 'start') {
        this.filter.startTime = dateStr
      } else {
        this.filter.endTime = dateStr
      }
      this.openDatePicker = null
    },
    toggleSelect (type) {
      this.openSelect = this.openSelect === type ? null : type
    },
    selectOption (type, value) {
      this.filter[type] = value
      this.openSelect = null
    },
    getSelectText (type, value) {
      const placeholderMap = {
        gate: '选择终端'
      }
      const optionsMap = {
        gate: this.gateOptions
      }
      const options = optionsMap[type]
      const option = options.find(opt => opt.value === value)
      return option && value !== 0 ? option.text : placeholderMap[type]
    },
    async loadGateOptions () {
      try {
        const res = await getGateList({ page: 1, per_page: 1000 })
        if (res.code === 0 && res.data) {
          const items = res.data.items || []
          this.gateOptions = [
            { text: '全部终端', value: 0 },
            ...items.map(g => ({ text: g.gate_name, value: g.id }))
          ]
        }
      } catch (e) {
        console.error(e)
      }
    },
    async loadData () {
      this.loading = true
      try {
        const params = {
          page: this.page,
          per_page: this.perPage
        }
        if (this.filter.gateId) {
          params.gate_id = this.filter.gateId
        }
        if (this.filter.startTime) {
          params.start_time = this.filter.startTime
        }
        if (this.filter.endTime) {
          params.end_time = this.filter.endTime
        }
        const res = await getPassLogs(params)
        if (res.code === 0 && res.data) {
          this.logList = res.data.items || []
          this.total = res.data.total || 0
        }
      } catch (e) {
        console.error(e)
      }
      if (!this.perPageReady) {
        this.$nextTick(() => {
          setTimeout(() => {
            if (this.calcPerPage()) {
              this.loadData()
              this.loadStats()
            } else {
              this.perPageReady = true
              this.loading = false
            }
          }, 150)
        })
      } else {
        this.loading = false
      }
    },
    async loadStats () {
      try {
        const res = await getPassLogs({ page: 1, per_page: 1000 })
        if (res.code === 0 && res.data) {
          const items = res.data.items || []
          this.stats.total = res.data.total

          const today = new Date()
          const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`
          this.stats.today = items.filter(a => {
            if (!a.pass_time) return false
            return a.pass_time.startsWith(todayStr)
          }).length
        }
      } catch (e) {
        console.error(e)
      }
    },
    onPageChange (newPage) {
      this.page = newPage
      this.loadData()
    },
    onSearch () {
      this.page = 1
      this.loadData()
    },
    onReset () {
      this.filter = {
        gateId: 0,
        startTime: '',
        endTime: ''
      }
      this.onSearch()
    },
    showLogDetail (item) {
      this.currentLog = item
      this.showDetail = true
    },
    getLevelText (level) {
      const map = {
        community_gate: '社区大门',
        unit_door: '单元门',
        entrance_door: '入户门',
        dangerous_area: '危险防护区域'
      }
      return map[level] || level
    },
    getLevelClass (level) {
      const map = {
        community_gate: 'level-community',
        unit_door: 'level-unit',
        entrance_door: 'level-entrance',
        dangerous_area: 'level-danger'
      }
      return map[level] || ''
    },
    formatTime (time) {
      if (!time) return ''
      return time.replace('T', ' ').substring(0, 19)
    },
    getImageUrl (path) {
      if (!path) return ''
      if (path.startsWith('http')) return path
      if (path.startsWith('alarm_captures/')) {
        return `${process.env.API_BASE_URL || '/api/v1'}/alarm/capture/${path.replace('alarm_captures/', '')}`
      }
      return `${process.env.API_BASE_URL || '/api/v1'}/alarm/capture/${path}`
    }
  }
}
</script>

<style scoped>
.pass-log-page {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.log-stats {
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
  font-size: 28px;
  font-weight: 700;
  color: var(--dark-text);
}

.stat-label {
  font-size: 12px;
  color: var(--dark-text-secondary);
  margin-top: 4px;
}

.stat-today .stat-value {
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

.custom-select {
  position: relative;
  width: 100%;
  overflow: visible;
}

.select-trigger {
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

.select-trigger:hover {
  background: rgba(255, 255, 255, 0.06);
  border-color: var(--dark-accent-light);
}

.select-trigger i {
  font-size: 12px;
  color: var(--dark-text-secondary);
  transition: transform 0.2s;
}

.select-trigger i.is-open {
  transform: rotate(180deg);
}

.select-trigger span.is-placeholder {
  color: var(--dark-text-secondary);
}

.select-dropdown {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  right: 0;
  background: #0a0a0a;
  border: 1px solid var(--dark-border-field);
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.5);
  z-index: 100;
  overflow: hidden;
  max-height: 200px;
  overflow-y: auto;
}

.select-option {
  padding: 10px 12px;
  color: var(--dark-text-secondary);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s;
}

.select-option:hover {
  background: rgba(99, 102, 241, 0.1);
  color: var(--dark-text);
}

.select-option.is-selected {
  background: rgba(99, 102, 241, 0.15);
  color: var(--dark-accent-light);
  font-weight: 500;
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

.filter-time {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr auto;
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

.log-list-section {
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

.log-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.probe-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 40px 0;
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

.level-community {
  color: var(--dark-accent-light);
  border-color: rgba(99, 102, 241, 0.3);
  background: rgba(99, 102, 241, 0.08);
}

.level-unit {
  color: #fbbf24;
  border-color: rgba(245, 158, 11, 0.3);
  background: rgba(245, 158, 11, 0.08);
}

.level-entrance {
  color: #34d399;
  border-color: rgba(52, 211, 153, 0.3);
  background: rgba(52, 211, 153, 0.08);
}

.level-danger {
  color: #f87171;
  border-color: rgba(239, 68, 68, 0.3);
  background: rgba(239, 68, 68, 0.08);
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

::v-deep .van-cell__value {
  display: flex;
  align-items: center;
}

::v-deep .van-cell__right-icon {
  display: flex;
  align-items: center;
}

.cell-status {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  height: 28px;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}

.dot-pass {
  background: var(--dark-success);
  box-shadow: 0 0 6px rgba(16, 185, 129, 0.4);
}

.dot-deny {
  background: #f59e0b;
  box-shadow: 0 0 6px rgba(245, 158, 11, 0.4);
}

.status-label {
  font-size: 13px;
  color: var(--dark-text-secondary);
}

.type-tag {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0 6px;
  height: 22px;
  border-radius: 4px;
  font-size: 12px;
  margin-right: 8px;
  border: 1px solid;
}

.cell-name {
  flex: 1;
  min-width: 0;
  font-size: 15px;
  color: var(--dark-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
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

.detail-content {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.detail-row {
  display: flex;
  align-items: center;
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

.detail-image {
  margin-top: 16px;
}

.detail-image h4 {
  margin: 0 0 12px;
  font-size: 15px;
  font-weight: 600;
}

.detail-image img {
  width: 100%;
  border-radius: 8px;
}

@media (max-width: 1024px) {
  .pass-log-page {
    height: auto;
    min-height: calc(100vh - 120px);
  }

  .log-stats {
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  }

  .stat-item {
    padding: 16px;
  }

  .stat-value {
    font-size: 24px;
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

  .filter-spacer {
    display: none;
  }

  .filter-actions-group {
    flex: 1 1 100%;
    gap: 8px;
  }

  .action-btn {
    flex: 1;
    padding: 8px 14px;
    font-size: 12px;
  }

  .log-list-section {
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
</style>
