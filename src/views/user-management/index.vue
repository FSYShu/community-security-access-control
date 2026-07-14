<template>
  <app-layout page-title="用户权限管理" :no-scroll="true">
    <div class="dark-card">
      <div class="filter-row">
        <div class="search-box">
          <i class="el-icon-search"></i>
          <input v-model="keyword" placeholder="搜索用户名或姓名" class="search-input" @input="debouncedSearch" />
          <i v-if="keyword" class="el-icon-circle-close search-clear" @click="keyword = ''; fetchUsers()"></i>
        </div>
        <div class="filter-select" :class="{ 'is-open': showRoleDropdown }">
          <div class="select-trigger" @click="showRoleDropdown = !showRoleDropdown">
            <span class="select-value">{{ roleFilterLabel || '角色筛选' }}</span>
            <i class="el-icon-arrow-down select-arrow" :class="{ 'is-reverse': showRoleDropdown }"></i>
          </div>
          <transition name="dropdown">
            <div v-if="showRoleDropdown" class="select-dropdown">
              <div class="select-option" :class="{ 'is-active': !roleFilter }" @click="roleFilter = ''; showRoleDropdown = false; fetchUsers()">全部</div>
              <div class="select-option" :class="{ 'is-active': roleFilter === 'admin' }" @click="roleFilter = 'admin'; showRoleDropdown = false; fetchUsers()">管理员</div>
              <div class="select-option" :class="{ 'is-active': roleFilter === 'guard' }" @click="roleFilter = 'guard'; showRoleDropdown = false; fetchUsers()">安保人员</div>
            </div>
          </transition>
        </div>
        <div class="filter-select" :class="{ 'is-open': showStatusDropdown }">
          <div class="select-trigger" @click="showStatusDropdown = !showStatusDropdown">
            <span class="select-value">{{ statusFilterLabel || '状态筛选' }}</span>
            <i class="el-icon-arrow-down select-arrow" :class="{ 'is-reverse': showStatusDropdown }"></i>
          </div>
          <transition name="dropdown">
            <div v-if="showStatusDropdown" class="select-dropdown">
              <div class="select-option" :class="{ 'is-active': !statusFilter }" @click="statusFilter = ''; showStatusDropdown = false; fetchUsers()">全部</div>
              <div class="select-option" :class="{ 'is-active': statusFilter === 'active' }" @click="statusFilter = 'active'; showStatusDropdown = false; fetchUsers()">正常</div>
              <div class="select-option" :class="{ 'is-active': statusFilter === 'disabled' }" @click="statusFilter = 'disabled'; showStatusDropdown = false; fetchUsers()">已禁用</div>
            </div>
          </transition>
        </div>
        <div class="filter-spacer"></div>
        <button class="perm-btn" @click="showPermInfo = true">
          <i class="el-icon-info"></i>
          <span>权限说明</span>
        </button>
        <button class="add-btn" @click="openAddDialog">
          <i class="el-icon-plus"></i>
          <span>新增用户</span>
        </button>
      </div>
    </div>

    <div class="dark-card list-section" ref="listSection">
      <div v-if="!perPageReady" class="probe-loading"><i class="el-icon-loading"></i><span>加载中...</span></div>
      <div class="list-content" ref="listContent" :style="{ visibility: perPageReady ? '' : 'hidden' }">
        <van-cell v-for="user in userList" :key="user.id">
          <template #title>
            <div class="cell-title-row">
              <span class="cell-status">
                <span class="status-dot" :class="user.status === 'active' ? 'dot-active' : 'dot-disabled'"></span>
                <span class="status-label">{{ user.status === 'active' ? '正常' : '已禁用' }}</span>
              </span>
              <span class="cell-name">{{ user.username }}</span>
              <span class="type-tag" :class="user.role === 'admin' ? 'tag-admin' : 'tag-guard'">{{ roleText(user.role) }}</span>
            </div>
          </template>
          <template #right-icon>
            <button v-if="user.status === 'disabled'" class="enable-btn" @click.stop="onToggleStatus(user)">
              <i class="el-icon-circle-check"></i>
              <span>启用</span>
            </button>
            <button v-if="user.status === 'active'" class="disable-btn" @click.stop="onToggleStatus(user)">
              <i class="el-icon-circle-close"></i>
              <span>禁用</span>
            </button>
            <button class="edit-btn" @click.stop="openEditDialog(user)">
              <i class="el-icon-edit"></i>
              <span>修改密码</span>
            </button>
            <button class="delete-btn" @click.stop="onDelete(user)">
              <i class="el-icon-delete"></i>
              <span>删除</span>
            </button>
          </template>
        </van-cell>
        <div v-if="userList.length === 0 && !loading" class="empty-state">
          <i class="el-icon-user" style="font-size:48px;color:var(--dark-text-muted)"></i>
          <p style="color:var(--dark-text-muted);margin-top:12px">暂无用户数据</p>
        </div>
      </div>
      <div class="pagination-wrapper" v-show="perPageReady">
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

    <el-dialog :visible.sync="showDialog" :title="dialogTitle" width="480px" :close-on-click-modal="false" append-to-body custom-class="dark-dialog" @close="resetForm">
      <div class="form-grid">
        <template v-if="!isEdit">
          <div class="form-item">
            <label class="form-label">角色 <span class="form-required">*</span></label>
            <div class="filter-select" :class="{ 'is-open': showFormRoleDropdown }">
              <div class="select-trigger" @click="showFormRoleDropdown = !showFormRoleDropdown">
                <span class="select-value">{{ formRoleLabel || '请选择角色' }}</span>
                <i class="el-icon-arrow-down select-arrow" :class="{ 'is-reverse': showFormRoleDropdown }"></i>
              </div>
              <transition name="dropdown">
                <div v-if="showFormRoleDropdown" class="select-dropdown">
                  <div class="select-option" :class="{ 'is-active': form.role === 'admin' }" @click="form.role = 'admin'; showFormRoleDropdown = false">管理员</div>
                  <div class="select-option" :class="{ 'is-active': form.role === 'guard' }" @click="form.role = 'guard'; showFormRoleDropdown = false">安保人员</div>
                </div>
              </transition>
            </div>
          </div>
          <div class="form-item">
            <label class="form-label">用户名 <span class="form-required">*</span></label>
            <input v-model="form.username" class="form-input" placeholder="请输入用户名" />
          </div>
          <div class="form-item">
            <label class="form-label">密码 <span class="form-required">*</span></label>
            <input v-model="form.password" type="password" class="form-input" placeholder="请输入密码" />
          </div>
        </template>
        <template v-if="isEdit">
          <div class="form-item">
            <label class="form-label">原密码 <span class="form-required">*</span></label>
            <input v-model="form.old_password" type="password" class="form-input" placeholder="请输入原密码" />
          </div>
          <div class="form-item">
            <label class="form-label">新密码 <span class="form-required">*</span></label>
            <input v-model="form.password" type="password" class="form-input" placeholder="请输入新密码" />
          </div>
        </template>
      </div>
      <div class="form-footer">
        <button class="form-btn form-btn-cancel" @click="showDialog = false">取消</button>
        <button class="form-btn form-btn-primary" @click="onSubmit">
          <i v-if="submitLoading" class="el-icon-loading"></i>
          确认
        </button>
      </div>
    </el-dialog>

    <el-dialog :visible.sync="showPermInfo" title="权限说明" width="520px" append-to-body custom-class="dark-dialog">
      <div class="perm-info">
        <div class="perm-role-block">
          <div class="perm-role-header">
            <span class="type-tag tag-admin">管理员</span>
            <span class="perm-role-name">admin</span>
          </div>
          <div class="perm-list">
            <div class="perm-item" v-for="p in adminPerms" :key="p">
              <i class="el-icon-check"></i>
              <span>{{ p }}</span>
            </div>
          </div>
        </div>
        <div class="perm-role-block">
          <div class="perm-role-header">
            <span class="type-tag tag-guard">安保人员</span>
            <span class="perm-role-name">guard</span>
          </div>
          <div class="perm-list">
            <div class="perm-item" v-for="p in guardPerms" :key="p">
              <i class="el-icon-check"></i>
              <span>{{ p }}</span>
            </div>
          </div>
        </div>
      </div>
    </el-dialog>
  </app-layout>
