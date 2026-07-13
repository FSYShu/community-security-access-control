<template>
  <app-layout page-title="禁区入侵检测">
    <div class="danger-zone-page">
      <div class="dz-header">
        <div class="dz-title">禁区管理</div>
        <div class="empty-hint">
          <i class="el-icon-info"></i>
          <span>禁区由门禁管理中"危险防护区域"类型的终端自动创建</span>
        </div>
      </div>

      <div class="dz-content">
        <van-pull-refresh v-model="refreshing" @refresh="onRefresh">
          <van-list v-model="loading" :finished="finished" finished-text="没有更多了" @load="loadZones">
            <div v-for="zone in zoneList" :key="zone.id" class="zone-card dark-card">
              <div class="zone-card-header">
                <div class="zone-info">
                  <span class="zone-name">{{ zone.zone_name }}</span>
                  <span class="zone-level" :class="'level-' + zone.alarm_level">
                    {{ levelMap[zone.alarm_level] || zone.alarm_level }}告警级别
                  </span>
                </div>
                <div class="zone-actions">
                  <button class="edit-btn" @click="openEditDialog(zone)">
                    <i class="el-icon-edit"></i>
                    <span>编辑</span>
                  </button>
                  <button class="toggle-btn" :class="zone.status === 'active' ? 'toggle-disable' : 'toggle-enable'" @click="toggleZoneStatus(zone)">
                    {{ zone.status === 'active' ? '停用' : '启用' }}
                  </button>
                </div>
              </div>
              <div class="zone-card-body">
                <span class="detail-item">
                  <span class="detail-label">关联摄像头</span>
                  <span class="detail-value">{{ zone.camera_names || zone.camera_ids }}</span>
                </span>
                <span class="detail-item">
                  <span class="detail-label">安全距离(近大远小)</span>
                  <span class="detail-value">{{ zone.safety_distance }}米</span>
                </span>
                <span class="detail-item">
                  <span class="detail-label">滞留告警</span>
                  <span class="detail-value">{{ zone.stay_duration }}秒</span>
                </span>
              </div>
            </div>
          </van-list>
        </van-pull-refresh>
      </div>

      <el-dialog :visible.sync="showFormDialog" title="编辑禁区" width="480px" :close-on-click-modal="false" append-to-body custom-class="dark-dialog" @close="resetForm">
        <div class="form-grid">
          <div class="form-item">
            <label class="form-label">禁区名称 <span class="form-required">*</span></label>
            <input v-model="formData.zone_name" class="form-input" placeholder="请输入禁区名称" />
          </div>
          <div class="form-item">
            <label class="form-label">安全距离(米) <span class="form-required">*</span></label>
            <input v-model.number="formData.safety_distance" class="form-input" type="number" step="0.5" min="0.5" max="50" />
            <span class="form-hint">基于近大远小原理，人体在画面中越大距离越近</span>
          </div>
          <div class="form-item">
            <label class="form-label">滞留告警时长(秒) <span class="form-required">*</span></label>
            <input v-model.number="formData.stay_duration" class="form-input" type="number" step="5" min="1" max="300" />
          </div>
          <div class="form-item">
            <label class="form-label">告警级别</label>
            <div class="filter-select" :class="{ 'is-open': showLevelDropdown }">
              <div class="select-trigger" @click="showLevelDropdown = !showLevelDropdown">
                <span class="select-value">{{ levelMap[formData.alarm_level] || '请选择' }}</span>
                <i class="el-icon-arrow-down select-arrow" :class="{ 'is-reverse': showLevelDropdown }"></i>
              </div>
              <transition name="dropdown">
                <div v-if="showLevelDropdown" class="select-dropdown">
                  <div class="select-option" :class="{ 'is-active': formData.alarm_level === 'low' }" @click="formData.alarm_level = 'low'; showLevelDropdown = false">低</div>
                  <div class="select-option" :class="{ 'is-active': formData.alarm_level === 'medium' }" @click="formData.alarm_level = 'medium'; showLevelDropdown = false">中</div>
                  <div class="select-option" :class="{ 'is-active': formData.alarm_level === 'high' }" @click="formData.alarm_level = 'high'; showLevelDropdown = false">高</div>
                </div>
              </transition>
            </div>
          </div>
        </div>
        <div class="form-footer">
          <button class="form-btn form-btn-cancel" @click="showFormDialog = false">取消</button>
          <button class="form-btn form-btn-primary" @click="submitForm">确认</button>
        </div>
      </el-dialog>
    </div>
  </app-layout>
