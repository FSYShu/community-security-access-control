import request from '@/utils/request'

export function getGateList (params) {
  return request({ url: '/gate/list', method: 'get', params })
}