
<template>
  <div class="gate-page idle-page">
    <video ref="bgVideo" class="bg-camera" autoplay playsinline muted></video>
    <canvas ref="captureCanvas" style="display:none;"></canvas>
    <div class="idle-top-bar">
      <div class="top-row">
        <div class="community-name">{{ communityName }}</div>
        <div class="top-right">
          <button v-if="isBound" class="gate-badge" @click="$router.push('/settings')">
            <span class="badge-dot" :class="{ 'dot-pulse': streaming }"></span>
            <span class="badge-text">{{ gateName }}{{ streaming ? ' · 推流中' : '' }}</span>
            <i class="el-icon-setting badge-settings-icon" style="font-size:14px"></i>
          </button>
          <button v-else class="gate-badge badge-unbound" @click="$router.push('/settings')">
            <i class="el-icon-warning-outline" style="font-size:14px"></i>
            <span class="badge-text">未绑定终端，点击设置</span>
            <i class="el-icon-setting badge-settings-icon" style="font-size:14px"></i>
          </button>
        </div>
      </div>
      <div class="current-time">
        <span class="time-date">{{ currentDate }}</span>
        <span class="time-clock">{{ currentClock }}</span>
      </div>
    </div>

    <transition name="face-result">
      <div v-if="faceResult" class="face-result-overlay">
        <div class="face-result-card" :class="faceResult.passed ? 'result-success' : 'result-fail'">
          <i :class="faceResult.passed ? 'el-icon-circle-check' : 'el-icon-close'" style="font-size:56px"></i>
          <div class="face-result-title">{{ faceResult.passed ? '认证通过' : '认证失败' }}</div>
          <div v-if="!faceResult.passed && faceResult.reason" class="face-result-reason">{{ faceResult.reason }}</div>
          <div v-if="faceResult.passed && faceResult.personName" class="face-result-name">{{ faceResult.personName }}</div>
        </div>
      </div>
    </transition>

    <van-popup v-model="showVisitorPopup" position="bottom" round :style="{ maxHeight: '85vh', overflow: 'hidden' }">
      <div class="visitor-popup-center">
        <div class="visitor-popup">
          <div class="visitor-popup-header">
            <span class="visitor-popup-title">访客临时通行申请</span>
            <i class="el-icon-close" style="font-size:20px;color:#9ca3af" @click="showVisitorPopup = false"></i>
          </div>
          <div class="visitor-popup-body">
            <div class="v-form-grid">
              <div class="v-form-item">
                <label class="v-form-label">访客人脸照片 <span class="v-form-required">*</span></label>
                <div v-if="visitorFaceCaptured" class="v-face-preview">
                  <img :src="'data:image/jpeg;base64,' + visitorFaceBase64" class="v-face-preview-img" />
                </div>
                <button class="v-capture-btn" @click="captureVisitorFace">
                  <i class="el-icon-camera"></i> {{ visitorFaceCaptured ? '重新采集' : '拍照采集' }}
                </button>
              </div>
              <div class="v-form-item">
                <label class="v-form-label">访问地址 <span class="v-form-required">*</span></label>
                <div class="v-address-row">
                  <div class="v-address-select" :class="{ 'is-open': showBuildingDrop }">
                    <div class="v-select-trigger" @click="toggleDrop('building')">
                      <span :class="visitorForm.building ? '' : 'v-placeholder'">{{ visitorForm.building || '楼栋' }}</span>
                      <i class="el-icon-arrow-down v-select-arrow" :class="{ 'is-reverse': showBuildingDrop }"></i>
                    </div>
                    <transition name="dropdown">
                      <div v-if="showBuildingDrop" class="v-select-dropdown">
                        <div v-for="b in buildingOptions" :key="b" class="v-select-option" :class="{ 'is-active': visitorForm.building === b }" @click="selectBuilding(b)">{{ b }}</div>
                      </div>
                    </transition>
                  </div>
                  <div class="v-address-select" :class="{ 'is-open': showUnitDrop }">
                    <div class="v-select-trigger" @click="toggleDrop('unit')">
                      <span :class="visitorForm.unit ? '' : 'v-placeholder'">{{ visitorForm.unit || '单元' }}</span>
                      <i class="el-icon-arrow-down v-select-arrow" :class="{ 'is-reverse': showUnitDrop }"></i>
                    </div>
                    <transition name="dropdown">
                      <div v-if="showUnitDrop" class="v-select-dropdown">
                        <div v-for="u in unitOptions" :key="u" class="v-select-option" :class="{ 'is-active': visitorForm.unit === u }" @click="selectUnit(u)">{{ u }}</div>
                      </div>
                    </transition>
                  </div>
                  <div class="v-address-select" :class="{ 'is-open': showRoomDrop }">
                    <div class="v-select-trigger" @click="toggleDrop('room')">
                      <span :class="visitorForm.room ? '' : 'v-placeholder'">{{ visitorForm.room || '门牌号' }}</span>
                      <i class="el-icon-arrow-down v-select-arrow" :class="{ 'is-reverse': showRoomDrop }"></i>
                    </div>
                    <transition name="dropdown">
                      <div v-if="showRoomDrop" class="v-select-dropdown">
                        <div v-for="r in roomOptions" :key="r" class="v-select-option" :class="{ 'is-active': visitorForm.room === r }" @click="selectRoom(r)">{{ r }}</div>
                      </div>
                    </transition>
                  </div>
                </div>
              </div>
              <div class="v-form-hint">业主确认后可获得小区大门和单元门的单次通行权</div>
            </div>
            <div class="v-form-footer">
              <button class="v-form-btn v-form-btn-primary v-form-btn-block" :disabled="!canSubmitVisitor || visitorSubmitting" @click="doSubmitVisitor">
                <van-loading v-if="visitorSubmitting" size="16" color="#fff" />
                <span v-else>提交申请</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </van-popup>

    <div v-if="isBound" class="idle-bottom-bar">
      <button
        class="gate-btn gate-btn-primary idle-btn"
        :disabled="faceLoading || !streaming"
        @click="doFacePass"
      >
        <van-loading v-if="faceLoading" size="20" color="#fff" />
        <template v-else>
          <i class="el-icon-camera" style="font-size:24px"></i>
          <span>刷脸通行</span>
        </template>
      </button>
      <button class="gate-btn gate-btn-outline idle-btn" @click="openVisitorApply">
        <i class="el-icon-user" style="font-size:24px"></i>
        <span>访客申请</span>
      </button>
    </div>

    <transition name="fade">
      <div v-if="showUnboundDialog" class="unbound-overlay" @click.prevent>
        <div class="unbound-dialog">
          <div class="unbound-dialog-title">终端未绑定</div>
          <div class="unbound-dialog-message">请先绑定门禁终端后再使用刷脸通行和访客申请功能</div>
          <button class="unbound-dialog-btn" @click="goToSettings">前往设置</button>
        </div>
      </div>
    </transition>
  </div>