</template>

<script>
import { getUserList, registerUser, updateUser, deleteUser } from '@/api/auth'

export default {
  name: 'UserManagementPage',
  data () {
    return {
      userList: [],
      loading: false,
      page: 1,
      perPage: 10,
      total: 0,
      keyword: '',
      roleFilter: '',
      statusFilter: '',
      showRoleDropdown: false,
      showStatusDropdown: false,
      showDialog: false,
      isEdit: false,
      editId: null,
      submitLoading: false,
      showFormRoleDropdown: false,
      form: { username: '', role: 'guard', password: '', status: 'active' },
      showPermInfo: false,
      perPageReady: false,
      searchTimer: null,
      adminPerms: [
        '用户权限管理（新增/编辑/删除用户）',
        '门禁终端管理（新增/编辑/删除/权限配置）',
        '人脸信息管理',
        '物业后台管理',
        '安防监控日报（生成/删除）',
        '告警处置与导出',
        '视频监控与回放',
        '审计日志查看',
        '通行日志查看'
      ],
      guardPerms: [
        '告警处置与导出',
        '视频监控与回放',
        '通行日志查看'
      ]
    }
  },
  computed: {
    dialogTitle () {
      return this.isEdit ? '修改密码' : '新增用户'
    },
    formRoleLabel () {
      const map = { admin: '管理员', guard: '安保人员' }
      return map[this.form.role] || ''
    },
    roleFilterLabel () {
      const map = { admin: '管理员', guard: '安保人员' }
      return map[this.roleFilter] || ''
    },
    statusFilterLabel () {
      const map = { active: '正常', disabled: '已禁用' }
      return map[this.statusFilter] || ''
    }
  },
  mounted () {
    document.addEventListener('click', this.closeDropdowns)
    this.fetchUsers()
  },
  beforeDestroy () {
    document.removeEventListener('click', this.closeDropdowns)
    if (this.searchTimer) {
      clearTimeout(this.searchTimer)
    }
  },
  methods: {
    closeDropdowns (e) {
      if (!e.target.closest('.filter-select')) {
        this.showRoleDropdown = false
        this.showStatusDropdown = false
        this.showFormRoleDropdown = false
      }
    },
    debouncedSearch () {
      if (this.searchTimer) clearTimeout(this.searchTimer)
      this.searchTimer = setTimeout(function () {
        this.page = 1
        this.fetchUsers()
      }.bind(this), 300)
    },
    fetchUsers (fallback) {
      this.loading = true
      const self = this
      const params = {
        page: this.page,
        per_page: this.perPage
      }
      if (this.keyword) params.keyword = this.keyword
      if (this.roleFilter) params.role = this.roleFilter
      if (this.statusFilter) params.status = this.statusFilter
      getUserList(params).then(function (res) {
        const data = res.data
        const items = data.items || []
        self.userList = items.filter(function (u) { return u.role === 'admin' || u.role === 'guard' })
        self.total = data.total || 0
        if (fallback && self.userList.length === 0 && self.page > 1) {
          self.page = self.page - 1
          self.fetchUsers()
          return
        }
        self.$nextTick(function () {
          self.perPageReady = true
        })
      }).catch(function () {
        self.$message.error('获取用户列表失败')
      }).finally(function () {
        self.loading = false
      })
    },
    onPageChange (val) {
      this.page = val
      this.fetchUsers()
    },
    roleText (role) {
      const map = { admin: '管理员', guard: '安保人员' }
      return map[role] || role
    },
    formatDate (dateStr) {
      if (!dateStr) return '--'
      return dateStr.substring(0, 10)
    },
    openAddDialog () {
      this.isEdit = false
      this.editId = null
      this.form = { username: '', role: 'guard', password: '' }
      this.showDialog = true
    },
    openEditDialog (user) {
      this.isEdit = true
      this.editId = user.id
      this.form = {
        old_password: '',
        password: ''
      }
      this.showDialog = true
    },
    resetForm () {
      this.form = { username: '', role: 'guard', password: '', old_password: '' }
      this.showFormRoleDropdown = false
    },
    onSubmit () {
      if (this.isEdit) {
        if (!this.form.old_password) {
          this.$message.warning('请输入原密码')
          return
        }
        if (!this.form.password) {
          this.$message.warning('请输入新密码')
          return
        }
      } else {
        if (!this.form.username) {
          this.$message.warning('请输入用户名')
          return
        }
        if (!this.form.role) {
          this.$message.warning('请选择角色')
          return
        }
        if (!this.form.password) {
          this.$message.warning('请输入密码')
          return
        }
      }
      this.submitLoading = true
      if (this.isEdit) {
        const editPayload = {
          old_password: this.form.old_password,
          password: this.form.password
        }
        updateUser(this.editId, editPayload).then(function () {
          this.$message.success('更新成功')
          this.showDialog = false
          this.fetchUsers()
        }.bind(this)).catch(function (err) {
          this.$message.error((err.response && err.response.data && err.response.data.message) || '更新失败')
        }.bind(this)).finally(function () {
          this.submitLoading = false
        }.bind(this))
      } else {
        const addPayload = {
          username: this.form.username,
          role: this.form.role,
          password: this.form.password
        }
        registerUser(addPayload).then(function () {
          this.$message.success('新增成功')
          this.showDialog = false
          this.fetchUsers()
        }.bind(this)).catch(function (err) {
          this.$message.error((err.response && err.response.data && err.response.data.message) || '新增失败')
        }.bind(this)).finally(function () {
          this.submitLoading = false
        }.bind(this))
      }
    },
    onDelete (user) {
      this.$confirm('确定要删除用户「' + user.username + '」吗？', '删除确认', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        customClass: 'dark-dialog'
      }).then(function () {
        deleteUser(user.id).then(function () {
          this.$message.success('删除成功')
          this.fetchUsers(true)
        }.bind(this)).catch(function (err) {
          this.$message.error((err.response && err.response.data && err.response.data.message) || '删除失败')
        }.bind(this))
      }.bind(this)).catch(function () {})
    },
    onToggleStatus (user) {
      const newStatus = user.status === 'active' ? 'disabled' : 'active'
      const label = newStatus === 'active' ? '启用' : '禁用'
      this.$confirm('确定要' + label + '用户「' + user.username + '」吗？', label + '确认', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        customClass: 'dark-dialog'
      }).then(function () {
        updateUser(user.id, { status: newStatus }).then(function () {
          this.$message.success(label + '成功')
          this.fetchUsers()
        }.bind(this)).catch(function (err) {
          this.$message.error((err.response && err.response.data && err.response.data.message) || label + '失败')
        }.bind(this))
      }.bind(this)).catch(function () {})
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
  gap: 12px;
  flex-wrap: wrap;
}

