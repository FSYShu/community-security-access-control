import request from '@/utils/request'

export function submitFacePass (data) {
  return request({ url: '/face/pass', method: 'post', data, timeout: 30000 })
}

export function getFaceList (params) {
  return request({ url: '/face/list', method: 'get', params })
}

export function updateFace (id, data) {
  return request({ url: '/face/' + id, method: 'put', data })
}

export function deleteFace (id) {
  return request({ url: '/face/' + id, method: 'delete' })
}

export function registerFace (data) {
  return request({ url: '/face/face-register', method: 'post', data, timeout: 60000 })
}