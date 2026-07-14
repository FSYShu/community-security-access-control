/* eslint-disable */
var NAV_ITEMS = [
  { label: '安防总览', icon: 'el-icon-monitor', path: '/dashboard', roles: ['admin', 'guard'] },
  { label: '实时监控', icon: 'el-icon-view', path: '/video-monitor', roles: ['admin', 'guard'] },
  { label: '历史回放', icon: 'el-icon-video-play', path: '/video-monitor/playback', roles: ['admin', 'guard'] },
  { label: '人脸管理', icon: 'el-icon-user', path: '/face-management', roles: ['admin'] },
  { label: '门禁管理', icon: 'el-icon-lock', path: '/access-control', roles: ['admin'] },
  { label: '告警中心', icon: 'el-icon-bell', path: '/alarm-center', roles: ['admin', 'guard'] },
  { label: '用户权限', icon: 'el-icon-key', path: '/user-management', roles: ['admin'] },
  { label: '安防日报', icon: 'el-icon-document', path: '/report', roles: ['admin'] },
  { label: '通行日志', icon: 'el-icon-notebook-2', path: '/property-admin/pass-logs', roles: ['admin', 'guard'] }
]

module.exports = {
  computed: {
    navItems: function () {
      var roles = this.$store.getters['user/roles'] || []
      var userRole = roles[0] || ''
      return NAV_ITEMS.filter(function (item) {
        return !item.roles || item.roles.indexOf(userRole) !== -1
      })
    }
  }
}

