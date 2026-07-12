import request from '@/utils/request'

export function getGateList (params) {
  return request({ url: '/gate/list', method: 'get', params })
}

export function bindGate (gateId) {
  return request({ url: '/gate/' + gateId + '/bind', method: 'post' })
}

export function unbindGate (gateId) {
  return request({ url: '/gate/' + gateId + '/unbind', method: 'post' })
}
