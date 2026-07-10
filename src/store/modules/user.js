/**
 * 用户状态模块
 * 管理用户登录态、角色权限等信息
 */
import { login, logout, getUserInfo } from '@/api/auth'

const state = {
  token: localStorage.getItem('access_token') || '',
  userInfo: null,
  roles: []
}

const mutations = {
  SET_TOKEN (state, token) {
    state.token = token
  },
  SET_USER_INFO (state, userInfo) {
    state.userInfo = userInfo
  },
  SET_ROLES (state, roles) {
    state.roles = roles
  },
  CLEAR_USER (state) {
    state.token = ''
    state.userInfo = null
    state.roles = []
    localStorage.removeItem('access_token')
  }
}

const actions = {
  /** 用户登录 */
  async loginAction ({ commit }, loginForm) {
    const res = await login(loginForm)
    const token = res.data.token
    commit('SET_TOKEN', token)
    localStorage.setItem('access_token', token)
    return res
  },

  /** 获取用户信息 */
  async getUserInfoAction ({ commit }) {
    const res = await getUserInfo()
    const userData = res.data
    commit('SET_USER_INFO', userData)
    const roles = userData.roles || (userData.role ? [userData.role] : [])
    commit('SET_ROLES', roles)
    return res.data
  },

  /** 用户登出 */
  async logoutAction ({ commit }) {
    try {
      await logout()
    } finally {
      commit('CLEAR_USER')
    }
  }
}

const getters = {
  token: state => state.token,
  userInfo: state => state.userInfo,
  roles: state => state.roles,
  isAdmin: state => state.roles.includes('admin'),
  isGuard: state => state.roles.includes('guard'),
  isOwner: state => state.roles.includes('owner')
}

export default {
  namespaced: true,
  state,
  mutations,
  actions,
  getters
}
