<template>
  <app-layout page-title="门禁终端管理">
    <div class="dark-card">
      <van-cell-group>
        <van-field v-model="filterLevel" label="终端层级" placeholder="全部" readonly is-link @click="showLevelPicker = true" />
        <van-field v-model="filterStatus" label="状态" placeholder="全部" readonly is-link @click="showStatusPicker = true" />
      </van-cell-group>
      <div style="margin: 12px 0">
        <van-button type="primary" size="small" @click="$router.push('/access-control/edit')">新增终端</van-button>
      </div>
    </div>
    <div class="dark-card">
      <van-pull-refresh v-model="refreshing" @refresh="onRefresh">
        <van-list v-model="loading" :finished="finished" finished-text="没有更多了" @load="loadData">
          <van-cell v-for="item in gateList" :key="item.id" is-link @click="goDetail(item)">
            <template #title>
              <span>{{ item.gate_name }}</span>
              <van-tag :type="levelTagType(item.gate_level)" style="margin-left: 8px">{{ item.level_name || item.gate_level }}</van-tag>
            </template>
            <template #label>
              <div>{{ item.location }}</div>
              <div v-if="item.building_unit">楼栋/单元: {{ item.building_unit }}</div>
            </template>
            <template #right-icon>
              <van-tag :type="item.status === 'online' ? 'success' : 'danger'">{{ item.status === 'online' ? '在线' : '离线' }}</van-tag>
            </template>
          </van-cell>
        </van-list>
      </van-pull-refresh>
    </div>
    <van-popup v-model="showLevelPicker" position="bottom">
      <van-picker :columns="levelOptions" @confirm="onLevelConfirm" @cancel="showLevelPicker = false" />
    </van-popup>
    <van-popup v-model="showStatusPicker" position="bottom">
      <van-picker :columns="statusOptions" @confirm="onStatusConfirm" @cancel="showStatusPicker = false" />
    </van-popup>
  </app-layout>
</template>

<script>
import { getGateList } from '@/api/property'

export default {
  name: 'GateListPage',
  data () {
    return {
      gateList: [],
      loading: false,
      finished: false,
      refreshing: false,
      page: 1,
      filterLevel: '',
      filterStatus: '',
      showLevelPicker: false,
      showStatusPicker: false,
      levelOptions: ['全部', '社区大门', '单元门', '危险防护区域'],
      statusOptions: ['全部', '在线', '离线', '维护中']
    }
  },
  methods: {
    async loadData () {
      try {
        const levelMap = { 社区大门: 'community_gate', 单元门: 'unit_door', 危险防护区域: 'dangerous_area' }
        const statusMap = { 在线: 'online', 离线: 'offline', 维护中: 'maintenance' }
        const params = { page: this.page, per_page: 20 }
        if (this.filterLevel && this.filterLevel !== '全部') params.gate_level = levelMap[this.filterLevel]
        if (this.filterStatus && this.filterStatus !== '全部') params.status = statusMap[this.filterStatus]
        const res = await getGateList(params)
        if (res.code === 0 && res.data) {
          const items = res.data.items || []
          if (this.page === 1) this.gateList = items
          else this.gateList.push(...items)
          this.finished = this.gateList.length >= res.data.total
          this.page++
        }
      } catch (e) {
        this.finished = true
      }
      this.loading = false
      this.refreshing = false
    },
    onRefresh () { this.page = 1; this.finished = false; this.loadData() },
    onLevelConfirm (val) { this.filterLevel = val; this.showLevelPicker = false; this.onRefresh() },
    onStatusConfirm (val) { this.filterStatus = val; this.showStatusPicker = false; this.onRefresh() },
    levelTagType (level) {
      const map = { community_gate: 'primary', unit_door: 'success', dangerous_area: 'danger' }
      return map[level] || 'default'
    },
    goDetail (item) { this.$router.push(`/access-control/edit/${item.id}`) }
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
