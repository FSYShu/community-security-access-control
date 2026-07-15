import request from '@/utils/request'

export function submitFacePass (data) {
  var silent = data && data._silent
  var config = { url: '/face/pass', method: 'post', data: data, timeout: 30000 }
  if (silent) {
    delete data._silent
    config._silent = true
  }
  return request(config)
}

export function createLivenessChallenge () {
  return request({ url: '/face/liveness-challenge', method: 'post' })
}

export function verifyLivenessFrame (data) {
  return request({ url: '/face/liveness-verify', method: 'post', data, timeout: 10000 })
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

export function getFacePassRecords (params) {
  return request({ url: '/face/pass/records', method: 'get', params })
}

export function getFacePassStats (params) {
  return request({ url: '/face/pass/stats', method: 'get', params })
}
