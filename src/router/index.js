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
    component: () => import('@/views/access-control/GateList.vue'),
    meta: { title: '门禁终端管理', requiresAuth: true, roles: ['admin'] }
  },
  {

    path: '/access-control/permission/:id',
    name: 'GatePermission',
    component: () => import('@/views/access-control/GatePermission.vue'),
    meta: { title: '门禁权限配置', requiresAuth: true, roles: ['admin'] }
  },

  // 实时视频监控模块
  {
    path: '/video-monitor',
    name: 'VideoMonitor',
    component: () => import('@/views/video-monitor/index.vue'),
    meta: { title: '实时视频监控', requiresAuth: true, roles: ['admin', 'guard'] }
  },
  {
    path: '/video-monitor/playback',
    name: 'VideoPlayback',
    component: () => import('@/views/video-monitor/VideoPlayback.vue'),
    meta: { title: '历史视频回放', requiresAuth: true, roles: ['admin', 'guard'] }
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
  },
  {
    path: '/property-admin/pass-logs',
    name: 'PassLogList',
    component: () => import('@/views/property-admin/PassLogList.vue'),
    meta: { title: '历史通行日志', requiresAuth: true, roles: ['admin', 'guard'] }
  },

  // 用户权限管理模块
  {
    path: '/user-management',
    name: 'UserManagement',
    component: () => import('@/views/user-management/index.vue'),
    meta: { title: '用户权限管理', requiresAuth: true, roles: ['admin'] }
  },
  // 安防监控日报模块
  {
    path: '/report',
    name: 'ReportList',
    component: () => import('@/views/report/ReportList.vue'),
    meta: { title: '安防监控日报', requiresAuth: true, roles: ['admin'] }
  },
  {
    path: '/report/detail/:id',
    name: 'ReportDetail',
    component: () => import('@/views/report/ReportDetail.vue'),
    meta: { title: '日报详情', requiresAuth: true, roles: ['admin'] }
  }
]

const originalPush = Router.prototype.push
const originalReplace = Router.prototype.replace
Router.prototype.push = function push (location) {
  return originalPush.call(this, location).catch(function (err) {
    if (err.name !== 'NavigationDuplicated') return Promise.reject(err)
  })
}
Router.prototype.replace = function replace (location) {
  return originalReplace.call(this, location).catch(function (err) {
    if (err.name !== 'NavigationDuplicated') return Promise.reject(err)
  })
}

const router = new Router({
  mode: 'history',
  routes
})

/**
 * 解析 JWT 判断是否过期
 */
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

// 路由守卫
router.beforeEach(async (to, from, next) => {
  document.title = to.meta.title ? to.meta.title + ' - 社区安防门禁系统' : '社区安防门禁系统'

  const token = store.getters['user/token']

  // 不需要认证的页面直接放行
  if (!to.meta.requiresAuth) {
    if (token && !isJwtExpired(token) && to.path === '/login') {
      next('/dashboard')
      return
    }
    next()
    return
  }

  // 需要认证但没有 token 或 token 已过期
  if (!token || isJwtExpired(token)) {
    store.commit('user/CLEAR_USER')
    next('/login?redirect=' + to.path)
    return
  }

  // 获取用户信息
  if (!store.getters['user/userInfo']) {
    try {
      await store.dispatch('user/getUserInfoAction')
    } catch (error) {
      store.commit('user/CLEAR_USER')
      next('/login?redirect=' + to.path)
      return
    }
  }

  // 角色权限校验
  const roles = to.meta.roles
  const userRoles = store.getters['user/roles'] || []
  if (roles && !roles.some(function (role) { return userRoles.includes(role) })) {
    next('/dashboard')
    return
  }

  next()
})

export default router
