/**
 * 告警中心相关接口
 */
import request from '@/utils/request'

/** 获取告警列表 */
export function getAlarmList (params) {
  return request({
    url: '/alarm/list',
    method: 'get',
    params
  })
}

/** 获取告警详情 */
export function getAlarmDetail (id) {
  return request({
    url: `/alarm/${id}`,
    method: 'get'
  })
}

/** 处置告警 */
export function handleAlarm (id, data) {
  return request({
    url: `/alarm/${id}/handle`,
    method: 'put',
    data
  })
}

/** 导出告警日志 */
export function exportAlarmLog (params) {
  return request({
    url: '/alarm/export',
    method: 'get',
    params,
    responseType: 'blob'
  })
}

/** 获取告警统计 */
export function getAlarmStats () {
  return request({
    url: '/alarm/stats',
    method: 'get'
  })
}
