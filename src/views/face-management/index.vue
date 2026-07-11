<template>
  <app-layout page-title="人脸信息管理">
    <div class="dark-card">
      <div class="filter-row">
        <div class="filter-spacer"></div>
        <button class="action-btn test-btn" @click="showTestDialog = true">
          <i class="el-icon-camera"></i>
          <span>人脸测试</span>
        </button>
        <button class="action-btn add-btn" @click="openAddDialog">
          <i class="el-icon-plus"></i>
          <span>新增人脸</span>
        </button>
      </div>
    </div>
    <div class="dark-card">
      <van-pull-refresh v-model="refreshing" @refresh="onRefresh">
        <van-list v-model="loading" :finished="finished" finished-text="没有更多了" @load="loadData">
          <van-cell v-for="item in list" :key="item.id">
            <template #title>
              <span class="type-tag" :class="item.person_type === 'owner' ? 'tag-owner' : 'tag-blacklist'">{{ typeMap[item.person_type] || item.person_type }}</span>
              <span class="cell-name">{{ item.person_name }}</span>
            </template>
            <template #right-icon>
              <span class="cell-status">
                <span class="status-dot" :class="item.status === 'active' ? 'dot-active' : 'dot-inactive'"></span>
                <span class="status-label">{{ item.status === 'active' ? '启用' : '停用' }}</span>
              </span>
              <button class="delete-btn" @click="onDelete(item)">
                <i class="el-icon-delete"></i>
                <span>删除</span>
              </button>
            </template>
          </van-cell>
        </van-list>

      </van-pull-refresh>
    </div>

    <el-dialog :visible.sync="showAddDialog" title="新增人脸" width="480px" :close-on-click-modal="false" append-to-body custom-class="dark-dialog" @close="resetAddForm">
      <div class="form-grid">
        <div class="form-item">
          <label class="form-label">摄像头画面</label>
          <div class="camera-area">
            <video ref="addVideo" class="camera-preview" autoplay playsinline></video>
            <canvas ref="addCanvas" style="display: none;"></canvas>
          </div>
        </div>
        <div class="form-item">
          <label class="form-label">姓名 <span class="form-required">*</span></label>
          <input v-model="addForm.personName" class="form-input" placeholder="请输入姓名" />
        </div>
        <div class="form-item">
          <label class="form-label">人员类型 <span class="form-required">*</span></label>
          <div class="filter-select" :class="{ 'is-open': showTypeDropdown }">
            <div class="select-trigger" @click="showTypeDropdown = !showTypeDropdown">
              <span class="select-value">{{ addFormTypeLabel || '请选择' }}</span>
              <i class="el-icon-arrow-down select-arrow" :class="{ 'is-reverse': showTypeDropdown }"></i>
            </div>
            <transition name="dropdown">
              <div v-if="showTypeDropdown" class="select-dropdown">
                <div v-for="opt in typeOptions" :key="opt.value" class="select-option" :class="{ 'is-active': addForm.personType === opt.value }" @click="addForm.personType = opt.value; showTypeDropdown = false">{{ opt.text }}</div>
              </div>
            </transition>
          </div>
        </div>
      </div>
      <div class="form-footer">
        <button class="form-btn form-btn-cancel" @click="showAddDialog = false">取消</button>
        <button class="form-btn form-btn-primary" @click="onAddSubmit" :disabled="addLoading">
          <i v-if="addLoading" class="el-icon-loading"></i>
          录入
        </button>
      </div>
    </el-dialog>

    <el-dialog :visible.sync="showTestDialog" title="人脸测试" width="480px" :close-on-click-modal="false" append-to-body custom-class="dark-dialog" @close="stopTestCamera">
      <div class="form-grid">
        <div class="form-item">
          <label class="form-label">摄像头画面</label>
          <div class="camera-area">
            <video ref="testVideo" class="camera-preview" autoplay playsinline></video>
            <canvas ref="testCanvas" style="display: none;"></canvas>
          </div>
        </div>
      </div>
      <div v-if="testResult" class="test-result">
        <template v-if="!testResult.detected">
          <div class="result-item result-warn">未检测到人脸</div>
        </template>
        <template v-else>
          <div class="result-item">检测到人脸：{{ testResult.face_count }}张</div>
          <div v-for="(face, idx) in testResult.results" :key="idx" class="face-result-card">
            <div class="result-row">
              <span>人脸 #{{ face.face_index }}</span>
              <span :class="face.matched ? 'result-success' : 'result-warn'">{{ face.matched ? '已识别' : '陌生人' }}</span>
            </div>
            <div v-if="face.matched" class="result-row">
              <span>姓名</span>
              <span>{{ face.person_name }}</span>
            </div>
            <div class="result-row">
              <span>置信度</span>
              <span>{{ face.confidence }}%</span>
            </div>
          </div>
        </template>
      </div>
      <div class="form-footer">
        <button class="form-btn form-btn-cancel" @click="showTestDialog = false">关闭</button>
        <button class="form-btn form-btn-primary" @click="onTestCapture" :disabled="testLoading">
          <i v-if="testLoading" class="el-icon-loading"></i>
          拍照识别
        </button>
      </div>
    </el-dialog>
  </app-layout>
