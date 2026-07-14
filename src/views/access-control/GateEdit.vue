<template>
  <app-layout :page-title="isEdit ? '编辑门禁终端' : '新增门禁终端'">
    <div class="dark-card">
      <van-cell-group>
        <van-field v-model="form.gate_level_label" label="终端层级" placeholder="请选择" readonly is-link required @click="showLevelPicker = true" />
        <van-field v-if="form.gate_level === 'entrance_door'" v-model="selectedUnitDoorLabel" label="所属单元门" placeholder="请选择所属单元门" readonly is-link required @click="showUnitDoorPicker = true" />
        <van-field v-if="form.gate_level === 'unit_door'" v-model="form.building_no" label="楼栋号" placeholder="楼栋" required />
        <van-field v-if="form.gate_level === 'unit_door'" v-model="form.unit_no" label="单元号" placeholder="单元" required />
        <van-field v-if="form.gate_level === 'entrance_door'" v-model="form.room_number" label="门牌号 " placeholder="如：501" required />
        <van-field v-if="form.gate_level !== 'unit_door' && form.gate_level !== 'entrance_door'" v-model="form.gate_name" :label="gateNameLabel" :placeholder="gateNamePlaceholder" required />
        <van-field v-if="form.gate_level !== 'entrance_door'" v-model="form.push_key" label="推流码" placeholder="请输入推流码" />
      </van-cell-group>
      <div style="margin: 16px 0">
        <van-button type="primary" block @click="onSubmit">保存</van-button>
      </div>
    </div>
    <van-popup v-model="showLevelPicker" position="bottom">
      <van-picker :columns="levelTexts" @confirm="onLevelConfirm" @cancel="showLevelPicker = false" show-toolbar title="选择终端层级" />
    </van-popup>
    <van-popup v-model="showUnitDoorPicker" position="bottom">
      <van-picker :columns="unitDoorTexts" @confirm="onUnitDoorConfirm" @cancel="showUnitDoorPicker = false" show-toolbar title="选择所属单元门" />
    </van-popup>
  </app-layout>
</template>

<script>
import { addGate, updateGate, getGateDetail, getUnitDoors } from '@/api/property'

export default {
  name: 'GateEditPage',
  data () {
    return {
      isEdit: false,
      gateId: null,
      form: { gate_name: '', gate_level: '', gate_level_label: '', parent_gate_id: '', building_no: '', unit_no: '', room_number: '', push_key: '' },
      showLevelPicker: false,
      unitDoorList: [],
      showUnitDoorPicker: false,
      levelOptions: [
        { text: '社区大门', value: 'community_gate' },
        { text: '单元门', value: 'unit_door' },
        { text: '入户门', value: 'entrance_door' },
        { text: '危险防护区域', value: 'dangerous_area' }
      ]
    }
  },
  computed: {
    levelTexts () { return this.levelOptions.map(o => o.text) },
    unitDoorTexts () { return this.unitDoorList.map(u => u.gate_name) },
    selectedUnitDoorLabel () {
      const ud = this.unitDoorList.find(u => u.id === this.form.parent_gate_id)
      return ud ? ud.gate_name : ''
    },
    gateNamePlaceholder () {
      const map = {
        community_gate: '如：东1门、西南2门',
        dangerous_area: '请输入区域名称'
      }
      return map[this.form.gate_level] || '请输入终端名称'
    },
    gateNameLabel () {
      const map = {
        community_gate: '大门编号',
        dangerous_area: '区域名称'
      }
      return map[this.form.gate_level] || '终端名称'
    }
  },
  created () {
    this.gateId = this.$route.params.id
    this.isEdit = !!this.gateId
    this.loadUnitDoors()
    if (this.isEdit) this.loadGateDetail()
  },
  methods: {
    async loadGateDetail () {
      try {
        const res = await getGateDetail(this.gateId)
        const d = res.data
        this.form.gate_name = d.gate_name || ''
        this.form.gate_level = d.gate_level || ''
        this.form.gate_level_label = d.level_name || d.gate_level || ''
        this.form.parent_gate_id = d.parent_gate_id || ''
        if (d.gate_level === 'unit_door' && d.gate_name) {
          const m = d.gate_name.match(/^(\d+)栋(\d+)单元$/)
          if (m) { this.form.building_no = m[1]; this.form.unit_no = m[2] }
        }
        this.form.room_number = d.gate_level === 'entrance_door' && d.gate_name ? d.gate_name.replace(/^.*单元/, '').replace('室', '') : ''
        this.form.push_key = d.push_key || ''

      } catch (e) {
        this.$message.error('加载终端信息失败')
      }
    },
    onLevelConfirm (value, index) {
      this.form.gate_level = this.levelOptions[index].value
      this.form.gate_level_label = value
      if (this.form.gate_level !== 'entrance_door') {
        this.form.parent_gate_id = ''
        this.form.room_number = ''
      }
      if (this.form.gate_level !== 'unit_door') {
        this.form.building_no = ''
        this.form.unit_no = ''
      }
      this.showLevelPicker = false
    },
    onUnitDoorConfirm (value, index) {
      this.form.parent_gate_id = this.unitDoorList[index].id
      this.showUnitDoorPicker = false
    },
    async loadUnitDoors () {
      try {
        const res = await getUnitDoors()
        this.unitDoorList = res.data || []
      } catch (e) {
        this.unitDoorList = []
      }
    },
    validateGateName (name, level) {
      if (!name) return false
      if (level === 'community_gate') return /^(东|南|西|北|东南|东北|西南|西北)\d+门$/.test(name)
      return true
    },
    async onSubmit () {
      const isEntrance = this.form.gate_level === 'entrance_door'
      const isUnit = this.form.gate_level === 'unit_door'
      if (isEntrance) {
        if (!this.form.parent_gate_id || !this.form.room_number) {
          return this.$message.warning('请填写必填项')
        }
        if (!/^\d+$/.test(this.form.room_number)) {
          return this.$message.warning('门牌号 请输入数字，如501')
        }
      } else if (isUnit) {
        if (!this.form.building_no || !this.form.unit_no) {
          return this.$message.warning('请填写必填项')
        }
        if (!/^\d+$/.test(this.form.building_no) || !/^\d+$/.test(this.form.unit_no)) {
          return this.$message.warning('楼栋号和单元号请输入数字')
        }
      } else {
        if (!this.form.gate_name || !this.form.gate_level) {
          return this.$message.warning('请填写必填项')
        }
        if (!this.validateGateName(this.form.gate_name, this.form.gate_level)) {
          return this.$message.warning('名称格式不正确')
        }
      }
      try {
        let gateName = this.form.gate_name
        if (isUnit) {
          gateName = this.form.building_no + '栋' + this.form.unit_no + '单元'
        } else if (isEntrance) {
          const ud = this.unitDoorList.find(u => u.id === this.form.parent_gate_id)
          gateName = (ud ? ud.gate_name : '') + this.form.room_number + '室'
        }
        const data = { gate_name: gateName, gate_level: this.form.gate_level, parent_gate_id: isEntrance ? this.form.parent_gate_id : undefined, push_key: this.form.push_key }
        if (this.isEdit) await updateGate(this.gateId, data)
        else await addGate(data)
        this.$message.success('保存成功')
        this.$router.back()
      } catch (e) {
        this.$message.error('保存失败')
      }
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
