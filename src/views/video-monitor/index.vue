<template>
  <div class="video-monitor-page">
    <van-nav-bar title="实时视频监控" left-arrow @click-left="$router.back()" />
    <div class="page-content">
      <!-- TODO: 实时视频监控页面 -->
      <van-empty description="实时视频监控模块开发中" />
    </div>
  </div>
</template>

<script>
export default {
  name: 'VideoMonitorPage'
}
</script>

<style scoped>
.page-content {
  padding: 12px;
}
</style>