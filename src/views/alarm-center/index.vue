<template>
  <div class="alarm-center-page">
    <van-nav-bar title="告警中心" left-arrow @click-left="$router.back()" />
    <div class="page-content">
      <!-- TODO: 告警中心页面 -->
      <van-empty description="告警中心模块开发中" />
    </div>
  </div>
</template>

<script>
export default {
  name: 'AlarmCenterPage'
}
</script>

<style scoped>
.page-content {
  padding: 12px;
}
</style>