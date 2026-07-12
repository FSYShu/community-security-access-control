<template>
  <div class="gate-page login-page">
    <div class="login-content">
      <div class="login-title">管理员登录</div>
      <p class="login-subtitle">登录后可配置门禁终端设置</p>
      <div class="gate-card">
        <van-field v-model="form.username" label="账号" placeholder="请输入管理员账号" clearable />
        <van-field v-model="form.password" label="密码" placeholder="请输入密码" type="password" clearable />
      </div>
      <button class="gate-btn gate-btn-primary" style="margin-top:20px;" :disabled="!canLogin || logging" @click="doLogin">
        <van-loading v-if="logging" size="20" color="#fff" />
        <span v-else>登录</span>
      </button>
      <button class="gate-btn gate-btn-outline" style="margin-top:12px;" @click="goBack">返回</button>
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
  computed: {
    canLogin () {
      return this.form.username && this.form.password
    }
  },
  mounted () {
    this.$store.commit('user/CLEAR_USER')
  },
  methods: {
    async doLogin () {
      this.logging = true
      try {
        await this.$store.dispatch('user/loginAction', this.form)
        await this.$store.dispatch('user/getUserInfoAction')
        var redirect = this.$route.query.redirect || '/settings'
        this.$router.push(redirect)
      } catch (err) {
        // error handled by interceptor
      } finally {
        this.logging = false
      }
    },
    goBack () {
      this.$router.go(-1)
    }
  }
}
</script>

<style scoped>
.login-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
}
.login-content {
  width: 100%;
  max-width: 400px;
  padding: 24px;
}
.login-title {
  font-size: 24px;
  font-weight: 700;
  color: var(--gate-text);
  text-align: center;
  margin-bottom: 8px;
}
.login-subtitle {
  text-align: center;
  color: var(--gate-text-muted);
  font-size: 14px;
  margin-bottom: 24px;
}
</style>
