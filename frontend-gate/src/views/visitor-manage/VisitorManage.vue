<template>
  <div class="gate-page">
    <div class="gate-header">
      <i class="el-icon-arrow-left" style="font-size:20px;color:#9ca3af" @click="$router.push('/idle')"></i>
      <span class="gate-header-title">访客申请管理</span>
      <span style="width:20px;"></span>
    </div>
    <div class="gate-content">
      <div class="filter-bar">
        <button
          v-for="f in statusFilters"
          :key="f.value"
          class="filter-btn"
          :class="{ 'is-active': currentStatus === f.value }"
          @click="currentStatus = f.value"
        >{{ f.label }}</button>
      </div>

      <van-pull-refresh v-model="refreshing" @refresh="onRefresh">
        <van-list
          v-model="loading"
          :finished="finished"
          finished-text="没有更多了"
          @load="loadMore"
        >
          <div v-if="list.length === 0 && !loading" class="empty-hint">
            <i class="el-icon-document" style="font-size:40px;color:var(--gate-text-dim)"></i>
            <p>暂无访客申请记录</p>
          </div>
          <div v-for="item in list" :key="item.id" class="visitor-card">
            <div class="visitor-card-header">
              <span class="visitor-name">{{ item.visitor_name || '未知访客' }}</span>
              <span class="visitor-status" :class="'status-' + item.approval_status">{{ statusMap[item.approval_status] || item.approval_status }}</span>
            </div>
            <div v-if="item.visitor_face_image_path" class="visitor-face-wrap">
              <img :src="formatFaceImage(item.visitor_face_image_path)" class="visitor-face-img" />
            </div>
            <div class="visitor-card-body">
              <div class="visitor-info-row">
                <span class="visitor-info-label">申请层级</span>
                <span class="visitor-info-value">{{ formatLevels(item.apply_gate_levels) }}</span>
              </div>
              <div class="visitor-info-row">
                <span class="visitor-info-label">申请来源</span>
                <span class="visitor-info-value">{{ formatSource(item.apply_source) }}</span>
              </div>
              <div class="visitor-info-row">
                <span class="visitor-info-label">申请时间</span>
                <span class="visitor-info-value">{{ formatTime(item.apply_time) }}</span>
              </div>
              <div v-if="item.approval_time" class="visitor-info-row">
                <span class="visitor-info-label">审批时间</span>
                <span class="visitor-info-value">{{ formatTime(item.approval_time) }}</span>
              </div>
            </div>
            <div class="visitor-card-footer">
              <button v-if="item.approval_status === 'pending'" class="gate-btn gate-btn-success visitor-action-btn" @click="doApprove(item, 'approved')">确认</button>
              <button v-if="item.approval_status === 'pending'" class="gate-btn gate-btn-danger visitor-action-btn" @click="doApprove(item, 'rejected')">拒绝</button>
              <button class="gate-btn gate-btn-outline visitor-action-btn" @click="doDelete(item)">删除</button>
            </div>
          </div>
        </van-list>
      </van-pull-refresh>
    </div>
  </div>
</template>

<script>
import { gateGetVisitorAuthList, gateApproveVisitorAuth, gateDeleteVisitorAuth } from '@/api/visitorAuth'

