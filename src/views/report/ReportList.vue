<template>
  <app-layout page-title="安防监控日报">
    <div class="dark-card">
      <van-cell-group>
        <van-field v-model="startDate" label="开始日期" placeholder="YYYY-MM-DD" />
        <van-field v-model="endDate" label="结束日期" placeholder="YYYY-MM-DD" />
      </van-cell-group>
      <div style="margin: 8px 0; display: flex; gap: 8px">
        <van-button type="primary" size="small" @click="loadData">查询</van-button>
        <van-button size="small" @click="showGenerate = true">生成日报</van-button>
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
