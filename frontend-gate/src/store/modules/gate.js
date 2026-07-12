var STORAGE_KEY = 'gate_bound_info'

function loadFromStorage () {
  var result = { gateId: '', gateName: '', pushKey: '', gateLevel: '', location: '' }
  try {
    var data = localStorage.getItem(STORAGE_KEY)
    if (data) {
      var parsed = JSON.parse(data)
      result.gateId = parsed.gateId || ''
      result.gateName = parsed.gateName || ''
      result.pushKey = parsed.pushKey || ''
      result.gateLevel = parsed.gateLevel || ''
      result.location = parsed.location || ''
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
    state.location = gateInfo.location || ''
    localStorage.setItem(STORAGE_KEY, JSON.stringify({
      gateId: state.gateId,
      gateName: state.gateName,
      pushKey: state.pushKey,
      gateLevel: state.gateLevel,
      location: state.location
    }))
  },
  CLEAR_GATE (state) {
    state.gateId = ''
    state.gateName = ''
    state.pushKey = ''
    state.gateLevel = ''
    state.location = ''
    localStorage.removeItem(STORAGE_KEY)
  }
}

var getters = {
  isBound: function (state) { return !!state.gateId },
  gateId: function (state) { return state.gateId },
  gateName: function (state) { return state.gateName },
  pushKey: function (state) { return state.pushKey },
  gateLevel: function (state) { return state.gateLevel },
  location: function (state) { return state.location }
}

export default {
  namespaced: true,
  state: loadFromStorage,
  mutations: mutations,
  getters: getters
}