.search-box {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 12px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--dark-border-field);
  border-radius: 8px;
  height: 36px;
  min-width: 180px;
  transition: border-color 0.2s;
}

.search-box:focus-within {
  border-color: var(--dark-accent-light);
}

.search-box i {
  font-size: 14px;
  color: var(--dark-text-secondary);
  flex-shrink: 0;
}

.search-input {
  flex: 1;
  background: none;
  border: none;
  outline: none;
  color: var(--dark-text);
  font-size: 13px;
  min-width: 0;
}

.search-input::placeholder {
  color: var(--dark-text-secondary);
}

.search-clear {
  cursor: pointer;
  font-size: 14px !important;
}

.search-clear:hover {
  color: var(--dark-text) !important;
}

.filter-select {
  position: relative;
  min-width: 140px;
}

.filter-select .select-trigger {
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

.filter-select .select-dropdown {
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

.filter-spacer {
  flex: 1;
}

.perm-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 8px 16px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--dark-border-field);
  border-radius: 8px;
  color: var(--dark-text-secondary);
  font-size: 13px;
  cursor: pointer;
  transition: background 0.2s, color 0.2s;
}

.perm-btn:hover {
  background: rgba(255, 255, 255, 0.08);
  color: var(--dark-text);
}

.add-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 8px 16px;
  background: var(--dark-accent);
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 13px;
  cursor: pointer;
  transition: background 0.2s;
}

