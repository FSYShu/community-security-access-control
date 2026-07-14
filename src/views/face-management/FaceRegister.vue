<template>
  <div class="face-register">
    <div class="camera-area">
      <video ref="video" class="camera-preview" autoplay playsinline></video>
      <canvas ref="canvas" style="display: none;"></canvas>
    </div>
    <div class="form-area">
      <van-field v-model="personName" label="姓名" placeholder="请输入姓名" required />
      <van-field name="selectedGateId" label="授权入户门" readonly clickable right-icon="arrow" :value="selectedGateLabel" placeholder="请选择" @click="showGatePicker = true" />
      <van-popup v-model="showGatePicker" position="bottom" round>
        <van-picker :columns="gateColumns" @confirm="onGateConfirm" @cancel="showGatePicker = false" />
      </van-popup>
      <div class="action-area">
        <van-button type="primary" block @click="captureAndRegister" :loading="loading" loading-text="录入中...">录入</van-button>
      </div>
    </div>
  </div>
</template>

<script>
import { registerFace } from '@/api/face'
import { getGateList } from '@/api/property'

export default {
  name: 'FaceRegister',
  data () {
    return {
      personName: '',
      personType: 'owner',
      selectedGateId: null,
      entranceDoors: [],
      showGatePicker: false,
      loading: false,
      stream: null
    }
  },
  computed: {
    selectedGateLabel () {
      if (!this.selectedGateId) return ''
      const door = this.entranceDoors.find(d => d.id === this.selectedGateId)
      return door ? door.gate_name : ''
    },
    gateColumns () {
      return this.entranceDoors.map(d => ({ text: d.gate_name, value: d.id }))
    }
  },
  mounted () {
    this.startCamera()
    this.loadEntranceDoors()
  },
  beforeDestroy () {
    this.stopCamera()
  },
  methods: {
    async loadEntranceDoors () {
      try {
        const res = await getGateList({ gate_level: 'entrance_door', per_page: 999 })
        const data = res.data
        this.entranceDoors = (data && data.items) ? data.items : []
      } catch (err) {
        this.entranceDoors = []
      }
    },
    onGateConfirm (val) {
      this.selectedGateId = val.value
      this.showGatePicker = false
    },
    async startCamera () {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        this.$message.error('当前环境不支持摄像头，请使用HTTPS或localhost访问')
        return
      }
      try {
        this.stream = await navigator.mediaDevices.getUserMedia({ video: true })
        this.$refs.video.srcObject = this.stream
      } catch (err) {
        if (err.name === 'NotAllowedError') {
          this.$message.error('摄像头权限被拒绝，请在浏览器设置中允许访问摄像头')
        } else if (err.name === 'NotFoundError') {
          this.$message.error('未检测到摄像头设备')
        } else {
          this.$message.error('无法访问摄像头：' + err.message)
        }
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
        return this.$message.warning('请输入姓名')
      }
      const video = this.$refs.video
      const canvas = this.$refs.canvas
      if (!video.videoWidth) {
        return this.$message.warning('摄像头未就绪')
      }
      canvas.width = video.videoWidth
      canvas.height = video.videoHeight
      const ctx = canvas.getContext('2d')
      ctx.drawImage(video, 0, 0)
      const base64Image = canvas.toDataURL('image/jpeg').split(',')[1]
      const allowedGates = this.selectedGateId ? [this.selectedGateId] : []
      this.loading = true
      try {
        const res = await registerFace({
          face_image: base64Image,
          person_name: this.personName,
          person_type: this.personType,
          allowed_gates: allowedGates
        })
        if (res.code === 0) {
          this.$message.success('录入成功')
          this.personName = ''
          this.selectedGateId = null
        }
      } catch (err) {
        if (!err.message || err.message === '请求失败') {
          this.$message.error('录入失败')
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
  overflow: hidden;
}
.camera-area {
  width: 100%;
  margin-bottom: 16px;
  overflow: hidden;
  border-radius: 12px;
  border: 1px solid var(--dark-border);
  background: #000;
  line-height: 0;
  max-width: 480px;
  margin-left: auto;
  margin-right: auto;
}
.camera-preview {
  width: 100%;
  display: block;
  object-fit: cover;
}
.form-area {
  margin-top: 12px;
}
.action-area {
  margin-top: 16px;
  padding: 0 16px;
}
</style>
