<template>
  <div class="gate-page idle-page">
    <video ref="bgVideo" class="bg-camera" autoplay playsinline muted></video>
    <div class="idle-overlay">
      <div class="idle-settings-icon" @click="$router.push('/settings')">
        <van-icon name="setting-o" size="20" />
      </div>
      <div class="idle-content">
        <div class="community-name">{{ communityName }}</div>
        <div class="current-time">{{ currentTime }}</div>

        <div v-if="isBound" class="gate-badge">
          <span class="badge-dot" :class="{ 'dot-pulse': streaming }"></span>
          <span class="badge-text">{{ gateName }}{{ streaming ? ' · 推流中' : '' }}</span>
        </div>
        <div v-else class="gate-badge badge-unbound">
          <van-icon name="warning-o" size="14" />
          <span class="badge-text" @click="$router.push('/settings')">未绑定终端，点击设置</span>
        </div>

        <div class="idle-actions">
          <button class="gate-btn gate-btn-primary idle-btn" @click="goFacePass">
            <van-icon name="scan" size="24" />
            <span>刷脸通行</span>
          </button>
          <button class="gate-btn gate-btn-outline idle-btn" @click="goVisitorApply">
            <van-icon name="friends-o" size="24" />
            <span>访客申请</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import GateStreamPusher from '@/utils/stream-pusher'

export default {
  name: 'IdleScreenPage',
  data () {
    return {
      communityName: '智慧社区',
      currentTime: '',
      timeTimer: null,
      stream: null,
      streamPusher: null,
      streaming: false
    }
  },
  computed: {
    isBound () { return this.$store.getters['gate/isBound'] },
    gateName () { return this.$store.getters['gate/gateName'] },
    pushKey () { return this.$store.getters['gate/pushKey'] }
  },
  watch: {
    pushKey () {
      this.restartStream()
    }
  },
  mounted () {
    this.updateTime()
    this.timeTimer = setInterval(this.updateTime, 1000)
    if (this.pushKey) {
      this.startCamera()
    }
  },
  beforeDestroy () {
    this.stopAll()
  },
  methods: {
    updateTime () {
      var now = new Date()
      var y = now.getFullYear()
      var m = String(now.getMonth() + 1).padStart(2, '0')
      var d = String(now.getDate()).padStart(2, '0')
      var h = String(now.getHours()).padStart(2, '0')
      var min = String(now.getMinutes()).padStart(2, '0')
      var s = String(now.getSeconds()).padStart(2, '0')
      var weekDays = ['日', '一', '二', '三', '四', '五', '六']
      var week = '星期' + weekDays[now.getDay()]
      this.currentTime = y + '年' + m + '月' + d + '日 ' + week + ' ' + h + ':' + min + ':' + s
    },
    async startCamera () {
      if (!this.pushKey) return
      try {
        this.stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: 'user', width: { ideal: 640 }, height: { ideal: 480 } }
        })
        var video = this.$refs.bgVideo
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
    goFacePass () {
      this.$router.push('/face-pass')
    },
    goVisitorApply () {
      this.$router.push('/visitor-apply')
    }
  }
}
</script>

<style scoped>
.idle-page {
  position: relative;
  min-height: 100vh;
  overflow: hidden;
}
.bg-camera {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  opacity: 0.25;
  z-index: 0;
}
.idle-overlay {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
}
.idle-settings-icon {
  position: absolute;
  top: 16px;
  right: 16px;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--gate-text-muted);
  cursor: pointer;
  transition: color 0.2s;
  -webkit-tap-highlight-color: transparent;
}
.idle-settings-icon:active {
  color: var(--gate-text-secondary);
}
.idle-content {
  text-align: center;
  padding: 32px 24px;
  width: 100%;
  max-width: 480px;
}
.community-name {
  font-size: 28px;
  font-weight: 700;
  color: var(--gate-text);
  margin-bottom: 12px;
  letter-spacing: 2px;
}
.current-time {
  font-size: 18px;
  color: var(--gate-text-secondary);
  margin-bottom: 24px;
  font-variant-numeric: tabular-nums;
}
.gate-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 16px;
  border-radius: 20px;
  background: rgba(16, 185, 129, 0.1);
  border: 1px solid rgba(16, 185, 129, 0.3);
  margin-bottom: 32px;
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
  font-size: 13px;
  color: var(--gate-success);
}
.badge-unbound {
  background: rgba(245, 158, 11, 0.1);
  border-color: rgba(245, 158, 11, 0.3);
  cursor: pointer;
}
.badge-unbound .badge-text {
  color: var(--gate-warning);
}
.idle-actions {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.idle-btn {
  height: 56px;
  font-size: 18px;
  border-radius: var(--gate-radius);
}
@media (min-width: 1024px) {
  .community-name {
    font-size: 36px;
  }
  .current-time {
    font-size: 22px;
  }
  .idle-actions {
    flex-direction: row;
    justify-content: center;
  }
  .idle-btn {
    width: 200px;
  }
}
</style>
