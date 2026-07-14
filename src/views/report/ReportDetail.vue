<template>
  <app-layout page-title="AI安防日报详情">
    <div v-if="report" class="report-page">
      <section class="report-header">
        <div>
          <span class="date-label">{{ report.report_date }}</span>
          <h2>社区安防日报</h2>
          <p>{{ sourceLabel(report.workflow_source) }} · {{ report.generated_at || '刚刚生成' }}</p>
        </div>
        <div class="risk-score" :class="`risk-${report.risk_level || 'low'}`">
          <strong>{{ report.risk_score || 0 }}</strong>
          <span>{{ riskLabel(report.risk_level) }}风险</span>
        </div>
      </section>

      <section class="report-section">
        <h3>智能摘要</h3>
        <p class="summary">{{ report.ai_summary || '暂无摘要' }}</p>
      </section>

      <section class="metrics">
        <div><strong>{{ passStats.total || 0 }}</strong><span>通行总数</span></div>
        <div><strong>{{ passStats.reject_count || 0 }}</strong><span>拒绝通行</span></div>
        <div><strong>{{ alarmStats.total || 0 }}</strong><span>告警总数</span></div>
        <div><strong>{{ alarmStats.pending_count || 0 }}</strong><span>待处理</span></div>
      </section>

      <report-charts
        :pass-stats="passStats"
        :alarm-stats="alarmStats"
        :risk-score="report.risk_score"
      />

      <section class="report-section">
        <h3>处置建议</h3>
        <ol v-if="recommendations.length" class="recommendation-list">
          <li v-for="(item, index) in recommendations" :key="index">{{ item }}</li>
        </ol>
        <p v-else class="muted">暂无处置建议</p>
      </section>

      <section v-if="alarmTypes.length" class="report-section">
        <h3>告警分类</h3>
        <div class="type-list">
          <div v-for="item in alarmTypes" :key="item.name">
            <span>{{ alarmTypeLabel(item.name) }}</span>
            <strong>{{ item.count }}</strong>
          </div>
        </div>
      </section>

      <section v-if="abnormalEvents.length" class="report-section">
        <h3>关键事件</h3>
        <div v-for="evt in abnormalEvents" :key="evt.id" class="event-row">
          <strong>{{ alarmTypeLabel(evt.alarm_type) }}</strong>
          <span>{{ evt.alarm_description }}</span>
          <small>{{ evt.alarm_time }}</small>
        </div>
      </section>

      <div class="report-actions">
        <van-button
          icon="replay"
          size="small"
          :loading="regenerating"
          :disabled="regenerating || deleting"
          loading-text="生成中..."
          @click="onRegenerate"
        >重新生成</van-button>
        <van-button
          type="danger"
          icon="delete"
          size="small"
          :loading="deleting"
          :disabled="regenerating || deleting"
          @click="onDelete"
        >删除日报</van-button>
      </div>
    </div>
  </app-layout>
</template>

<script>
import { Dialog } from 'vant'
import { getReportDetail, regenerateReport, deleteReport } from '@/api/property'
import ReportCharts from '@/components/report/ReportCharts'

