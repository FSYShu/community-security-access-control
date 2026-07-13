<template>
  <div class="gate-page visitor-apply-page">
    <div class="gate-header">
      <i class="el-icon-arrow-left" style="font-size:20px;color:#9ca3af" @click="$router.push('/idle')"></i>
      <span class="gate-header-title">访客临时授权申请</span>
      <span style="width:20px;"></span>
    </div>
    <div class="gate-content">
      <div class="gate-card">
        <van-field v-model="form.visitorName" label="访客姓名" placeholder="请输入姓名" required />
        <van-field v-model="form.ownerName" label="被访业主" placeholder="请输入业主姓名" required />

        <div class="form-item">
          <label class="form-label">申请通行层级</label>
          <van-checkbox-group v-model="form.gateLevels" direction="horizontal">
            <van-checkbox name="community_gate" shape="square">社区大门</van-checkbox>
            <van-checkbox name="unit_door" shape="square">单元门</van-checkbox>
          </van-checkbox-group>
        </div>

        <div class="form-item">
          <label class="form-label">申请通行时段</label>
          <div class="time-range">
            <van-field v-model="form.startTime" placeholder="开始时间" readonly @click="showStartPicker = true" />
            <span class="time-sep">至</span>
            <van-field v-model="form.endTime" placeholder="结束时间" readonly @click="showEndPicker = true" />
          </div>
        </div>

        <div class="form-item">
          <label class="form-label">访客人脸照片</label>
          <face-camera ref="camera" :show-switch="true" :device-id="cameraDeviceId" style="max-width:320px;margin:0 auto;" />
          <button class="gate-btn gate-btn-outline" style="margin-top:8px;" @click="captureFace">
            <i class="el-icon-camera"></i> 拍照采集
          </button>
          <p v-if="faceCaptured" class="capture-hint">已采集人脸照片</p>
        </div>
      </div>

      <button class="gate-btn gate-btn-primary" :disabled="!canSubmit || submitting" @click="doSubmit">
        <van-loading v-if="submitting" size="20" color="#fff" />
        <span v-else>提交申请</span>
      </button>
    </div>

    <van-popup v-model="showStartPicker" position="bottom" round>
      <van-datetime-picker type="datetime" v-model="startPickerValue" @confirm="onStartConfirm" @cancel="showStartPicker = false" />
    </van-popup>
    <van-popup v-model="showEndPicker" position="bottom" round>
      <van-datetime-picker type="datetime" v-model="endPickerValue" @confirm="onEndConfirm" @cancel="showEndPicker = false" />
    </van-popup>
  </div>
</template>

<script>
import FaceCamera from '@/components/FaceCamera.vue'
import { applyVisitorAuth } from '@/api/visitorAuth'

export default {
  name: 'VisitorApplyPage',
  components: { FaceCamera: FaceCamera },
  data () {
    return {
      form: {
        visitorName: '',
        ownerName: '',
        gateLevels: [],
        startTime: '',
        endTime: ''
      },
      faceBase64: '',
      faceCaptured: false,
      submitting: false,
      showStartPicker: false,
      showEndPicker: false,
      startPickerValue: new Date(),
      endPickerValue: new Date()
    }
  },
  computed: {
    cameraDeviceId () { return this.$store.getters['gate/cameraDeviceId'] },
    canSubmit () {
      return this.form.visitorName && this.form.ownerName && this.form.gateLevels.length > 0 && this.form.startTime && this.form.endTime && this.faceCaptured
    }
  },
  methods: {
    captureFace () {
      if (!this.$refs.camera) return
      var base64 = this.$refs.camera.captureFrame()
      if (base64) {
        this.faceBase64 = base64
        this.faceCaptured = true
        this.$toast.success('人脸照片已采集')
      } else {
        this.$toast.fail('摄像头未就绪')
      }
    },
    formatTime (date) {
      var y = date.getFullYear()
      var m = String(date.getMonth() + 1).padStart(2, '0')
      var d = String(date.getDate()).padStart(2, '0')
      var h = String(date.getHours()).padStart(2, '0')
      var min = String(date.getMinutes()).padStart(2, '0')
      return y + '-' + m + '-' + d + ' ' + h + ':' + min
    },
    onStartConfirm (val) {
      this.form.startTime = this.formatTime(val)
      this.showStartPicker = false
    },
    onEndConfirm (val) {
      this.form.endTime = this.formatTime(val)
      this.showEndPicker = false
    },
    async doSubmit () {
      this.submitting = true
      try {
        await applyVisitorAuth({
          visitor_name: this.form.visitorName,
          owner_name: this.form.ownerName,
          apply_gate_levels: JSON.stringify(this.form.gateLevels),
          apply_time_range: JSON.stringify({ start: this.form.startTime, end: this.form.endTime }),
          visitor_face_image: this.faceBase64,
          apply_source: 'gate_terminal'
        })
        this.$toast.success('申请已提交，等待业主审批')
        this.$router.push('/idle')
      } catch (err) {
        // error handled by interceptor
      } finally {
        this.submitting = false
      }
    }
  }
}
</script>

<style scoped>
.form-item {
  padding: 10px 16px;
}
.form-label {
  display: block;
  font-size: 14px;
  color: var(--gate-text-secondary);
  margin-bottom: 8px;
}
.time-range {
  display: flex;
  align-items: center;
  gap: 8px;
}
.time-sep {
  color: var(--gate-text-muted);
  font-size: 14px;
  flex-shrink: 0;
}
.capture-hint {
  margin-top: 8px;
  font-size: 13px;
  color: var(--gate-success);
  text-align: center;
}
</style>