<template>
  <div class="face-camera">
    <video ref="video" class="camera-preview" autoplay playsinline></video>
    <canvas ref="canvas" style="display: none;"></canvas>
    <div v-if="!cameraReady" class="camera-loading">
      <van-loading size="24px" color="#6366f1">摄像头启动中...</van-loading>
    </div>
    <div v-if="cameraError" class="camera-error">
      <i class="el-icon-warning-outline" style="font-size:40px;color:#ef4444"></i>
      <p class="error-msg">{{ cameraError }}</p>
      <button class="gate-btn gate-btn-outline" style="width:auto;padding:8px 16px;margin-top:8px;" @click="startCamera">重试</button>
    </div>
    <div v-if="cameraReady && showSwitch" class="camera-switch" @click="switchCamera">
      <i class="el-icon-refresh" style="font-size:20px"></i>
    </div>
  </div>
</template>

<script>
import GateStreamPusher from '@/utils/stream-pusher'

export default {
  name: 'FaceCamera',
  props: {
    facingMode: {
      type: String,
      default: 'user'
    },
    showSwitch: {
      type: Boolean,
      default: true
    },
    pushKey: {
      type: String,
      default: ''
    },
    deviceId: {
      type: String,
      default: ''
    }
  },
  data () {
    return {
      stream: null,
      cameraReady: false,
      cameraError: '',
      currentFacing: this.facingMode,
      streamPusher: null
    }
  },
  mounted () {
    this.startCamera()
  },
  beforeDestroy () {
    this.stopCamera()
  },
  watch: {
    deviceId () {
      this.stopCamera()
      this.startCamera()
    }
  },
  methods: {
    async startCamera () {
      this.cameraError = ''
      this.cameraReady = false
      try {
        const constraints = { video: { width: { ideal: 1280 }, height: { ideal: 720 } } }
        if (this.deviceId) {
          constraints.video.deviceId = { exact: this.deviceId }
        } else {
          constraints.video.facingMode = this.currentFacing
        }
        this.stream = await navigator.mediaDevices.getUserMedia(constraints)
        this.$refs.video.srcObject = this.stream
        await this.$refs.video.play()
        this.cameraReady = true
        this.$emit('ready')
        const self = this
        await new Promise(function (resolve) {
          function checkReady () {
            if (self.$refs.video && self.$refs.video.videoWidth > 0) {
              resolve()
            } else {
              requestAnimationFrame(checkReady)
            }
          }
          checkReady()
        })
        this.startPushStream()
      } catch (err) {
        if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
          this.cameraError = '需要摄像头权限才能进行人脸识别，请在浏览器设置中开启摄像头权限'
        } else if (err.name === 'NotFoundError') {
          this.cameraError = '未检测到摄像头设备'
        } else {
          this.cameraError = '摄像头启动失败：' + err.message
        }
        this.$emit('error', this.cameraError)
      }
    },
    stopCamera () {
      this.stopPushStream()
      if (this.stream) {
        this.stream.getTracks().forEach(function (track) { track.stop() })
        this.stream = null
      }
      this.cameraReady = false
    },
    async switchCamera () {
      if (this.deviceId) {
        try {
          const stream = await navigator.mediaDevices.getUserMedia({ video: true })
          stream.getTracks().forEach(function (t) { t.stop() })
          const devices = await navigator.mediaDevices.enumerateDevices()
          const videoDevices = devices.filter(function (d) { return d.kind === 'videoinput' })
          if (videoDevices.length <= 1) return
          let currentIdx = -1
          for (let i = 0; i < videoDevices.length; i++) {
            if (videoDevices[i].deviceId === this.deviceId) {
              currentIdx = i
              break
            }
          }
          const nextIdx = (currentIdx + 1) % videoDevices.length
          const nextDevice = videoDevices[nextIdx]
          this.$store.commit('gate/SET_CAMERA', { deviceId: nextDevice.deviceId, label: nextDevice.label || '未命名摄像头' })
        } catch (e) {
          // ignore
        }
        return
      }
      this.currentFacing = this.currentFacing === 'user' ? 'environment' : 'user'
      this.stopCamera()
      await this.startCamera()
    },
    captureFrame () {
      const video = this.$refs.video
      const canvas = this.$refs.canvas
      if (!video || !video.videoWidth) return null
      canvas.width = video.videoWidth
      canvas.height = video.videoHeight
      const ctx = canvas.getContext('2d')
      ctx.drawImage(video, 0, 0)
      return canvas.toDataURL('image/jpeg').split(',')[1]
    },
    startPushStream () {
      if (!this.pushKey || !this.$refs.video) return
      this.streamPusher = new GateStreamPusher(this.$refs.video, this.pushKey)
      this.streamPusher.start()
    },
    stopPushStream () {
      if (this.streamPusher) {
        this.streamPusher.stop()
        this.streamPusher = null
      }
    }
  }
}
</script>

<style scoped>
.face-camera {
  position: relative;
  width: 100%;
  border-radius: var(--gate-radius);
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
.camera-loading,
.camera-error {
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
}
.error-msg {
  margin-top: 12px;
  font-size: 14px;
  color: var(--gate-text-secondary);
  text-align: center;
  padding: 0 24px;
  line-height: 1.5;
}
.camera-switch {
  position: absolute;
  top: 12px;
  right: 12px;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #fff;
}
</style>
