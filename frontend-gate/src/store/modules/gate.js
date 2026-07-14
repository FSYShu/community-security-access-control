const STORAGE_KEY = 'gate_bound_info'

function loadFromStorage () {
  const result = { gateId: '', gateName: '', pushKey: '', gateLevel: '', cameraDeviceId: '', cameraLabel: '' }
  try {
    const data = localStorage.getItem(STORAGE_KEY)
    if (data) {
      const parsed = JSON.parse(data)
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
  }
}

const getters = {
  isBound: function (state) { return !!state.gateId },
  gateId: function (state) { return state.gateId },
  gateName: function (state) { return state.gateName },
  pushKey: function (state) { return state.pushKey },
  gateLevel: function (state) { return state.gateLevel },
  cameraDeviceId: function (state) { return state.cameraDeviceId },
  cameraLabel: function (state) { return state.cameraLabel }
}

export default {
  namespaced: true,
  state: loadFromStorage,
  mutations: mutations,
  getters: getters
}
