/**
 * 告警状态模块
 * 管理告警实时数据与未读数量
 */
const state = {
  unreadCount: 0,
  latestAlarms: []
}

const mutations = {
  SET_UNREAD_COUNT (state, count) {
    state.unreadCount = count
  },
  SET_LATEST_ALARMS (state, alarms) {
    state.latestAlarms = alarms
  },
  INCREMENT_UNREAD (state) {
    state.unreadCount += 1
  },
  DECREMENT_UNREAD (state) {
    if (state.unreadCount > 0) {
      state.unreadCount -= 1
    }
  }
}

const actions = {
  /** 新告警到达 */
  onNewAlarm ({ commit }, alarm) {
    commit('INCREMENT_UNREAD')
    commit('SET_LATEST_ALARMS', [alarm, ...state.latestAlarms.slice(0, 49)])
  },

  /** 重置未读数量 */
  resetUnread ({ commit }) {
    commit('SET_UNREAD_COUNT', 0)
  }
}

const getters = {
  unreadCount: state => state.unreadCount,
  latestAlarms: state => state.latestAlarms
}

export default {
  namespaced: true,
  state,
  mutations,
  actions,
  getters
}
