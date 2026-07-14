<template>
  <div class="gate-page settings-page">
    <div class="gate-header">
      <i class="el-icon-arrow-left" style="font-size:20px;color:#9ca3af" @click="$router.push('/idle')"></i>
      <span class="gate-header-title">门禁终端设置</span>
      <span style="width:20px;"></span>
    </div>
    <div class="gate-content">
      <div class="gate-card">
        <div class="setting-section-title">选择门禁终端</div>
        <div class="custom-select" :class="{ 'is-open': showDropdown }">
          <div class="custom-select-trigger" @click="toggleDropdown">
            <span class="custom-select-value">{{ selectedLabel || '请选择门禁终端' }}</span>
            <i class="el-icon-arrow-down custom-select-arrow" :class="{ 'is-reverse': showDropdown }"></i>
          </div>
          <transition name="dropdown-slide">
            <div v-if="showDropdown" class="custom-select-dropdown">
              <div
                v-for="item in sortedList"
                :key="item.id"
                class="custom-select-option"
                :class="{ 'is-bound': isCurrentBound(item) }"
                @click="onGateSelect(item)"
              >
                <div class="option-main">
                  <span class="option-name">{{ item.gate_name }}</span>
                  <span class="option-level-tag" :class="'tag-' + item.gate_level">{{ levelMap[item.gate_level] || item.gate_level }}</span>
                </div>
                <span v-if="isCurrentBound(item)" class="option-bound-tag">已绑定</span>
              </div>
              <div v-if="sortedList.length === 0" class="custom-select-empty">暂无门禁终端</div>
            </div>
          </transition>
        </div>
      </div>

      <div class="gate-card">
        <div class="setting-section-title">当前绑定</div>
        <div v-if="isBound" class="bound-info">
          <div class="bound-row">
            <span class="bound-label">终端名称</span>
            <span class="bound-value">{{ gateName }}</span>
          </div>
          <div class="bound-row">
            <span class="bound-label">终端层级</span>
            <span class="bound-value">{{ levelMap[gateLevel] || gateLevel }}</span>
          </div>
          <div class="bound-row">
            <span class="bound-label">推流码</span>
            <span class="bound-value">{{ pushKey || '未配置' }}</span>
          </div>
          <button class="gate-btn gate-btn-danger" style="margin-top:12px;" @click="unbindGate">解除绑定</button>
        </div>
        <div v-else class="unbound-hint">
          <i class="el-icon-info" style="font-size:24px;color:#f59e0b"></i>
          <p>尚未绑定门禁终端，请选择要绑定的终端</p>
        </div>
      </div>

      <div class="gate-card">
        <div class="setting-section-title">功能设置</div>
        <div class="setting-row">
          <div class="setting-row-info">
            <span class="setting-row-label">实时人脸识别</span>
            <span class="setting-row-desc">开启后将实时检测并识别人脸</span>
          </div>
          <van-switch v-model="faceRecognitionEnabled" size="20px" disabled />
        </div>
        <div class="setting-divider"></div>
        <div class="setting-row-label" style="margin-bottom:8px;">摄像头选择</div>
        <div class="custom-select" :class="{ 'is-open': showCameraDropdown }">
          <div class="custom-select-trigger" @click="toggleCameraDropdown">
            <span class="custom-select-value">{{ currentCameraLabel || '请选择摄像头' }}</span>
            <i class="el-icon-arrow-down custom-select-arrow" :class="{ 'is-reverse': showCameraDropdown }"></i>
          </div>
          <transition name="dropdown-slide">
            <div v-if="showCameraDropdown" class="custom-select-dropdown">
              <div
                v-for="cam in cameraList"
                :key="cam.deviceId"
                class="custom-select-option"
                :class="{ 'is-active': cam.deviceId === selectedCameraId }"
                @click="onCameraSelect(cam)"
              >
                <div class="option-main">
                  <i class="el-icon-camera" style="font-size:16px;color:var(--gate-text-muted)"></i>
                  <span class="option-name">{{ cam.label || '未命名摄像头' }}</span>
                </div>
                <i v-if="cam.deviceId === selectedCameraId" class="el-icon-circle-check" style="font-size:14px;color:var(--gate-accent, #818cf8)"></i>
              </div>
              <div v-if="cameraList.length === 0" class="custom-select-empty">未检测到摄像头</div>
            </div>
          </transition>
        </div>
        <div v-if="previewStream" class="camera-preview-wrap">
          <video ref="previewVideo" class="camera-preview" autoplay playsinline muted></video>
          <div class="camera-preview-badge">预览</div>
          <div v-if="liveDistance !== null" class="camera-dist-live">{{ liveDistance }}m</div>
        </div>
        <template v-if="isBound">
          <div class="setting-divider" style="margin-top:12px;"></div>
          <div class="setting-section-title" style="margin-top:4px;">距离校准</div>
          <p class="calib-hint">分别在近处和远处各校准一次，两点校准更准确。先站在近处（如1米），再站在远处（如3米）。</p>
          <div class="calib-form-row">
            <span class="calib-form-label">校准点</span>
            <div class="calib-point-select">
              <button class="calib-point-btn" :class="{ 'is-active': calibPoint === 'near' }" @click="calibPoint = 'near'">近点</button>
              <button class="calib-point-btn" :class="{ 'is-active': calibPoint === 'far' }" @click="calibPoint = 'far'">远点</button>
            </div>
          </div>
          <div class="calib-form-row">
            <span class="calib-form-label">实际距离(米)</span>
            <input v-model.number="calibDistance" class="calib-input" type="number" step="0.1" min="0.5" max="20" />
          </div>
          <div v-if="calibNearDist || calibFarDist" class="calib-status">
            <span v-if="calibNearDist" class="calib-status-item calib-near">近点: {{ calibNearDist }}m (比例{{ calibNearRatio }})</span>
            <span v-if="calibFarDist" class="calib-status-item calib-far">远点: {{ calibFarDist }}m (比例{{ calibFarRatio }})</span>
          </div>
          <p v-if="calibResult" class="calib-result" :class="calibSuccess ? 'calib-success' : 'calib-error'">{{ calibResult }}</p>
          <button class="gate-btn gate-btn-primary" style="margin-top:12px;" :disabled="calibLoading" @click="doCalibrate">{{ calibLoading ? '校准中...' : '校准此点' }}</button>
        </template>
      </div>
    </div>
  </div>
