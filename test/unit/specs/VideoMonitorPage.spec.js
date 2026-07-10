import Vue from 'vue'
import VideoMonitorPage from '@/views/video-monitor/index.vue'

describe('VideoMonitorPage.vue', () => {
  function createComponent () {
    const Constructor = Vue.extend(VideoMonitorPage)
    const vm = new Constructor()
    return vm
  }

  it('should have default layoutMode as single', () => {
    const vm = createComponent()
    expect(vm.layoutMode).toBe('single')
  })

  it('should have empty streamList by default', () => {
    const vm = createComponent()
    expect(vm.streamList).toEqual([])
  })

  it('should contain VideoStreamViewer component', () => {
    const vm = createComponent()
    expect(vm.$options.components.VideoStreamViewer).toBeDefined()
  })
})
