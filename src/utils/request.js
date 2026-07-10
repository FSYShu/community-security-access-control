/**
 * Axios 请求封装
 * 统一处理请求拦截、响应拦截、错误处理
 */
import axios from 'axios'
import { Toast } from 'vant'
import router from '@/router'

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
    // 从 localStorage 获取 token
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
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
    // 业务状态码判断
    if (res.code !== 0) {
      Toast.fail(res.message || '请求失败')
      // token 过期或无效
      if (res.code === 401) {
        localStorage.removeItem('access_token')
        if (router.currentRoute.path !== '/login') {
          router.push('/login')
        }
      }
      return Promise.reject(new Error(res.message || '请求失败'))
    }
    return res
  },
  error => {
    const status = error.response ? error.response.status : 0
    const messageMap = {
      400: '请求参数错误',
      401: '未授权，请重新登录',
      403: '拒绝访问',
      404: '请求资源不存在',
      500: '服务器内部错误'
    }
    const message = messageMap[status] || `网络异常(${status})`
    Toast.fail(message)

    if (status === 401) {
      localStorage.removeItem('access_token')
      if (router.currentRoute.path !== '/login') {
        router.replace('/login').catch(function () {})
      }
    }
    return Promise.reject(error)
  }
)

export default service
