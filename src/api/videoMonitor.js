/**
 * 视频监控相关接口
 */
import request from '@/utils/request'

/** 获取监控区域列表 */
export function getMonitorList (params) {
  return request({
    url: '/video-monitor/list',
    method: 'get',
    params
  })
}

/** 获取视频回放地址 */
export function getVideoPlayback (id, params) {
  return request({
    url: `/video-monitor/${id}/playback`,
    method: 'get',
    params
  })
}

/** 获取可用视频流通道列表 */
export function getStreamList (params) {
  return request({
    url: '/stream/list',
    method: 'get',
    params
  })
}

/** 获取绑定了视频流的门禁终端列表 */
export function getGatesWithStream (params) {
  return request({
    url: '/gate/with-stream',
    method: 'get',
    params
  })
}

/** 获取历史录像列表 */
export function getRecordings (params) {
  return request({
    url: '/video-monitor/recordings',
    method: 'get',
    params
  })
}

/** 删除历史录像 */
export function deleteRecording (filename) {
  return request({
    url: '/video-monitor/recordings/' + filename,
    method: 'delete'
  })
}
