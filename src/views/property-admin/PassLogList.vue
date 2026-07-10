<template>
  <app-layout page-title="历史通行日志">
    <div class="dark-card">
      <van-cell-group>
        <van-field v-model="filter.startTime" label="开始时间" placeholder="YYYY-MM-DD" />
        <van-field v-model="filter.endTime" label="结束时间" placeholder="YYYY-MM-DD" />
        <van-field v-model="filter.gateLevel" label="终端层级" placeholder="全部" readonly is-link @click="showLevelPicker = true" />
      </van-cell-group>
      <div style="margin: 8px 0"><van-button type="primary" size="small" @click="onSearch">查询</van-button></div>
    </div>
    <div class="dark-card">
      <van-list v-model="loading" :finished="finished" finished-text="没有更多了" @load="loadData">
        <van-cell v-for="item in logList" :key="item.id">
          <template #title>{{ item.person_name || '未知' }}</template>
          <template #label>
            <div>{{ item.gate_name }} | {{ item.pass_result === 'pass' ? '放行' : '拒绝' }}</div>
            <div>{{ item.pass_time }}</div>
          </template>
        </van-cell>
      </van-list>
    </div>
    <van-popup v-model="showLevelPicker" position="bottom">
      <van-picker :columns="levelOptions" @confirm="onLevelConfirm" @cancel="showLevelPicker = false" />
    </van-popup>
  </app-layout>
</template>

<script>
import { getPassLogs } from '@/api/property'

export default {
  name: 'PassLogListPage',
  data () {
    return {
      logList: [],
      loading: false,
      finished: false,
      page: 1,
      filter: { startTime: '', endTime: '', gateLevel: '' },
      showLevelPicker: false,
      levelOptions: ['全部', '社区大门', '单元门', '危险防护区域']
    }
  },
  methods: {
    async loadData () {
      try {
        const levelMap = { 社区大门: 'community_gate', 单元门: 'unit_door', 危险防护区域: 'dangerous_area' }
        const params = { page: this.page, per_page: 20 }
        if (this.filter.startTime) params.start_time = this.filter.startTime
        if (this.filter.endTime) params.end_time = this.filter.endTime
        if (this.filter.gateLevel && this.filter.gateLevel !== '全部') params.gate_level = levelMap[this.filter.gateLevel]
        const res = await getPassLogs(params)
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
    onLevelConfirm (val) { this.filter.gateLevel = val; this.showLevelPicker = false }
  }
}
</script>

<style scoped>
.dark-card {
  background: rgba(10, 10, 10, 0.8);
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  padding: 20px;
  margin-bottom: 16px;
}
</style>