</template>

<script>
import GateStreamPusher from '@/utils/stream-pusher'
import { submitFacePass } from '@/api/face'
import { applyVisitorAuth } from '@/api/visitorAuth'
import { enqueue, setupOnlineHandler } from '@/utils/offline-queue'

const RESULT_DISPLAY_TIME = 5000

export default {
  name: 'IdleScreenPage',
  data () {
    return {
      communityName: '智慧社区',
      currentDate: '',
      currentClock: '',
      timeTimer: null,
      stream: null,
      streamPusher: null,
      streaming: false,
      faceLoading: false,
      faceResult: null,
      resultTimer: null,
      showVisitorPopup: false,
      visitorForm: {
        building: '',
        unit: '',
        room: ''
      },
      visitorFaceBase64: '',
      visitorFaceCaptured: false,
      visitorSubmitting: false,
      showBuildingDrop: false,
      showUnitDrop: false,
      showRoomDrop: false,
      showUnboundDialog: false
    }
  },
  computed: {
    isBound () { return this.$store.getters['gate/isBound'] },
    gateName () { return this.$store.getters['gate/gateName'] },
    pushKey () { return this.$store.getters['gate/pushKey'] },
    gateId () { return this.$store.getters['gate/gateId'] || '' },
    canSubmitVisitor () {
      return this.visitorForm.building && this.visitorForm.unit && this.visitorForm.room && this.visitorFaceCaptured
    },
    buildingOptions () {
      const list = []
      for (let i = 1; i <= 20; i++) list.push(i + '栋')
      return list
    },
    unitOptions () {
      const list = []
      for (let i = 1; i <= 6; i++) list.push(i + '单元')
      return list
    },
    roomOptions () {
      const list = []
      for (let f = 1; f <= 33; f++) {
        for (let r = 1; r <= 4; r++) {
          list.push(f + '0' + r)
        }
      }
      return list
    }
  },
  watch: {
    pushKey () {
      this.restartStream()
    },
    isBound (val) {
      if (val) {
        this.showUnboundDialog = false
      } else {
        this.stopAll()
      }
    }
  },
  mounted () {
    this.updateTime()
    this.timeTimer = setInterval(this.updateTime, 1000)
    if (this.pushKey) {
      this.startCamera()
    }
    const self = this
    setupOnlineHandler(function (data) {
      self.submitOfflineItem(data)
    })
    if (!this.isBound) {
      this.showUnboundDialog = true
    }
    window.addEventListener('beforeunload', this._onPageHide)
    window.addEventListener('pagehide', this._onPageHide)
  },
  beforeDestroy () {
    this.stopAll()
    this.clearResultTimer()
    window.removeEventListener('beforeunload', this._onPageHide)
    window.removeEventListener('pagehide', this._onPageHide)
  },
  methods: {
    _onPageHide () {
      this.stopAll()
      if (this.pushKey) {
        navigator.sendBeacon(
          '/api/v1/video-monitor/gate-stop-push',
          JSON.stringify({ push_key: this.pushKey })
        )
      }
    },
    goToSettings () {
      this.showUnboundDialog = false
      this.$router.push('/settings')
    },
    updateTime () {
      const now = new Date()
      const y = now.getFullYear()
      const m = String(now.getMonth() + 1).padStart(2, '0')
      const d = String(now.getDate()).padStart(2, '0')
      const h = String(now.getHours()).padStart(2, '0')
      const min = String(now.getMinutes()).padStart(2, '0')
      const s = String(now.getSeconds()).padStart(2, '0')
      const weekDays = ['日', '一', '二', '三', '四', '五', '六']
      const week = '星期' + weekDays[now.getDay()]
      this.currentDate = y + '年' + m + '月' + d + '日 ' + week
      this.currentClock = h + ':' + min + ':' + s
    },
    async startCamera () {
      if (!this.pushKey) return
      try {
        this.stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: 'user', width: { ideal: 640 }, height: { ideal: 480 } }
        })
        const video = this.$refs.bgVideo
        if (video) {
          video.srcObject = this.stream
          await video.play()
        }
        this.streamPusher = new GateStreamPusher(video, this.pushKey)
        this.streamPusher.start()
        this.streaming = true
      } catch (err) {
        this.streaming = false
      }
    },
    stopAll () {
      if (this.streamPusher) {
        this.streamPusher.stop()
        this.streamPusher = null
      }
      if (this.stream) {
        this.stream.getTracks().forEach(function (t) { t.stop() })
        this.stream = null
      }
      this.streaming = false
    },
    async restartStream () {
      this.stopAll()
      if (this.pushKey) {
        await this.startCamera()
      }
    },
    captureFrame () {
      const video = this.$refs.bgVideo
      const canvas = this.$refs.captureCanvas
      if (!video || !video.videoWidth) return null
      canvas.width = video.videoWidth
      canvas.height = video.videoHeight
      const ctx = canvas.getContext('2d')
      ctx.drawImage(video, 0, 0)
      return canvas.toDataURL('image/jpeg').split(',')[1]
    },
    async doFacePass () {
      if (this.faceLoading) return
      const base64Image = this.captureFrame()
      if (!base64Image) {
        this.faceResult = { passed: false, reason: '摄像头未就绪' }
        this.startResultTimer()
        return
      }
      this.faceLoading = true
      this.faceResult = null
      this.clearResultTimer()
      try {
        const res = await submitFacePass({
          face_image: base64Image,
          gate_id: this.gateId,
          _silent: true
        })
        this.faceResult = {
          passed: true,
          personName: res.data && res.data.person_name ? res.data.person_name : ''
        }
      } catch (err) {
        if (!navigator.onLine) {
          enqueue({ face_image: base64Image, gate_id: this.gateId })
          this.faceResult = { passed: false, reason: '网络断开，已暂存待网络恢复后自动提交' }
        } else {
          const msg = (err && err.message) || '识别失败'
          const noFaceKeywords = ['未检测到人脸', '未找到人脸', 'no face']
          const isNoFace = noFaceKeywords.some(function (k) { return msg.includes(k) })
          if (isNoFace) {
            this.faceResult = { passed: false, reason: '未检测到人脸，请正对摄像头' }
          } else {
            const reasonMap = {
              生人: '未登记人员，禁止通行',
              黑名单: '黑名单人员，禁止通行',
              授权过期: '访客授权已过期',
              权限不足: '无此门禁通行权限'
            }
            let reason = ''
            Object.keys(reasonMap).forEach(function (key) {
              if (msg.includes(key)) reason = reasonMap[key]
            })
            this.faceResult = { passed: false, reason: reason || msg }
          }
        }
      } finally {
        this.faceLoading = false
      }
      this.startResultTimer()
    },
    startResultTimer () {
      this.clearResultTimer()
      const self = this
      this.resultTimer = setTimeout(function () {
        self.faceResult = null
      }, RESULT_DISPLAY_TIME)
    },
    clearResultTimer () {
      if (this.resultTimer) {
        clearTimeout(this.resultTimer)
        this.resultTimer = null
      }
    },
    async submitOfflineItem (data) {
      try {
        await submitFacePass(data)
      } catch (err) {
        // silent fail for offline retry
      }
    },
    openVisitorApply () {
      const base64 = this.captureFrame()
      if (base64) {
        this.visitorFaceBase64 = base64
        this.visitorFaceCaptured = true
      }
      this.showVisitorPopup = true
    },
    captureVisitorFace () {
      const base64 = this.captureFrame()
      if (base64) {
        this.visitorFaceBase64 = base64
        this.visitorFaceCaptured = true
        this.$toast.success('人脸照片已采集')
      } else {
        this.$toast.fail('摄像头未就绪')
      }
    },
    toggleDrop (type) {
      if (type === 'building') {
        this.showBuildingDrop = !this.showBuildingDrop
        this.showUnitDrop = false
        this.showRoomDrop = false
      } else if (type === 'unit') {
        this.showUnitDrop = !this.showUnitDrop
        this.showBuildingDrop = false
        this.showRoomDrop = false
      } else {
        this.showRoomDrop = !this.showRoomDrop
        this.showBuildingDrop = false
        this.showUnitDrop = false
      }
    },
    selectBuilding (val) {
      this.visitorForm.building = val
      this.showBuildingDrop = false
    },
    selectUnit (val) {
      this.visitorForm.unit = val
      this.showUnitDrop = false
    },
    selectRoom (val) {
      this.visitorForm.room = val
      this.showRoomDrop = false
    },
    async doSubmitVisitor () {
      this.visitorSubmitting = true
      try {
        await applyVisitorAuth({
          visitor_face_image: this.visitorFaceBase64,
          apply_gate_levels: JSON.stringify(['community_gate', 'unit_door']),
          visit_address: this.visitorForm.building + this.visitorForm.unit + this.visitorForm.room,
          apply_source: 'gate_terminal'
        })
        this.$toast.success('申请已提交，可通行小区大门和单元门')
        this.showVisitorPopup = false
        this.resetVisitorForm()
      } catch (err) {
        // error handled by interceptor
      } finally {
        this.visitorSubmitting = false
      }
    },
    resetVisitorForm () {
      this.visitorForm = {
        building: '',
        unit: '',
        room: ''
      }
      this.visitorFaceBase64 = ''
      this.visitorFaceCaptured = false
      this.showBuildingDrop = false
      this.showUnitDrop = false
      this.showRoomDrop = false
    }
  }
}
</script>

