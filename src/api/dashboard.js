/**
 * 安防总览相关接口
 */
import request from '@/utils/request'

/** 获取总览统计数据 */
export function getDashboardStats () {
  return request({
    url: '/dashboard/stats',
    method: 'get'
  })
}

/** 获取最近告警列表 */
export function getRecentAlarms (params) {
  return request({
    url: '/dashboard/recent-alarms',
    method: 'get',
    params
  })
}

/** 获取设备在线状态 */
export function getDeviceStatus () {
  return request({
    url: '/dashboard/device-status',
    method: 'get'
  })
}
