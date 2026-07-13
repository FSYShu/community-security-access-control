<template>
  <app-layout page-title="人脸信息管理" :no-scroll="true">
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
    <div class="dark-card list-section">
      <div class="list-content">
        <van-cell v-for="item in list" :key="item.id">
          <template #title>
            <div class="cell-title-row">
              <span class="cell-status">
                <span class="status-dot" :class="item.status === 'active' ? 'dot-active' : 'dot-inactive'"></span>
                <span class="status-label">{{ item.status === 'active' ? '启用' : '停用' }}</span>
              </span>
              <span class="cell-name">{{ item.person_name }}</span>
              <span class="type-tag" :class="item.person_type === 'owner' ? 'tag-owner' : 'tag-blacklist'">{{ typeMap[item.person_type] || item.person_type }}</span>
            </div>
          </template>
          <template #right-icon>
            <button class="delete-btn" @click="onDelete(item)">
              <i class="el-icon-delete"></i>
              <span>删除</span>
            </button>
          </template>
        </van-cell>
        <div v-if="list.length === 0 && !loading" class="empty-state">
          <i class="el-icon-user" style="font-size:48px;color:var(--dark-text-muted)"></i>
          <p style="color:var(--dark-text-muted);margin-top:12px">暂无人脸信息</p>
        </div>
      </div>
      <div class="pagination-wrapper">
        <el-pagination
          background
          layout="prev, pager, next"
          :current-page="page"
          :page-size="perPage"
          :total="total"
          @current-change="onPageChange"
        />
      </div>
    </div>

    <el-dialog :visible.sync="showAddDialog" title="新增人脸" width="480px" :close-on-click-modal="false" append-to-body custom-class="dark-dialog" @close="resetAddForm">
      <div class="form-grid">
        <div class="form-item">
          <label class="form-label">录入方式</label>
          <div class="mode-tabs">
            <div class="mode-tab" :class="{ active: addMode === 'camera' }" @click="switchAddMode('camera')">
              <i class="el-icon-camera"></i>
              <span>摄像头拍照</span>
            </div>
            <div class="mode-tab" :class="{ active: addMode === 'photo' }" @click="switchAddMode('photo')">
              <i class="el-icon-picture"></i>
              <span>照片上传</span>
            </div>
          </div>
        </div>
        <div v-if="addMode === 'camera'" class="form-item">
          <label class="form-label">摄像头画面</label>
          <div class="camera-area">
            <video ref="addVideo" class="camera-preview" autoplay playsinline></video>
            <canvas ref="addCanvas" style="display: none;"></canvas>
          </div>
        </div>
        <div v-if="addMode === 'photo'" class="form-item">
          <label class="form-label">上传照片</label>
          <div class="upload-area" @click="triggerPhotoUpload">
            <div v-if="!addPhotoPreview" class="upload-placeholder">
              <i class="el-icon-plus upload-icon"></i>
              <span class="upload-text">点击上传人脸照片</span>
              <span class="upload-hint">支持 JPG/PNG 格式</span>
            </div>
            <div v-else class="upload-preview-wrap">
              <img :src="addPhotoPreview" class="upload-preview-img" />
              <div class="upload-replace">
                <i class="el-icon-refresh"></i>
                <span>更换照片</span>
              </div>
            </div>
          </div>
          <input ref="photoInput" type="file" accept="image/jpeg,image/png,image/jpg" style="display: none;" @change="onPhotoSelected" />
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
      page: 1,
      perPage: 20,
      total: 0,
      typeMap: { owner: '业主', blacklist: '黑名单' },
      showAddDialog: false,
      showTestDialog: false,
      showTypeDropdown: false,
      addLoading: false,
      testLoading: false,
      testResult: null,
      addStream: null,
      testStream: null,
      addMode: 'camera',
      addPhotoPreview: null,
      addPhotoBase64: null,
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
    this.loadData()
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
        this.loading = true
        const res = await getFaceList({ page: this.page, per_page: this.perPage })
        const data = res.data
        if (data && data.items) {
          this.list = data.items
          this.total = data.total || 0
        }
      } catch (err) {
        console.error(err)
      } finally {
        this.loading = false
      }
    },
    onPageChange (newPage) {
      this.page = newPage
      this.loadData()
    },
    onRefresh () {
      this.page = 1
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
      this.addMode = 'camera'
      this.addPhotoPreview = null
      this.addPhotoBase64 = null
      this.stopAddCamera()
    },
    openAddDialog () {
      this.resetAddForm()
      this.showAddDialog = true
      this.$nextTick(() => {
        if (this.addMode === 'camera') this.startAddCamera()
      })
    },
    switchAddMode (mode) {
      if (this.addMode === mode) return
      this.addMode = mode
      if (mode === 'camera') {
        this.addPhotoPreview = null
        this.addPhotoBase64 = null
        this.$nextTick(() => this.startAddCamera())
      } else {
        this.stopAddCamera()
      }
    },
    triggerPhotoUpload () {
      this.$refs.photoInput && this.$refs.photoInput.click()
    },
    onPhotoSelected (e) {
      const file = e.target.files && e.target.files[0]
      if (!file) return
      if (!['image/jpeg', 'image/png', 'image/jpg'].includes(file.type)) {
        this.$message.warning('仅支持 JPG/PNG 格式')
        return
      }
      if (file.size > 5 * 1024 * 1024) {
        this.$message.warning('图片大小不能超过5MB')
        return
      }
      const reader = new FileReader()
      reader.onload = (ev) => {
        this.addPhotoPreview = ev.target.result
        this.addPhotoBase64 = ev.target.result.split(',')[1]
      }
      reader.readAsDataURL(file)
      e.target.value = ''
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
      let base64Image = null
      if (this.addMode === 'camera') {
        const video = this.$refs.addVideo
        const canvas = this.$refs.addCanvas
        if (!video || !video.videoWidth) {
          return this.$message.warning('摄像头未就绪')
        }
        canvas.width = video.videoWidth
        canvas.height = video.videoHeight
        const ctx = canvas.getContext('2d')
        ctx.drawImage(video, 0, 0)
        base64Image = canvas.toDataURL('image/jpeg').split(',')[1]
      } else {
        if (!this.addPhotoBase64) {
          return this.$message.warning('请上传人脸照片')
        }
        base64Image = this.addPhotoBase64
      }
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
        // 拦截器已弹出后端错误消息，此处不再重复提示
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
        // 拦截器已弹出后端错误消息，此处不再重复提示
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

.list-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.list-content {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.pagination-wrapper {
  padding-top: 16px;
  display: flex;
  justify-content: center;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
  min-height: 200px;
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

.cell-title-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

::v-deep .van-cell__title {
  display: flex;
  align-items: center;
}

.cell-status {
  display: inline-flex;
  align-items: center;
  gap: 4px;

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
  margin-left: 12px;
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

.mode-tabs {
  display: flex;
  gap: 8px;
}

.mode-tab {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px 0;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  font-size: 13px;
  color: var(--dark-text-secondary);
  cursor: pointer;
  transition: all 0.2s;
}

.mode-tab:hover {
  background: rgba(255, 255, 255, 0.08);
  color: var(--dark-text);
}

.mode-tab.active {
  background: rgba(99, 102, 241, 0.1);
  border-color: var(--dark-accent-light);
  color: var(--dark-accent-light);
}

.upload-area {
  width: 100%;
  max-width: 480px;
  margin: 0 auto;
  min-height: 200px;
  border-radius: 12px;
  border: 1px dashed rgba(255, 255, 255, 0.15);
  background: rgba(255, 255, 255, 0.02);
  cursor: pointer;
  overflow: hidden;
  transition: border-color 0.2s;
}

.upload-area:hover {
  border-color: var(--dark-accent-light);
}

.upload-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 200px;
  gap: 8px;
}

.upload-icon {
  font-size: 32px;
  color: var(--dark-text-muted);
}

.upload-text {
  font-size: 14px;
  color: var(--dark-text-secondary);
}

.upload-hint {
  font-size: 12px;
  color: var(--dark-text-muted);
}

.upload-preview-wrap {
  position: relative;
  line-height: 0;
}

.upload-preview-img {
  width: 100%;
  max-height: 300px;
  object-fit: contain;
  display: block;
}

.upload-replace {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 8px 0;
  background: rgba(0, 0, 0, 0.6);
  font-size: 12px;
  color: rgba(255, 255, 255, 0.8);
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

.el-pagination.is-background .btn-prev,
.el-pagination.is-background .btn-next,
.el-pagination.is-background .el-pager li {
  background: rgba(255, 255, 255, 0.04) !important;
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
  color: var(--dark-text-secondary) !important;
}

.el-pagination.is-background .btn-prev:hover,
.el-pagination.is-background .btn-next:hover,
.el-pagination.is-background .el-pager li:hover {
  background: rgba(255, 255, 255, 0.08) !important;
  color: var(--dark-text) !important;
}

.el-pagination.is-background .el-pager li.active {
  background: var(--dark-accent) !important;
  border-color: var(--dark-accent) !important;
  color: #fff !important;
}

.el-pagination.is-background .btn-prev:disabled,
.el-pagination.is-background .btn-next:disabled {
  background: rgba(255, 255, 255, 0.02) !important;
  color: var(--dark-text-dim) !important;
}
</style>
