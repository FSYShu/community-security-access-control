<template>
  <app-layout page-title="告警中心" :no-scroll="true">
    <div class="alarm-center">
      <div class="alarm-stats">
        <div class="stat-item">
          <span class="stat-value">{{ stats.total }}</span>
          <span class="stat-label">总告警</span>
        </div>
        <div class="stat-item stat-pending">
          <span class="stat-value">{{ stats.pending }}</span>
          <span class="stat-label">待处理</span>
        </div>
        <div class="stat-item stat-handled">
          <span class="stat-value">{{ stats.handled }}</span>
          <span class="stat-label">已处理</span>
        </div>
        <div class="stat-item stat-today">
          <span class="stat-value">{{ stats.today }}</span>
          <span class="stat-label">今日告警</span>
        </div>
      </div>

      <div class="filter-section">
        <div class="filter-row">
          <div class="filter-group">
            <div class="custom-select">
              <div class="select-trigger" @click="toggleSelect('alarmType')">
                <span :class="{ 'is-placeholder': filter.alarmType === 0 }">{{ getSelectText('alarmType', filter.alarmType) }}</span>
                <i class="el-icon-arrow-down" :class="{ 'is-open': openSelect === 'alarmType' }"></i>
              </div>
              <div v-if="openSelect === 'alarmType'" class="select-dropdown">
                <div
                  v-for="opt in typeOptions"
                  :key="opt.value"
                  class="select-option"
                  :class="{ 'is-selected': filter.alarmType === opt.value }"
                  @click="selectOption('alarmType', opt.value)"
                >
                  {{ opt.text }}
                </div>
              </div>
            </div>
          </div>
          <div class="filter-group">
            <div class="custom-select">
              <div class="select-trigger" @click="toggleSelect('alarmLevel')">
                <span :class="{ 'is-placeholder': filter.alarmLevel === 0 }">{{ getSelectText('alarmLevel', filter.alarmLevel) }}</span>
                <i class="el-icon-arrow-down" :class="{ 'is-open': openSelect === 'alarmLevel' }"></i>
              </div>
              <div v-if="openSelect === 'alarmLevel'" class="select-dropdown">
                <div
                  v-for="opt in levelOptions"
                  :key="opt.value"
                  class="select-option"
                  :class="{ 'is-selected': filter.alarmLevel === opt.value }"
                  @click="selectOption('alarmLevel', opt.value)"
                >
                  {{ opt.text }}
                </div>
              </div>
            </div>
          </div>
          <div class="filter-group">
            <div class="custom-select">
              <div class="select-trigger" @click="toggleSelect('handleStatus')">
                <span :class="{ 'is-placeholder': filter.handleStatus === 0 }">{{ getSelectText('handleStatus', filter.handleStatus) }}</span>
                <i class="el-icon-arrow-down" :class="{ 'is-open': openSelect === 'handleStatus' }"></i>
              </div>
              <div v-if="openSelect === 'handleStatus'" class="select-dropdown">
                <div
                  v-for="opt in statusOptions"
                  :key="opt.value"
                  class="select-option"
                  :class="{ 'is-selected': filter.handleStatus === opt.value }"
                  @click="selectOption('handleStatus', opt.value)"
                >
                  {{ opt.text }}
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="filter-row filter-time">
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
          <div class="filter-group filter-spacer"></div>
          <div class="filter-group filter-actions-group">
            <button class="action-btn action-btn-primary" @click="onSearch">
              <i class="el-icon-search"></i>
              <span>查询</span>
            </button>
            <button class="action-btn action-btn-default" @click="onReset">
              <i class="el-icon-refresh"></i>
              <span>重置</span>
            </button>
            <button class="action-btn action-btn-info" @click="onExport">
              <i class="el-icon-download"></i>
              <span>导出</span>
            </button>
            <button class="action-btn action-btn-danger" @click="onClearConfirm">
              <i class="el-icon-delete"></i>
              <span>清空</span>
            </button>
          </div>
        </div>
      </div>

      <div class="alarm-list-section">
        <div class="alarm-list">
          <van-cell v-for="alarm in alarmList" :key="alarm.id" is-link @click="showAlarmDetail(alarm)">
            <template #title>
              <div class="cell-title-row">
                <span class="type-tag" :class="getTypeClass(alarm.alarm_type)">{{ getTypeText(alarm.alarm_type) }}</span>
                <span class="cell-name">{{ alarm.alarm_description }}</span>
                <span class="type-tag" :class="getLevelClass(alarm.alarm_level)">{{ getLevelText(alarm.alarm_level) }}</span>
              </div>

              <div class="cell-label-row">
                <span class="cell-meta">
                  <i class="el-icon-time"></i>
                  <span>{{ formatTime(alarm.alarm_time) }}</span>
                </span>
              </div>
            </template>
            <template #right-icon>
              <span class="cell-status">
                <span class="status-dot" :class="alarm.handle_status === 'pending' ? 'dot-pending' : 'dot-handled'"></span>
                <span class="status-label">{{ getStatusText(alarm.handle_status) }}</span>
              </span>
              <button
                v-if="alarm.handle_status === 'pending'"
                class="handle-btn"
                @click.stop="showHandleDialog(alarm)"
              >
                <i class="el-icon-check"></i>
                <span>处置</span>
              </button>
            </template>
          </van-cell>
          <div v-if="alarmList.length === 0 && !loading" class="empty-state">
            <i class="el-icon-bell" style="font-size:48px;color:var(--dark-text-muted)"></i>
            <p style="color:var(--dark-text-muted);margin-top:12px">暂无告警记录</p>
          </div>
        </div>
        <div class="pagination-wrapper">
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

    <el-dialog :visible.sync="showDetail" title="告警详情" width="500px" append-to-body custom-class="dark-dialog">
      <div v-if="currentAlarm" class="detail-content">
        <div class="detail-row">
          <span class="detail-label">告警ID</span>
          <span class="detail-value">{{ currentAlarm.id }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">告警类型</span>
          <span class="detail-value">{{ getTypeText(currentAlarm.alarm_type) }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">告警级别</span>
          <span class="detail-value">{{ getLevelText(currentAlarm.alarm_level) }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">告警描述</span>
          <span class="detail-value">{{ currentAlarm.alarm_description }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">告警时间</span>
          <span class="detail-value">{{ formatTime(currentAlarm.alarm_time) }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">处置状态</span>
          <span class="detail-value">{{ getStatusText(currentAlarm.handle_status) }}</span>
        </div>
        <div v-if="currentAlarm.handler_name" class="detail-row">
          <span class="detail-label">处置人</span>
          <span class="detail-value">{{ currentAlarm.handler_name }}</span>
        </div>
        <div v-if="currentAlarm.handle_time" class="detail-row">
          <span class="detail-label">处置时间</span>
          <span class="detail-value">{{ formatTime(currentAlarm.handle_time) }}</span>
        </div>
        <div v-if="currentAlarm.handle_remark" class="detail-row">
          <span class="detail-label">处置备注</span>
          <span class="detail-value">{{ currentAlarm.handle_remark }}</span>
        </div>
        <div v-if="currentAlarm.capture_image_path" class="detail-image">
          <h4>抓拍图片</h4>
          <img :src="getImageUrl(currentAlarm.capture_image_path)" alt="抓拍图片" />
        </div>
        <div v-if="currentAlarm.video_path" class="detail-video">
          <h4>关联视频</h4>
          <video :src="getVideoUrl(currentAlarm.video_path)" controls style="width: 100%"></video>
        </div>
      </div>
      <div v-if="currentAlarm && currentAlarm.handle_status === 'pending'" slot="footer">
        <el-button size="small" @click="showDetail = false">关闭</el-button>
        <el-button size="small" type="primary" @click="showHandleDialog(currentAlarm)">处置</el-button>
      </div>
    </el-dialog>

    <el-dialog :visible.sync="showHandle" title="处置告警" width="400px" :close-on-click-modal="false" append-to-body custom-class="dark-dialog">
      <div class="handle-form">
        <div class="form-item">
          <label class="form-label">处置结果 <span class="required">*</span></label>
          <el-select v-model="handleForm.handle_status" size="small" placeholder="请选择处置结果">
            <el-option label="已处置" value="已处置" />
            <el-option label="误报" value="误报" />
          </el-select>
        </div>
        <div class="form-item">
          <label class="form-label">处置备注</label>
          <el-input v-model="handleForm.handle_remark" type="textarea" :rows="3" size="small" placeholder="请输入处置备注" />
        </div>
      </div>
      <div slot="footer">
        <el-button size="small" @click="showHandle = false">取消</el-button>
        <el-button size="small" type="primary" @click="onHandleConfirm">确认</el-button>
      </div>
    </el-dialog>
  </app-layout>
</template>

<script>
import { getAlarmList, getAlarmDetail, handleAlarm, exportAlarmLog, clearAllAlarms } from '@/api/alarm'

export default {
  name: 'AlarmCenterPage',
  data () {
    return {
      alarmList: [],
      loading: false,
      page: 1,
      perPage: 20,
      total: 0,
      refreshing: false,
      openSelect: null,
      openDatePicker: null,
      showMonthYearPicker: null,
      startPickerDate: new Date(),
      endPickerDate: new Date(),
      weekdays: ['日', '一', '二', '三', '四', '五', '六'],
      stats: {
        today: 0,
        total: 0,
        pending: 0,
        handled: 0
      },
      filter: {
        alarmType: 0,
        alarmLevel: 0,
        handleStatus: 0,
        startTime: '',
        endTime: ''
      },
      typeOptions: [
        { text: '全部类型', value: 0 },
        { text: '人脸告警', value: 'face_alarm' },
        { text: '禁区入侵', value: 'zone_intrusion' },
        { text: '行为异常', value: 'behavior_abnormal' },
        { text: '险情告警', value: 'danger_alarm' }
      ],
      levelOptions: [
        { text: '全部级别', value: 0 },
        { text: '一般', value: 'normal' },
        { text: '警告', value: 'warning' },
        { text: '严重', value: 'critical' }
      ],
      statusOptions: [
        { text: '全部状态', value: 0 },
        { text: '待处置', value: 'pending' },
        { text: '已处置', value: 'handled' },
        { text: '误报', value: 'false_alarm' }
      ],
      showDetail: false,
      currentAlarm: null,
      showHandle: false,
      handleForm: {
        handle_status: '已处置',
        handle_remark: ''
      }
    }
  },
  mounted () {
    this.loadData()
    this.loadStats()
    document.addEventListener('click', this.handleClickOutside)
  },
  beforeDestroy () {
    document.removeEventListener('click', this.handleClickOutside)
  },
  methods: {
    handleClickOutside (event) {
      if (!event.target.closest('.custom-select') && !event.target.closest('.custom-date-picker')) {
        this.openSelect = null
        this.openDatePicker = null
      }
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
        alarmType: '告警类型',
        alarmLevel: '告警级别',
        handleStatus: '处置状态'
      }
      const optionsMap = {
        alarmType: this.typeOptions,
        alarmLevel: this.levelOptions,
        handleStatus: this.statusOptions
      }
      const options = optionsMap[type]
      const option = options.find(opt => opt.value === value)
      return option && value !== 0 ? option.text : placeholderMap[type]
    },
    async loadData () {
      this.loading = true
      try {
        const params = {
          page: this.page,
          per_page: this.perPage
        }
        if (this.filter.alarmType) {
          params.alarm_type = this.filter.alarmType
        }
        if (this.filter.alarmLevel) {
          params.alarm_level = this.filter.alarmLevel
        }
        if (this.filter.handleStatus) {
          params.handle_status = this.filter.handleStatus
        }
        if (this.filter.startTime) {
          params.start_time = this.filter.startTime
        }
        if (this.filter.endTime) {
          params.end_time = this.filter.endTime
        }

        const res = await getAlarmList(params)
        if (res.code === 0 && res.data) {
          this.alarmList = res.data.items || []
          this.total = res.data.total || 0
        }
      } catch (e) {
        console.error(e)
      }
      this.loading = false
    },
    onPageChange (newPage) {
      this.page = newPage
      this.loadData()
    },
    async loadStats () {
      try {
        const res = await getAlarmList({ page: 1, per_page: 1000 })
        if (res.code === 0 && res.data) {
          const items = res.data.items || []
          this.stats.total = res.data.total
          this.stats.pending = items.filter(a => a.handle_status === 'pending').length
          this.stats.handled = items.filter(a => a.handle_status !== 'pending').length
          const today = new Date()
          const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`
          this.stats.today = items.filter(a => {
            if (!a.alarm_time) return false
            return a.alarm_time.startsWith(todayStr)
          }).length
        }
      } catch (e) {
        console.error(e)
      }
    },
    onRefresh () {
      this.page = 1
      this.loadData()
      this.loadStats()
    },
    onSearch () {
      this.page = 1
      this.loadData()
    },
    onReset () {
      this.filter = {
        alarmType: 0,
        alarmLevel: 0,
        handleStatus: 0,
        startTime: '',
        endTime: ''
      }
      this.onSearch()
    },
    async onExport () {
      try {
        const params = {}
        if (this.filter.alarmType) {
          params.alarm_type = this.filter.alarmType
        }
        if (this.filter.alarmLevel) {
          params.alarm_level = this.filter.alarmLevel
        }
        if (this.filter.handleStatus) {
          params.handle_status = this.filter.handleStatus
        }
        if (this.filter.startTime) {
          params.start_time = this.filter.startTime
        }
        if (this.filter.endTime) {
          params.end_time = this.filter.endTime
        }

        const res = await exportAlarmLog(params)
        if (!res || res.size === 0) {
          this.$message.error('导出数据为空')
          return
        }
        const blob = new Blob([res], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
        const url = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.download = `alarm_log_${new Date().getTime()}.xlsx`
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        window.URL.revokeObjectURL(url)
        this.$message.success('导出成功')
      } catch (e) {
        console.error('Export error:', e)
        this.$message.error('导出失败')
      }
    },
    onClearConfirm () {
      this.$confirm('确定要清空所有告警记录吗？此操作不可恢复！', '警告', {
        confirmButtonText: '确定清空',
        cancelButtonText: '取消',
        type: 'warning',
        confirmButtonClass: 'el-button--danger'
      }).then(function () {
        this.doClearAlarms()
      }.bind(this)).catch(function () {})
    },
    async doClearAlarms () {
      try {
        const res = await clearAllAlarms()
        if (res.code === 0) {
          this.$message.success(res.message || '清空成功')
          this.alarmList = []
          this.loadStats()
        } else {
          this.$message.error(res.message || '清空失败')
        }
      } catch (e) {
        console.error('Clear error:', e)
        this.$message.error('清空失败')
      }
    },
    async showAlarmDetail (alarm) {
      try {
        const res = await getAlarmDetail(alarm.id)
        if (res.code === 0) {
          this.currentAlarm = res.data
          this.showDetail = true
        }
      } catch (e) {
        this.$message.error('获取详情失败')
      }
    },
    showHandleDialog (alarm) {
      this.currentAlarm = alarm
      this.handleForm = {
        handle_status: '已处置',
        handle_remark: ''
      }
      this.showHandle = true
    },
    async onHandleConfirm () {
      if (!this.currentAlarm) return

      try {
        const handleStatus = this.handleForm.handle_status === '误报' ? 'false_alarm' : 'handled'
        const res = await handleAlarm(this.currentAlarm.id, {
          handle_status: handleStatus,
          handle_remark: this.handleForm.handle_remark
        })
        if (res.code === 0) {
          this.$message.success('处置成功')
          this.showDetail = false
          this.onRefresh()
        }
      } catch (e) {
        this.$message.error('处置失败')
      }
    },

    getTypeText (type) {
      const map = {
        face_alarm: '人脸告警',
        zone_intrusion: '禁区入侵',
        behavior_abnormal: '行为异常',
        danger_alarm: '险情告警'
      }
      return map[type] || type
    },
    getTypeClass (type) {
      const map = {
        face_alarm: 'type-face',
        zone_intrusion: 'type-zone',
        behavior_abnormal: 'type-behavior',
        danger_alarm: 'type-danger'
      }
      return map[type] || ''
    },
    getLevelText (level) {
      const map = {
        normal: '一般',
        warning: '警告',
        critical: '严重'
      }
      return map[level] || level
    },
    getLevelClass (level) {
      const map = {
        normal: 'level-normal',
        warning: 'level-warning',
        critical: 'level-critical'
      }
      return map[level] || ''
    },
    getStatusText (status) {
      const map = {
        pending: '待处置',
        handled: '已处置',
        false_alarm: '误报'
      }
      return map[status] || status
    },
    formatTime (time) {
      if (!time) return ''
      return time.replace('T', ' ').substring(0, 19)
    },
    getImageUrl (path) {
      if (!path) return ''
      if (path.startsWith('http')) return path
      return `${process.env.API_BASE_URL || '/api/v1'}/../${path}`
    },
    getVideoUrl (path) {
      return this.getImageUrl(path)
    }
  }
}
</script>

<style scoped>
.alarm-center {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
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

.filter-label {
  display: block;
  font-size: 12px;
  color: var(--dark-text-secondary);
  margin-bottom: 6px;
  font-weight: 500;
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

.filter-input {
  width: 100%;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--dark-border-field);
  border-radius: 8px;
  color: var(--dark-text);
  font-size: 13px;
  outline: none;
  transition: all 0.2s;
  cursor: pointer;
}

.filter-input:hover {
  background: rgba(255, 255, 255, 0.06);
  border-color: var(--dark-accent-light);
}

.filter-input:focus {
  border-color: var(--dark-accent-light);
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.1);
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

.date-title {
  font-size: 14px;
  font-weight: 500;
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

.filter-spacer {
  visibility: hidden;
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

.action-btn-info {
  background: rgba(59, 130, 246, 0.1);
  border-color: rgba(59, 130, 246, 0.3);
  color: #60a5fa;
}

.action-btn-info:hover {
  background: rgba(59, 130, 246, 0.15);
  border-color: #60a5fa;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.2);
}

.action-btn-danger {
  background: rgba(239, 68, 68, 0.1);
  border-color: rgba(239, 68, 68, 0.3);
  color: #f87171;
}

.action-btn-danger:hover {
  background: rgba(239, 68, 68, 0.15);
  border-color: #f87171;
  box-shadow: 0 2px 8px rgba(239, 68, 68, 0.2);
}

.alarm-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
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

.stat-pending .stat-value {
  color: var(--dark-danger);
}

.stat-handled .stat-value {
  color: var(--dark-success);
}

.alarm-list-section {
  background: var(--dark-card);
  border-radius: 16px;
  border: 1px solid var(--dark-border);
  padding: 20px;
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.alarm-list {
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

.type-face {
  color: #818cf8;
  border-color: rgba(99, 102, 241, 0.3);
  background: rgba(99, 102, 241, 0.08);
}

.type-zone {
  color: #fbbf24;
  border-color: rgba(245, 158, 11, 0.3);
  background: rgba(245, 158, 11, 0.08);
}

.type-behavior {
  color: #a78bfa;
  border-color: rgba(139, 92, 246, 0.3);
  background: rgba(139, 92, 246, 0.08);
}

.type-danger {
  color: #f87171;
  border-color: rgba(239, 68, 68, 0.3);
  background: rgba(239, 68, 68, 0.08);
}

.level-normal {
  background: rgba(16, 185, 129, 0.15);
  color: #34d399;
}

.level-warning {
  background: rgba(245, 158, 11, 0.15);
  color: #fbbf24;
}

.level-critical {
  background: rgba(239, 68, 68, 0.15);
  color: #f87171;
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

.dot-pending {
  background: #f59e0b;
  box-shadow: 0 0 6px rgba(245, 158, 11, 0.4);
}

.dot-handled {
  background: var(--dark-success);
  box-shadow: 0 0 6px rgba(16, 185, 129, 0.4);
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

.handle-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 0 10px;
  height: 28px;
  background: var(--dark-accent);
  border: none;
  border-radius: 6px;
  color: #fff;
  font-size: 13px;
  cursor: pointer;
  transition: background 0.2s;
  margin-left: 16px;
}

.handle-btn:hover {
  background: var(--dark-accent-light);
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: var(--dark-text-secondary);
}

.empty-state i {
  font-size: 48px;
  margin-bottom: 16px;
  display: block;
}

.empty-state p {
  font-size: 16px;
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

.detail-image,
.detail-video {
  margin-top: 16px;
}

.detail-image h4,
.detail-video h4 {
  margin: 0 0 12px;
  font-size: 15px;
  font-weight: 600;
}

.detail-image img {
  width: 100%;
  border-radius: 8px;
}

.handle-form {
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

@media (max-width: 1024px) {
  .alarm-center {
    height: auto;
    min-height: calc(100vh - 120px);
  }

  .alarm-stats {
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

  .alarm-list-section {
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

.dark-dialog .el-input__inner,
.dark-dialog .el-textarea__inner {
  background: rgba(255, 255, 255, 0.04) !important;
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
  color: #EDEDEF !important;
}

.dark-dialog .el-input__inner::placeholder,
.dark-dialog .el-textarea__inner::placeholder {
  color: #8A8F98 !important;
}

.dark-dialog .el-select .el-input__inner {
  background: rgba(255, 255, 255, 0.04) !important;
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
  color: #EDEDEF !important;
}

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
