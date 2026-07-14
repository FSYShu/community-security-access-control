import Vue from 'vue'
import Router from 'vue-router'
import store from '@/store'

Vue.use(Router)

const routes = [
  {
    path: '/',
    redirect: '/idle'
  },
  {
    path: '/idle',
    name: 'IdleScreen',
    component: function () { return import('@/views/idle/IdleScreen.vue') },
    meta: { title: '门禁终端' }
  },
  {
    path: '/face-pass',
    name: 'FacePass',
    component: function () { return import('@/views/face-pass/FacePass.vue') },
    meta: { title: '刷脸通行' }
  },
  {
    path: '/visitor-apply',
    name: 'VisitorApply',
    component: function () { return import('@/views/visitor-apply/VisitorApply.vue') },
    meta: { title: '访客申请' }
  },
  {
    path: '/visitor-manage',
    name: 'VisitorManage',
    component: function () { return import('@/views/visitor-manage/VisitorManage.vue') },
    meta: { title: '访客管理' }
  },
  {
    path: '/settings',
    name: 'GateSettings',
    component: function () { return import('@/views/settings/GateSettings.vue') },
    meta: { title: '门禁设置', requiresAuth: true, roles: ['admin'] }
  },
  {
    path: '/settings/login',
    name: 'SettingsLogin',
    component: function () { return import('@/views/login/index.vue') },
    meta: { title: '管理员登录' }
  }
]

const router = new Router({
  mode: 'hash',
  routes: routes
})

function isJwtExpired (token) {
  try {
    const parts = token.split('.')
    if (parts.length !== 3) return true
    const payload = JSON.parse(atob(parts[1].replace(/-/g, '+').replace(/_/g, '/')))
    if (!payload.exp) return false
    return Date.now() >= payload.exp * 1000
  } catch (e) {
    return true
  }
}

router.beforeEach(function (to, from, next) {
  document.title = to.meta.title ? to.meta.title + ' - 门禁终端' : '门禁终端'

  if (!to.meta.requiresAuth) {
    next()
    return
  }

  const token = store.getters['user/token']

  if (!token || isJwtExpired(token)) {
    store.commit('user/CLEAR_USER')
    next('/settings/login?redirect=' + to.path)
    return
  }

  if (!store.getters['user/userInfo']) {
    store.dispatch('user/getUserInfoAction').then(function () {
      checkRoles(to, next)
    }).catch(function () {
      store.commit('user/CLEAR_USER')
      next('/settings/login?redirect=' + to.path)
    })
    return
  }

  checkRoles(to, next)
})

function checkRoles (to, next) {
  const roles = to.meta.roles
  const userRoles = store.getters['user/roles'] || []
  if (roles && !roles.some(function (role) { return userRoles.includes(role) })) {
    next('/idle')
    return
  }
  next()
}

export default router
