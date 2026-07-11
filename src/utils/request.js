/**
 * Axios 请求封装
 * 统一处理请求拦截、响应拦截、错误处理
 */
import axios from 'axios'
import { Toast } from 'vant'
import router from '@/router'

let isRedirecting = false

/**
 * 解析 JWT payload，判断 token 是否过期
 * @param {string} token - JWT token
 * @returns {boolean} true 表示已过期或无效
 */
function isTokenExpired (token) {
  try {
    const parts = token.split('.')
    if (parts.length !== 3) return true
    const payload = JSON.parse(atob(parts[1].replace(/-/g, '+').replace(/_/g, '/')))
    if (!payload.exp) return false
    return Date.now() >= payload.exp * 1000
  } catch (e) {
    return true
  }
}

/**
 * 清除登录态并跳转登录页（防抖）
 */
function handleUnauthorized () {
  localStorage.removeItem('access_token')
  if (store) {
    store.commit('user/CLEAR_USER')
  }
  if (!isRedirecting && router.currentRoute.path !== '/login') {
    isRedirecting = true
    const redirect = router.currentRoute.fullPath
    router.replace({ path: '/login', query: { redirect: redirect } }).catch(function () {}).finally(function () {
      setTimeout(function () { isRedirecting = false }, 500)
    })
  }
}

// 延迟引入 store，避免循环依赖
let store = null
function getStore () {
  if (!store) {
    store = require('@/store').default
  }
  return store
}

// 创建 axios 实例
const service = axios.create({
  baseURL: process.env.API_BASE_URL || '/api/v1',
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json;charset=UTF-8'
  }
})

// 请求拦截器
service.interceptors.request.use(
  config => {
    const token = localStorage.getItem('access_token')
    if (token) {
      if (isTokenExpired(token)) {
        handleUnauthorized()
        return Promise.reject(new Error('登录已过期，请重新登录'))
      }
      config.headers.Authorization = 'Bearer ' + token
    }
    return config
  },
  error => {
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
service.interceptors.response.use(
  response => {
    const res = response.data
    if (res.code !== 0) {
      Toast.fail(res.message || '请求失败')
      if (res.code === 401) {
        handleUnauthorized()
      }
      return Promise.reject(new Error(res.message || '请求失败'))
    }
    return res
  },
  error => {
    if (error.message === '登录已过期，请重新登录') {
      Toast.fail(error.message)
      return Promise.reject(error)
    }
    const status = error.response ? error.response.status : 0
    if (status === 429) {
      const config = error.config
      config.__retryCount = config.__retryCount || 0
      if (config.__retryCount < 2) {
        config.__retryCount++
        return new Promise(function (resolve) {
          setTimeout(function () {
            resolve(service(config))
          }, 2000)
        })
      }
      Toast.fail('请求过于频繁，请稍后再试')
      return Promise.reject(error)
    }
    const messageMap = {
      400: '请求参数错误',
      401: '未授权，请重新登录',
      403: '拒绝访问',
      404: '请求资源不存在',
      500: '服务器内部错误'
    }
    const message = messageMap[status] || '网络异常(' + status + ')'
    Toast.fail(message)

    if (status === 401) {
      handleUnauthorized()
    }
    return Promise.reject(error)
  }
)

// 初始化 store 引用
getStore()

export default service