export default {
  name: 'VisitorManagePage',
  data () {
    return {
      list: [],
      loading: false,
      refreshing: false,
      finished: false,
      page: 1,
      perPage: 20,
      currentStatus: '',
      statusFilters: [
        { label: '全部', value: '' },
        { label: '待处理', value: 'pending' },
        { label: '已确认', value: 'approved' },
        { label: '已拒绝', value: 'rejected' }
      ],
      statusMap: {
        pending: '待处理',
        approved: '已确认',
        rejected: '已拒绝'
      },
      sourceTypeMap: {
        gate_terminal: '门禁终端',
        gate_web: '门禁网页'

      }
    }
  },
  computed: {
    gateId () { return this.$store.getters['gate/gateId'] || '' },
    gateName () { return this.$store.getters['gate/gateName'] || '' },
    pushKey () { return this.$store.getters['gate/pushKey'] || '' }
  },
  watch: {
    currentStatus () {
      this.list = []
      this.page = 1
      this.finished = false
      this.loading = true
      this.fetchList()
    }
  },
  methods: {
    async fetchList () {
      try {
        var params = {
          page: this.page,
          per_page: this.perPage,
          gate_id: this.gateId,
          push_key: this.pushKey
        }
        if (this.currentStatus) {
          params.status = this.currentStatus
        }
        var res = await gateGetVisitorAuthList(params)
        var data = res.data
        if (data && data.items) {
          if (this.page === 1) {
            this.list = data.items
          } else {
            this.list = this.list.concat(data.items)
          }
          this.finished = this.list.length >= data.total
        } else {
          this.finished = true
        }
      } catch (err) {
        this.finished = true
      } finally {
        this.loading = false
        this.refreshing = false
      }
    },
    loadMore () {
      this.fetchList()
    },
    onRefresh () {
      this.page = 1
      this.finished = false
      this.fetchList()
    },
    formatFaceImage (path) {
      if (!path) return ''
      if (path.startsWith('data:')) return path
      return 'data:image/jpeg;base64,' + path
    },
    formatSource (str) {
      if (!str) return '-'
      var parts = str.split('|')
      var name = parts[1] || ''
      if (!name && parts[0] === 'gate_terminal' && this.gateName) {
        name = this.gateName
      }
      if (name) return name
      return this.sourceTypeMap[parts[0]] || parts[0]
    },
    formatLevels (str) {
      if (!str) return '-'
      var arr = str
      if (typeof str === 'string') {
        try {
          arr = JSON.parse(str)
          if (typeof arr === 'string') {
            arr = JSON.parse(arr)
          }
        } catch (e) {
          return str
        }
      }
      if (!Array.isArray(arr)) return str
      return arr.filter(function (l) { return l !== 'entrance_door' }).join('、')
    },
    formatTime (str) {
      if (!str) return '-'
      try {
        var s = str.endsWith('Z') ? str : str + 'Z'
        var d = new Date(s)
        var utc8 = new Date(d.getTime() + 8 * 3600000)
        var y = utc8.getUTCFullYear()
        var m = String(utc8.getUTCMonth() + 1).padStart(2, '0')
        var day = String(utc8.getUTCDate()).padStart(2, '0')
        var h = String(utc8.getUTCHours()).padStart(2, '0')
        var min = String(utc8.getUTCMinutes()).padStart(2, '0')
        return y + '-' + m + '-' + day + ' ' + h + ':' + min
      } catch (e) {
        return str
      }
    },
    async doApprove (item, status) {
      try {
        await gateApproveVisitorAuth(item.id, {
          approval_status: status,
          gate_id: this.gateId,
          push_key: this.pushKey
        })
        item.approval_status = status
        this.$toast.success(status === 'approved' ? '已确认' : '已拒绝')
      } catch (err) {
        this.$toast.fail('操作失败')
      }
    },
    async doDelete (item) {
      try {
        await gateDeleteVisitorAuth(item.id, {
          gate_id: this.gateId,
          push_key: this.pushKey
        })
        var idx = this.list.indexOf(item)
        if (idx > -1) this.list.splice(idx, 1)
        this.$toast.success('已删除')
      } catch (err) {
        this.$toast.fail('删除失败')
      }
    }
  }
}
</script>

<style scoped>
.gate-content {
  width: 100%;
  max-width: 480px;
  margin: 0 auto;
}
.filter-bar {
  display: flex;
  justify-content: center;
  gap: 8px;
  margin-bottom: 16px;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}
.filter-btn {
  padding: 6px 16px;
  border-radius: 20px;
  border: 1px solid var(--gate-border-field);
  background: transparent;
  color: var(--gate-text-secondary);
  font-size: 13px;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.2s;
}
.filter-btn.is-active {
  background: var(--gate-accent);
  border-color: var(--gate-accent);
  color: #fff;
}
.empty-hint {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 60px 0;
  color: var(--gate-text-muted);
  font-size: 14px;
}
.visitor-card {
  background: var(--gate-bg-card);
  border: 1px solid var(--gate-border);
  border-radius: var(--gate-radius);
  padding: 16px;
  margin-bottom: 12px;
}
.visitor-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.visitor-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--gate-text);
}
.visitor-status {
  font-size: 12px;
  padding: 2px 10px;
  border-radius: 10px;
  font-weight: 500;
}
.status-pending {
  background: rgba(251, 191, 36, 0.15);
  color: var(--gate-warning);
}
.status-approved {
  background: rgba(16, 185, 129, 0.15);
  color: var(--gate-success);
}
.status-rejected {
  background: rgba(239, 68, 68, 0.15);
  color: var(--gate-danger);
}
.visitor-face-wrap {
  margin-bottom: 12px;
  border-radius: var(--gate-radius-sm, 8px);
  overflow: hidden;
  background: #000;
}
.visitor-face-img {
  display: block;
  width: 100%;
  max-height: 200px;
  object-fit: contain;
  border-radius: var(--gate-radius-sm, 8px);
}
.visitor-card-body {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.visitor-info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.visitor-info-label {
  font-size: 13px;
  color: var(--gate-text-muted);
}
.visitor-info-value {
  font-size: 13px;
  color: var(--gate-text-secondary);
  text-align: right;
  max-width: 60%;
  word-break: break-all;
}
.visitor-card-footer {
  display: flex;
  gap: 10px;
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px solid var(--gate-border);
}
.visitor-action-btn {
  flex: 1;
  padding: 10px 0;
  font-size: 14px;
}
</style>
