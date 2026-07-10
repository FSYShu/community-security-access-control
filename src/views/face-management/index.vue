<template>
  <div class="face-management-page">
    <van-nav-bar title="人脸信息管理" left-arrow @click-left="$router.back()" />
    <div class="page-content">
      <!-- TODO: 人脸信息管理页面 -->
      <van-empty description="人脸信息管理模块开发中" />
    </div>
  </div>
</template>

<script>
export default {
  name: 'FaceManagementPage'
}
</script>

<style scoped>
.page-content {
  padding: 12px;
}
</style>