</template>

<script>
import { getDangerZoneList, updateDangerZone } from '@/api/dangerZone'

export default {
  name: 'DangerZonePage',
  data () {
    return {
      zoneList: [],
      loading: false,
      finished: false,
      refreshing: false,
      showFormDialog: false,
      editingZone: null,
      showLevelDropdown: false,
      formData: {
        zone_name: '',
        safety_distance: 2.0,
        stay_duration: 30,
        alarm_level: 'high'
      },
      levelMap: { low: '低', medium: '中', high: '高' }
    }
  },
  mounted () {
    document.addEventListener('click', this.closeDropdowns)
  },
  beforeDestroy () {
    document.removeEventListener('click', this.closeDropdowns)
  },
  methods: {
    closeDropdowns (e) {
      if (!e.target.closest('.filter-select')) {
        this.showLevelDropdown = false
      }
    },
    async loadZones () {
      try {
        const res = await getDangerZoneList()
        if (res.code === 0 && res.data) {
          this.zoneList = res.data || []
        }
        this.finished = true
      } catch (e) {
        console.error('Failed to load zones:', e)
        this.finished = true
      } finally {
        this.loading = false
      }
    },
    onRefresh () {
      this.finished = false
      this.loading = true
      this.loadZones().then(function () {
        this.refreshing = false
      }.bind(this))
    },
    openEditDialog (zone) {
      this.editingZone = zone
      this.formData = {
        zone_name: zone.zone_name,
        safety_distance: zone.safety_distance,
        stay_duration: zone.stay_duration,
        alarm_level: zone.alarm_level || 'high'
      }
      this.showLevelDropdown = false
      this.showFormDialog = true
    },
    async submitForm () {
      if (!this.formData.zone_name) {
        this.$message.warning('请输入禁区名称')
        return
      }
      const submitData = {
        zone_name: this.formData.zone_name,
        safety_distance: this.formData.safety_distance,
        stay_duration: this.formData.stay_duration,
        alarm_level: this.formData.alarm_level
      }
      try {
        const res = await updateDangerZone(this.editingZone.id, submitData)
        if (res.code === 0) {
          this.$message.success('更新成功')
          this.showFormDialog = false
          this.onRefresh()
        }
      } catch (e) {
        console.error('Submit failed:', e)
      }
    },
    resetForm () {
      this.editingZone = null
      this.showLevelDropdown = false
    },
    async toggleZoneStatus (zone) {
      const newStatus = zone.status === 'active' ? 'inactive' : 'active'
      try {
        const res = await updateDangerZone(zone.id, { status: newStatus })
        if (res.code === 0) {
          this.$message.success(newStatus === 'active' ? '已启用' : '已停用')
          this.onRefresh()
        }
      } catch (e) {
        console.error('Toggle failed:', e)
      }
    }
  }
}
</script>

<style scoped>
.danger-zone-page {
  height: calc(100vh - 120px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.dz-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  gap: 12px;
}

.dz-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--dark-text);
  white-space: nowrap;
  line-height: 20px;
}

.empty-hint {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--dark-text-muted);
  line-height: 20px;
}

.empty-hint i {
  font-size: 14px;
  vertical-align: middle;
}

.dz-content {
  flex: 1;
  overflow-y: auto;
}

.zone-card {
  margin-bottom: 12px;
  padding: 16px;
}

.zone-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.zone-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.zone-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--dark-text);
}

.zone-level {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 500;
}

.level-low {
  background: rgba(59, 130, 246, 0.12);
  color: var(--dark-info);
}

.level-medium {
  background: rgba(251, 191, 36, 0.12);
  color: var(--dark-warning);
}

.level-high {
  background: rgba(239, 68, 68, 0.12);
  color: var(--dark-danger);
}

