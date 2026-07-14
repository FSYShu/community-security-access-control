<template>
  <app-layout page-title="门禁终端管理" :no-scroll="true">
    <div class="dark-card">
      <div class="filter-row">
        <div class="filter-select" :class="{ 'is-open': showLevelDropdown }">
          <div class="select-trigger" @click="toggleLevelDropdown">
            <span class="select-value">{{ filterLevel || '终端层级' }}</span>
            <i class="el-icon-arrow-down select-arrow" :class="{ 'is-reverse': showLevelDropdown }"></i>
          </div>
          <transition name="dropdown">
            <div v-if="showLevelDropdown" class="select-dropdown">
              <div
                v-for="opt in levelOptions"
                :key="opt"
                class="select-option"
                :class="{ 'is-active': filterLevel === opt || (!filterLevel && opt === '全部') }"
                @click="selectLevel(opt)"
              >{{ opt }}</div>
            </div>
          </transition>
        </div>
        <div class="filter-select" :class="{ 'is-open': showStatusDropdown }">
          <div class="select-trigger" @click="toggleStatusDropdown">
            <span class="select-value">{{ filterStatus || '状态' }}</span>
            <i class="el-icon-arrow-down select-arrow" :class="{ 'is-reverse': showStatusDropdown }"></i>
          </div>
          <transition name="dropdown">
            <div v-if="showStatusDropdown" class="select-dropdown">
              <div
                v-for="opt in statusOptions"
                :key="opt"
                class="select-option"
                :class="{ 'is-active': filterStatus === opt || (!filterStatus && opt === '全部') }"
                @click="selectStatus(opt)"
              >{{ opt }}</div>
            </div>
          </transition>
        </div>
        <div class="filter-spacer"></div>
        <button class="zone-btn" @click="openZoneDialog">
          <i class="el-icon-warning-outline"></i>
          <span>禁区管理</span>
        </button>
        <button class="add-btn" @click="openAddDialog">
          <i class="el-icon-plus"></i>
          <span>新增终端</span>
        </button>
      </div>
    </div>
    <div class="dark-card list-section">
      <div class="list-content">
        <van-cell v-for="item in gateList" :key="item.id" is-link @click="goToMonitor(item)">
          <template #title>
            <div class="cell-title-row">
              <span class="cell-status">
                <span class="status-dot" :class="statusDotClass(item)"></span>
                <span class="status-label">{{ displayStatusText(item) }}</span>
              </span>
              <span class="cell-name">{{ item.gate_name }}</span>
              <span class="type-tag" :class="levelTagClass(item.gate_level)">{{ item.level_name || item.gate_level }}</span>
            </div>
          </template>

          <template #right-icon>
            <button class="edit-btn" @click.stop="openEditDialog(item)">
              <i class="el-icon-edit"></i>
              <span>编辑</span>
            </button>

            <button class="delete-btn" @click.stop="onDelete(item)">
              <i class="el-icon-delete"></i>
              <span>删除</span>
            </button>
          </template>
        </van-cell>
        <div v-if="gateList.length === 0 && !loading" class="empty-state">
          <i class="el-icon-office-building" style="font-size:48px;color:var(--dark-text-muted)"></i>
          <p style="color:var(--dark-text-muted);margin-top:12px">暂无门禁终端</p>
        </div>
      </div>
      <div class="pagination-wrapper">
        <el-pagination
          background
          layout="prev, pager, next"
          :current-page="page"
          :page-size="perPage"
          :total="total"
          @current-change="onPageChange"
        />
      </div>
    </div>

    <el-dialog :visible.sync="showDialog" :title="dialogTitle" width="480px" :close-on-click-modal="false" append-to-body custom-class="dark-dialog" @close="resetForm">
      <div class="form-grid">
        <div class="form-item">
          <label class="form-label">终端名称 <span class="form-required">*</span></label>
          <input v-model="form.gate_name" class="form-input" placeholder="请输入终端名称" />
        </div>
        <div class="form-item">
          <label class="form-label">终端层级 <span class="form-required">*</span></label>
          <div class="filter-select" :class="{ 'is-open': showFormLevelDropdown }">
            <div class="select-trigger" @click="showFormLevelDropdown = !showFormLevelDropdown">
              <span class="select-value">{{ formLevelLabel || '请选择终端层级' }}</span>
              <i class="el-icon-arrow-down select-arrow" :class="{ 'is-reverse': showFormLevelDropdown }"></i>
            </div>
            <transition name="dropdown">
              <div v-if="showFormLevelDropdown" class="select-dropdown">
                <div v-for="opt in formLevelOptions" :key="opt.value" class="select-option" :class="{ 'is-active': form.gate_level === opt.value }" @click="form.gate_level = opt.value; showFormLevelDropdown = false">{{ opt.text }}</div>
              </div>
            </transition>
          </div>
        </div>
        <div class="form-item">
          <label class="form-label">推流码 <span class="form-required">*</span></label>
          <input v-model="form.push_key" class="form-input" placeholder="请输入推流码" />
        </div>
      </div>
      <div class="form-footer">
        <button class="form-btn form-btn-cancel" @click="showDialog = false">取消</button>
        <button class="form-btn form-btn-primary" @click="onSubmit">
          <i v-if="submitLoading" class="el-icon-loading"></i>
          确认
        </button>
      </div>
    </el-dialog>

    <el-dialog :visible.sync="showZoneDialog" title="禁区管理" width="650px" :close-on-click-modal="false" append-to-body custom-class="dark-dialog" @close="resetZoneForm">
      <div class="zone-container">
        <div class="zone-list">
          <div class="zone-list-content">
            <div
              v-for="item in zoneList"
              :key="item.id"
              class="zone-item"
              :class="{ 'is-active': selectedZoneId === item.id }"
              @click="selectZone(item)"
            >
              <div class="zone-item-body">
                <div class="zone-item-header">
                  <span class="zone-name">{{ item.zone_name }}</span>
                  <span class="zone-tag" :class="zoneTagClass(item.alarm_level)">{{ zoneAlarmText(item.alarm_level) }}</span>
                </div>
                <div class="zone-item-info">
                  <span>安全距离: {{ item.safety_distance }}m</span>
                  <span>滞留时长: {{ item.stay_duration }}s</span>
                </div>
              </div>
              <button
                v-if="item.status === 'active'"
                class="zone-status-btn zone-disable-btn"
                @click.stop="toggleZoneStatus(item, 'inactive')"
              >禁用</button>
              <button
                v-else
                class="zone-status-btn zone-enable-btn"
                @click.stop="toggleZoneStatus(item, 'active')"
              >启用</button>
            </div>
            <div v-if="zoneList.length === 0 && !zoneLoading" class="zone-empty">
              <p>暂无禁区数据</p>
            </div>
          </div>
        </div>
        <div class="zone-form">
          <div class="zone-form-content">
            <div class="form-item">
              <label class="form-label">禁区名称</label>
              <input v-model="zoneForm.zone_name" class="form-input" placeholder="请输入禁区名称" disabled />
            </div>
            <div class="form-item">
              <label class="form-label">安全距离 (米)</label>
              <input v-model.number="zoneForm.safety_distance" type="number" class="form-input form-number" placeholder="请输入安全距离" />
            </div>
            <div class="form-item">
              <label class="form-label">滞留警告时长 (秒)</label>
              <input v-model.number="zoneForm.stay_duration" type="number" class="form-input form-number" placeholder="请输入滞留警告时长" />
            </div>
            <div class="form-item">
              <label class="form-label">告警级别</label>
              <div class="filter-select" :class="{ 'is-open': showZoneLevelDropdown }">
                <div class="select-trigger" @click="showZoneLevelDropdown = !showZoneLevelDropdown">
                  <span class="select-value">{{ zoneLevelLabel || '请选择告警级别' }}</span>
                  <i class="el-icon-arrow-down select-arrow" :class="{ 'is-reverse': showZoneLevelDropdown }"></i>
                </div>
                <transition name="dropdown">
                  <div v-if="showZoneLevelDropdown" class="select-dropdown">
                    <div v-for="opt in zoneLevelOptions" :key="opt.value" class="select-option" :class="{ 'is-active': zoneForm.alarm_level === opt.value }" @click="zoneForm.alarm_level = opt.value; showZoneLevelDropdown = false">{{ opt.text }}</div>
                  </div>
                </transition>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div class="zone-footer">
        <span class="zone-tip"><i class="el-icon-info"></i> 禁区由门禁管理中"危险防护区域"类型的终端自动创建</span>
        <div class="zone-footer-btns">
          <button class="form-btn form-btn-cancel" @click="showZoneDialog = false">取消</button>
          <button class="form-btn form-btn-primary" @click="onZoneSubmit">
            <i v-if="zoneSubmitLoading" class="el-icon-loading"></i>
            保存
          </button>
        </div>
      </div>
    </el-dialog>

  </app-layout>
