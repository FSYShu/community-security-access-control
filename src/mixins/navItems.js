/* eslint-disable */
const NAV_ITEMS = [
  { label: '安防总览', icon: 'el-icon-monitor', path: '/dashboard' },
  { label: '实时监控', icon: 'el-icon-view', path: '/video-monitor' },
  { label: '历史回放', icon: 'el-icon-video-play', path: '/video-monitor/playback' },
  { label: '人脸管理', icon: 'el-icon-user', path: '/face-management' },
  { label: '门禁管理', icon: 'el-icon-lock', path: '/access-control' },
  { label: '禁区检测', icon: 'el-icon-warning-outline', path: '/danger-zone' },
  { label: '告警中心', icon: 'el-icon-bell', path: '/alarm-center' },
  { label: '安防日报', icon: 'el-icon-document', path: '/report' },
  { label: '通行日志', icon: 'el-icon-notebook-2', path: '/property-admin/pass-logs' },
  { label: '告警日志', icon: 'el-icon-tickets', path: '/property-admin/alarm-logs' }
]

module.exports = {
  data: function () {
    return {
      navItems: NAV_ITEMS
    }
  }
}
