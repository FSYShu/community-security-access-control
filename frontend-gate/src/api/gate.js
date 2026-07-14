import request from '@/utils/request'

export function getGateList (params) {
  return request({ url: '/gate/list', method: 'get', params })
}

export function getPublicAddresses () {
  return request({ url: '/gate/public-addresses', method: 'get' })
}

export function bindGate (gateId) {
  return request({ url: '/gate/' + gateId + '/bind', method: 'post' })
}

export function getGateDetail (gateId, extraConfig) {
  return request(Object.assign({ url: '/gate/' + gateId, method: 'get', _silent: true }, extraConfig))
}

export function unbindGate (gateId) {
  return request({ url: '/gate/' + gateId + '/unbind', method: 'post' })
}
