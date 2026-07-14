<template>
  <div class="face-register">
    <div class="camera-area">
      <video ref="video" class="camera-preview" autoplay playsinline></video>
      <canvas ref="canvas" style="display: none;"></canvas>
    </div>
    <div class="form-area">
      <van-field v-model="personName" label="姓名" placeholder="请输入姓名" required />
      <div class="gate-form-item">
        <label class="gate-form-label">授权入户门</label>
        <div class="gate-address-select" :class="{ 'is-open': showGateDrop }">
          <div class="gate-select-trigger" @click="showGateDrop = !showGateDrop">
            <span :class="selectedGateId ? '' : 'gate-placeholder'">{{ selectedGateLabel || '请选择' }}</span>
            <i class="el-icon-arrow-down gate-select-arrow" :class="{ 'is-reverse': showGateDrop }"></i>
          </div>
          <transition name="dropdown">
            <div v-if="showGateDrop" class="gate-select-dropdown">
              <div v-for="door in entranceDoors" :key="door.id" class="gate-select-option" :class="{ 'is-active': selectedGateId === door.id }" @click="selectGateDoor(door)">{{ door.gate_name }}</div>
            </div>
          </transition>
        </div>
      </div>
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
      showGateDrop: false,
      loading: false,
      stream: null
    }
  },
  computed: {
    selectedGateLabel () {
      if (!this.selectedGateId) return ''
      const door = this.entranceDoors.find(d => d.id === this.selectedGateId)
      return door ? door.gate_name : ''
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
    selectGateDoor (door) {
      this.selectedGateId = door.id
      this.showGateDrop = false
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
          this.showGateDrop = false
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
.gate-form-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 10px 16px;
}
.gate-form-label {
  font-size: 14px;
  color: var(--dark-text-secondary);
  font-weight: 500;
}
.gate-address-select {
  position: relative;
}
.gate-select-trigger {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--dark-border-field);
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
  color: var(--dark-text);
  transition: border-color 0.2s;
}
.gate-address-select.is-open .gate-select-trigger {
  border-color: var(--dark-accent-light);
}
.gate-placeholder {
  color: var(--dark-text-muted);
}
.gate-select-arrow {
  font-size: 12px;
  color: var(--dark-text-secondary);
  transition: transform 0.2s;
  flex-shrink: 0;
}
.gate-select-arrow.is-reverse {
  transform: rotate(180deg);
}
.gate-select-dropdown {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  right: 0;
  background: var(--dark-bg-secondary);
  border: 1px solid var(--dark-border-field);
  border-radius: 8px;
  padding: 4px 0;
  z-index: 100;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
  max-height: 200px;
  overflow-y: auto;
}
.gate-select-option {
  padding: 8px 12px;
  font-size: 13px;
  color: var(--dark-text-secondary);
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}
.gate-select-option:hover {
  background: rgba(255, 255, 255, 0.06);
  color: var(--dark-text);
}
.gate-select-option.is-active {
  color: var(--dark-accent-light);
  background: rgba(99, 102, 241, 0.1);
}
.dropdown-enter-active,
.dropdown-leave-active {
  transition: opacity 0.2s, transform 0.2s;
}
.dropdown-enter,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>
