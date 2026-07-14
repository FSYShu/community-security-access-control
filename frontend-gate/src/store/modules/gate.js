var STORAGE_KEY = 'gate_bound_info'
var GATES_CACHE_KEY = 'gate_list_cache'

function loadFromStorage () {
  var result = { gateId: '', gateName: '', pushKey: '', gateLevel: '', cameraDeviceId: '', cameraLabel: '' }
  try {
    var data = localStorage.getItem(STORAGE_KEY)
    if (data) {
      var parsed = JSON.parse(data)
      result.gateId = parsed.gateId || ''
      result.gateName = parsed.gateName || ''
      result.pushKey = parsed.pushKey || ''
      result.gateLevel = parsed.gateLevel || ''
      result.cameraDeviceId = parsed.cameraDeviceId || ''
      result.cameraLabel = parsed.cameraLabel || ''
    }
  } catch (e) {
    // ignore
  }
  return result
}

function loadGatesCache () {
  try {
    var data = localStorage.getItem(GATES_CACHE_KEY)
    if (data) return JSON.parse(data)
  } catch (e) {
    // ignore
  }
  return []
}

const mutations = {
  SET_GATE (state, gateInfo) {
    state.gateId = String(gateInfo.id || '')
    state.gateName = gateInfo.gate_name || ''
    state.pushKey = gateInfo.push_key || ''
    state.gateLevel = gateInfo.gate_level || ''
    localStorage.setItem(STORAGE_KEY, JSON.stringify({
      gateId: state.gateId,
      gateName: state.gateName,
      pushKey: state.pushKey,
      gateLevel: state.gateLevel,
      cameraDeviceId: state.cameraDeviceId,
      cameraLabel: state.cameraLabel
    }))
  },
  SET_CAMERA (state, payload) {
    state.cameraDeviceId = payload.deviceId || ''
    state.cameraLabel = payload.label || ''
    localStorage.setItem(STORAGE_KEY, JSON.stringify({
      gateId: state.gateId,
      gateName: state.gateName,
      pushKey: state.pushKey,
      gateLevel: state.gateLevel,
      cameraDeviceId: state.cameraDeviceId,
      cameraLabel: state.cameraLabel
    }))
  },
  CLEAR_GATE (state) {
    state.gateId = ''
    state.gateName = ''
    state.pushKey = ''
    state.gateLevel = ''
    state.cameraDeviceId = ''
    state.cameraLabel = ''
    localStorage.removeItem(STORAGE_KEY)
  },
  SET_GATES_CACHE (state, items) {
    state.gatesCache = items
    localStorage.setItem(GATES_CACHE_KEY, JSON.stringify(items))
  }
}

var getters = {
  isBound: function (state) { return !!state.gateId },
  gateId: function (state) { return state.gateId },
  gateName: function (state) { return state.gateName },
  pushKey: function (state) { return state.pushKey },
  gateLevel: function (state) { return state.gateLevel },
  cameraDeviceId: function (state) { return state.cameraDeviceId },
  cameraLabel: function (state) { return state.cameraLabel },
  gatesCache: function (state) { return state.gatesCache }
}

export default {
  namespaced: true,
  state: function () {
    var base = loadFromStorage()
    base.gatesCache = loadGatesCache()
    return base
  },
  mutations: mutations,
  getters: getters
}