.add-btn:hover {
  background: var(--dark-accent-light);
}

.list-section {
  position: relative;
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.probe-loading {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: var(--dark-text-secondary);
  font-size: 14px;
}

.probe-loading i {
  font-size: 18px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.list-content {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
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

.dot-disabled {
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
  border: 1px solid;
}

.tag-admin {
  color: var(--dark-accent-light);
  border-color: rgba(99, 102, 241, 0.3);
  background: rgba(99, 102, 241, 0.08);
}

.tag-guard {
  color: var(--dark-success-green);
  border-color: rgba(16, 185, 129, 0.3);
  background: rgba(16, 185, 129, 0.08);
}

.cell-name {
  font-size: 15px;
  color: var(--dark-text);
}

.enable-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 0 10px;
  height: 28px;
  background: rgba(16, 185, 129, 0.06);
  border: 1px solid rgba(16, 185, 129, 0.3);
  border-radius: 6px;
  color: #34d399;
  font-size: 13px;
  cursor: pointer;
  transition: background 0.2s;
  margin-left: 8px;
}

.enable-btn:hover {
  background: rgba(16, 185, 129, 0.12);
}

.disable-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 0 10px;
  height: 28px;
  background: rgba(251, 191, 36, 0.06);
  border: 1px solid rgba(251, 191, 36, 0.3);
  border-radius: 6px;
  color: #fbbf24;
  font-size: 13px;
  cursor: pointer;
  transition: background 0.2s;
  margin-left: 8px;
}

.disable-btn:hover {
  background: rgba(251, 191, 36, 0.12);
}

.edit-btn {
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
  cursor: pointer;
  transition: background 0.2s, color 0.2s, border-color 0.2s;
  margin-left: 8px;
}

.edit-btn:hover {
  background: rgba(99, 102, 241, 0.1);
  border-color: var(--dark-accent-light);
  color: var(--dark-accent-light);
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
  cursor: pointer;
  transition: background 0.2s, color 0.2s, border-color 0.2s;
  margin-left: 8px;
}

.delete-btn:hover {
  background: rgba(239, 68, 68, 0.1);
  border-color: #ef4444;
  color: #ef4444;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
  min-height: 200px;
}

.pagination-wrapper {
  padding-top: 16px;
  display: flex;
  justify-content: center;
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
  width: 100%;
  box-sizing: border-box;
}

.form-input::placeholder {
  color: var(--dark-text-muted);
}

.form-input:focus {
  border-color: var(--dark-accent-light);
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

.perm-info {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.perm-role-block {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--dark-border-light);
  border-radius: 12px;
  padding: 16px;
}

.perm-role-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.perm-role-name {
  font-size: 12px;
  color: var(--dark-text-muted);
  font-family: monospace;
}

.perm-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.perm-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--dark-text-secondary);
}

.perm-item i {
  color: var(--dark-success);
  font-size: 14px;
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

<style>
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
