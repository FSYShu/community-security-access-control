import { login, logout, getUserInfo } from '@/api/auth'

const state = {
  token: localStorage.getItem('gate_token') || '',
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
    localStorage.removeItem('gate_token')
  }
}

const actions = {
  async loginAction ({ commit }, loginForm) {
    var res = await login(loginForm)
    var token = res.data.token
    commit('SET_TOKEN', token)
    localStorage.setItem('gate_token', token)
    return res
  },
  async getUserInfoAction ({ commit }) {
    var res = await getUserInfo()
    var userData = res.data
    commit('SET_USER_INFO', userData)
    var roles = userData.roles || (userData.role ? [userData.role] : [])
    commit('SET_ROLES', roles)
    return res.data
  },
  async logoutAction ({ commit }) {
    try {
      await logout()
    } finally {
      commit('CLEAR_USER')
    }
  }
}

const getters = {
  token: function (state) { return state.token },
  userInfo: function (state) { return state.userInfo },
  roles: function (state) { return state.roles },
  isOwner: function (state) { return state.roles.includes('owner') },
  isVisitor: function (state) { return state.roles.includes('visitor') }
}

export default {
  namespaced: true,
  state: state,
  mutations: mutations,
  actions: actions,
  getters: getters
}