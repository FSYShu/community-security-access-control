<template>
  <app-layout :page-title="isEdit ? '编辑门禁终端' : '新增门禁终端'">
    <div class="dark-card">
      <van-cell-group>
        <van-field v-model="form.gate_name" label="终端名称" placeholder="请输入终端名称" required />
        <van-field v-model="form.gate_level_label" label="终端层级" placeholder="请选择" readonly is-link required @click="showLevelPicker = true" />
        <van-field v-model="form.building_unit" label="楼栋/单元" placeholder="单元门层级必填" :required="form.gate_level === 'unit_door'" />
        <van-field v-model="form.push_key" label="推流码" placeholder="请输入推流码" />
      </van-cell-group>
      <div style="margin: 16px 0">
        <van-button type="primary" block @click="onSubmit">保存</van-button>
      </div>
    </div>
    <van-popup v-model="showLevelPicker" position="bottom">
      <van-picker :columns="levelTexts" @confirm="onLevelConfirm" @cancel="showLevelPicker = false" show-toolbar title="选择终端层级" />
    </van-popup>
  </app-layout>
</template>

<script>
import { addGate, updateGate, getGateDetail } from '@/api/property'

export default {
  name: 'GateEditPage',
  data () {
    return {
      isEdit: false,
      gateId: null,
      form: { gate_name: '', gate_level: '', gate_level_label: '', building_unit: '', push_key: '' },
      showLevelPicker: false,
      levelOptions: [
        { text: '社区大门', value: 'community_gate' },
        { text: '单元门', value: 'unit_door' },
        { text: '危险防护区域', value: 'dangerous_area' }
      ]
    }
  },
  computed: {
    levelTexts () { return this.levelOptions.map(o => o.text) }
  },
  created () {
    this.gateId = this.$route.params.id
    this.isEdit = !!this.gateId
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
        this.form.building_unit = d.building_unit || ''
        this.form.push_key = d.push_key || ''
      } catch (e) {
        this.$message.error('加载终端信息失败')
      }
    },
    onLevelConfirm (value, index) {
      this.form.gate_level = this.levelOptions[index].value
      this.form.gate_level_label = value
      this.showLevelPicker = false
    },
    async onSubmit () {
      if (!this.form.gate_name || !this.form.gate_level) {
        return this.$message.warning('请填写必填项')
      }
      try {
        const data = { gate_name: this.form.gate_name, gate_level: this.form.gate_level, building_unit: this.form.building_unit, push_key: this.form.push_key }
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
