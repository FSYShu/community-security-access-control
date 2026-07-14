/**
 * 登录认证相关接口
 */
import request from '@/utils/request'

/** 用户登录 */
export function login (data) {
  return request({
    url: '/auth/login',
    method: 'post',
    data
  })
}

/** 用户登出 */
export function logout () {
  return request({
    url: '/auth/logout',
    method: 'post'
  })
}

/** 获取当前用户信息 */
export function getUserInfo () {
  return request({
    url: '/auth/userinfo',
    method: 'get'
  })
}

/** 获取用户列表 */
export function getUserList (params) {
  return request({ url: '/auth/users', method: 'get', params })
}

/** 注册新用户 */
export function registerUser (data) {
  return request({ url: '/auth/register', method: 'post', data })
}

/** 获取指定用户信息 */
export function getUserDetail (userId) {
  return request({ url: `/auth/users/${userId}`, method: 'get' })
}

/** 更新用户信息 */
export function updateUser (userId, data) {
  return request({ url: `/auth/users/${userId}`, method: 'put', data })
}

/** 删除用户 */
export function deleteUser (userId) {
  return request({ url: `/auth/users/${userId}`, method: 'delete' })
}

/** 获取角色权限说明 */
export function getRolePermissions () {
  return request({ url: '/auth/role-permissions', method: 'get' })
}
