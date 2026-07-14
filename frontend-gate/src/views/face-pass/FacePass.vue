<template>
  <div class="gate-page face-pass-page">
    <div class="gate-header">
      <span class="gate-header-title">刷脸通行</span>
      <i class="el-icon-close" style="font-size:20px;color:#9ca3af" @click="$router.push('/idle')"></i>
    </div>
    <div class="gate-content">
      <face-camera ref="camera" :push-key="pushKey" :device-id="cameraDeviceId" @error="onCameraError" />

      <div v-if="!result" class="pass-action">
        <button class="gate-btn gate-btn-primary" :disabled="!cameraReady || loading" @click="doFacePass">
          <van-loading v-if="loading" size="20" color="#fff" />
          <span v-else>刷脸通行</span>
        </button>
      </div>

      <div v-if="result" class="pass-result-wrap">
        <pass-result :passed="result.passed" :reason="result.reason" :personName="result.personName" />
        <button class="gate-btn gate-btn-outline" style="margin-top:16px;" @click="resetPass">重新识别</button>
      </div>

      <div v-if="cameraError" class="camera-error-hint">
        <p>{{ cameraError }}</p>
      </div>
    </div>
  </div>
</template>

<script>
import FaceCamera from '@/components/FaceCamera.vue'
import PassResult from '@/components/PassResult.vue'
import { submitFacePass } from '@/api/face'
import { checkBrowserSupport, checkHTTPS } from '@/utils/browser-check'
import { enqueue, setupOnlineHandler } from '@/utils/offline-queue'

const RESULT_DISPLAY_TIME = 5000

export default {
  name: 'FacePassPage',
  components: { FaceCamera: FaceCamera, PassResult: PassResult },
  data () {
    return {
      loading: false,
      result: null,
      cameraReady: false,
      cameraError: '',
      resultTimer: null,
      gateId: '',
      browserCheck: null
    }
  },
  computed: {
    pushKey () { return this.$store.getters['gate/pushKey'] },
    cameraDeviceId () { return this.$store.getters['gate/cameraDeviceId'] }
  },
  mounted () {
    this.gateId = this.$store.getters['gate/gateId'] || this.$route.query.gate_id || ''
    const browser = checkBrowserSupport()
    const https = checkHTTPS()
    if (!browser.supported) {
      this.cameraError = browser.message
      this.browserCheck = browser
    } else if (!https.secure) {
      this.cameraError = https.message
      this.browserCheck = https
    }
    const self = this
    setupOnlineHandler(function (data) {
      self.submitOfflineItem(data)
    })
  },
  beforeDestroy () {
    this.clearResultTimer()
  },
  methods: {
    onCameraError (msg) {
      this.cameraError = msg
    },
    async doFacePass () {
      if (this.browserCheck && !this.browserCheck.supported) return
      if (!this.$refs.camera) return
      const base64Image = this.$refs.camera.captureFrame()
      if (!base64Image) {
        this.$toast.fail('摄像头未就绪')
        return
      }
      this.loading = true
      this.result = null
      try {
        const res = await submitFacePass({
          face_image: base64Image,
          gate_id: this.gateId
        })
        this.result = {
          passed: true,
          personName: res.data && res.data.person_name ? res.data.person_name : ''
        }
      } catch (err) {
        if (!navigator.onLine) {
          enqueue({ face_image: base64Image, gate_id: this.gateId })
          this.result = { passed: false, reason: '网络断开，已暂存待网络恢复后自动提交' }
        } else {
          const msg = (err && err.message) || '识别失败'
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
          this.result = { passed: false, reason: reason || msg }
        }
      } finally {
        this.loading = false
      }
      this.startResultTimer()
    },
    startResultTimer () {
      this.clearResultTimer()
      const self = this
      this.resultTimer = setTimeout(function () {
        self.$router.push('/idle')
      }, RESULT_DISPLAY_TIME)
    },
    clearResultTimer () {
      if (this.resultTimer) {
        clearTimeout(this.resultTimer)
        this.resultTimer = null
      }
    },
    resetPass () {
      this.result = null
      this.clearResultTimer()
    },
    async submitOfflineItem (data) {
      try {
        await submitFacePass(data)
      } catch (err) {
        // silent fail for offline retry
      }
    }
  }
}
</script>

<style scoped>
.pass-action {
  margin-top: 20px;
}
.pass-result-wrap {
  margin-top: 20px;
}
.camera-error-hint {
  margin-top: 16px;
  padding: 12px;
  background: rgba(239, 68, 68, 0.1);
  border-radius: var(--gate-radius-sm);
  color: var(--gate-danger);
  font-size: 14px;
  text-align: center;
  line-height: 1.5;
}
</style>
