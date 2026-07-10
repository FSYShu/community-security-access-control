<template>
  <app-layout page-title="物业后台管理">
    <div class="dark-card">

      <van-cell-group title="安防监控日报">
        <van-cell title="日报列表" is-link to="/report" />
      </van-cell-group>
      <van-cell-group title="历史日志查询">
        <van-cell title="通行日志" is-link to="/property-admin/pass-logs" />
        <van-cell title="告警日志" is-link to="/property-admin/alarm-logs" />
      </van-cell-group>

    </div>
  </app-layout>
</template>

<script>
export default {
  name: 'PropertyAdminPage'
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
