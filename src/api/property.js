/**
 * 物业后台管理相关接口
 */
import request from '@/utils/request'

/** 获取门禁终端列表 */
export function getGateList (params) {
  return request({ url: '/gate/list', method: 'get', params })
}

/** 新增门禁终端 */
export function addGate (data) {
  return request({ url: '/gate/add', method: 'post', data })
}

/** 更新门禁终端 */
export function updateGate (id, data) {
  return request({ url: `/gate/${id}`, method: 'put', data })
}

/** 获取门禁终端详情 */
export function getGateDetail (id) {
  return request({ url: `/gate/${id}`, method: 'get' })
}

/** 删除门禁终端 */
export function deleteGate (id) {
  return request({ url: `/gate/${id}`, method: 'delete' })
}

/** 配置门禁权限 */
export function updateGatePermission (id, data) {
  return request({ url: `/gate/${id}/permission`, method: 'put', data })
}

/** 获取安防监控日报列表 */
export function getReportList (params) {
  return request({ url: '/report/list', method: 'get', params })
}

/** 获取安防监控日报详情 */
export function getReportDetail (id) {
  return request({ url: `/report/${id}`, method: 'get' })
}

/** 手动生成安防监控日报 */
export function generateReport (data) {
  return request({ url: '/report/generate', method: 'post', data })
}

/** 重新生成安防监控日报 */
export function regenerateReport (id) {
  return request({ url: `/report/${id}/regenerate`, method: 'post' })
}

/** 历史通行日志 */
export function getPassLogs (params) {
  return request({ url: '/property/pass-logs', method: 'get', params })
}

/** 批量导入业主 */
export function importOwners (data) {
  return request({ url: '/property/import-owners', method: 'post', data })
}
