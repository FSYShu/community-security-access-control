<template>
  <section class="charts-section">
    <div class="charts-heading">
      <h3>数据可视化</h3>
      <span>{{ reportOverview }}</span>
    </div>

    <div class="risk-strip">
      <div class="risk-summary">
        <span>综合风险</span>
        <div>
          <strong :class="riskColorClass">{{ normalizedRiskScore }}</strong>
          <em :class="riskColorClass">{{ riskLevelText }}</em>
        </div>
      </div>
      <div class="risk-scale">
        <div class="risk-scale-labels">
          <span>低风险</span>
          <span>中风险</span>
          <span>高风险</span>
        </div>
        <div class="risk-track">
          <span class="risk-segment risk-segment-low"></span>
          <span class="risk-segment risk-segment-medium"></span>
          <span class="risk-segment risk-segment-high"></span>
          <i :style="riskMarkerStyle"></i>
        </div>
      </div>
    </div>

    <div class="chart-grid">
      <article v-if="hasPassData" class="chart-panel">
        <div class="chart-title">
          <h4>通行结果</h4>
          <span>{{ passRateText }}</span>
        </div>
        <div ref="passChart" class="chart-canvas"></div>
      </article>

      <article v-if="hasAlarmData" class="chart-panel">
        <div class="chart-title">
          <h4>告警处置</h4>
          <span>{{ handlingRateText }}</span>
        </div>
        <div ref="handlingChart" class="chart-canvas"></div>
      </article>

      <article
        v-if="hasAlarmTypeData"
        class="chart-panel"
        :class="{ 'chart-panel-wide': hasPassData }"
      >
        <div class="chart-title">
          <h4>告警类型分布</h4>
          <span>共 {{ alarmTotal }} 条</span>
        </div>
        <div ref="alarmTypeChart" class="chart-canvas chart-canvas-wide"></div>
      </article>

      <article v-if="hasHourlyData" class="chart-panel chart-panel-wide">
        <div class="chart-title">
          <h4>24小时通行趋势</h4>
          <span>峰值 {{ peakPassCount }} 次</span>
        </div>
        <div ref="hourlyChart" class="chart-canvas chart-canvas-wide"></div>
      </article>
    </div>
  </section>
</template>