</template>

<script>
import { getFaceList, deleteFace, registerFace, testFace } from '@/api/face'

export default {
  name: 'FaceManagementPage',
  data () {
    return {
      list: [],
      loading: false,
      finished: false,
      refreshing: false,
      page: 1,
      typeMap: { owner: '业主', blacklist: '黑名单' },
      showAddDialog: false,
      showTestDialog: false,
      showTypeDropdown: false,
      addLoading: false,
      testLoading: false,
      testResult: null,
      addStream: null,
      testStream: null,
      addForm: { personName: '', personType: 'owner' },
      typeOptions: [
        { text: '业主', value: 'owner' },
        { text: '黑名单', value: 'blacklist' }
      ]
    }
  },
  computed: {
    addFormTypeLabel () {
      const opt = this.typeOptions.find(o => o.value === this.addForm.personType)
      return opt ? opt.text : ''
    }
  },
  mounted () {
    document.addEventListener('click', this.closeDropdowns)
  },
  beforeDestroy () {
    document.removeEventListener('click', this.closeDropdowns)
    this.stopAddCamera()
    this.stopTestCamera()
  },
  methods: {
    closeDropdowns (e) {
      if (!e.target.closest('.filter-select')) {
        this.showTypeDropdown = false
      }
    },
    async loadData () {
      try {
        const res = await getFaceList({ page: this.page, per_page: 20 })
        const data = res.data
        if (data && data.items) {
          if (this.page === 1) {
            this.list = data.items
          } else {
            this.list = this.list.concat(data.items)
          }
          this.finished = this.list.length >= data.total
          this.page++
        } else {
          this.finished = true
        }
      } catch (err) {
        this.finished = true
      } finally {
        this.loading = false
        this.refreshing = false
      }
    },
    onRefresh () {
      this.page = 1
      this.finished = false
      this.loadData()
    },
    onDelete (item) {
      this.$confirm('确定要删除「' + item.person_name + '」的人脸数据吗？', '确认删除', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        customClass: 'dark-dialog'
      }).then(() => {
        this.doDelete(item.id)
      }).catch(() => {})
    },
    async doDelete (id) {
      try {
        await deleteFace(id)
        this.$message.success('删除成功')
        this.onRefresh()
      } catch (err) {
        this.$message.error('删除失败')
      }
    },
    resetAddForm () {
      this.addForm = { personName: '', personType: 'owner' }
      this.showTypeDropdown = false
      this.stopAddCamera()
    },
    openAddDialog () {
      this.resetAddForm()
      this.showAddDialog = true
      this.$nextTick(() => this.startAddCamera())
    },
    async startAddCamera () {
      try {
        this.addStream = await navigator.mediaDevices.getUserMedia({ video: true })
        if (this.$refs.addVideo) this.$refs.addVideo.srcObject = this.addStream
      } catch (err) {
        this.$message.warning('无法访问摄像头')
      }
    },
    stopAddCamera () {
      if (this.addStream) {
        this.addStream.getTracks().forEach(track => track.stop())
        this.addStream = null
      }
    },
    async onAddSubmit () {
      if (!this.addForm.personName) {
        return this.$message.warning('请输入姓名')
      }
      const video = this.$refs.addVideo
      const canvas = this.$refs.addCanvas
      if (!video || !video.videoWidth) {
        return this.$message.warning('摄像头未就绪')
      }
      canvas.width = video.videoWidth
      canvas.height = video.videoHeight
      const ctx = canvas.getContext('2d')
      ctx.drawImage(video, 0, 0)
      const base64Image = canvas.toDataURL('image/jpeg').split(',')[1]
      this.addLoading = true
      try {
        const res = await registerFace({
          face_image: base64Image,
          person_name: this.addForm.personName,
          person_type: this.addForm.personType
        })
        if (res.code === 0) {
          this.$message.success('录入成功')
          this.showAddDialog = false
          this.onRefresh()
        }
      } catch (err) {
        this.$message.error('录入失败')
      } finally {
        this.addLoading = false
      }
    },
    async startTestCamera () {
      try {
        this.testStream = await navigator.mediaDevices.getUserMedia({ video: true })
        if (this.$refs.testVideo) this.$refs.testVideo.srcObject = this.testStream
      } catch (err) {
        this.$message.warning('无法访问摄像头')
      }
    },
    stopTestCamera () {
      if (this.testStream) {
        this.testStream.getTracks().forEach(track => track.stop())
        this.testStream = null
      }
      this.testResult = null
    },
    async onTestCapture () {
      const video = this.$refs.testVideo
      const canvas = this.$refs.testCanvas
      if (!video || !video.videoWidth) {
        return this.$message.warning('摄像头未就绪')
      }
      canvas.width = video.videoWidth
      canvas.height = video.videoHeight
      const ctx = canvas.getContext('2d')
      ctx.drawImage(video, 0, 0)
      const base64Image = canvas.toDataURL('image/jpeg').split(',')[1]
      this.testLoading = true
      this.testResult = null
      try {
        const res = await testFace({ face_image: base64Image })
        if (res.code === 0) {
          this.testResult = res.data
        } else {
          this.$message.error(res.message || '识别失败')
        }
      } catch (err) {
        this.$message.error('识别请求失败')
      } finally {
        this.testLoading = false
      }
    }
  },
  watch: {
    showTestDialog (val) {
      if (val) {
        this.$nextTick(() => this.startTestCamera())
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

.filter-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.filter-spacer {
  flex: 1;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 8px 16px;
  border: none;
  border-radius: 8px;
  font-size: 13px;
  cursor: pointer;
  transition: background 0.2s;
}

.action-btn i {
  font-size: 14px;
}

.add-btn {
  background: var(--dark-accent);
  color: #fff;
}

.add-btn:hover {
  background: var(--dark-accent-light);
}

.test-btn {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--dark-border-field);
  color: var(--dark-text-secondary);
}

.test-btn:hover {
  background: rgba(255, 255, 255, 0.08);
  color: var(--dark-text);
}

.cell-status {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  margin-right: 8px;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}

.dot-active {
  background: var(--dark-success);
  box-shadow: 0 0 6px rgba(16, 185, 129, 0.4);
}

.dot-inactive {
  background: #ef4444;
  box-shadow: 0 0 6px rgba(239, 68, 68, 0.4);
}

.status-label {
  font-size: 13px;
  color: var(--dark-text-secondary);
}

.type-tag {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0 6px;
  height: 22px;
  border-radius: 4px;
  font-size: 12px;
  margin-right: 8px;
  border: 1px solid;
}

.tag-owner {
  color: var(--dark-accent-light);
  border-color: rgba(99, 102, 241, 0.3);
  background: rgba(99, 102, 241, 0.08);
}

.tag-blacklist {
  color: #ef4444;
  border-color: rgba(239, 68, 68, 0.3);
  background: rgba(239, 68, 68, 0.08);
}

.cell-name {
  font-size: 15px;
  color: var(--dark-text);
}

.delete-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 0 10px;
  height: 28px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--dark-border-field);
  border-radius: 6px;
  color: var(--dark-text-secondary);
  font-size: 13px;
  transition: background 0.2s, color 0.2s, border-color 0.2s;
}