export default {
  name: 'ReportDetailPage',
  components: { ReportCharts },
  data () {
    return {
      report: null,
      passStats: {},
      alarmStats: {},
      abnormalEvents: [],
      recommendations: [],
      regenerating: false,
      deleting: false
    }
  },
  computed: {
    alarmTypes () {
      const distribution = this.alarmStats.type_distribution || {}
      return Object.keys(distribution)
        .map(name => ({ name, count: distribution[name] }))
        .sort((a, b) => b.count - a.count)
    }
  },
  created () {
    this.loadDetail()
  },
  methods: {
    async loadDetail () {
      try {
        const res = await getReportDetail(this.$route.params.id)
        if (res.code !== 0 || !res.data) throw new Error(res.message)
        this.report = res.data
        this.passStats = this.parseJson(res.data.pass_stats, {})
        this.alarmStats = this.parseJson(res.data.alarm_stats, {})
        this.abnormalEvents = this.parseJson(res.data.abnormal_events, [])
        this.recommendations = this.parseJson(res.data.recommendations, [])
      } catch (e) {
        if (!e.__messageShown) this.$message.error(e.message || '日报加载失败')
      }
    },
    async onRegenerate () {
      if (this.regenerating || this.deleting || !this.report) return
      this.regenerating = true
      try {
        const res = await regenerateReport(this.report.id)
        if (res.code !== 0) throw new Error(res.message)
        this.$message.success('日报已重新生成')
        await this.loadDetail()
      } catch (e) {
        if (!e.__messageShown) this.$message.error(e.message || '重新生成失败')
      } finally {
        this.regenerating = false
      }
    },
    onDelete () {
      if (this.regenerating || this.deleting || !this.report) return
      Dialog.confirm({
        title: '确认删除',
        message: '删除后不可恢复，确定删除这份日报吗？'
      }).then(() => this.doDelete()).catch(() => {})
    },
    async doDelete () {
      this.deleting = true
      try {
        const res = await deleteReport(this.report.id)
        if (res.code !== 0) throw new Error(res.message)
        this.$message.success('日报已删除')
        this.$router.replace('/report')
      } catch (e) {
        if (!e.__messageShown) this.$message.error(e.message || '删除日报失败')
      } finally {
        this.deleting = false
      }
    },
    parseJson (value, fallback) {
      try { return JSON.parse(value || '') } catch (e) { return fallback }
    },
    riskLabel (level) {
      return { low: '低', medium: '中', high: '高' }[level] || '低'
    },
    sourceLabel (source) {
      if (source === 'siliconflow') return '硅基流动API生成'
      if (source === 'ollama') return '历史Ollama生成'
      return source === 'ai_service' ? 'AI服务生成' : '本地智能分析'
    },
    alarmTypeLabel (type) {
      const labels = {
        device_blocked: '摄像头遮挡',
        device_blurred: '画面模糊',
        device_moved: '设备移动',
        camera_impact: '设备拍打',
        open_flame: '明火',
        smoke: '烟雾',
        tailgating: '贴身尾随',
        stream_offline: '视频断流',
        danger_zone_intrusion: '危险区域入侵'
      }
      return labels[type] || type
    }
  }
}
</script>

<style scoped>
.report-page { color: var(--dark-text); }
.report-header,
.report-section,
.metrics {
  border: 1px solid var(--dark-border);
  background: var(--dark-card);
  margin-bottom: 14px;
}
.report-header {
  min-height: 132px;
  padding: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
}
.date-label,
.report-header p,
.muted { color: var(--dark-text-secondary); }
.report-header h2 { margin: 6px 0; font-size: 22px; }
.report-header p { margin: 0; font-size: 12px; }
.risk-score {
  width: 76px;
  height: 76px;
  border: 2px solid currentColor;
  border-radius: 50%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 0 0 76px;
}
.risk-score strong { font-size: 22px; }
.risk-score span { font-size: 11px; }
.risk-low { color: #38c78f; }
.risk-medium { color: #e8a84e; }
.risk-high { color: #ef5b5b; }
.report-section { padding: 18px 20px; }
.report-section h3 { margin: 0 0 12px; font-size: 15px; }
.summary { margin: 0; line-height: 1.8; }
.metrics {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
}
.metrics div {
  min-height: 88px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-right: 1px solid var(--dark-border);
}
.metrics div:last-child { border-right: 0; }
.metrics strong { font-size: 22px; color: var(--dark-accent-light); }
.metrics span { margin-top: 5px; font-size: 12px; color: var(--dark-text-secondary); }
.recommendation-list { margin: 0; padding-left: 22px; }
.recommendation-list li { margin: 8px 0; line-height: 1.6; }
.type-list div,
.event-row {
  padding: 10px 0;
  border-top: 1px solid var(--dark-border);
}
.type-list div { display: flex; justify-content: space-between; }
.event-row { display: grid; gap: 4px; }
.event-row span { color: var(--dark-text-secondary); }
.event-row small { color: var(--dark-text-secondary); }
.report-actions {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}
@media (max-width: 640px) {
  .metrics { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .metrics div:nth-child(2) { border-right: 0; }
  .metrics div:nth-child(-n+2) { border-bottom: 1px solid var(--dark-border); }
}
</style>
