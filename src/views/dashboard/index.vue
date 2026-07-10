<template>
  <div class="dashboard-page">
    <van-nav-bar title="安防总览" />
    <div class="dashboard-content">
      <van-row gutter="12">
        <van-col span="12">
          <van-cell
            title="今日通行"
            :value="stats.passCount"
            is-link
            to="/face-management"
          />
        </van-col>
        <van-col span="12">
          <van-cell
            title="待处理告警"
            :value="stats.alarmCount"
            is-link
            to="/alarm-center"
          />
        </van-col>
      </van-row>
      <van-row gutter="12" style="margin-top: 12px;">
        <van-col span="12">
          <van-cell
            title="在线设备"
            :value="stats.onlineDevices"
          />
        </van-col>
        <van-col span="12">
          <van-cell
            title="禁区状态"
            :value="stats.zoneStatus"
          />
        </van-col>
      </van-row>
      <!-- 功能快捷入口 -->
      <van-grid :column-num="4" style="margin-top: 16px;">
        <van-grid-item icon="friends-o" text="人脸管理" to="/face-management" />
        <van-grid-item icon="shield-o" text="门禁权限" to="/access-control" />
        <van-grid-item icon="warning-o" text="禁区检测" to="/danger-zone" />
        <van-grid-item icon="eye-o" text="视频监控" to="/video-monitor" />
        <van-grid-item icon="bell" text="告警中心" to="/alarm-center" />
        <van-grid-item icon="setting-o" text="物业后台" to="/property-admin" />
      </van-grid>
    </div>
  </div>
</template>

<script>
export default {
  name: 'DashboardPage',
  data() {
    return {
      stats: {
        passCount: 0,
        alarmCount: 0,
        onlineDevices: 0,
        zoneStatus: '正常'
      }
    }
  },
  mounted() {
    this.loadDashboardStats()
  },
  methods: {
    loadDashboardStats() {
      // TODO: 调用接口获取总览数据
    }
  }
}
</script>

<style scoped>
.dashboard-page {
  min-height: 100vh;
  background-color: #f5f5f5;
}
.dashboard-content {
  padding: 12px;
}
</style>