<style scoped>
.idle-page {
  position: relative;
  min-height: 100vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.bg-camera {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  z-index: 0;
}
.idle-top-bar {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 16px 0;
  background: linear-gradient(180deg, rgba(0,0,0,0.55) 0%, rgba(0,0,0,0) 100%);
}
.top-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
}
.top-right {
  display: flex;
  align-items: center;
  gap: 10px;
}
.community-name {
  font-size: 20px;
  font-weight: 700;
  color: #fff;
  letter-spacing: 1px;
  text-shadow: 0 1px 4px rgba(0,0,0,0.5);
}
.current-time {
  display: flex;
  flex-direction: column;
  align-items: center;
  color: rgba(255,255,255,0.95);
  font-variant-numeric: tabular-nums;
  text-shadow: 0 1px 4px rgba(0,0,0,0.5);
  font-weight: 600;
  margin-top: 8px;
  text-align: center;
  width: 100%;
}
.time-date {
  font-size: clamp(22px, 5vw, 36px);
  opacity: 0.8;
}
.time-clock {
  font-size: clamp(64px, 16vw, 128px);
  letter-spacing: 2px;
}
.gate-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 4px 12px;
  border-radius: 16px;
  background: rgba(16, 185, 129, 0.15);
  border: 1px solid rgba(16, 185, 129, 0.35);
  cursor: pointer;
  -webkit-tap-highlight-color: transparent;
  font-size: inherit;
  font-family: inherit;
  line-height: 1;
  outline: none;
}
.badge-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--gate-success);
}
.dot-pulse {
  animation: pulse 2s ease-in-out infinite;
}
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}
.badge-text {
  font-size: 12px;
  color: rgba(16, 185, 129, 0.9);
}
.badge-settings-icon {
  opacity: 0.6;
  margin-left: 2px;
}
.badge-unbound {
  background: rgba(245, 158, 11, 0.15);
  border-color: rgba(245, 158, 11, 0.35);
  cursor: pointer;
}
.badge-unbound .badge-text {
  color: var(--gate-warning);
}

