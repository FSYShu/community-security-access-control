<template>
  <div class="login-page">
    <van-form @submit="onSubmit" class="login-form">
      <h2 class="login-title">社区安防门禁系统</h2>
      <van-field
        v-model="form.username"
        name="username"
        label="用户名"
        placeholder="请输入用户名"
        :rules="[{ required: true, message: '请输入用户名' }]"
      />
      <van-field
        v-model="form.password"
        type="password"
        name="password"
        label="密码"
        placeholder="请输入密码"
        :rules="[{ required: true, message: '请输入密码' }]"
      />
      <div style="margin: 16px;">
        <van-button round block type="primary" native-type="submit">登录</van-button>
      </div>
    </van-form>
  </div>
</template>

<script>
import { mapActions } from 'vuex'

export default {
  name: 'LoginPage',
  data() {
    return {
      form: {
        username: '',
        password: ''
      }
    }
  },
  methods: {
    ...mapActions('user', ['loginAction']),
    async onSubmit() {
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
.login-page {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #1a73e8, #0d47a1);
}
.login-form {
  width: 90%;
  max-width: 400px;
  padding: 32px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}
.login-title {
  text-align: center;
  margin-bottom: 24px;
  color: #1a73e8;
  font-size: 22px;
}
</style>