<template>
  <div class="danger-zone-page">
    <van-nav-bar title="禁区入侵检测" left-arrow @click-left="$router.back()" />
    <div class="page-content">
      <!-- TODO: 禁区入侵检测页面 -->
      <van-empty description="禁区入侵检测模块开发中" />
    </div>
  </div>
</template>

<script>
export default {
  name: 'DangerZonePage'
}
</script>

<style scoped>
.page-content {
  padding: 12px;
}
</style>
