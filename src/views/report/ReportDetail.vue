<template>
  <app-layout page-title="日报详情">
    <div v-if="report" class="dark-card">
      <van-cell-group title="基本信息">
        <van-cell title="日报日期" :value="report.report_date" />
        <van-cell title="生成状态" :value="report.generate_status" />
      </van-cell-group>
      <van-cell-group title="通行统计">
        <div class="stats-card" v-if="passStats">
          <van-row><van-col span="8"><div class="stat-item"><div class="stat-value">{{ passStats.total || 0 }}</div><div class="stat-label">总通行</div></div></van-col><van-col span="8"><div class="stat-item"><div class="stat-value">{{ passStats.pass_count || 0 }}</div><div class="stat-label">放行</div></div></van-col><van-col span="8"><div class="stat-item"><div class="stat-value">{{ passStats.reject_count || 0 }}</div><div class="stat-label">拒绝</div></div></van-col></van-row>
        </div>
      </van-cell-group>
      <van-cell-group title="告警统计">
        <div class="stats-card" v-if="alarmStats">
          <van-row><van-col span="12"><div class="stat-item"><div class="stat-value">{{ alarmStats.total || 0 }}</div><div class="stat-label">告警总数</div></div></van-col></van-row>
        </div>
      </van-cell-group>
      <van-cell-group title="异常事件" v-if="abnormalEvents && abnormalEvents.length > 0">
        <van-cell v-for="evt in abnormalEvents" :key="evt.id" :title="evt.alarm_type" :label="evt.alarm_description" />
      </van-cell-group>
      <div style="margin: 12px 0">
        <van-button size="small" @click="onRegenerate">重新生成</van-button>
      </div>
    </div>
  </app-layout>
</template>

<script>
import { getReportDetail, regenerateReport } from '@/api/property'

export default {
  name: 'ReportDetailPage',
  data () {
    return { report: null, passStats: null, alarmStats: null, abnormalEvents: [] }
  },
  created () { this.loadDetail() },
  methods: {
    async loadDetail () {
      const id = this.$route.params.id
      try {
        const res = await getReportDetail(id)
        if (res.code === 0 && res.data) {
          this.report = res.data
          try { this.passStats = JSON.parse(res.data.pass_stats || '{}') } catch (e) { this.passStats = {} }
          try { this.alarmStats = JSON.parse(res.data.alarm_stats || '{}') } catch (e) { this.alarmStats = {} }
          try { this.abnormalEvents = JSON.parse(res.data.abnormal_events || '[]') } catch (e) { this.abnormalEvents = [] }
        }
      } catch (e) { this.$toast.fail('加载失败') }
    },
    async onRegenerate () {
      try {
        await regenerateReport(this.report.id)
        this.$toast.success('重新生成成功')
        this.loadDetail()
      } catch (e) { this.$toast.fail('重新生成失败') }
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
.stats-card { padding: 12px; }
.stat-item { text-align: center; }
.stat-value { font-size: 24px; font-weight: bold; color: var(--dark-accent-light); }
.stat-label { font-size: 12px; color: var(--dark-text-secondary); margin-top: 4px; }
</style>
