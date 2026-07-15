/**
 * 人脸识别通行相关接口
 */
import request from '@/utils/request'

/** 提交人脸识别通行请求 */
export function submitFacePass (data) {
  return request({
    url: '/face/pass',
    method: 'post',
    data
  })
}

/** 获取通行记录列表 */
export function getPassRecords (params) {
  return request({
    url: '/face/records',
    method: 'get',
    params
  })
}

/** 获取人脸信息列表 */
export function getFaceList (params) {
  return request({
    url: '/face/list',
    method: 'get',
    params
  })
}

/** 新增人脸信息 */
export function addFace (data) {
  return request({
    url: '/face/add',
    method: 'post',
    data
  })
}

/** 更新人脸信息 */
export function updateFace (id, data) {
  return request({
    url: `/face/${id}`,
    method: 'put',
    data
  })
}

/** 删除人脸信息 */
export function deleteFace (id) {
  return request({
    url: `/face/${id}`,
    method: 'delete'
  })
}

/** 申请访客临时授权 */
export function applyVisitorAuth (data) {
  return request({
    url: '/face/visitor-auth',
    method: 'post',
    data
  })
}

/** 人脸注册 */
export function registerFace (data) {
  return request({
    url: '/face/face-register',
    method: 'post',
    data,
    timeout: 60000
  })
}

/** 人脸识别测试 */
export function testFace (data) {
  return request({
    url: '/face/test',
    method: 'post',
    data,
    timeout: 60000
  })
}

/** 创建活体检测挑战 */
export function createLivenessChallenge () {
  return request({
    url: '/face/liveness-challenge',
    method: 'post'
  })
}

/** 提交活体检测帧验证 */
export function verifyLivenessFrame (data) {
  return request({
    url: '/face/liveness-verify',
    method: 'post',
    data,
    timeout: 10000
  })
}
