<template>
  <div class="video-stream-viewer">
    <div class="gate-selector" v-if="gateList.length > 0">
      <div class="selector-label">选择门禁终端：</div>
      <van-radio-group v-model="selectedGate" direction="horizontal">
        <van-radio v-for="gate in gateList" :key="gate.id" :name="String(gate.id)">
          {{ gate.gate_name }}
        </van-radio>
      </van-radio-group>
    </div>
    <van-empty v-else description="暂无绑定推流码的门禁终端" />
    <div class="controls" v-if="selectedGate">
      <van-switch v-model="faceDetectionEnabled" size="20px" />
      <span class="control-label">人脸检测</span>
      <van-button
        size="mini"
        icon="replay"
        type="info"
        plain
        class="refresh-btn"
        :loading="refreshing"
        @click="manualRefresh"
      >刷新</van-button>
    </div>
    <div class="stream-container" v-if="selectedGate">
      <div class="stream-wrapper">
        <img
          v-if="showStream"
          :src="videoFeedUrl"
          alt="视频流"
          class="stream-image"
          @load="onStreamLoad"
          @error="onStreamError"
        />
      </div>
      <div v-if="streamError" class="stream-error-overlay">
        <van-icon name="warning-o" size="40" color="#ff976a" />
        <p class="error-text">{{ statusText }}</p>
        <p class="retry-text" v-if="autoRetrying">自动重连中（第{{ retryCount }}次）...</p>
        <van-button size="small" type="info" @click="manualRefresh">立即重试</van-button>
      </div>
    </div>
    <div class="status-bar" v-if="selectedGate && !streamError">
      <span class="status-dot" :class="connected ? 'dot-green' : 'dot-yellow'"></span>
      <span class="status-text">{{ connected ? '已连接' : '连接中...' }}</span>
    </div>
    <div v-if="faceDetectionEnabled && selectedGate" class="detection-status">
      <van-notice-bar left-icon="info-o" :text="detectionNotice" />
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
    }
  },
  data () {
    return {
      selectedGate: '',
      faceDetectionEnabled: false,
      detectionNotice: '人脸检测已开启：绿色框=已注册人员，红色框=陌生人',
      streamError: false,
      showStream: true,
      connected: false,
      refreshing: false,
      autoRetrying: false,
      retryCount: 0,
      retryTimer: null,
      urlVersion: 0
    }
  },
  computed: {
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
    }
  },
  watch: {
    gateList: {
      handler (val) {
        if (val.length > 0 && !this.selectedGate) {
          this.selectedGate = String(val[0].id)
        }
      },
      immediate: true
    },
    selectedGate () {
      this.resetConnection()
    },
    faceDetectionEnabled () {
      this.detectionNotice = this.faceDetectionEnabled ? '人脸检测已开启：绿色框=已注册人员，红色框=陌生人' : '人脸检测已关闭'
      this.resetConnection()
    }
  },
  beforeDestroy () {
    this.clearRetryTimer()
  },
  methods: {
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
      this.refreshing = true
      this.streamError = false
      this.autoRetrying = false
      this.retryCount = 0
      this.clearRetryTimer()
      this.urlVersion = Date.now()
      this.showStream = false
      const self = this
      this.$nextTick(function () {
        self.showStream = true
        setTimeout(function () {
          self.refreshing = false
        }, 1500)
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
}
.gate-selector {
  margin-bottom: 12px;
  padding: 8px 0;
}
.selector-label {
  font-size: 14px;
  color: #333;
  margin-bottom: 8px;
}
.controls {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
  padding: 0 4px;
}
.control-label {
  margin-left: 8px;
  font-size: 14px;
  color: #333;
}
.refresh-btn {
  margin-left: auto;
}
.stream-container {
  width: 100%;
  background: #000;
  border-radius: 8px;
  overflow: hidden;
  position: relative;
}
.stream-wrapper {
  position: relative;
  width: 100%;
  padding-bottom: 56.25%;
  overflow: hidden;
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
  color: #fff;
}
.error-text {
  margin: 8px 0 4px;
  font-size: 14px;
  color: #ff976a;
}
.retry-text {
  margin: 0 0 12px;
  font-size: 12px;
  color: #999;
}
.status-bar {
  display: flex;
  align-items: center;
  padding: 6px 8px;
  font-size: 12px;
  color: #666;
}
.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 6px;
}
.dot-green {
  background: #07c160;
}
.dot-yellow {
  background: #ff976a;
}
.detection-status {
  margin-top: 8px;
}
</style>
