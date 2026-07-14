import Vue from 'vue'
import Vuex from 'vuex'
import user from './modules/user'
import gate from './modules/gate'

Vue.use(Vuex)

const store = new Vuex.Store({
  modules: {
    user: user,
    gate: gate
  }
})

window.gateStore = store

export default store
