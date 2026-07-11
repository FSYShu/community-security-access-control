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
      </div>
    </div>
    <div class="stream-container">
      <div class="stream-wrapper">
        <img
          v-if="showStream && selectedGate"
          :src="videoFeedUrl"
          alt="视频流"
          class="stream-image"
          @load="onStreamLoad"
          @error="onStreamError"
        />
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
const AUTO_RETRY_INTERVAL = 5000

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
      urlVersion: 0
    }
  },
  computed: {
    statusDotClass () {
      if (!this.selectedGate) return 'dot-gray'
      if (this.streamError) return 'dot-red'
      return this.connected ? 'dot-green' : 'dot-yellow'
    },
    statusLabel () {
      if (!this.selectedGate) return '未连接'
      if (this.streamError) return '连接失败'
      return this.connected ? '已连接' : '连接中...'
    },
    videoFeedUrl () {
      if (!this.selectedGate) return ''
      const base = this.faceDetectionEnabled
        ? '/api/v1/video-monitor/video_feed/gate/' + this.selectedGate + '/detect'
        : '/api/v1/video-monitor/video_feed/gate/' + this.selectedGate
      return base + '?t=' + this.urlVersion
    },
    statusText () {
      if (this.autoRetrying) return '视频流连接失败'
      return '视频流连接断开'
    },
    selectedGateName () {
      if (!this.selectedGate) return ''
      const gate = this.gateList.find(g => String(g.id) === this.selectedGate)
      return gate ? gate.gate_name : ''
    }
  },
  watch: {
    selectedGate () {
      this.resetConnection()
    },
    faceDetectionEnabled () {
      this.resetConnection()
    }
  },
  mounted () {
    if (this.initialGateId) {
      this.selectedGate = this.initialGateId
    }
    document.addEventListener('click', this.onDocumentClick)
  },
  beforeDestroy () {
    this.clearRetryTimer()
    document.removeEventListener('click', this.onDocumentClick)
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
    },
    onStreamError () {
      this.connected = false
      this.streamError = true
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
</style>
