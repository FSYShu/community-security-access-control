<template>
  <div class="login-page">
    <div class="login-bg">
      <div class="bg-orb bg-orb-1"></div>
      <div class="bg-orb bg-orb-2"></div>
    </div>
    <div class="login-card">
      <div class="login-brand">
        <div class="brand-icon">
          <i class="el-icon-lock" style="font-size:28px;color:var(--dark-accent-light)"></i>
        </div>
        <h2 class="login-title">社区安防门禁系统</h2>
        <p class="login-subtitle">Community Security Access Control</p>
      </div>
      <van-form @submit="onSubmit" class="login-form">
        <van-field
          v-model="form.username"
          name="username"
          placeholder="请输入用户名"
          :rules="[{ required: true, message: '请输入用户名' }]"
        >
          <template #left-icon>
            <i class="el-icon-user" :style="{ color: 'var(--dark-text-secondary)' }"></i>
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
            <i class="el-icon-lock" :style="{ color: 'var(--dark-text-secondary)' }"></i>
          </template>
        </van-field>
        <div class="login-action">
          <van-button round block type="primary" native-type="submit">登 录</van-button>
        </div>
      </van-form>
    </div>
  </div>
</template>

<script>
import { mapActions } from 'vuex'

export default {
  name: 'LoginPage',
  data () {
    return {
      form: {
        username: '',
        password: ''
      }
    }
  },
  methods: {
    ...mapActions('user', ['loginAction']),
    async onSubmit () {
      try {
        await this.loginAction(this.form)
        const redirect = this.$route.query.redirect || '/dashboard'
        this.$router.push(redirect)
      } catch (error) {
        // 错误已在拦截器中处理
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
  background: var(--dark-bg);
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
  background: var(--dark-accent);
  top: -150px;
  right: -100px;
  animation: float-orb 20s ease-in-out infinite;
}

.bg-orb-2 {
  width: 400px;
  height: 400px;
  background: var(--dark-purple);
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
  background: var(--dark-card);
  border-radius: 20px;
  border: 1px solid var(--dark-border);
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
  color: var(--dark-text);
  margin: 0;
}

.login-subtitle {
  font-size: 12px;
  color: var(--dark-text-muted);
  margin-top: 6px;
  letter-spacing: 0.05em;
}

.login-form .van-field {
  background: rgba(255, 255, 255, 0.04) !important;
  border-radius: 12px;
  margin-bottom: 12px;
  border: 1px solid var(--dark-border);
}

.login-action {
  margin-top: 24px;
}
</style>
