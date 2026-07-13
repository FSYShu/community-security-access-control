<template>
  <div class="video-stream-viewer">
    <div class="viewer-header">
      <div class="gate-select" :class="{ 'is-open': showDropdown }">
        <div class="select-trigger" @click="toggleDropdown">
          <span class="select-value">{{ selectedGateName || '选择终端' }}</span>
          <i class="el-icon-arrow-down select-arrow" :class="{ 'is-reverse': showDropdown }"></i>
        </div>
        <transition name="dropdown">
          <div v-if="showDropdown" class="select-dropdown">
            <div
              v-for="gate in gateList"
              :key="gate.id"
              class="select-option"
              :class="{ 'is-active': selectedGate === String(gate.id) }"
              @click="selectGate(gate)"
            >{{ gate.gate_name }}</div>
            <div v-if="gateList.length === 0" class="select-option is-disabled">暂无终端</div>
          </div>
        </transition>
      </div>
      <div class="status-indicator">
        <span class="status-dot" :class="statusDotClass"></span>
        <span class="status-text">{{ statusLabel }}</span>
        <span v-if="latencyMs !== null" class="latency-tag" :class="latencyClass">{{ latencyText }}</span>
      </div>
    </div>
    <div class="stream-container">
      <div class="stream-wrapper">
        <img
          v-if="showStream && selectedGate"
          ref="streamImage"
          :src="videoFeedUrl"
          alt="视频流"
          class="stream-image"
          @load="onStreamLoad"
          @error="onStreamError"
        />
        <canvas
          v-if="showStream && selectedGate && faceDetectionEnabled"
          ref="overlayCanvas"
          class="overlay-canvas"
        ></canvas>
      </div>

      <div v-if="!selectedGate" class="stream-error-overlay">
        <i class="el-icon-video-camera" style="font-size:40px;color:var(--dark-text-muted)"></i>
        <p class="error-text" style="color:var(--dark-text-muted)">请选择门禁终端</p>
      </div>
      <div v-else-if="streamError" class="stream-error-overlay">
        <i class="el-icon-warning-outline" style="font-size:40px;color:var(--dark-orange)"></i>
        <p class="error-text">{{ statusText }}</p>
        <p class="retry-text" v-if="autoRetrying">自动重连中（第{{ retryCount }}次）...</p>
        <button class="retry-button" @click="manualRefresh">立即重试</button>
      </div>
    </div>
  </div>
</template>

<script>
const AUTO_RETRY_MAX = 10
const AUTO_RETRY_INTERVAL = 10000