</template>

<script>
import { getGateList, addGate, updateGate, getGateDetail, deleteGate } from '@/api/property'
import { getDangerZoneList, updateDangerZone, cleanupOrphanZones } from '@/api/dangerZone'

export default {
  name: 'GateListPage',
  data () {
    return {
      gateList: [],
      loading: false,
      page: 1,
      perPage: 20,
      total: 0,
      filterLevel: '',
      filterStatus: '',
      showLevelDropdown: false,
      showStatusDropdown: false,
      levelOptions: ['全部', '社区大门', '单元门', '危险防护区域'],
      statusOptions: ['全部', '未绑定', '在线', '离线', '维护中'],
      showDialog: false,
      isEdit: false,
      editId: null,
      submitLoading: false,
      showFormLevelDropdown: false,
      form: { gate_name: '', gate_level: '', building_unit: '', push_key: '' },
      formLevelOptions: [
        { text: '社区大门', value: 'community_gate' },
        { text: '单元门', value: 'unit_door' },
        { text: '危险防护区域', value: 'dangerous_area' }
      ],
      pollTimer: null,
      showZoneDialog: false,
      zoneList: [],
      zoneLoading: false,
      selectedZoneId: null,
      zoneForm: { zone_name: '', safety_distance: 0, stay_duration: 0, alarm_level: '' },
      zoneLevelOptions: [
        { text: '低告警级别', value: 'low' },
        { text: '中告警级别', value: 'medium' },
        { text: '高告警级别', value: 'high' }
      ],
      showZoneLevelDropdown: false,
      zoneSubmitLoading: false
    }
  },
  computed: {
    dialogTitle () {
      return this.isEdit ? '编辑门禁终端' : '新增门禁终端'
    },
    formLevelLabel () {
      const opt = this.formLevelOptions.find(o => o.value === this.form.gate_level)
      return opt ? opt.text : ''
    },
    zoneLevelLabel () {
      const opt = this.zoneLevelOptions.find(o => o.value === this.zoneForm.alarm_level)
      return opt ? opt.text : ''
    }
  },
  mounted () {
    document.addEventListener('click', this.closeDropdowns)
    this.loadData()
    this.pollTimer = setInterval(this.silentRefresh, 15000)
  },
  beforeDestroy () {
    document.removeEventListener('click', this.closeDropdowns)
    if (this.pollTimer) {
      clearInterval(this.pollTimer)
      this.pollTimer = null
    }
  },
  methods: {
    closeDropdowns (e) {
      if (!e.target.closest('.filter-select')) {
        this.showLevelDropdown = false
        this.showStatusDropdown = false
        this.showFormLevelDropdown = false
        this.showZoneLevelDropdown = false
      }
    },
    toggleLevelDropdown () {
      this.showStatusDropdown = false
      this.showLevelDropdown = !this.showLevelDropdown
    },
    toggleStatusDropdown () {
      this.showLevelDropdown = false
      this.showStatusDropdown = !this.showStatusDropdown
    },
    selectLevel (opt) {
      this.filterLevel = opt === '全部' ? '' : opt
      this.showLevelDropdown = false
      this.onRefresh()
    },
    selectStatus (opt) {
      this.filterStatus = opt === '全部' ? '' : opt
      this.showStatusDropdown = false
      this.onRefresh()
    },
    async loadData () {
      try {
        this.loading = true
        const levelMap = { 社区大门: 'community_gate', 单元门: 'unit_door', 危险防护区域: 'dangerous_area' }
        const statusMap = { 未绑定: 'unbound', 在线: 'online', 离线: 'offline', 维护中: 'maintenance' }
        const params = { page: this.page, per_page: this.perPage }
        if (this.filterLevel && this.filterLevel !== '全部') params.gate_level = levelMap[this.filterLevel]
        if (this.filterStatus && this.filterStatus !== '全部') params.status = statusMap[this.filterStatus]
        const res = await getGateList(params)
        if (res.code === 0 && res.data) {
          this.gateList = res.data.items || []
          this.total = res.data.total || 0
        }
      } catch (e) {
        console.error(e)
      }
      this.loading = false
    },
    onPageChange (newPage) {
      this.page = newPage
      this.loadData()
    },
    onRefresh () { this.page = 1; this.loadData() },
    silentRefresh () {
      this.page = 1
      this.loadData()
    },
    goToMonitor (item) {
      this.$router.push({ path: '/video-monitor', query: { gate_id: item.id } })
    },
    levelTagClass (level) {
      const map = { community_gate: 'tag-community', unit_door: 'tag-unit', dangerous_area: 'tag-danger' }
      return map[level] || ''
    },
    displayStatusText (item) {
      const isBound = item.bound === true || item.bound === 'true' || item.bound === 1
      if (!isBound) return '未绑定'
      const map = { online: '在线', offline: '离线', maintenance: '维护中' }
      return map[item.status] || item.status
    },
    statusDotClass (item) {
      const isBound = item.bound === true || item.bound === 'true' || item.bound === 1
      if (!isBound) return 'dot-unbound'
      if (item.status === 'online') return 'dot-online'
      if (item.status === 'maintenance') return 'dot-maintenance'
      return 'dot-offline'
    },
    onDelete (item) {
      this.$confirm('确定要删除「' + item.gate_name + '」终端吗？', '确认删除', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        customClass: 'dark-dialog'
      }).then(() => {
        this.doDelete(item.id)
      }).catch(() => {})
    },
    async doDelete (id) {
      try {
        await deleteGate(id)
        this.$message.success('删除成功')
        this.onRefresh()
      } catch (e) {
        this.$message.error('删除失败')
      }
    },
    resetForm () {
      this.form = { gate_name: '', gate_level: '', building_unit: '', push_key: '' }
      this.isEdit = false
      this.editId = null
      this.showFormLevelDropdown = false
    },
    openAddDialog () {
      this.resetForm()
      this.showDialog = true
    },
    async openEditDialog (item) {
      this.resetForm()
      this.isEdit = true
      this.editId = item.id
      try {
        const res = await getGateDetail(item.id)
        const d = res.data
        this.form.gate_name = d.gate_name || ''
        this.form.gate_level = d.gate_level || ''
        this.form.building_unit = d.building_unit || ''
        this.form.push_key = d.push_key || ''
      } catch (e) {
        this.$message.error('加载终端信息失败')
      }
      this.showDialog = true
    },
    async onSubmit () {
      if (!this.form.gate_name || !this.form.gate_level || !this.form.push_key) {
        return this.$message.warning('请填写必填项')
      }
      this.submitLoading = true
      try {
        const data = {
          gate_name: this.form.gate_name,
          gate_level: this.form.gate_level,
          building_unit: this.form.building_unit,
          push_key: this.form.push_key
        }
        if (this.isEdit) {
          await updateGate(this.editId, data)
          this.$message.success('保存成功')
        } else {
          await addGate(data)
          this.$message.success('新增成功')
        }
        this.showDialog = false
        this.onRefresh()
      } catch (e) {
        this.$message.error(this.isEdit ? '保存失败' : '新增失败')
      }
      this.submitLoading = false
    },
    async openZoneDialog () {
      this.showZoneDialog = true
      try {
        await cleanupOrphanZones()
      } catch (e) {
        console.error(e)
      }
      this.loadZoneList()
    },
    async loadZoneList () {
      try {
        this.zoneLoading = true
        const res = await getDangerZoneList()
        if (res.code === 0 && res.data) {
          this.zoneList = res.data.items || res.data || []
          if (this.zoneList.length > 0) {
            this.selectZone(this.zoneList[0])
          }
        }
      } catch (e) {
        console.error(e)
      }
      this.zoneLoading = false
    },
    selectZone (item) {
      this.selectedZoneId = item.id
      this.zoneForm.zone_name = item.zone_name || ''
      this.zoneForm.safety_distance = item.safety_distance || 0
      this.zoneForm.stay_duration = item.stay_duration || 0
      this.zoneForm.alarm_level = item.alarm_level || ''
    },
    zoneTagClass (level) {
      const map = { low: 'zone-tag-low', medium: 'zone-tag-medium', high: 'zone-tag-high' }
      return map[level] || ''
    },
    zoneAlarmText (level) {
      const map = { low: '低告警级别', medium: '中告警级别', high: '高告警级别' }
      return map[level] || level
    },
    async toggleZoneStatus (item, status) {
      try {
        await updateDangerZone(item.id, { status })
        this.$message.success(status === 'active' ? '启用成功' : '禁用成功')
        this.loadZoneList()
      } catch (e) {
        this.$message.error('操作失败')
      }
    },
    resetZoneForm () {
      this.zoneForm = { zone_name: '', safety_distance: 0, stay_duration: 0, alarm_level: '' }
      this.selectedZoneId = null
      this.showZoneLevelDropdown = false
    },
    async onZoneSubmit () {
      if (!this.selectedZoneId) {
        return this.$message.warning('请选择要编辑的禁区')
      }
      if (!this.zoneForm.safety_distance || !this.zoneForm.stay_duration || !this.zoneForm.alarm_level) {
        return this.$message.warning('请填写完整信息')
      }
      this.zoneSubmitLoading = true
      try {
        const data = {
          safety_distance: this.zoneForm.safety_distance,
          stay_duration: this.zoneForm.stay_duration,
          alarm_level: this.zoneForm.alarm_level
        }
        await updateDangerZone(this.selectedZoneId, data)
        this.$message.success('保存成功')
        this.showZoneDialog = false
      } catch (e) {
        this.$message.error('保存失败')
      }
      this.zoneSubmitLoading = false

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

.list-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.list-content {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.pagination-wrapper {
  padding-top: 16px;
  display: flex;
  justify-content: center;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
  min-height: 200px;
}

.filter-spacer {
  flex: 1;
}

.filter-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.filter-select {
  position: relative;
  min-width: 140px;
}

.select-trigger {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--dark-border-field);
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

.add-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 8px 16px;
  background: var(--dark-accent);
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 13px;
  cursor: pointer;
  transition: background 0.2s;
}

.add-btn:hover {
  background: var(--dark-accent-light);
}

.add-btn i {
  font-size: 14px;
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

.cell-title-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

::v-deep .van-cell__title {
  display: flex;
  align-items: center;
}

.cell-status {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}

.dot-online {
  background: var(--dark-success);
  box-shadow: 0 0 6px rgba(16, 185, 129, 0.4);
}

.dot-offline {
  background: #ef4444;
  box-shadow: 0 0 6px rgba(239, 68, 68, 0.4);
}

.dot-unbound {
  background: #9ca3af !important;
  box-shadow: 0 0 6px rgba(156, 163, 175, 0.3) !important;
}

.dot-maintenance {
  background: #f59e0b;
  box-shadow: 0 0 6px rgba(245, 158, 11, 0.4);
}

.status-label {
  font-size: 13px;
  color: var(--dark-text-secondary);
}

.type-tag {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0 6px;
  height: 22px;
  border-radius: 4px;
  font-size: 12px;
  margin-right: 8px;
  border: 1px solid;
}

.tag-community {
  color: var(--dark-accent-light);
  border-color: rgba(99, 102, 241, 0.3);
  background: rgba(99, 102, 241, 0.08);
}

.tag-unit {
  color: var(--dark-success-green);
  border-color: rgba(16, 185, 129, 0.3);
  background: rgba(16, 185, 129, 0.08);
}

.tag-danger {
  color: #ef4444;
  border-color: rgba(239, 68, 68, 0.3);
  background: rgba(239, 68, 68, 0.08);
}

.cell-name {
  font-size: 15px;
  color: var(--dark-text);
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
  margin-left: 8px;
}

.edit-btn:hover {
  background: rgba(99, 102, 241, 0.1);
  border-color: var(--dark-accent-light);
  color: var(--dark-accent-light);
}

.delete-btn {
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
  margin-left: 8px;
}

.delete-btn:hover {
  background: rgba(239, 68, 68, 0.1);
  border-color: #ef4444;
  color: #ef4444;
}
</style>

<style>
.el-pagination.is-background .btn-prev,
.el-pagination.is-background .btn-next,
.el-pagination.is-background .el-pager li {
  background: rgba(255, 255, 255, 0.04) !important;
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
  color: var(--dark-text-secondary) !important;
}

.el-pagination.is-background .btn-prev:hover,
.el-pagination.is-background .btn-next:hover,
.el-pagination.is-background .el-pager li:hover {
  background: rgba(255, 255, 255, 0.08) !important;
  color: var(--dark-text) !important;
}

.el-pagination.is-background .el-pager li.active {
  background: var(--dark-accent) !important;
  border-color: var(--dark-accent) !important;
  color: #fff !important;
}

.el-pagination.is-background .btn-prev:disabled,
.el-pagination.is-background .btn-next:disabled {
  background: rgba(255, 255, 255, 0.02) !important;
  color: var(--dark-text-dim) !important;
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

.zone-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 8px 16px;
  background: rgba(245, 158, 11, 0.1);
  color: #f59e0b;
  border: 1px solid rgba(245, 158, 11, 0.3);
  border-radius: 8px;
  font-size: 13px;
  cursor: pointer;
  transition: background 0.2s, color 0.2s;
}

.zone-btn:hover {
  background: rgba(245, 158, 11, 0.2);
  color: #fbbf24;
}

.zone-btn i {
  font-size: 14px;
}

.zone-container {
  display: flex;
  gap: 20px;
  min-height: 400px;
}

.zone-list {
  flex: 0 0 280px;
  display: flex;
  flex-direction: column;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 8px;
  overflow: hidden;
  max-height: 400px;
}

.zone-list-content {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.zone-list-content::-webkit-scrollbar {
  width: 6px;
}

.zone-list-content::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.02);
  border-radius: 3px;
}

.zone-list-content::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
}

.zone-list-content::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.15);
}

