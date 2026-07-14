/**
 * 禁区入侵检测相关接口
 */
import request from '@/utils/request'

/** 获取禁区列表 */
export function getDangerZoneList (params) {
  return request({
    url: '/danger-zone/list',
    method: 'get',
    params
  })
}

/** 更新禁区配置 */
export function updateDangerZone (id, data) {
  return request({
    url: `/danger-zone/${id}`,
    method: 'put',
    data
  })
}

/** 清理孤立禁区 */
export function cleanupOrphanZones () {
  return request({
    url: '/danger-zone/cleanup',
    method: 'post'
  })
}