<script>
import * as echarts from 'echarts/core'
import { BarChart, LineChart, PieChart } from 'echarts/charts'
import {
  GridComponent,
  LegendComponent,
  TitleComponent,
  TooltipComponent
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

echarts.use([
  BarChart,
  LineChart,
  PieChart,
  GridComponent,
  LegendComponent,
  TitleComponent,
  TooltipComponent,
  CanvasRenderer
])

const TEXT_COLOR = '#dce3ec'
const MUTED_COLOR = '#8792a2'
const GRID_COLOR = 'rgba(148, 163, 184, 0.16)'

const ALARM_LABELS = {
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

const ALARM_COLORS = {
  device_blocked: '#8c7ae6',
  device_blurred: '#7393b3',
  device_moved: '#3f8fc4',
  camera_impact: '#df5d83',
  open_flame: '#ef5b5b',
  smoke: '#d98a43',
  tailgating: '#e1b64b',
  stream_offline: '#788391',
  danger_zone_intrusion: '#46a889'
}

export default {
  name: 'ReportCharts',
  props: {
    passStats: {
      type: Object,
      default: () => ({})
    },
    alarmStats: {
      type: Object,
      default: () => ({})
    },
    riskScore: {
      type: [Number, String],
      default: 0
    }
  },
  computed: {
    passTotal () {
      return this.toNumber(this.passStats.total)
    },
    alarmTotal () {
      return this.toNumber(this.alarmStats.total)
    },
    hasPassData () {
      return this.passTotal > 0
    },
    hasAlarmData () {
      return this.alarmTotal > 0
    },
    alarmTypeItems () {
      const distribution = this.alarmStats.type_distribution || {}
      return Object.keys(distribution)
        .map(type => ({
          type,
          name: ALARM_LABELS[type] || type,
          value: this.toNumber(distribution[type])
        }))
        .filter(item => item.value > 0)
        .sort((a, b) => b.value - a.value)
    },
    hasAlarmTypeData () {
      return this.alarmTypeItems.length > 0
    },
    hourlyValues () {
      const distribution = this.passStats.hourly_distribution || {}
      return Array.from({ length: 24 }, (_, hour) => {
        const key = `${String(hour).padStart(2, '0')}:00`
        return this.toNumber(distribution[key])
      })
    },
    hasHourlyData () {
      return this.hourlyValues.some(value => value > 0)
    },
    peakPassCount () {
      return Math.max(0, ...this.hourlyValues)
    },
    passRateText () {
      if (!this.passTotal) return '放行率 0%'
      const rate = this.toNumber(this.passStats.pass_count) * 100 / this.passTotal
      return `放行率 ${rate.toFixed(1)}%`
    },
    handlingRateText () {
      if (!this.alarmTotal) return '处理率 0%'
      const rate = this.toNumber(this.alarmStats.handled_count) * 100 / this.alarmTotal
      return `处理率 ${rate.toFixed(1)}%`
    },
    reportOverview () {
      return `${this.passTotal} 次通行 · ${this.alarmTotal} 条告警`
    },
    normalizedRiskScore () {
      return Math.min(100, Math.max(0, this.toNumber(this.riskScore)))
    },
    riskLevelText () {
      if (this.normalizedRiskScore >= 60) return '高风险'
      if (this.normalizedRiskScore >= 20) return '中风险'
      return '低风险'
    },
    riskColorClass () {
      if (this.normalizedRiskScore >= 60) return 'risk-color-high'
      if (this.normalizedRiskScore >= 20) return 'risk-color-medium'
      return 'risk-color-low'
    },
    riskMarkerStyle () {
      const position = Math.min(99, Math.max(1, this.normalizedRiskScore))
      return { left: `${position}%` }
    }
  },
  watch: {
    passStats: {
      deep: true,
      handler () { this.scheduleRender() }
    },
    alarmStats: {
      deep: true,
      handler () { this.scheduleRender() }
    },
    riskScore () {
      this.scheduleRender()
    }
  },
  mounted () {
    this.scheduleRender()
    window.addEventListener('resize', this.resizeCharts)
  },
  beforeDestroy () {
    window.removeEventListener('resize', this.resizeCharts)
    this.chartElements().forEach(element => {
      const chart = element && echarts.getInstanceByDom(element)
      if (chart) chart.dispose()
    })
  },
  methods: {
    toNumber (value) {
      const number = Number(value)
      return Number.isFinite(number) ? number : 0
    },
    scheduleRender () {
      this.$nextTick(() => this.renderCharts())
    },
    chartElements () {
      return [
        this.$refs.passChart,
        this.$refs.handlingChart,
        this.$refs.alarmTypeChart,
        this.$refs.hourlyChart
      ]
    },
    resizeCharts () {
      this.chartElements().forEach(element => {
        const chart = element && echarts.getInstanceByDom(element)
        if (chart) chart.resize()
      })
    },
    renderCharts () {
      this.renderChart(this.$refs.passChart, this.hasPassData, this.passOption())
      this.renderChart(
        this.$refs.handlingChart,
        this.hasAlarmData,
        this.handlingOption()
      )
      this.renderChart(
        this.$refs.alarmTypeChart,
        this.hasAlarmTypeData,
        this.alarmTypeOption()
      )
      this.renderChart(
        this.$refs.hourlyChart,
        this.hasHourlyData,
        this.hourlyOption()
      )
    },
    renderChart (element, hasData, option) {
      if (!element) return
      const existing = echarts.getInstanceByDom(element)
      if (!hasData) {
        if (existing) existing.dispose()
        return
      }
      const chart = existing || echarts.init(element)
      chart.setOption(option, true)
    },
    donutOption (total, centerLabel, data, colors) {
      return {
        animationDuration: 500,
        color: colors,
        textStyle: { color: TEXT_COLOR },
        title: {
          text: String(total),
          subtext: centerLabel,
          left: 'center',
          top: '34%',
          textStyle: { color: TEXT_COLOR, fontSize: 24, fontWeight: 600 },
          subtextStyle: { color: MUTED_COLOR, fontSize: 11 }
        },
        tooltip: {
          trigger: 'item',
          formatter: '{b}<br/>{c} 次（{d}%）',
          backgroundColor: '#171b21',
          borderColor: '#343b45',
          textStyle: { color: TEXT_COLOR }
        },
        legend: {
          bottom: 4,
          icon: 'circle',
          itemWidth: 8,
          itemHeight: 8,
          textStyle: { color: MUTED_COLOR }
        },
        series: [{
          type: 'pie',
          radius: ['54%', '72%'],
          center: ['50%', '43%'],
          avoidLabelOverlap: true,
          label: { show: false },
          emphasis: { scaleSize: 6 },
          itemStyle: { borderColor: '#11151a', borderWidth: 3 },
          data: data.filter(item => item.value > 0)
        }]
      }
    },
    passOption () {
      return this.donutOption(this.passTotal, '总通行', [
        { name: '正常放行', value: this.toNumber(this.passStats.pass_count) },
        { name: '拒绝通行', value: this.toNumber(this.passStats.reject_count) }
      ], ['#43b88d', '#ef6a67'])
    },
    handlingOption () {
      return this.donutOption(this.alarmTotal, '总告警', [
        { name: '已处理', value: this.toNumber(this.alarmStats.handled_count) },
        { name: '待处理', value: this.toNumber(this.alarmStats.pending_count) }
      ], ['#4e9ccf', '#e1aa4d'])
    },
    alarmTypeOption () {
      const items = this.alarmTypeItems.slice().reverse()
      return {
        animationDuration: 500,
        textStyle: { color: TEXT_COLOR },
        grid: { left: 12, right: 28, top: 8, bottom: 18, containLabel: true },
        tooltip: {
          trigger: 'axis',
          axisPointer: { type: 'shadow' },
          backgroundColor: '#171b21',
          borderColor: '#343b45',
          textStyle: { color: TEXT_COLOR }
        },
        xAxis: {
          type: 'value',
          minInterval: 1,
          axisLabel: { color: MUTED_COLOR },
          splitLine: { lineStyle: { color: GRID_COLOR } }
        },
        yAxis: {
          type: 'category',
          data: items.map(item => item.name),
          axisLine: { show: false },
          axisTick: { show: false },
          axisLabel: { color: MUTED_COLOR, width: 90, overflow: 'truncate' }
        },
        series: [{
          type: 'bar',
          barMaxWidth: 18,
          data: items.map(item => ({
            value: item.value,
            itemStyle: {
              color: ALARM_COLORS[item.type] || '#5d91c4',
              borderRadius: [0, 3, 3, 0]
            }
          })),
          label: { show: true, position: 'right', color: TEXT_COLOR }
        }]
      }
    },
    hourlyOption () {
      const hours = Array.from(
        { length: 24 },
        (_, hour) => `${String(hour).padStart(2, '0')}:00`
      )
      return {
        animationDuration: 500,
        textStyle: { color: TEXT_COLOR },
        grid: { left: 18, right: 24, top: 16, bottom: 24, containLabel: true },
        tooltip: {
          trigger: 'axis',
          formatter: params => `${params[0].axisValue}<br/>通行 ${params[0].value} 次`,
          backgroundColor: '#171b21',
          borderColor: '#343b45',
          textStyle: { color: TEXT_COLOR }
        },
        xAxis: {
          type: 'category',
          boundaryGap: false,
          data: hours,
          axisLine: { lineStyle: { color: GRID_COLOR } },
          axisTick: { show: false },
          axisLabel: { color: MUTED_COLOR, interval: 2 }
        },
        yAxis: {
          type: 'value',
          minInterval: 1,
          axisLine: { show: false },
          axisTick: { show: false },
          axisLabel: { color: MUTED_COLOR },
          splitLine: { lineStyle: { color: GRID_COLOR } }
        },
        series: [{
          name: '通行次数',
          type: 'line',
          data: this.hourlyValues,
          smooth: 0.25,
          showSymbol: false,
          symbolSize: 7,
          lineStyle: { color: '#4bc0a2', width: 2 },
          itemStyle: { color: '#4bc0a2' },
          areaStyle: { color: 'rgba(75, 192, 162, 0.12)' }
        }]
      }
    }
  }
}
</script>

<style scoped>
.charts-section { margin: 20px 0; }
.charts-heading {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 10px;
}
.charts-heading h3 { margin: 0; font-size: 15px; }
.charts-heading span,
.chart-title span { color: var(--dark-text-secondary); font-size: 12px; }
.risk-strip {
  min-height: 104px;
  margin-bottom: 12px;
  padding: 18px 20px;
  display: grid;
  grid-template-columns: 180px minmax(240px, 1fr);
  align-items: center;
  gap: 32px;
  border: 1px solid var(--dark-border);
  border-radius: 6px;
  background: var(--dark-card);
}
.risk-summary > span {
  display: block;
  margin-bottom: 5px;
  color: var(--dark-text-secondary);
  font-size: 12px;
}
.risk-summary div { display: flex; align-items: baseline; gap: 10px; }
.risk-summary strong { font-size: 30px; line-height: 1; }
.risk-summary em { font-size: 13px; font-style: normal; font-weight: 600; }
.risk-color-low { color: #43b88d; }
.risk-color-medium { color: #e1aa4d; }
.risk-color-high { color: #ef6461; }
.risk-scale-labels {
  display: grid;
  grid-template-columns: 35fr 25fr 40fr;
  margin-bottom: 8px;
  color: var(--dark-text-secondary);
  font-size: 11px;
}
.risk-scale-labels span:nth-child(2) { text-align: center; }
.risk-scale-labels span:last-child { text-align: right; }
.risk-track {
  position: relative;
  height: 8px;
  display: grid;
  grid-template-columns: 35fr 25fr 40fr;
  gap: 3px;
}
.risk-segment { display: block; height: 8px; border-radius: 2px; }
.risk-segment-low { background: rgba(67, 184, 141, 0.45); }
.risk-segment-medium { background: rgba(225, 170, 77, 0.52); }
.risk-segment-high { background: rgba(239, 100, 97, 0.56); }
.risk-track i {
  position: absolute;
  top: -4px;
  width: 10px;
  height: 16px;
  border: 2px solid #f2f5f8;
  border-radius: 3px;
  background: #11151a;
  box-shadow: 0 0 0 2px rgba(17, 21, 26, 0.7);
  transform: translateX(-50%);
}
.chart-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}
.chart-panel {
  position: relative;
  min-width: 0;
  border: 1px solid var(--dark-border);
  border-radius: 6px;
  background: var(--dark-card);
  overflow: hidden;
}
.chart-panel-wide { grid-column: span 2; }
.chart-title {
  min-height: 44px;
  padding: 0 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  border-bottom: 1px solid var(--dark-border);
}
.chart-title h4 { margin: 0; font-size: 14px; }
.chart-canvas { width: 100%; height: 218px; }
.chart-canvas-wide { height: 250px; }
@media (max-width: 720px) {
  .risk-strip {
    grid-template-columns: minmax(0, 1fr);
    gap: 18px;
  }
  .chart-grid { grid-template-columns: minmax(0, 1fr); }
  .chart-panel-wide { grid-column: span 1; }
  .chart-canvas,
  .chart-canvas-wide { height: 220px; }
  .charts-heading { align-items: center; }
}
</style>
