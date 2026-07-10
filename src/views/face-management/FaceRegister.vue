<template>
  <div class="face-register">
    <div class="camera-area">
      <video ref="video" class="camera-preview" autoplay playsinline></video>
      <canvas ref="canvas" style="display: none;"></canvas>
    </div>
    <div class="form-area">
      <van-field v-model="personName" label="姓名" placeholder="请输入姓名" required />
      <van-field name="personType" label="人员类型">
        <template #input>
          <van-radio-group v-model="personType" direction="horizontal">
            <van-radio name="owner">业主</van-radio>

            <van-radio name="blacklist">黑名单</van-radio>
          </van-radio-group>
        </template>
      </van-field>
      <div class="action-area">
        <van-button type="primary" block @click="captureAndRegister" :loading="loading" loading-text="录入中...">录入</van-button>
      </div>
    </div>
  </div>
</template>

<script>
import { registerFace } from '@/api/face'
import { Toast } from 'vant'

export default {
  name: 'FaceRegister',
  data () {
    return {
      personName: '',
      personType: 'owner',
      loading: false,
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
        Toast.fail('无法访问摄像头，请检查权限设置')
      }
    },
    stopCamera () {
      if (this.stream) {
        this.stream.getTracks().forEach(track => track.stop())
        this.stream = null
      }
    },
    async captureAndRegister () {
      if (!this.personName) {
        Toast.fail('请输入姓名')
        return
      }
      const video = this.$refs.video
      const canvas = this.$refs.canvas
      if (!video.videoWidth) {
        Toast.fail('摄像头未就绪')
        return
      }
      canvas.width = video.videoWidth
      canvas.height = video.videoHeight
      const ctx = canvas.getContext('2d')
      ctx.drawImage(video, 0, 0)
      const base64Image = canvas.toDataURL('image/jpeg').split(',')[1]
      this.loading = true
      try {
        const res = await registerFace({
          face_image: base64Image,
          person_name: this.personName,
          person_type: this.personType
        })
        if (res.code === 0) {
          Toast.success('录入成功')
          this.personName = ''
        }
      } catch (err) {
        if (!err.message || err.message === '请求失败') {
          Toast.fail('录入失败')
        }
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style scoped>
.face-register {
  padding: 12px;
}
.camera-area {
  width: 100%;
  margin-bottom: 16px;
  text-align: center;
}
.camera-preview {
  width: 100%;
  max-width: 480px;
  border-radius: 12px;
  background: #000;
  border: 1px solid var(--dark-border);
}
.form-area {
  margin-top: 12px;
}
.action-area {
  margin-top: 16px;
  padding: 0 16px;
}
</style>