.delete-btn:hover {
  background: rgba(239, 68, 68, 0.1);
  border-color: #ef4444;
  color: #ef4444;
}

.form-grid {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-label {
  font-size: 13px;
  color: var(--dark-text-secondary);
  font-weight: 500;
}

.form-required {
  color: var(--dark-danger);
}

.form-input {
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  color: var(--dark-text);
  font-size: 13px;
  outline: none;
  transition: border-color 0.2s;
}

.form-input::placeholder {
  color: var(--dark-text-muted);
}

.form-input:focus {
  border-color: var(--dark-accent-light);
}

.camera-area {
  width: 100%;
  max-width: 480px;
  margin: 0 auto;
  overflow: hidden;
  border-radius: 12px;
  border: 1px solid var(--dark-border);
  background: #000;
  line-height: 0;
}

.camera-preview {
  width: 100%;
  display: block;
  object-fit: cover;
}

.filter-select {
  position: relative;
  min-width: 140px;
}

.select-trigger {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--dark-border-field);
  border-radius: 8px;
  cursor: pointer;
  transition: border-color 0.2s;
}

.filter-select.is-open .select-trigger {
  border-color: var(--dark-accent);
}

.select-value {
  font-size: 13px;
  color: var(--dark-text);
  white-space: nowrap;
}

