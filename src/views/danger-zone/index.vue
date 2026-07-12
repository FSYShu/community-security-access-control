<template>
  <app-layout page-title="禁区入侵检测">
    <div class="danger-zone-page">
      <div class="dz-header">
        <div class="dz-title">禁区管理</div>
        <button class="action-btn add-btn" @click="openAddDialog">
          <i class="el-icon-plus"></i>
          <span>新增禁区</span>
        </button>
      </div>

      <div class="dz-content">
        <van-pull-refresh v-model="refreshing" @refresh="onRefresh">
          <van-list v-model="loading" :finished="finished" finished-text="没有更多了" @load="loadZones">
            <div v-for="zone in zoneList" :key="zone.id" class="zone-card dark-card">
              <div class="zone-card-header">
                <div class="zone-info">
                  <span class="zone-name">{{ zone.zone_name }}</span>
                  <span class="zone-status" :class="zone.status === 'active' ? 'status-active' : 'status-inactive'">
                    {{ zone.status === 'active' ? '启用' : '停用' }}
                  </span>
                  <span class="zone-level" :class="'level-' + zone.alarm_level">
                    {{ levelMap[zone.alarm_level] || zone.alarm_level }}
                  </span>
                </div>
                <div class="zone-actions">
                  <button class="action-sm edit-btn" @click="openEditDialog(zone)">
                    <i class="el-icon-edit"></i>
                  </button>
                  <button class="action-sm del-btn" @click="onDeleteZone(zone)">
                    <i class="el-icon-delete"></i>
                  </button>
                </div>
              </div>
              <div class="zone-card-body">
                <div class="zone-detail-row">
                  <span class="detail-label">关联摄像头</span>
                  <span class="detail-value">{{ zone.camera_names || zone.camera_ids }}</span>
                </div>
                <div class="zone-detail-row">
                  <span class="detail-label">安全距离</span>
                  <span class="detail-value">{{ zone.safety_distance }}米</span>
                </div>
                <div class="zone-detail-row">
                  <span class="detail-label">滞留告警</span>
                  <span class="detail-value">{{ zone.stay_duration }}秒</span>
                </div>
              </div>
            </div>
          </van-list>
          <div v-if="!loading && zoneList.length === 0" class="empty-state">
            <i class="el-icon-warning-outline empty-icon"></i>
            <p>暂无禁区，请在门禁管理中添加"危险防护区域"类型的门禁终端</p>
          </div>
        </van-pull-refresh>
      </div>

      <el-dialog :visible.sync="showFormDialog" :title="formMode === 'add' ? '新增禁区' : '编辑禁区'" width="480px" :close-on-click-modal="false" append-to-body custom-class="dark-dialog" @close="resetForm">
        <div class="form-grid">
          <div class="form-item">
            <label class="form-label">禁区名称 <span class="required">*</span></label>
            <el-input v-model="formData.zone_name" placeholder="请输入禁区名称" size="small" />
          </div>
          <div class="form-item">
            <label class="form-label">关联摄像头 <span class="required">*</span></label>
            <el-select v-model="formData.camera_ids" placeholder="请选择摄像头" size="small" multiple>
              <el-option v-for="cam in cameraList" :key="cam.gate_id" :label="cam.gate_name" :value="cam.gate_id" />
            </el-select>
          </div>
          <div class="form-item">
            <label class="form-label">安全距离(米) <span class="required">*</span></label>
            <el-input-number v-model="formData.safety_distance" :min="0.5" :max="50" :step="0.5" size="small" />
          </div>
          <div class="form-item">
            <label class="form-label">滞留告警时长(秒) <span class="required">*</span></label>
            <el-input-number v-model="formData.stay_duration" :min="1" :max="300" :step="5" size="small" />
          </div>
          <div class="form-item">
            <label class="form-label">告警级别</label>
            <el-select v-model="formData.alarm_level" size="small">
              <el-option label="低" value="low" />
              <el-option label="中" value="medium" />
              <el-option label="高" value="high" />
            </el-select>
          </div>
          <div class="form-item">
            <label class="form-label">状态</label>
            <el-select v-model="formData.status" size="small">
              <el-option label="启用" value="active" />
              <el-option label="停用" value="inactive" />
            </el-select>
          </div>
        </div>
        <div slot="footer">
          <el-button size="small" @click="showFormDialog = false">取消</el-button>
          <el-button size="small" type="primary" @click="submitForm">确定</el-button>
        </div>
      </el-dialog>
    </div>
  </app-layout>
</template>

<script>
import { getDangerZoneList, addDangerZone, updateDangerZone, deleteDangerZone, getAvailableCameras } from '@/api/dangerZone'

