<template>
  <div class="alarm-log-page">
    <van-nav-bar title="历史告警日志" left-arrow @click-left="$router.back()" />
    <div class="page-content">
      <van-cell-group>
        <van-field v-model="filter.startTime" label="开始时间" placeholder="YYYY-MM-DD" />
        <van-field v-model="filter.endTime" label="结束时间" placeholder="YYYY-MM-DD" />
        <van-field v-model="filter.alarmType" label="告警类型" placeholder="全部" readonly is-link @click="showTypePicker = true" />
        <van-field v-model="filter.alarmLevel" label="告警级别" placeholder="全部" readonly is-link @click="showLevelPicker = true" />
      </van-cell-group>
      <div style="margin: 8px 0"><van-button type="primary" size="small" @click="onSearch">查询</van-button></div>
      <van-list v-model="loading" :finished="finished" finished-text="没有更多了" @load="loadData">
        <van-cell v-for="item in logList" :key="item.id">
          <template #title>
            <van-tag :type="levelTagType(item.alarm_level)">{{ item.alarm_level }}</van-tag>
            {{ item.alarm_type }}
          </template>
          <template #label>
            <div>{{ item.alarm_description }}</div>
            <div>{{ item.alarm_time }} | {{ item.handle_status }}</div>
          </template>
        </van-cell>
      </van-list>
    </div>
    <van-popup v-model="showTypePicker" position="bottom">
      <van-picker :columns="typeOptions" @confirm="onTypeConfirm" @cancel="showTypePicker = false" />
    </van-popup>
    <van-popup v-model="showLevelPicker" position="bottom">
      <van-picker :columns="levelOptions" @confirm="onLevelConfirm" @cancel="showLevelPicker = false" />
    </van-popup>
  </div>
</template>

<script>
import { getAlarmLogs } from '@/api/property'

export default {
  name: 'AlarmLogListPage',
  data () {
    return {
      logList: [],
      loading: false,
      finished: false,
      page: 1,
      filter: { startTime: '', endTime: '', alarmType: '', alarmLevel: '' },
      showTypePicker: false,
      showLevelPicker: false,
      typeOptions: ['全部', '人脸告警', '禁区入侵', '行为异常', '险情告警'],
      levelOptions: ['全部', '一般', '警告', '严重']
    }
  },
  methods: {
    async loadData () {
      try {
        const typeMap = { 人脸告警: 'face_alarm', 禁区入侵: 'zone_intrusion', 行为异常: 'behavior_abnormal', 险情告警: 'danger_alarm' }
        const levelMap = { 一般: 'normal', 警告: 'warning', 严重: 'critical' }
        const params = { page: this.page, per_page: 20 }
        if (this.filter.startTime) params.start_time = this.filter.startTime
        if (this.filter.endTime) params.end_time = this.filter.endTime
        if (this.filter.alarmType && this.filter.alarmType !== '全部') params.alarm_type = typeMap[this.filter.alarmType]
        if (this.filter.alarmLevel && this.filter.alarmLevel !== '全部') params.alarm_level = levelMap[this.filter.alarmLevel]
        const res = await getAlarmLogs(params)
        if (res.code === 0 && res.data) {
          const items = res.data.items || []
          if (this.page === 1) this.logList = items
          else this.logList.push(...items)
          this.finished = this.logList.length >= res.data.total
          this.page++
        }
      } catch (e) { this.finished = true }
      this.loading = false
    },
    onSearch () { this.page = 1; this.finished = false; this.logList = []; this.loadData() },
    onTypeConfirm (val) { this.filter.alarmType = val; this.showTypePicker = false },
    onLevelConfirm (val) { this.filter.alarmLevel = val; this.showLevelPicker = false },
    levelTagType (level) { return { normal: 'default', warning: 'warning', critical: 'danger' }[level] || 'default' }
  }
}
</script>

<style scoped>
.page-content { padding: 12px; }
</style>