.select-arrow {
  font-size: 12px;
  color: var(--dark-text-secondary);
  transition: transform 0.2s;
  margin-left: 6px;
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
  border-radius: 8px;
  padding: 4px 0;
  z-index: 100;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
}

.select-option {
  padding: 8px 12px;
  font-size: 13px;
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

.dropdown-enter-active,
.dropdown-leave-active {
  transition: opacity 0.2s, transform 0.2s;
}

.dropdown-enter,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

.form-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.form-btn {
  padding: 8px 20px;
  border-radius: 8px;
  font-size: 13px;
  cursor: pointer;
  border: none;
  transition: background 0.2s;
}

.form-btn-cancel {
  background: rgba(255, 255, 255, 0.06);
  color: var(--dark-text);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.form-btn-cancel:hover {
  background: rgba(255, 255, 255, 0.1);
}

.form-btn-primary {
  background: var(--dark-accent);
  color: #fff;
}

.form-btn-primary:hover {
  background: var(--dark-accent-light);
}

.test-result {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.result-item {
  font-size: 13px;
  color: var(--dark-text-secondary);
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.04);
  border-radius: 6px;
}

.result-success {
  color: var(--dark-success-green);
}

.result-warn {
  color: var(--dark-orange);
}

.face-result-card {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--dark-border);
  border-radius: 8px;
  padding: 8px 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.result-row {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  color: var(--dark-text-secondary);
}
</style>

<style>
.dark-dialog {
  background: #0A0A0A !important;
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 16px;
}

.dark-dialog .el-dialog__header {
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  padding: 16px 20px;
}

.dark-dialog .el-dialog__title {
  color: #EDEDEF;
  font-weight: 600;
}

.dark-dialog .el-dialog__headerbtn .el-dialog__close {
  color: #8A8F98;
}

.dark-dialog .el-dialog__body {
  padding: 20px;
}
</style>
