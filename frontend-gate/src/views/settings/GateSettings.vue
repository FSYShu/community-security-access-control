<template>
  <div class="gate-page settings-page">
    <div class="gate-header">
      <van-icon name="arrow-left" size="20" color="#9ca3af" @click="$router.push('/idle')" />
      <span class="gate-header-title">门禁终端设置</span>
      <span style="width:20px;"></span>
    </div>
    <div class="gate-content">
      <div class="gate-card">
        <div class="setting-section-title">当前绑定</div>
        <div v-if="isBound" class="bound-info">
          <div class="bound-row">
            <span class="bound-label">终端名称</span>
            <span class="bound-value">{{ gateName }}</span>
          </div>
          <div class="bound-row">
            <span class="bound-label">安装位置</span>
            <span class="bound-value">{{ location }}</span>
          </div>
          <div class="bound-row">
            <span class="bound-label">终端层级</span>
            <span class="bound-value">{{ levelMap[gateLevel] || gateLevel }}</span>
          </div>
          <div class="bound-row">
            <span class="bound-label">推流码</span>
            <span class="bound-value bound-push-key">{{ pushKey || '未配置' }}</span>
          </div>
          <button class="gate-btn gate-btn-danger" style="margin-top:12px;" @click="unbindGate">解除绑定</button>
        </div>
        <div v-else class="unbound-hint">
          <van-icon name="info-o" size="24" color="#f59e0b" />
          <p>尚未绑定门禁终端，请选择要绑定的终端</p>
        </div>
      </div>

      <div class="gate-card">
        <div class="setting-section-title">选择门禁终端</div>
        <van-pull-refresh v-model="refreshing" @refresh="onRefresh">
          <van-list v-model="loading" :finished="finished" finished-text="没有更多了" @load="loadData">
            <div v-for="item in list" :key="item.id" class="gate-item" :class="{ 'is-active': String(item.id) === gateId }" @click="bindGate(item)">
              <div class="gate-item-info">
                <div class="gate-item-name">{{ item.gate_name }}</div>
                <div class="gate-item-location">{{ item.location }}</div>
              </div>
              <div class="gate-item-meta">
                <span class="level-tag" :class="'tag-' + item.gate_level">{{ levelMap[item.gate_level] || item.gate_level }}</span>
                <span class="gate-item-status" :class="item.status === 'online' ? 'status-online' : 'status-offline'">{{ item.status === 'online' ? '在线' : '离线' }}</span>
              </div>
            </div>
            <div v-if="list.length === 0 && !loading" class="empty-hint">暂无门禁终端</div>
          </van-list>
        </van-pull-refresh>
      </div>

    </div>
  </div>
</template>

<script>
import { getGateList } from '@/api/gate'

export default {
  name: 'GateSettingsPage',
  data () {
    return {
      list: [],
      loading: false,
      finished: false,
      refreshing: false,
      page: 1,
      levelMap: { community_gate: '社区大门', unit_door: '单元门', dangerous_area: '危险防护区域' }
    }
  },
  beforeDestroy () {
    this.$store.commit('user/CLEAR_USER')
  },
  computed: {
    isBound () { return this.$store.getters['gate/isBound'] },
    gateId () { return this.$store.getters['gate/gateId'] },
    gateName () { return this.$store.getters['gate/gateName'] },
    pushKey () { return this.$store.getters['gate/pushKey'] },
    gateLevel () { return this.$store.getters['gate/gateLevel'] },
    location () { return this.$store.getters['gate/location'] },
    isLoggedIn () { return !!this.$store.getters['user/token'] },
    userInfo () { return this.$store.getters['user/userInfo'] }
  },
  methods: {
    async loadData () {
      try {
        var res = await getGateList({ page: this.page, per_page: 50 })
        var data = res.data
        if (data && data.items) {
          if (this.page === 1) {
            this.list = data.items
          } else {
            this.list = this.list.concat(data.items)
          }
          this.finished = this.list.length >= data.total
          this.page++
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
    onRefresh () {
      this.page = 1
      this.finished = false
      this.list = []
      this.loading = true
      this.loadData()
    },
    bindGate (item) {
      this.$store.commit('gate/SET_GATE', item)
      this.$toast.success('已绑定：' + item.gate_name)
    },
    unbindGate () {
      this.$store.commit('gate/CLEAR_GATE')
      this.$toast.success('已解除绑定')
    },
    async doLogout () {
      await this.$store.dispatch('user/logoutAction')
      this.$toast.success('已退出登录')
    }
  }
}
</script>

<style scoped>
.setting-section-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--gate-text-secondary);
  margin-bottom: 12px;
  text-transform: uppercase;
  letter-spacing: 1px;
}
.bound-info {
  padding: 4px 0;
}
.bound-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 0;
}
.bound-label {
  font-size: 13px;
  color: var(--gate-text-muted);
}
.bound-value {
  font-size: 14px;
  color: var(--gate-text);
}
.bound-push-key {
  font-family: monospace;
  font-size: 12px;
  word-break: break-all;
  max-width: 200px;
  text-align: right;
}
.unbound-hint {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 0;
  color: var(--gate-text-secondary);
  font-size: 14px;
}
.gate-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  margin-bottom: 8px;
  border-radius: var(--gate-radius-sm);
  border: 1px solid var(--gate-border);
  cursor: pointer;
  transition: border-color 0.2s;
}
.gate-item:active {
  opacity: 0.8;
}
.gate-item.is-active {
  border-color: var(--gate-accent);
  background: rgba(99, 102, 241, 0.08);
}
.gate-item-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--gate-text);
}
.gate-item-location {
  font-size: 12px;
  color: var(--gate-text-muted);
  margin-top: 2px;
}
.gate-item-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
}
.level-tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
}
.tag-community_gate {
  background: rgba(16, 185, 129, 0.15);
  color: #10b981;
}
.tag-unit_door {
  background: rgba(99, 102, 241, 0.15);
  color: #818cf8;
}
.tag-dangerous_area {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
}
.gate-item-status {
  font-size: 11px;
}
.status-online {
  color: var(--gate-success);
}
.status-offline {
  color: var(--gate-text-muted);
}
.admin-info {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.admin-name {
  font-size: 14px;
  color: var(--gate-text);
}
.empty-hint {
  text-align: center;
  padding: 24px 0;
  color: var(--gate-text-muted);
  font-size: 14px;
}
</style>