</template>

<script>
import { getGateList, bindGate as bindGateApi, unbindGate as unbindGateApi } from '@/api/gate'

export default {
  name: 'GateSettingsPage',
  data () {
    return {
      list: [],
      showDropdown: false,
      selectedGateId: '',
      faceRecognitionEnabled: false,
      levelMap: { community_gate: '社区大门', unit_door: '单元门', dangerous_area: '危险防护区域' },
      showCameraDropdown: false,
      cameraList: [],
      selectedCameraId: '',
      previewStream: null,
      calibDistance: 1.0,
      calibPoint: 'near',
      calibLoading: false,
      calibResult: '',
      calibSuccess: false,
      calibNearDist: null,
      calibNearRatio: null,
      calibFarDist: null,
      calibFarRatio: null,
      liveDistance: null,
      distDetectTimer: null,
      distFailCount: 0
    }
  },
  computed: {
    isBound () { return this.$store.getters['gate/isBound'] },
    gateId () { return this.$store.getters['gate/gateId'] },
    gateName () { return this.$store.getters['gate/gateName'] },
    pushKey () { return this.$store.getters['gate/pushKey'] },
    gateLevel () { return this.$store.getters['gate/gateLevel'] },
    currentCameraLabel () { return this.$store.getters['gate/cameraLabel'] },
    selectedLabel () {
      if (!this.selectedGateId) return ''
      const item = this.list.find(function (g) { return String(g.id) === this.selectedGateId }.bind(this))
      return item ? item.gate_name : ''
    },
    sortedList () {
      const boundId = this.gateId
      const unbound = []
      const bound = []
      this.list.forEach(function (item) {
        if (String(item.id) === boundId) {
          bound.push(item)
        } else {
          unbound.push(item)
        }
      })
      unbound.sort(function (a, b) { return a.id - b.id })
      return unbound.concat(bound)
    }
  },
  created () {
    this.selectedGateId = this.$store.getters['gate/gateId'] || ''
    this.selectedCameraId = this.$store.getters['gate/cameraDeviceId'] || ''
    this.loadGateList()
    this.refreshCameras()
    document.addEventListener('click', this.onDocumentClick)
  },
  beforeDestroy () {
    this.$store.commit('user/CLEAR_USER')
    document.removeEventListener('click', this.onDocumentClick)
    this.stopPreview()
    this.stopDistDetect()
  },
  methods: {
    onDocumentClick (e) {
      if (!e.target.closest('.custom-select')) {
        this.showDropdown = false
        this.showCameraDropdown = false
      }
    },
    toggleDropdown () {
      this.showDropdown = !this.showDropdown
      this.showCameraDropdown = false
    },
    toggleCameraDropdown () {
      this.showCameraDropdown = !this.showCameraDropdown
      this.showDropdown = false
    },
    async loadGateList () {
      try {
        const res = await getGateList({ page: 1, per_page: 200 })
        const data = res.data
        if (data && data.items) {
          this.list = data.items
        }
      } catch (err) {
        // ignore
      }
    },
    async onGateSelect (item) {
      if (this.isCurrentBound(item)) return
      this.showDropdown = false
      try {
        if (this.gateId) {
          await unbindGateApi(this.gateId)
        }
        await bindGateApi(item.id)
        this.selectedGateId = String(item.id)
        this.$store.commit('gate/SET_GATE', item)
        this.$toast.success('已绑定：' + item.gate_name)
      } catch (e) {
        this.$toast.fail('绑定失败')
      }
    },
    isCurrentBound (item) {
      return String(item.id) === this.gateId
    },
    async unbindGate () {
      try {
        await unbindGateApi(this.gateId)
        this.selectedGateId = ''
        this.$store.commit('gate/CLEAR_GATE')
        this.$toast.success('已解除绑定')
      } catch (e) {
        this.$toast.fail('解绑失败')
      }
    },
    async refreshCameras () {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true })
        stream.getTracks().forEach(function (t) { t.stop() })
        const devices = await navigator.mediaDevices.enumerateDevices()
        this.cameraList = devices.filter(function (d) { return d.kind === 'videoinput' })
      } catch (e) {
        this.cameraList = []
      }
    },
    onCameraSelect (cam) {
      this.selectedCameraId = cam.deviceId
      this.$store.commit('gate/SET_CAMERA', { deviceId: cam.deviceId, label: cam.label || '未命名摄像头' })
      this.showCameraDropdown = false
      this.$toast.success('已切换摄像头')
      this.startPreview(cam.deviceId)
    },
    async startPreview (deviceId) {
      this.stopPreview()
      try {
        const constraints = { video: { width: { ideal: 320 }, height: { ideal: 240 } } }
        if (deviceId) {
          constraints.video.deviceId = { exact: deviceId }
        }
        this.previewStream = await navigator.mediaDevices.getUserMedia(constraints)
        const self = this
        this.$nextTick(function () {
          if (self.$refs.previewVideo) {
            self.$refs.previewVideo.srcObject = self.previewStream
          }
        })
      } catch (e) {
        this.previewStream = null
      }
    },
    stopPreview () {
      if (this.previewStream) {
        this.previewStream.getTracks().forEach(function (t) { t.stop() })
        this.previewStream = null
      }
      this.stopDistDetect()
    },
    startDistDetect () {
      this.stopDistDetect()
      if (!this.isBound) return
      const self = this
      this.distDetectTimer = setInterval(function () {
        self.detectDistance()
      }, 2000)
    },
    stopDistDetect () {
      if (this.distDetectTimer) {
        clearInterval(this.distDetectTimer)
        this.distDetectTimer = null
      }
      this.liveDistance = null
    },
    async detectDistance () {
      if (!this.$refs.previewVideo || !this.previewStream || !this.gateId) return
      try {
        const canvas = document.createElement('canvas')
        const video = this.$refs.previewVideo
        const w = Math.min(video.videoWidth || 320, 320)
        const h = Math.min(video.videoHeight || 240, 240)
        canvas.width = w
        canvas.height = h
        canvas.getContext('2d').drawImage(video, 0, 0, w, h)
        const blob = await new Promise(function (resolve) { canvas.toBlob(resolve, 'image/jpeg', 0.5) })
        if (!blob) return
        const formData = new FormData()
        formData.append('frame', blob, 'frame.jpg')
        const url = '/api/v1/video-monitor/detect-distance/' + this.gateId
        const headers = {}
        const token = localStorage.getItem('gate_token')
        if (token) { headers.Authorization = 'Bearer ' + token }
        const res = await fetch(url, { method: 'POST', headers: headers, body: formData })
        const data = await res.json()
        if (data.code === 0 && data.data && data.data.persons && data.data.persons.length > 0) {
          const d = data.data.persons[0].distance
          if (d !== null && d !== undefined) {
            this.liveDistance = d
            this.distFailCount = 0
          } else {
            this.distFailCount++
            if (this.distFailCount >= 3) { this.liveDistance = null }
          }
        } else {
          this.distFailCount++
          if (this.distFailCount >= 3) { this.liveDistance = null }
        }
      } catch (e) {
        this.distFailCount++
        if (this.distFailCount >= 3) { this.liveDistance = null }
      }
    },
    async doCalibrate () {
      if (!this.calibDistance || this.calibDistance <= 0) {
        this.$toast.fail('请输入有效距离')
        return
      }
      const formData = new FormData()
      formData.append('distance', String(parseFloat(this.calibDistance)))
      formData.append('point', this.calibPoint)
      if (this.$refs.previewVideo && this.previewStream) {
        try {
          const canvas = document.createElement('canvas')
          const video = this.$refs.previewVideo
          const w = Math.min(video.videoWidth || 320, 320)
          const h = Math.min(video.videoHeight || 240, 240)
          canvas.width = w
          canvas.height = h
          canvas.getContext('2d').drawImage(video, 0, 0, w, h)
          const blob = await new Promise(function (resolve) { canvas.toBlob(resolve, 'image/jpeg', 0.7) })
          if (blob) { formData.append('frame', blob, 'frame.jpg') }
        } catch (e) { /* ignore */ }
      }
      this.calibLoading = true
      this.calibResult = ''
      try {
        const url = '/api/v1/video-monitor/calibrate-distance/' + this.gateId
        const headers = {}
        const token = localStorage.getItem('gate_token')
        if (token) { headers.Authorization = 'Bearer ' + token }
        const res = await fetch(url, {
          method: 'POST',
          headers: headers,
          body: formData
        })
        const data = await res.json()
        if (data.code === 0) {
          this.calibSuccess = true
          const label = this.calibPoint === 'near' ? '近点' : '远点'
          this.calibResult = label + '校准成功！' + data.data[this.calibPoint === 'near' ? 'calib_near_dist' : 'calib_far_dist'] + '米'
          this.calibNearDist = data.data.calib_near_dist
          this.calibNearRatio = data.data.calib_near_ratio
          this.calibFarDist = data.data.calib_far_dist
          this.calibFarRatio = data.data.calib_far_ratio
        } else {
          this.calibSuccess = false
          this.calibResult = data.error || '校准失败'
        }
      } catch (e) {
        this.calibSuccess = false
        this.calibResult = '请求失败: ' + e.message
      } finally {
        this.calibLoading = false
      }
    }
  },
  watch: {
    selectedCameraId: {
      immediate: true,
      handler (val) {
        if (val) {
          this.startPreview(val)
        }
      }
    },
    isBound (val) {
      if (val && this.previewStream) {
        this.startDistDetect()
      } else {
        this.stopDistDetect()
      }
    },
    previewStream (val) {
      if (val && this.isBound) {
        this.startDistDetect()
      } else {
        this.stopDistDetect()
      }
    }
  }
}
</script>

