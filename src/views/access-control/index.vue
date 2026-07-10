<template>
  <div class="access-control-page">
    <van-nav-bar title="门禁权限配置" left-arrow @click-left="$router.back()" />
    <div class="page-content">
      <!-- TODO: 门禁权限配置页面 -->
      <van-empty description="门禁权限配置模块开发中" />
    </div>
  </div>
</template>

<script>
export default {
  name: 'AccessControlPage'
}
</script>

<style scoped>
.page-content {
  padding: 12px;
}
</style>