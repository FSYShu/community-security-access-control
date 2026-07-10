/**
 * 物业后台管理相关接口
 */
import request from '@/utils/request'

/** 获取门禁终端列表 */
export function getGateList(params) {
  return request({
    url: '/gate/list',
    method: 'get',
    params
  })
}

/** 配置门禁权限 */
export function configGatePermission(id, data) {
  return request({
    url: `/gate/${id}/permission`,
    method: 'put',
    data
  })
}

/** 获取安防监控日报列表 */
export function getDailyReportList(params) {
  return request({
    url: '/report/daily/list',
    method: 'get',
    params
  })
}

/** 获取安防监控日报详情 */
export function getDailyReportDetail(id) {
  return request({
    url: `/report/daily/${id}`,
    method: 'get'
  })
}

/** 手动生成安防监控日报 */
export function generateDailyReport(data) {
  return request({
    url: '/report/daily/generate',
    method: 'post',
    data
  })
}

/** 获取历史监控日志 */
export function getHistoryLogs(params) {
  return request({
    url: '/log/history',
    method: 'get',
    params
  })
}