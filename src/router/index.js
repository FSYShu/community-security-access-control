/**
 * 路由配置
 * 按角色权限划分路由模块
 */
import Vue from 'vue'
import Router from 'vue-router'
import store from '@/store'

Vue.use(Router)

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/login/index.vue'),
    meta: { title: '登录', requiresAuth: false }
  },
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/views/dashboard/index.vue'),
    meta: { title: '安防总览', requiresAuth: true }
  },
  // 人脸管理模块
  {
    path: '/face-management',
    name: 'FaceManagement',
    component: () => import('@/views/face-management/index.vue'),
    meta: { title: '人脸信息管理', requiresAuth: true, roles: ['admin', 'owner'] }
  },
  // 门禁权限模块
  {
    path: '/access-control',
    name: 'AccessControl',
    component: () => import('@/views/access-control/index.vue'),
    meta: { title: '门禁权限配置', requiresAuth: true, roles: ['admin'] }
  },
  // 禁区入侵检测模块
  {
    path: '/danger-zone',
    name: 'DangerZone',
    component: () => import('@/views/danger-zone/index.vue'),
    meta: { title: '禁区入侵检测', requiresAuth: true, roles: ['admin', 'guard'] }
  },
  // 实时视频监控模块
  {
    path: '/video-monitor',
    name: 'VideoMonitor',
    component: () => import('@/views/video-monitor/index.vue'),
    meta: { title: '实时视频监控', requiresAuth: true, roles: ['admin', 'guard'] }
  },
  // 告警中心模块
  {
    path: '/alarm-center',
    name: 'AlarmCenter',
    component: () => import('@/views/alarm-center/index.vue'),
    meta: { title: '告警中心', requiresAuth: true, roles: ['admin', 'guard'] }
  },
  // 物业后台管理模块
  {
    path: '/property-admin',
    name: 'PropertyAdmin',
    component: () => import('@/views/property-admin/index.vue'),
    meta: { title: '物业后台管理', requiresAuth: true, roles: ['admin'] }
  }
]

const router = new Router({
  mode: 'history',
  routes
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  // 设置页面标题
  document.title = to.meta.title ? `${to.meta.title} - 社区安防门禁系统` : '社区安防门禁系统'

  const token = store.getters['user/token']

  // 不需要认证的页面直接放行
  if (!to.meta.requiresAuth) {
    if (token && to.path === '/login') {
      next('/dashboard')
      return
    }
    next()
    return
  }

  // 需要认证但没有 token，跳转登录
  if (!token) {
    next(`/login?redirect=${to.path}`)
    return
  }

  // 获取用户信息
  if (!store.getters['user/userInfo']) {
    try {
      await store.dispatch('user/getUserInfoAction')
    } catch (error) {
      store.commit('user/CLEAR_USER')
      next(`/login?redirect=${to.path}`)
      return
    }
  }

  // 角色权限校验
  const roles = to.meta.roles
  if (roles && !roles.some(role => store.getters['user/roles'].includes(role))) {
    next('/dashboard')
    return
  }

  next()
})

export default router