.face-result-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: none;
}
.face-result-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 32px 40px;
  border-radius: 16px;
  animation: resultIn 0.3s ease;
}
@keyframes resultIn {
  from { opacity: 0; transform: scale(0.85); }
  to { opacity: 1; transform: scale(1); }
}
.result-success {
  background: rgba(16, 185, 129, 0.45);
  border: 1px solid rgba(16, 185, 129, 0.6);
  color: var(--gate-success);
}
.result-fail {
  background: rgba(239, 68, 68, 0.45);
  border: 1px solid rgba(239, 68, 68, 0.6);
  color: var(--gate-danger);
}
.face-result-title {
  font-size: 20px;
  font-weight: 600;
  color: #fff;
  margin-top: 12px;
}
.face-result-reason {
  margin-top: 8px;
  font-size: 14px;
  color: rgba(255,255,255,0.75);
}
.face-result-name {
  margin-top: 8px;
  font-size: 16px;
  color: rgba(255,255,255,0.75);
  font-weight: 500;
}
.face-result-enter-active {
  transition: opacity 0.3s;
}
.face-result-leave-active {
  transition: opacity 0.3s;
}
.face-result-enter,
.face-result-leave-to {
  opacity: 0;
}

.visitor-popup-center {
  display: flex;
  justify-content: center;
}
.visitor-popup {
  background: var(--gate-bg-card);
  border-radius: 16px 16px 0 0;
  overflow: hidden;
  width: 100%;
  max-width: min(480px, calc(100vw - 16px));
}
.visitor-popup-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 24px;
  border-bottom: 1px solid var(--gate-border);
}
.visitor-popup-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--gate-text);
}
.visitor-popup-body {
  padding: 24px 24px 28px;
  overflow-x: hidden;
  overflow-y: auto;
}
.v-form-grid {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.v-form-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.v-form-label {
  font-size: 15px;
  color: var(--gate-text-secondary);
  font-weight: 500;
}
.v-form-required {
  color: var(--gate-danger);
}
.v-face-preview {
  margin-bottom: 4px;
  border-radius: 8px;
  overflow: hidden;
  background: #000;
}
.v-face-preview-img {
  display: block;
  width: 100%;
  border-radius: 8px;
}
.v-capture-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px 18px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  color: var(--gate-text-secondary);
  font-size: 15px;
  cursor: pointer;
  transition: background 0.2s, border-color 0.2s;
  width: 100%;
  box-sizing: border-box;
}
.v-capture-btn:active {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.2);
}
.v-form-hint {
  font-size: 13px;
  color: var(--gate-text-muted);
  line-height: 1.5;
}
.v-address-row {
  display: flex;
  gap: 8px;
}
.v-address-select {
  position: relative;
  flex: 1;
  min-width: 0;
}
.v-select-trigger {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 12px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  cursor: pointer;
  font-size: 15px;
  color: var(--gate-text);
  transition: border-color 0.2s;
}
.v-address-select.is-open .v-select-trigger {
  border-color: var(--gate-accent-light);
}
.v-placeholder {
  color: var(--gate-text-muted);
}
.v-select-arrow {
  font-size: 12px;
  color: var(--gate-text-muted);
  transition: transform 0.2s;
  flex-shrink: 0;
}
.v-select-arrow.is-reverse {
  transform: rotate(180deg);
}
.v-select-dropdown {
  position: absolute;
  bottom: calc(100% + 4px);
  left: 0;
  right: 0;
  background: var(--gate-bg-card);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 4px 0;
  z-index: 100;
  box-shadow: 0 -4px 24px rgba(0, 0, 0, 0.5);
  max-height: 200px;
  overflow-y: auto;
  scrollbar-width: thin;
  scrollbar-color: rgba(255,255,255,0.2) transparent;
}
.v-select-dropdown::-webkit-scrollbar {
  width: 4px;
}
.v-select-dropdown::-webkit-scrollbar-track {
  background: transparent;
}
.v-select-dropdown::-webkit-scrollbar-thumb {
  background: rgba(255,255,255,0.2);
  border-radius: 2px;
}
.v-select-dropdown::-webkit-scrollbar-thumb:hover {
  background: rgba(255,255,255,0.35);
}
.v-select-option {
  padding: 12px 14px;
  font-size: 15px;
  color: var(--gate-text-secondary);
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}
.v-select-option:active {
  background: rgba(255, 255, 255, 0.06);
  color: var(--gate-text);
}
.v-select-option.is-active {
  color: var(--gate-accent-light);
  background: rgba(99, 102, 241, 0.1);
}
.dropdown-enter-active,
.dropdown-leave-active {
  transition: opacity 0.2s, transform 0.2s;
}
.dropdown-enter,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}
.v-form-footer {
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}
.v-form-btn-block {
  width: 100%;
  justify-content: center;
  padding: 14px 20px;
}
.v-form-btn {
  padding: 10px 20px;
  border-radius: 8px;
  font-size: 15px;
  cursor: pointer;
  border: none;
  transition: background 0.2s;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.v-form-btn-primary {
  background: var(--gate-accent);
  color: #fff;
}
.v-form-btn-primary:active {
  background: var(--gate-accent-light);
}
.v-form-btn-primary:disabled {
  opacity: 0.5;
  pointer-events: none;
}
::v-deep .van-popup--bottom {
  background: transparent;
}

.idle-bottom-bar {
  position: relative;
  z-index: 1;
  display: flex;
  justify-content: center;
  gap: 16px;
  padding: 20px 24px 32px;
  margin-top: auto;
  background: linear-gradient(0deg, rgba(0,0,0,0.55) 0%, rgba(0,0,0,0) 100%);
}
.idle-btn {
  height: 52px;
  font-size: 16px;
  border-radius: var(--gate-radius);
  min-width: 140px;
}
@media (min-width: 1024px) {
  .community-name {
    font-size: 24px;
  }
  .idle-btn {
    min-width: 180px;
    height: 56px;
    font-size: 18px;
  }
}
</style>

<style>
.unbound-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 9999;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
}
.unbound-dialog {
  background: #1a1a2e;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  width: 320px;
  max-width: 85vw;
  overflow: hidden;
}
.unbound-dialog-title {
  font-size: 16px;
  font-weight: 600;
  color: #ededf0;
  padding: 24px 24px 8px;
  text-align: center;
}
.unbound-dialog-message {
  font-size: 14px;
  color: #9ca3af;
  line-height: 1.6;
  padding: 0 24px 20px;
}
.unbound-dialog-btn {
  display: block;
  width: 100%;
  padding: 14px 0;
  border: none;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  background: transparent;
  color: #818cf8;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  -webkit-tap-highlight-color: transparent;
}
.unbound-dialog-btn:active {
  background: rgba(99, 102, 241, 0.08);
}
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.25s;
}
.fade-enter,
.fade-leave-to {
  opacity: 0;
}
</style>