.zone-item {
  display: flex;
  align-items: center;
  padding: 12px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 6px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: background 0.2s, border-color 0.2s;
}

.zone-item:last-child {
  margin-bottom: 0;
}

.zone-item:hover {
  background: rgba(255, 255, 255, 0.04);
}

.zone-item.is-active {
  background: rgba(99, 102, 241, 0.08);
  border-color: var(--dark-accent-light);
}

.zone-item-body {
  flex: 1;
  min-width: 0;
}

.zone-item-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.zone-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--dark-text);
}

.zone-tag {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
}

.zone-tag-low {
  background: rgba(16, 185, 129, 0.15);
  color: #10b981;
}

.zone-tag-medium {
  background: rgba(245, 158, 11, 0.15);
  color: #f59e0b;
}

.zone-tag-high {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
}

.zone-item-info {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: var(--dark-text-secondary);
  margin-bottom: 8px;
}

.zone-status-btn {
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  border: none;
  transition: background 0.2s;
  flex-shrink: 0;
}

.zone-enable-btn {
  background: rgba(16, 185, 129, 0.15);
  color: #10b981;
}

.zone-enable-btn:hover {
  background: rgba(16, 185, 129, 0.25);
}

.zone-disable-btn {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
}

.zone-disable-btn:hover {
  background: rgba(239, 68, 68, 0.25);
}

.zone-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 200px;
  color: var(--dark-text-muted);
  font-size: 13px;
}

.zone-form {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 8px;
  overflow: hidden;
}

.zone-form-content {
  flex: 1;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-number {
  -moz-appearance: textfield;
}

.form-number::-webkit-inner-spin-button,
.form-number::-webkit-outer-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

.zone-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  gap: 0;
}

.zone-tip {
  font-size: 12px;
  color: var(--dark-text-muted);
  margin-left: 0;
}

.zone-footer-btns {
  display: flex;
  gap: 8px;
}

</style>
