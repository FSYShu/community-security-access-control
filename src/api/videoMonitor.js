/**
 * 视频监控相关接口
 */
import request from '@/utils/request'

/** 获取监控区域列表 */
export function getMonitorList(params) {
  return request({
    url: '/video-monitor/list',
    method: 'get',
    params
  })
}

/** 获取视频回放地址 */
export function getVideoPlayback(id, params) {
  return request({
    url: `/video-monitor/${id}/playback`,
    method: 'get',
    params
  })
}