export default {
  name: 'DangerZonePage',
  data () {
    return {
      zoneList: [],
      loading: false,
      finished: false,
      refreshing: false,
      cameraList: [],
      showFormDialog: false,
      formMode: 'add',
      editingZone: null,
      formData: {
        zone_name: '',
        camera_ids: [],
        safety_distance: 2.0,
        stay_duration: 30,
        alarm_level: 'high',
        status: 'active'
      },
      levelMap: { low: '低', medium: '中', high: '高' }
    }
  },
  created () {
    this.fetchCameras()
  },
  methods: {
    async fetchCameras () {
      try {
        const res = await getAvailableCameras()
        if (res.code === 0 && res.data) {
          this.cameraList = res.data || []
        }
      } catch (e) {
        console.error('Failed to fetch cameras:', e)
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
    openAddDialog () {
      this.formMode = 'add'
      this.editingZone = null
      this.formData = {
        zone_name: '',
        camera_ids: [],
        safety_distance: 2.0,
        stay_duration: 30,
        alarm_level: 'high',
        status: 'active'
      }
      this.showFormDialog = true
    },
    openEditDialog (zone) {
      this.formMode = 'edit'
      this.editingZone = zone
      const cameraIds = zone.camera_ids ? zone.camera_ids.split(',').map(function (s) { return parseInt(s.trim()) }).filter(function (n) { return !isNaN(n) }) : []
      this.formData = {
        zone_name: zone.zone_name,
        camera_ids: cameraIds,
        safety_distance: zone.safety_distance,
        stay_duration: zone.stay_duration,
        alarm_level: zone.alarm_level || 'high',
        status: zone.status
      }
      this.showFormDialog = true
    },
    async submitForm () {
      if (!this.formData.zone_name) {
        this.$message.warning('请输入禁区名称')
        return
      }
      if (!this.formData.camera_ids || this.formData.camera_ids.length === 0) {
        this.$message.warning('请选择至少一个摄像头')
        return
      }
      const submitData = {
        zone_name: this.formData.zone_name,
        camera_ids: this.formData.camera_ids.join(','),
        safety_distance: this.formData.safety_distance,
        stay_duration: this.formData.stay_duration,
        alarm_level: this.formData.alarm_level,
        status: this.formData.status
      }
      try {
        let res
        if (this.formMode === 'add') {
          res = await addDangerZone(submitData)
        } else {
          res = await updateDangerZone(this.editingZone.id, submitData)
        }
        if (res.code === 0) {
          this.$message.success(this.formMode === 'add' ? '新增成功' : '更新成功')
          this.showFormDialog = false
          this.onRefresh()
        }
      } catch (e) {
        console.error('Submit failed:', e)
      }
    },
    resetForm () {
      this.editingZone = null
    },
    async onDeleteZone (zone) {
      try {
        await this.$confirm('确定删除禁区"' + zone.zone_name + '"？', '确认删除', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
        const res = await deleteDangerZone(zone.id)
        if (res.code === 0) {
          this.$message.success('删除成功')
          this.onRefresh()
        }
      } catch (e) {
        if (e !== 'cancel') {
          console.error('Delete failed:', e)
        }
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
}

.dz-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--dark-text);
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 7px 14px;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  transition: background 0.2s, color 0.2s;
  border: 1px solid var(--dark-border-field);
  background: rgba(255, 255, 255, 0.04);
  color: var(--dark-text-secondary);
}

.add-btn {
  border-color: var(--dark-accent);
  color: var(--dark-accent-light);
  background: rgba(99, 102, 241, 0.08);
}

.add-btn:hover {
  background: rgba(99, 102, 241, 0.15);
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

.zone-status {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 500;
}

.status-active {
  background: rgba(16, 185, 129, 0.12);
  color: var(--dark-success);
}

.status-inactive {
  background: rgba(139, 139, 139, 0.12);
  color: var(--dark-text-muted);
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

.action-sm {
  display: flex;
  align-items: center;
  gap: 3px;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  border: 1px solid var(--dark-border-field);
  background: rgba(255, 255, 255, 0.04);
  color: var(--dark-text-secondary);
  transition: background 0.2s;
}

.edit-btn:hover {
  color: var(--dark-accent-light);
  border-color: var(--dark-accent);
}

.del-btn:hover {
  color: var(--dark-danger);
  border-color: var(--dark-danger);
}

.zone-card-body {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.zone-detail-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}

.detail-label {
  color: var(--dark-text-secondary);
  min-width: 80px;
}

.detail-value {
  color: var(--dark-text);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: var(--dark-text-muted);
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 12px;
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

.required {
  color: var(--dark-danger);
}
</style>
