<template>
  <app-layout page-title="AI安防日报">
    <section class="workflow-strip">
      <div>
        <strong>自动日报</strong>
        <span v-if="workflowStatus && workflowStatus.auto_enabled">
          每天 {{ workflowStatus.generate_time }} 生成前一天日报
        </span>
        <span v-else>当前未开启自动生成</span>
      </div>
      <span class="workflow-state" :class="{ active: workflowStatus && workflowStatus.ai_enabled && workflowStatus.ai_configured }">
        {{ workflowStateLabel }}
      </span>
    </section>

    <section class="filter-panel">
      <van-cell-group>
        <van-field v-model="startDate" label="开始日期" placeholder="YYYY-MM-DD" />
        <van-field v-model="endDate" label="结束日期" placeholder="YYYY-MM-DD" />
      </van-cell-group>
      <div class="actions">
        <van-button type="primary" size="small" @click="onSearch">查询</van-button>
        <van-button icon="description" size="small" @click="showGenerate = true">AI生成日报</van-button>
        <van-button icon="setting-o" size="small" @click="openApiConfig">API配置</van-button>
      </div>
    </section>

    <section class="report-list">
      <van-list v-model="loading" :finished="finished" finished-text="没有更多日报" @load="loadData">
        <van-cell v-for="item in reportList" :key="item.id" is-link @click="goDetail(item)">
          <template #title>
            <div class="report-title">
              <strong>{{ item.report_date }}</strong>
              <span class="risk-tag" :class="`risk-${item.risk_level || 'low'}`">
                {{ riskLabel(item.risk_level) }}风险
              </span>
            </div>
          </template>
          <template #label>
            <div>{{ sourceLabel(item.workflow_source) }} · {{ statusLabel(item.generate_status) }}</div>
          </template>
        </van-cell>
      </van-list>
    </section>

    <van-dialog v-model="showGenerate" title="生成AI安防日报" show-cancel-button @confirm="onGenerate">
      <van-field v-model="generateDate" label="日期" placeholder="YYYY-MM-DD" />
    </van-dialog>

    <van-dialog
      v-model="showApiConfig"
      title="配置硅基流动API"
      show-cancel-button
      :before-close="beforeApiConfigClose"
      :confirm-button-loading="savingApiKey"
    >
      <van-field
        v-model.trim="apiKey"
        type="password"
        label="API密钥"
        :placeholder="apiKeyPlaceholder"
        clearable
        autocomplete="new-password"
      />
    </van-dialog>
  </app-layout>
</template>

<script>
import {
  getReportList,
  generateReport,
  getReportWorkflowStatus,
  saveReportApiKey
} from '@/api/property'

export default {
  name: 'ReportListPage',
  data () {
    return {
      reportList: [],
      workflowStatus: null,
      loading: false,
      finished: false,
      page: 1,
      startDate: '',
      endDate: '',
      showGenerate: false,
      generateDate: '',
      showApiConfig: false,
      savingApiKey: false,
      apiKey: ''
    }
  },
  computed: {
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
    this.loadWorkflowStatus()
  },
  methods: {
    async loadWorkflowStatus () {
      try {
        const res = await getReportWorkflowStatus()
        if (res.code === 0) this.workflowStatus = res.data
      } catch (e) {}
    },
    async loadData () {
      try {
        const params = { page: this.page, per_page: 20 }
        if (this.startDate) params.start_date = this.startDate
        if (this.endDate) params.end_date = this.endDate
        const res = await getReportList(params)
        if (res.code === 0 && res.data) {
          const items = res.data.items || []
          this.reportList = this.page === 1 ? items : this.reportList.concat(items)
          this.finished = this.reportList.length >= res.data.total
          this.page++
        }
      } catch (e) {
        this.finished = true
      } finally {
        this.loading = false
      }
    },
    onSearch () {
      this.page = 1
      this.finished = false
      this.reportList = []
      this.loadData()
    },
    goDetail (item) {
      this.$router.push(`/report/detail/${item.id}`)
    },
    openApiConfig () {
      this.apiKey = ''
      this.showApiConfig = true
    },
    beforeApiConfigClose (action, done) {
      if (action !== 'confirm') {
        this.apiKey = ''
        done()
        return
      }
      this.saveApiConfig(done)
    },
    async saveApiConfig (done) {
      const apiKey = this.apiKey.trim()
      if (!apiKey) {
        this.$message.warning('请输入硅基流动 API 密钥')
        done(false)
        return
      }
      this.savingApiKey = true
      try {
        await saveReportApiKey(apiKey)
        this.apiKey = ''
        await this.loadWorkflowStatus()
        this.$message.success('API 密钥保存成功，现在可以生成 AI 日报')
        done()
      } catch (e) {
        if (!e.__messageShown) this.$message.error(e.message || 'API 密钥保存失败')
        done(false)
      } finally {
        this.savingApiKey = false
      }
    },
    async onGenerate () {
      if (!/^\d{4}-\d{2}-\d{2}$/.test(this.generateDate)) {
        return this.$message.warning('请输入正确日期')
      }
      const existing = this.reportList.find(item => item.report_date === this.generateDate)
      if (existing) {
        this.$message.warning('该日期日报已存在，已打开日报详情')
        this.goDetail(existing)
        return
      }
      try {
        const res = await generateReport({ report_date: this.generateDate })
        if (res.code !== 0) throw new Error(res.message)
        this.$message.success('AI安防日报生成成功')
        this.onSearch()
      } catch (e) {
        if (!e.__messageShown) this.$message.error(e.message || '生成失败')
      }
    },
    riskLabel (level) {
      return { low: '低', medium: '中', high: '高' }[level] || '低'
    },
    sourceLabel (source) {
      if (source === 'siliconflow') return '硅基流动生成'
      if (source === 'ollama') return '历史Ollama生成'
      return source === 'ai_service' ? 'AI生成' : '本地智能分析'
    },
    statusLabel (status) {
      return status === 'generated' ? '已完成' : '生成中'
    },
    formatDate (date) {
      const year = date.getFullYear()
      const month = String(date.getMonth() + 1).padStart(2, '0')
      const day = String(date.getDate()).padStart(2, '0')
      return `${year}-${month}-${day}`
    }
  }
}
</script>

<style scoped>
.workflow-strip,
.filter-panel,
.report-list {
  border: 1px solid var(--dark-border);
  background: var(--dark-card);
  margin-bottom: 16px;
}
.workflow-strip {
  min-height: 64px;
  padding: 14px 18px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}
.workflow-strip strong,
.workflow-strip span {
  display: block;
}
.workflow-strip div > span {
  margin-top: 4px;
  color: var(--dark-text-secondary);
  font-size: 12px;
}
.workflow-state {
  color: #aeb6c2;
  white-space: nowrap;
}
.workflow-state.active { color: #38c78f; }
.filter-panel { padding: 12px; }
.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
}
.report-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.risk-tag {
  padding: 2px 7px;
  border: 1px solid currentColor;
  font-size: 11px;
  line-height: 18px;
}
.risk-low { color: #38c78f; }
.risk-medium { color: #e8a84e; }
.risk-high { color: #ef5b5b; }
</style>