.zone-actions {
  display: flex;
  align-items: center;
  gap: 6px;
}

.edit-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 0 10px;
  height: 28px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--dark-border-field);
  border-radius: 6px;
  color: var(--dark-text-secondary);
  font-size: 13px;
  cursor: pointer;
  transition: background 0.2s, color 0.2s, border-color 0.2s;
}

.edit-btn:hover {
  background: rgba(99, 102, 241, 0.1);
  border-color: var(--dark-accent-light);
  color: var(--dark-accent-light);
}

.toggle-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0 10px;
  height: 28px;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  border: 1px solid;
  transition: background 0.2s, color 0.2s, border-color 0.2s;
}

.toggle-disable {
  background: rgba(239, 68, 68, 0.08);
  border-color: rgba(239, 68, 68, 0.3);
  color: #ef4444;
}

.toggle-disable:hover {
  background: rgba(239, 68, 68, 0.15);
}

.toggle-enable {
  background: rgba(16, 185, 129, 0.08);
  border-color: rgba(16, 185, 129, 0.3);
  color: var(--dark-success);
}

.toggle-enable:hover {
  background: rgba(16, 185, 129, 0.15);
}

.zone-card-body {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.detail-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
}

.detail-label {
  color: var(--dark-text-secondary);
}

.detail-value {
  color: var(--dark-text);
}

.form-grid {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-label {
  font-size: 13px;
  color: var(--dark-text-secondary);
  font-weight: 500;
}

.form-required {
  color: var(--dark-danger);
}

.form-input {
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  color: var(--dark-text);
  font-size: 13px;
  outline: none;
  transition: border-color 0.2s;
}

.form-input::placeholder {
  color: var(--dark-text-muted);
}

.form-input:focus {
  border-color: var(--dark-accent-light);
}

.form-hint {
  font-size: 11px;
  color: var(--dark-text-muted);
  line-height: 1.4;
}

.filter-select {
  position: relative;
}

.select-trigger {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  cursor: pointer;
  transition: border-color 0.2s;
}

.filter-select.is-open .select-trigger {
  border-color: var(--dark-accent);
}

.select-value {
  font-size: 13px;
  color: var(--dark-text);
  white-space: nowrap;
}

.select-arrow {
  font-size: 12px;
  color: var(--dark-text-secondary);
  transition: transform 0.2s;
  margin-left: 6px;
}

.select-arrow.is-reverse {
  transform: rotate(180deg);
}

.select-dropdown {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  right: 0;
  background: var(--dark-bg-secondary);
  border: 1px solid var(--dark-border-field);
  border-radius: 8px;
  padding: 4px 0;
  z-index: 100;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
}

.select-option {
  padding: 8px 12px;
  font-size: 13px;
  color: var(--dark-text-secondary);
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}

.select-option:hover {
  background: rgba(255, 255, 255, 0.06);
  color: var(--dark-text);
}

.select-option.is-active {
  color: var(--dark-accent-light);
  background: rgba(99, 102, 241, 0.1);
}

.dropdown-enter-active,
.dropdown-leave-active {
  transition: opacity 0.2s, transform 0.2s;
}

.dropdown-enter,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

.form-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.form-btn {
  padding: 8px 20px;
  border-radius: 8px;
  font-size: 13px;
  cursor: pointer;
  border: none;
  transition: background 0.2s;
}

.form-btn-cancel {
  background: rgba(255, 255, 255, 0.06);
  color: var(--dark-text);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.form-btn-cancel:hover {
  background: rgba(255, 255, 255, 0.1);
}

.form-btn-primary {
  background: var(--dark-accent);
  color: #fff;
}

.form-btn-primary:hover {
  background: var(--dark-accent-light);
}
</style>

<style>
.dark-dialog {
  background: #0A0A0A !important;
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 16px;
}

.dark-dialog .el-dialog__header {
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  padding: 16px 20px;
}

.dark-dialog .el-dialog__title {
  color: #EDEDEF;
  font-weight: 600;
}

.dark-dialog .el-dialog__headerbtn .el-dialog__close {
  color: #8A8F98;
}

.dark-dialog .el-dialog__body {
  padding: 20px;
}
</style>