<style scoped>
.setting-section-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--gate-text-secondary);
  margin-bottom: 12px;
  text-transform: uppercase;
  letter-spacing: 1px;
}
.custom-select {
  position: relative;
}
.custom-select-trigger {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--gate-border);
  border-radius: var(--gate-radius-sm, 8px);
  cursor: pointer;
  transition: border-color 0.2s;
}
.custom-select.is-open .custom-select-trigger {
  border-color: var(--gate-accent, #818cf8);
}
.custom-select-value {
  font-size: 14px;
  color: var(--gate-text);
}
.custom-select-arrow {
  font-size: 14px;
  color: var(--gate-text-muted);
  transition: transform 0.2s;
}
.custom-select-arrow.is-reverse {
  transform: rotate(180deg);
}
.custom-select-dropdown {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  right: 0;
  background: var(--gate-bg-secondary, #1e1e2e);
  border: 1px solid var(--gate-border);
  border-radius: var(--gate-radius-sm, 8px);
  padding: 4px 0;
  z-index: 100;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
  max-height: 240px;
  overflow-y: auto;
}
.custom-select-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  cursor: pointer;
  transition: background 0.15s;
}
.custom-select-option:active {
  background: rgba(255, 255, 255, 0.06);
}
.custom-select-option.is-bound {
  opacity: 0.45;
}
.custom-select-option.is-bound .option-name,
.custom-select-option.is-bound .option-level-tag {
  opacity: 0.7;
}
.option-main {
  display: flex;
  align-items: center;
  gap: 8px;
}
.option-name {
  font-size: 14px;
  color: var(--gate-text);
}
.option-level-tag {
  display: inline-block;
  padding: 1px 6px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
}
.tag-community_gate {
  background: rgba(16, 185, 129, 0.15);
  color: #10b981;
}
.tag-unit_door {
  background: rgba(99, 102, 241, 0.15);
  color: #818cf8;
}
.tag-dangerous_area {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
}
.option-bound-tag {
  font-size: 11px;
  color: var(--gate-text-muted);
  padding: 1px 6px;
  border: 1px solid var(--gate-border);
  border-radius: 4px;
}
.custom-select-empty {
  text-align: center;
  padding: 16px 0;
  color: var(--gate-text-muted);
  font-size: 13px;
}
.dropdown-slide-enter-active,
.dropdown-slide-leave-active {
  transition: opacity 0.2s, transform 0.2s;
}
.dropdown-slide-enter,
.dropdown-slide-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}
.bound-info {
  padding: 4px 0;
}
.bound-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 0;
}
.bound-label {
  font-size: 13px;
  color: var(--gate-text-muted);
}
.bound-value {
  font-size: 14px;
  color: var(--gate-text);
  word-break: break-all;
  max-width: 200px;
  text-align: right;
}
.unbound-hint {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 0;
  color: var(--gate-text-secondary);
  font-size: 14px;
}
.setting-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
}
.setting-row-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.setting-row-label {
  font-size: 14px;
  color: var(--gate-text);
}
.setting-row-desc {
  font-size: 12px;
  color: var(--gate-text-muted);
}
.setting-divider {
  height: 1px;
  background: var(--gate-border);
  margin: 4px 0;
}
.custom-select-option.is-active {
  background: rgba(129, 140, 248, 0.1);
}
.camera-preview-wrap {
  position: relative;
  margin-top: 12px;
  border-radius: var(--gate-radius-sm, 8px);
  overflow: hidden;
  background: #000;
  aspect-ratio: 4 / 3;
}
.camera-preview {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.camera-preview-badge {
  position: absolute;
  top: 8px;
  left: 8px;
  padding: 2px 8px;
  border-radius: 4px;
  background: rgba(0, 0, 0, 0.6);
  color: #fff;
  font-size: 11px;
}
.camera-dist-live {
  position: absolute;
  top: 8px;
  right: 8px;
  padding: 4px 10px;
  border-radius: 6px;
  background: rgba(245, 158, 11, 0.85);
  color: #fff;
  font-size: 14px;
  font-weight: 600;
}
.calib-hint {
  font-size: 12px;
  color: var(--gate-text-muted);
  line-height: 1.6;
  margin-bottom: 8px;
}
.calib-form-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 0;
}
.calib-form-label {
  font-size: 13px;
  color: var(--gate-text-secondary);
  white-space: nowrap;
}
.calib-point-select {
  display: flex;
  gap: 6px;
}
.calib-point-btn {
  padding: 4px 14px;
  border: 1px solid var(--gate-border);
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.04);
  color: var(--gate-text-secondary);
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}
.calib-point-btn.is-active {
  border-color: var(--gate-accent, #818cf8);
  color: var(--gate-accent, #818cf8);
  background: rgba(129, 140, 248, 0.1);
}
.calib-input {
  flex: 1;
  max-width: 120px;
  padding: 6px 10px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--gate-border);
  border-radius: 6px;
  color: var(--gate-text);
  font-size: 13px;
  outline: none;
}
.calib-input:focus {
  border-color: var(--gate-accent, #818cf8);
}
.calib-status {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 8px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 6px;
  margin-top: 4px;
}
.calib-status-item {
  font-size: 11px;
}
.calib-near {
  color: #10b981;
}
.calib-far {
  color: #f59e0b;
}
.calib-result {
  font-size: 12px;
  line-height: 1.5;
  margin-top: 4px;
}
.calib-success {
  color: #10b981;
}
.calib-error {
  color: #ef4444;
}
</style>
