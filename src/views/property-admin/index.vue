<template>
  <div class="property-admin-page">
    <van-nav-bar title="物业后台管理" left-arrow @click-left="$router.back()" />
    <div class="page-content">
      <!-- TODO: 物业后台管理页面 -->
      <van-empty description="物业后台管理模块开发中" />
    </div>
  </div>
</template>

<script>
export default {
  name: 'PropertyAdminPage'
}
</script>

<style scoped>
.page-content {
  padding: 12px;
}
</style>