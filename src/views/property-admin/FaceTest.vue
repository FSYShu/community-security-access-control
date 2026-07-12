<template>
  <app-layout page-title="人脸识别测试">
    <div class="dark-card">
      <div class="camera-area">
        <video ref="video" class="camera-preview" autoplay playsinline></video>
        <canvas ref="canvas" style="display:none;"></canvas>
      </div>
      <div class="action-bar">
        <van-button
          type="primary"
          block
          :loading="testing"
          loading-text="识别中..."
          @click="captureAndTest"
        >拍照识别</van-button>
      </div>
      <div v-if="result" class="result-section">
        <van-cell-group title="识别结果">
          <van-cell
            v-if="!result.detected"
            title="检测结果"
            value="未检测到人脸"
            value-class="value-warn"
          />
          <template v-else>
            <van-cell title="检测到人脸" :value="result.face_count + '张'" />
            <div
              v-for="(face, idx) in result.results"
              :key="idx"
              class="face-result-card"
            >
              <van-cell
                :title="'人脸 #' + face.face_index"
                :value="face.matched ? '已识别' : '陌生人'"
                :value-class="face.matched ? 'value-success' : 'value-warn'"
              />
              <van-cell v-if="face.matched" title="姓名" :value="face.person_name" />
              <van-cell title="置信度" :value="face.confidence + '%'" />
              <van-cell title="特征距离" :value="String(face.distance)" />
            </div>
          </template>
        </van-cell-group>
      </div>
    </div>
  </app-layout>
</template>

<script>
import { testFace } from '@/api/face'

export default {
  name: 'FaceTest',
  data () {
    return {
      testing: false,
      result: null,
      stream: null
    }
  },
  mounted () {
    this.startCamera()
  },
  beforeDestroy () {
    this.stopCamera()
  },
  methods: {
    async startCamera () {
      try {
        this.stream = await navigator.mediaDevices.getUserMedia({ video: true })
        this.$refs.video.srcObject = this.stream
      } catch (err) {
        this.$message.warning('无法访问摄像头，请检查权限设置')
      }
    },
    stopCamera () {
      if (this.stream) {
        this.stream.getTracks().forEach(function (track) { track.stop() })
        this.stream = null
      }
    },
    async captureAndTest () {
      const video = this.$refs.video
      const canvas = this.$refs.canvas
      if (!video.videoWidth) {
        return this.$message.warning('摄像头未就绪')
        return
      }
      canvas.width = video.videoWidth
      canvas.height = video.videoHeight
      const ctx = canvas.getContext('2d')
      ctx.drawImage(video, 0, 0)
      const base64Image = canvas.toDataURL('image/jpeg').split(',')[1]

      this.testing = true
      this.result = null
      try {
        const res = await testFace({ face_image: base64Image })
        if (res.code === 0) {
          this.result = res.data
        } else {
          this.$message.error(res.message || '识别失败')
        }
      } catch (error) {
        // 拦截器已弹出后端错误消息，此处不再重复提示
      } finally {
        this.testing = false
      }
    }
  }
}
</script>

<style scoped>
.dark-card {
  background: var(--dark-card);
  border-radius: 16px;
  border: 1px solid var(--dark-border);
  padding: 20px;
  margin-bottom: 16px;
}
.camera-area {
  width: 100%;
  margin-bottom: 12px;
  text-align: center;
}
.camera-preview {
  width: 100%;
  max-width: 480px;
  border-radius: 12px;
  background: #000;
  border: 1px solid rgba(255, 255, 255, 0.06);
}
.action-bar {
  margin-top: 8px;
}
.result-section {
  margin-top: 16px;
}
.face-result-card {
  margin: 8px 0;
  border: 1px solid var(--dark-border);
  border-radius: 8px;
  overflow: hidden;
}
.value-success {
  color: var(--dark-success-green);
  font-weight: 500;
}
.value-warn {
  color: var(--dark-orange);
  font-weight: 500;
}
</style>
