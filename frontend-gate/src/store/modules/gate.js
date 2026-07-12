var STORAGE_KEY = 'gate_bound_info'

function loadFromStorage () {
  var result = { gateId: '', gateName: '', pushKey: '', gateLevel: '' }
  try {
    var data = localStorage.getItem(STORAGE_KEY)
    if (data) {
      var parsed = JSON.parse(data)
      result.gateId = parsed.gateId || ''
      result.gateName = parsed.gateName || ''
      result.pushKey = parsed.pushKey || ''
      result.gateLevel = parsed.gateLevel || ''
    }
  } catch (e) {
    // ignore
  }
  return result
}

var mutations = {
  SET_GATE (state, gateInfo) {
    state.gateId = String(gateInfo.id || '')
    state.gateName = gateInfo.gate_name || ''
    state.pushKey = gateInfo.push_key || ''
    state.gateLevel = gateInfo.gate_level || ''
    localStorage.setItem(STORAGE_KEY, JSON.stringify({
      gateId: state.gateId,
      gateName: state.gateName,
      pushKey: state.pushKey,
      gateLevel: state.gateLevel
    }))
  },
  CLEAR_GATE (state) {
    state.gateId = ''
    state.gateName = ''
    state.pushKey = ''
    state.gateLevel = ''
    localStorage.removeItem(STORAGE_KEY)
  }
}

var getters = {
  isBound: function (state) { return !!state.gateId },
  gateId: function (state) { return state.gateId },
  gateName: function (state) { return state.gateName },
  pushKey: function (state) { return state.pushKey },
  gateLevel: function (state) { return state.gateLevel }
}

export default {
  namespaced: true,
  state: loadFromStorage,
  mutations: mutations,
  getters: getters
}
