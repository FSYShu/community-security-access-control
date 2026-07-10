/**
 * 应用入口文件
 * 初始化 Vue 实例，注册全局插件
 */
import Vue from 'vue'
import App from './App'
import router from './router'
import store from './store'

// 注册 Vant 组件
import Vant from 'vant'
import 'vant/lib/index.css'
import ElementUI from 'element-ui'
import 'element-ui/lib/theme-chalk/index.css'
import './styles/dark-theme.css'

Vue.use(Vant)
Vue.use(ElementUI)
Vue.component('AppLayout', () => import('@/components/AppLayout.vue'))

Vue.config.productionTip = false

/* eslint-disable no-new */
new Vue({
  el: '#app',
  router,
  store,
  components: { App },
  template: '<App/>'
})
