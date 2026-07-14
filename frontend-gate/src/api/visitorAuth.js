import request from '@/utils/request'

export function applyVisitorAuth (data) {
  return request({ url: '/visitor-auth/apply', method: 'post', data })
}

export function getVisitorAuthList (params) {
  return request({ url: '/visitor-auth/list', method: 'get', params })
}

export function approveVisitorAuth (id, data) {
  return request({ url: '/visitor-auth/' + id + '/approve', method: 'put', data })
}

export function gateGetVisitorAuthList (params) {
  return request({ url: '/visitor-auth/gate-list', method: 'get', params })
}

export function gateApproveVisitorAuth (id, data) {
  return request({ url: '/visitor-auth/gate-approve/' + id, method: 'put', data })
}

export function gateApplyVisitorAuth (data) {
  return request({ url: '/visitor-auth/gate-apply', method: 'post', data })
}

export function gateDeleteVisitorAuth (id, data) {
  return request({ url: '/visitor-auth/gate-delete/' + id, method: 'delete', data })
}