export default {
  name: 'VideoStreamViewer',
  props: {
    gateList: {
      type: Array,
      default: () => []
    },
    faceDetectionEnabled: {
      type: Boolean,
      default: false
    },
    dangerousBehaviorEnabled: {
      type: Boolean,
      default: false
    },
    initialGateId: {
      type: String,
      default: ''
    }
  },
  data () {
    return {
      selectedGate: '',
      showDropdown: false,
      streamError: false,
      showStream: true,
      connected: false,
      autoRetrying: false,
      retryCount: 0,
      retryTimer: null,
      urlVersion: 0,
      latencyMs: null,
      detectionEventSource: null,
      latestBoxes: [],
      detectionFrameWidth: 0,
      detectionFrameHeight: 0,
      boxExpireTimer: null,
      latencyTimer: null,
      sseErrorCount: 0,
      sseConnectTimer: null
    }
  },
  computed: {
    selectedGateData () {
      if (!this.selectedGate) return null
      return this.gateList.find(g => String(g.id) === this.selectedGate) || null
    },
    statusDotClass () {
      if (!this.selectedGate) return 'dot-gray'
      if (this.selectedGateData && this.selectedGateData.display_status === 'offline') return 'dot-red'
      if (this.streamError) return 'dot-red'
      if (this.connected && this.latencyMs < 0) return 'dot-yellow'
      return this.connected ? 'dot-green' : 'dot-yellow'
    },
    statusLabel () {
      if (!this.selectedGate) return '未连接'
      if (this.selectedGateData && this.selectedGateData.display_status === 'offline') return '离线'
      if (this.streamError) return '连接失败'
      if (this.connected && this.latencyMs < 0) return '无信号'
      return this.connected ? '已连接' : '连接中...'
    },
    videoFeedUrl () {
      if (!this.selectedGate) return ''
      const suffix = this.dangerousBehaviorEnabled ? '/dangerous-behavior' : ''
      return '/api/v1/video-monitor/video_feed/gate/' + this.selectedGate + suffix + '?t=' + this.urlVersion
    },
    statusText () {
      if (this.autoRetrying) return '视频流连接失败'
      return '视频流连接断开'
    },
    selectedGateName () {
      if (!this.selectedGateData) return ''
      return this.selectedGateData.gate_name || ''
    },
    latencyText () {
      if (this.latencyMs === null) return ''
      return this.latencyMs + 'ms'
    },
    latencyClass () {
      if (this.latencyMs === null) return ''
      if (this.latencyMs < 500) return 'latency-good'
      if (this.latencyMs < 2000) return 'latency-warn'
      return 'latency-bad'
    }
  },
  watch: {
    selectedGate () {
      this.resetConnection()
      this.stopDetectionSSE()
      this.latestBoxes = []
      if (this.selectedGate && this.faceDetectionEnabled) {
        this.startDetectionSSE()
      }
      this.fetchLatency()
      const self = this
      setTimeout(function () {
        if (self.selectedGate && self.faceDetectionEnabled && !self.detectionEventSource) {
          self.startDetectionSSE()
        }
      }, 1500)
    },
    faceDetectionEnabled (val) {
      if (val && this.selectedGate) {
        this.startDetectionSSE()
      } else {
        this.stopDetectionSSE()
        this.latestBoxes = []
        this.clearOverlay()
      }
    },
    dangerousBehaviorEnabled () {
      this.resetConnection()
    }
  },
  mounted () {
    if (this.initialGateId) {
      this.selectedGate = this.initialGateId
    }
    document.addEventListener('click', this.onDocumentClick)
    window.addEventListener('resize', this.onWindowResize)
    this.warmupStream()
    this.fetchLatency()
    const self = this
    this.latencyTimer = setInterval(function () {
      self.fetchLatency()
    }, 10000)
    setTimeout(function () {
      if (self.selectedGate && self.faceDetectionEnabled && !self.detectionEventSource) {
        self.startDetectionSSE()
      }
    }, 2000)
  },

  beforeDestroy () {
    this.cleanup()
    document.removeEventListener('click', this.onDocumentClick)
    window.removeEventListener('resize', this.onWindowResize)
  },
  methods: {
    toggleDropdown () {
      this.showDropdown = !this.showDropdown
    },
    selectGate (gate) {
      this.selectedGate = String(gate.id)
      this.showDropdown = false
    },
    onDocumentClick (e) {
      if (!this.$el.contains(e.target)) {
        this.showDropdown = false
      }
    },
    resetConnection () {
      this.streamError = false
      this.connected = false
      this.autoRetrying = false
      this.retryCount = 0
      this.clearRetryTimer()
      this.stopDetectionSSE()
      this.urlVersion = Date.now()
      this.showStream = false
      const self = this
      this.$nextTick(function () {
        self.showStream = true
      })
    },
    manualRefresh () {
      this.streamError = false
      this.autoRetrying = false
      this.retryCount = 0
      this.clearRetryTimer()
      this.urlVersion = Date.now()
      this.showStream = false
      const self = this
      this.$nextTick(function () {
        self.showStream = true
      })
    },
    onStreamLoad () {
      this.connected = true
      this.streamError = false
      this.autoRetrying = false
      this.retryCount = 0
      this.clearRetryTimer()
      if (this.faceDetectionEnabled && this.selectedGate) {
        this.startDetectionSSE()
      }
    },
    onStreamError () {
      this.connected = false
      this.streamError = true
      this.stopDetectionSSE()
      this.startAutoRetry()
    },
    startAutoRetry () {
      if (this.retryTimer) return
      if (this.retryCount >= AUTO_RETRY_MAX) {
        this.autoRetrying = false
        return
      }
      this.autoRetrying = true
      this.retryCount++
      const self = this
      this.retryTimer = setTimeout(function () {
        self.retryTimer = null
        self.urlVersion = Date.now()
        self.showStream = false
        self.$nextTick(function () {
          self.showStream = true
        })
      }, AUTO_RETRY_INTERVAL)
    },
    clearRetryTimer () {
      if (this.retryTimer) {
        clearTimeout(this.retryTimer)
        this.retryTimer = null
      }
    },
    startDetectionSSE () {
      if (this.detectionEventSource) return
      if (!this.selectedGate || !this.faceDetectionEnabled) return
      const self = this
      const url = '/api/v1/video-monitor/face-detection/' + this.selectedGate + '/stream'
      console.log('[FaceDetection] connecting SSE:', url)
      this.detectionEventSource = new EventSource(url)
      this.sseConnectTimer = setTimeout(function () {
        if (self.detectionEventSource && self.sseErrorCount === 0) {
          console.error('[FaceDetection] SSE connection timeout (10s), backend may not be running')
          self.$message({ message: '人脸检测服务连接超时，请检查后端服务是否启动', type: 'error' })
          self.stopDetectionSSE()
        }
      }, 10000)
      this.detectionEventSource.addEventListener('detection', function (e) {
        try {
          const data = JSON.parse(e.data)
          const boxes = data.boxes || []
          console.log('[FaceDetection] detection event, boxes:', boxes.length, 'frame:', data.frame_width, 'x', data.frame_height)
          if (data.frame_width) self.detectionFrameWidth = data.frame_width
          if (data.frame_height) self.detectionFrameHeight = data.frame_height
          if (boxes.length > 0) {
            self.latestBoxes = boxes
            self.drawFaceBoxes()
            self.resetBoxExpire()
            if (!self.$refs.overlayCanvas || !self.$refs.overlayCanvas.getBoundingClientRect().width) {
              setTimeout(function () { self.drawFaceBoxes() }, 500)
            }
          }
        } catch (err) {
          console.error('[FaceDetection] parse error:', err)
        }
      })
      this.detectionEventSource.addEventListener('error', function (e) {
        try {
          const msg = e.data ? JSON.parse(e.data) : {}
          console.error('[FaceDetection] backend error:', msg.error || 'unknown')
        } catch (err) {}
      })
      this.detectionEventSource.onopen = function () {
        console.log('[FaceDetection] SSE connected')
        self.sseErrorCount = 0
        if (self.sseConnectTimer) {
          clearTimeout(self.sseConnectTimer)
          self.sseConnectTimer = null
        }
      }
      this.detectionEventSource.onerror = function () {
        self.sseErrorCount++
        console.error('[FaceDetection] SSE error, retry in 3s')
        if (self.sseConnectTimer) {
          clearTimeout(self.sseConnectTimer)
          self.sseConnectTimer = null
        }
        if (self.sseErrorCount === 3) {
          self.$message({ message: '人脸检测连接失败，正在重试...', type: 'warning' })
        }
        self.stopDetectionSSE()
        setTimeout(function () {
          if (self.faceDetectionEnabled && self.selectedGate) {
            self.startDetectionSSE()
          }
        }, 3000)
      }
    },
    stopDetectionSSE () {
      if (this.sseConnectTimer) {
        clearTimeout(this.sseConnectTimer)
        this.sseConnectTimer = null
      }
      if (this.detectionEventSource) {
        this.detectionEventSource.close()
        this.detectionEventSource = null
      }
      this.latestBoxes = []
      this.detectionFrameWidth = 0
      this.detectionFrameHeight = 0
      this.clearBoxExpire()
      this.clearOverlay()
    },
    drawFaceBoxes (retryCount) {
      if (retryCount === undefined) retryCount = 0
      const canvas = this.$refs.overlayCanvas
      const img = this.$refs.streamImage
      if (!canvas) {
        if (retryCount < 10) {
          const self = this
          requestAnimationFrame(function () { self.drawFaceBoxes(retryCount + 1) })
        }
        return
      }
      const rect = canvas.getBoundingClientRect()
      const containerWidth = rect.width || canvas.clientWidth
      const containerHeight = rect.height || canvas.clientHeight
      if (!containerWidth || !containerHeight) {
        if (retryCount < 10) {
          const self = this
          requestAnimationFrame(function () { self.drawFaceBoxes(retryCount + 1) })
        }
        return
      }
      const boxes = this.latestBoxes
      if (!boxes || boxes.length === 0) return
      const naturalWidth = img && img.naturalWidth ? img.naturalWidth : this.detectionFrameWidth || 640
      const naturalHeight = img && img.naturalHeight ? img.naturalHeight : this.detectionFrameHeight || 480
      const dpr = window.devicePixelRatio || 1
      canvas.width = containerWidth * dpr
      canvas.height = containerHeight * dpr
      const ctx = canvas.getContext('2d')
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
      ctx.clearRect(0, 0, containerWidth, containerHeight)
      const scaleX = containerWidth / naturalWidth
      const scaleY = containerHeight / naturalHeight
      const displayScale = Math.min(scaleX, scaleY)
      const displayWidth = naturalWidth * displayScale
      const displayHeight = naturalHeight * displayScale
      const offsetX = (containerWidth - displayWidth) / 2
      const offsetY = (containerHeight - displayHeight) / 2
      const frameWidth = this.detectionFrameWidth || naturalWidth
      const frameHeight = this.detectionFrameHeight || naturalHeight
      const frameScaleX = displayWidth / frameWidth
      const frameScaleY = displayHeight / frameHeight
      for (let i = 0; i < boxes.length; i++) {
        const box = boxes[i]
        const x1 = box.rect[0]
        const y1 = box.rect[1]
        const x2 = box.rect[2]
        const y2 = box.rect[3]
        const drawX = x1 * frameScaleX + offsetX
        const drawY = y1 * frameScaleY + offsetY
        const drawW = (x2 - x1) * frameScaleX
        const drawH = (y2 - y1) * frameScaleY
        const color = box.is_stranger ? '#ef4444' : '#10b981'
        ctx.strokeStyle = color
        ctx.lineWidth = 2
        ctx.shadowColor = color
        ctx.shadowBlur = 6
        this.drawRoundRect(ctx, drawX, drawY, drawW, drawH, 3)
        ctx.stroke()
        ctx.shadowBlur = 0
        const label = box.is_stranger ? '陌生人' : box.name
        ctx.font = 'bold 13px "PingFang SC","Microsoft YaHei","Helvetica Neue",sans-serif'
        const textMetrics = ctx.measureText(label)
        const textHeight = 14
        const padX = 6
        const padY = 3
        const labelH = textHeight + padY * 2
        const labelW = textMetrics.width + padX * 2
        const labelX = drawX
        let labelY = drawY - labelH - 2
        if (labelY < 0) labelY = drawY + 2
        ctx.fillStyle = box.is_stranger ? 'rgba(239,68,68,0.9)' : 'rgba(16,185,129,0.9)'
        this.drawRoundRect(ctx, labelX, labelY, labelW, labelH, 3)
        ctx.fill()
        ctx.fillStyle = '#ffffff'
        ctx.textBaseline = 'top'
        ctx.fillText(label, labelX + padX, labelY + padY)
      }
    },
    drawRoundRect (ctx, x, y, w, h, r) {
      ctx.beginPath()
      ctx.moveTo(x + r, y)
      ctx.lineTo(x + w - r, y)
      ctx.quadraticCurveTo(x + w, y, x + w, y + r)
      ctx.lineTo(x + w, y + h - r)
      ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h)
      ctx.lineTo(x + r, y + h)
      ctx.quadraticCurveTo(x, y + h, x, y + h - r)
      ctx.lineTo(x, y + r)
      ctx.quadraticCurveTo(x, y, x + r, y)
      ctx.closePath()
    },
    clearOverlay () {
      const canvas = this.$refs.overlayCanvas
      if (!canvas) return
      const ctx = canvas.getContext('2d')
      ctx.clearRect(0, 0, canvas.width, canvas.height)
    },
    resetBoxExpire () {
      this.clearBoxExpire()
      const self = this
      this.boxExpireTimer = setTimeout(function () {
        self.latestBoxes = []
        self.clearOverlay()
      }, 5000)
    },
    clearBoxExpire () {
      if (this.boxExpireTimer) {
        clearTimeout(this.boxExpireTimer)
        this.boxExpireTimer = null
      }
    },
    cleanup () {
      this.showStream = false
      this.clearRetryTimer()
      this.stopDetectionSSE()
      this.clearBoxExpire()
      if (this.latencyTimer) {
        clearInterval(this.latencyTimer)
        this.latencyTimer = null
      }
      const img = this.$refs.streamImage
      if (img) {
        img.src = ''
        img.onload = null
        img.onerror = null
      }
    },
    onWindowResize () {
      if (this.faceDetectionEnabled && this.latestBoxes.length > 0) {
        this.drawFaceBoxes()
      }
    },
    async fetchLatency () {
      const pushKey = this.selectedGateData && this.selectedGateData.push_key
      if (!this.selectedGate || !pushKey) {
        this.latencyMs = null
        return
      }
      try {
        const res = await fetch('/api/v1/video-monitor/gate-latency/' + encodeURIComponent(pushKey))
        const data = await res.json()
        if (data.code === 0 && data.data && data.data.latency_ms !== undefined) {
          this.latencyMs = data.data.latency_ms
          if (data.data.fps) this.currentFps = data.data.fps
          if (data.data.latency_ms >= 0 && !this.connected) this.connected = true
          if (data.data.latency_ms < 0 && this.connected) this.connected = false
        }
      } catch (e) {
        // ignore
      }
    },
    warmupStream () {
      if (!this.selectedGate) return
      fetch('/api/v1/video-monitor/gate-warmup?gate_id=' + this.selectedGate).catch(function () {})
    }
  }
}
</script>

