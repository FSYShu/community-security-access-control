/**
 * Vuex Store 入口文件
 * 统一管理应用状态
 */
import Vue from 'vue'
import Vuex from 'vuex'
import user from './modules/user'
import alarm from './modules/alarm'

Vue.use(Vuex)

export default new Vuex.Store({
  modules: {
    user,
    alarm
  }
})