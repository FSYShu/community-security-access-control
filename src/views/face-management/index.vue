<template>
  <div class="face-management-page">
    <van-nav-bar title="人脸信息管理" left-arrow @click-left="$router.back()" />
    <div class="page-content">
      <van-tabs v-model="activeTab">
        <van-tab title="人脸录入">
          <FaceRegister />
        </van-tab>
        <van-tab title="人脸列表">
          <FaceList />
        </van-tab>
      </van-tabs>
    </div>
  </div>
</template>

<script>
import FaceRegister from './FaceRegister.vue'
import FaceList from './FaceList.vue'

export default {
  name: 'FaceManagementPage',
  components: { FaceRegister, FaceList },
  data () {
    return {
      activeTab: 0
    }
  }
}
</script>

<style scoped>
.page-content {
  padding: 0;
}
</style>
