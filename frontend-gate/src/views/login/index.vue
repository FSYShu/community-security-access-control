<template>
  <div class="gate-page login-page">
    <div class="login-bg">
      <div class="bg-orb bg-orb-1"></div>
      <div class="bg-orb bg-orb-2"></div>
    </div>
    <div class="login-card">
      <div class="login-brand">
        <div class="brand-icon">
          <i class="el-icon-lock" style="font-size:28px;color:var(--gate-accent-light)"></i>
        </div>
        <h2 class="login-title">社区安防门禁系统</h2>
        <p class="login-subtitle">管理员登录 · 终端配置</p>
      </div>
      <van-form @submit="doLogin" class="login-form">
        <van-field
          v-model="form.username"
          name="username"
          placeholder="请输入管理员账号"
          :rules="[{ required: true, message: '请输入管理员账号' }]"
        >
          <template #left-icon>
            <i class="el-icon-user" style="color:var(--gate-text-secondary)"></i>
          </template>
        </van-field>
        <van-field
          v-model="form.password"
          type="password"
          name="password"
          placeholder="请输入密码"
          :rules="[{ required: true, message: '请输入密码' }]"
        >
          <template #left-icon>
            <i class="el-icon-lock" style="color:var(--gate-text-secondary)"></i>
          </template>
        </van-field>
        <div class="login-action">
          <button class="login-btn" type="submit" :disabled="logging">
            <van-loading v-if="logging" size="20" color="#fff" />
            <span v-else>登 录</span>
          </button>
          <button class="login-btn login-btn-outline" type="button" @click="goBack">返回</button>
        </div>
      </van-form>
    </div>
  </div>
</template>

<script>
export default {
  name: 'GateLoginPage',
  data () {
    return {
      form: { username: '', password: '' },
      logging: false
    }
  },
  mounted () {
    this.$store.commit('user/CLEAR_USER')
  },
  methods: {
    goBack () {
      this.$router.go(-1)
    },
    async doLogin () {
      this.logging = true
      try {
        await this.$store.dispatch('user/loginAction', this.form)
        await this.$store.dispatch('user/getUserInfoAction')
        var redirect = this.$route.query.redirect || '/settings'
        this.$router.push(redirect)
      } catch (err) {
        this.form.username = ''
        this.form.password = ''
      } finally {
        this.logging = false
      }
    }
  }
}
</script>

<style scoped>
@keyframes float-orb {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(30px, -20px) scale(1.05); }
  66% { transform: translate(-20px, 15px) scale(0.95); }
}

.login-page {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: var(--gate-bg);
  position: relative;
  overflow: hidden;
}

.login-bg {
  position: fixed;
  inset: 0;
  pointer-events: none;
}

.bg-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(120px);
  opacity: 0.15;
}

.bg-orb-1 {
  width: 500px;
  height: 500px;
  background: var(--gate-accent);
  top: -150px;
  right: -100px;
  animation: float-orb 20s ease-in-out infinite;
}

.bg-orb-2 {
  width: 400px;
  height: 400px;
  background: var(--gate-purple);
  bottom: -100px;
  left: -80px;
  animation: float-orb 25s ease-in-out infinite reverse;
}

.login-card {
  position: relative;
  z-index: 1;
  width: 90%;
  max-width: 420px;
  padding: 40px 32px;
  background: var(--gate-bg-card);
  border-radius: 20px;
  border: 1px solid var(--gate-border);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
}

.login-brand {
  text-align: center;
  margin-bottom: 32px;
}

.brand-icon {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  background: rgba(99, 102, 241, 0.15);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 16px;
}

.login-title {
  font-size: 22px;
  font-weight: 600;
  letter-spacing: -0.02em;
  color: var(--gate-text);
  margin: 0;
}

.login-subtitle {
  font-size: 12px;
  color: var(--gate-text-muted);
  margin-top: 6px;
  letter-spacing: 0.05em;
}

.login-form .van-field {
  background: var(--gate-border-light) !important;
  border-radius: 12px;
  margin-bottom: 12px;
  border: 1px solid var(--gate-border);
}

.login-action {
  margin-top: 24px;
}

.login-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  padding: 12px 20px;
  background: var(--gate-accent);
  color: #fff;
  border: none;
  border-radius: 12px;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
  letter-spacing: 0.1em;
}

.login-btn:hover {
  background: var(--gate-accent-light);
}

.login-btn:active {
  opacity: 0.9;
}

.login-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.login-btn-outline {
  margin-top: 12px;
  background: rgba(255, 255, 255, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: rgba(255, 255, 255, 0.9);
}

.login-btn-outline:hover {
  background: rgba(255, 255, 255, 0.18);
}
</style>
