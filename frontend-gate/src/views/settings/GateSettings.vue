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
        </div>
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
      previewStream: null
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
      var item = this.list.find(function (g) { return String(g.id) === this.selectedGateId }.bind(this))
      return item ? item.gate_name : ''
    },
    sortedList () {
      var boundId = this.gateId
      var unbound = []
      var bound = []
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
        var res = await getGateList({ page: 1, per_page: 200 })
        var data = res.data
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
        var stream = await navigator.mediaDevices.getUserMedia({ video: true })
        stream.getTracks().forEach(function (t) { t.stop() })
        var devices = await navigator.mediaDevices.enumerateDevices()
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
        var constraints = { video: { width: { ideal: 320 }, height: { ideal: 240 } } }
        if (deviceId) {
          constraints.video.deviceId = { exact: deviceId }
        }
        this.previewStream = await navigator.mediaDevices.getUserMedia(constraints)
        var self = this
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
</style>
