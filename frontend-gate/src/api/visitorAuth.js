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
