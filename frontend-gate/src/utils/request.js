import axios from 'axios'
import { Toast } from 'vant'

let isRedirecting = false

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

function handleUnauthorized () {
  localStorage.removeItem('gate_token')
  if (window.gateStore) {
    window.gateStore.commit('user/CLEAR_USER')
  }
  if (!isRedirecting && window.location.hash !== '#/login') {
    isRedirecting = true
    window.location.hash = '#/login'
    setTimeout(function () { isRedirecting = false }, 500)
  }
}

const service = axios.create({
  baseURL: '/api/v1',
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json;charset=UTF-8'
  }
})

service.interceptors.request.use(
  function (config) {
    const token = localStorage.getItem('gate_token')
    if (token) {
      if (isTokenExpired(token)) {
        handleUnauthorized()
        return Promise.reject(new Error('登录已过期，请重新登录'))
      }
      config.headers.Authorization = 'Bearer ' + token
    }
    return config
  },
  function (error) {
    return Promise.reject(error)
  }
)

service.interceptors.response.use(
  function (response) {
    const res = response.data
    const silent = response.config && response.config._silent
    if (res.code !== 0) {
      if (!silent) {
        Toast.fail(res.message || '请求失败')
      }
      if (res.code === 401) {
        handleUnauthorized()
      }
      return Promise.reject(new Error(res.message || '请求失败'))
    }
    return res
  },
  function (error) {
    const silent = error.config && error.config._silent
    if (error.message === '登录已过期，请重新登录') {
      if (!silent) {
        Toast.fail(error.message)
      }
      return Promise.reject(error)
    }
    const status = error.response ? error.response.status : 0
    const messageMap = {
      400: '请求参数错误',
      401: '未授权，请重新登录',
      403: '拒绝访问',
      404: '请求资源不存在',
      500: '服务器内部错误'
    }
    const message = (error.response && error.response.data && error.response.data.message) || messageMap[status] || '网络异常'
    if (!silent) {
      Toast.fail(message)
    }
    if (status === 401) {
      handleUnauthorized()
    }
    return Promise.reject(error)
  }
)

export default service