<style scoped>
.video-stream-viewer {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}
.viewer-header {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 10px;
  border-bottom: 1px solid var(--dark-border);
}
.gate-select {
  position: relative;
  width: 100%;
}
.select-trigger {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 5px 10px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--dark-border-field);
  border-radius: 6px;
  cursor: pointer;
  transition: border-color 0.2s;
  height: 30px;
  box-sizing: border-box;
}
.gate-select.is-open .select-trigger {
  border-color: var(--dark-accent);
}
.select-value {
  font-size: 12px;
  color: var(--dark-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 1;
  min-width: 0;
}
.select-arrow {
  font-size: 12px;
  color: var(--dark-text-secondary);
  transition: transform 0.2s;
  margin-left: 4px;
  flex-shrink: 0;
}
.select-arrow.is-reverse {
  transform: rotate(180deg);
}
.select-dropdown {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  right: 0;
  background: var(--dark-bg-secondary);
  border: 1px solid var(--dark-border-field);
  border-radius: 6px;
  padding: 4px 0;
  z-index: 100;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
  max-height: 200px;
  overflow-y: auto;
}
.select-option {
  padding: 6px 10px;
  font-size: 12px;
  color: var(--dark-text-secondary);
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}
.select-option:hover {
  background: rgba(255, 255, 255, 0.06);
  color: var(--dark-text);
}
.select-option.is-active {
  color: var(--dark-accent-light);
  background: rgba(99, 102, 241, 0.1);
}
.select-option.is-disabled {
  color: var(--dark-text-secondary);
  opacity: 0.5;
  cursor: default;
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
.stream-container {
  width: 100%;
  background: #000;
  overflow: hidden;
  position: relative;
  flex: 1;
  min-height: 0;
}
.stream-wrapper {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}
.stream-image {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: contain;
}
.stream-error-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.85);
  color: var(--dark-text);
}
.error-text {
  margin: 8px 0 4px;
  font-size: 14px;
  color: var(--dark-orange);
}
.retry-text {
  margin: 0 0 12px;
  font-size: 12px;
  color: var(--dark-text-secondary);
}
.retry-button {
  padding: 6px 16px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid var(--dark-border-field);
  border-radius: 6px;
  color: var(--dark-text-secondary);
  font-size: 12px;
  cursor: pointer;
  transition: background 0.2s, color 0.2s;
}
.retry-button:hover {
  background: rgba(255, 255, 255, 0.1);
  color: var(--dark-text);
}
.status-indicator {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
  font-size: 11px;
  color: var(--dark-text-secondary);
  white-space: nowrap;
  padding: 0 4px;
  width: 58px;
  justify-content: center;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}
.dot-green {
  background: var(--dark-success-green);
}
.dot-yellow {
  background: var(--dark-orange);
}
.dot-red {
  background: #ef4444;
  box-shadow: 0 0 6px rgba(239, 68, 68, 0.4);
}
.dot-gray {
  background: var(--dark-text-secondary);
}
.overlay-canvas {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 2;
}
.latency-tag {
  font-size: 10px;
  padding: 1px 4px;
  border-radius: 3px;
  margin-left: 2px;
  font-weight: 500;
}
.latency-good {
  background: rgba(16, 185, 129, 0.15);
  color: #10b981;
}
.latency-warn {
  background: rgba(245, 158, 11, 0.15);
  color: #f59e0b;
}
.latency-bad {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
}

</style>
