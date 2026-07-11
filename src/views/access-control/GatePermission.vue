<template>
  <app-layout page-title="门禁权限配置">
    <div class="dark-card">
      <van-cell-group title="通行时段配置">
        <van-field v-model="form.pass_time_config" label="通行时段" type="textarea" rows="3" placeholder='{"start":"06:00","end":"22:00"}' />
      </van-cell-group>
      <van-cell-group title="可通行人员范围">
        <van-field v-model="form.allowed_persons" label="人员范围" type="textarea" rows="3" placeholder='{"allow_owner":true,"allow_visitor":true}' />
      </van-cell-group>
      <van-cell-group title="自定义通行策略">
        <van-field v-model="form.custom_pass_policy" label="自定义策略" type="textarea" rows="3" placeholder='{}' />
      </van-cell-group>
      <van-cell-group title="二次验证">
        <van-cell title="启用二次验证">
          <van-switch v-model="form.require_secondary_auth" />
        </van-cell>
      </van-cell-group>
      <div style="margin: 16px 0">
        <van-button type="primary" block @click="onSubmit">保存配置</van-button>
      </div>
    </div>
  </app-layout>
</template>

<script>
import { updateGatePermission } from '@/api/property'

export default {
  name: 'GatePermissionPage',
  data () {
    return {
      gateId: null,
      form: {
        pass_time_config: '',
        allowed_persons: '',
        custom_pass_policy: '',
        require_secondary_auth: false
      }
    }
  },
  created () {
    this.gateId = this.$route.params.id
  },
  methods: {
    async onSubmit () {
      try {
        const data = {
          pass_time_config: this.form.pass_time_config ? JSON.parse(this.form.pass_time_config) : {},
          allowed_persons: this.form.allowed_persons ? JSON.parse(this.form.allowed_persons) : {},
          custom_pass_policy: this.form.custom_pass_policy ? JSON.parse(this.form.custom_pass_policy) : {},
          require_secondary_auth: this.form.require_secondary_auth
        }
        await updateGatePermission(this.gateId, data)
        this.$message.success('配置保存成功')
        this.$router.back()
      } catch (e) {
        this.$message.error('配置保存失败，请检查JSON格式')
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
