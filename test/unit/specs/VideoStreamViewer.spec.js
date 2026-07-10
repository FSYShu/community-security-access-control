import Vue from 'vue'
import VideoStreamViewer from '@/views/video-monitor/VideoStreamViewer.vue'

describe('VideoStreamViewer.vue', () => {
  function createComponent (propsData = {}) {
    const Constructor = Vue.extend(VideoStreamViewer)
    const vm = new Constructor({ propsData }).$mount()
    return vm
  }

  it('should render empty placeholder when no stream selected', () => {
    const vm = createComponent({ streamList: [] })
    expect(vm.selectedStream).toBe('')
    expect(vm.videoFeedUrl).toBe('')
  })

  it('should compute streamOptions from streamList prop', () => {
    const streamList = [
      { channel_id: '1', channel_name: '大门摄像头' },
      { channel_id: '2', channel_name: '单元门摄像头' }
    ]
    const vm = createComponent({ streamList })
    expect(vm.streamOptions).toEqual([
      { text: '大门摄像头', value: '1' },
      { text: '单元门摄像头', value: '2' }
    ])
  })

  it('should auto-select first stream when streamList is provided', () => {
    const streamList = [
      { channel_id: 'cam01', channel_name: '通道1' },
      { channel_id: 'cam02', channel_name: '通道2' }
    ]
    const vm = createComponent({ streamList })
    expect(vm.selectedStream).toBe('cam01')
  })

  it('should compute correct videoFeedUrl based on selectedStream', () => {
    const streamList = [
      { channel_id: 'test_cam', channel_name: '测试' }
    ]
    const vm = createComponent({ streamList })
    expect(vm.videoFeedUrl).toBe('/api/v1/video-monitor/video_feed/test_cam')
  })

  it('should return empty string for videoFeedUrl when no stream selected', () => {
    const vm = createComponent({ streamList: [] })
    expect(vm.videoFeedUrl).toBe('')
  })

  it('should fallback to id when channel_id is missing', () => {
    const streamList = [
      { id: 5, channel_name: '通道5' }
    ]
    const vm = createComponent({ streamList })
    expect(vm.streamOptions[0].value).toBe('5')
    expect(vm.selectedStream).toBe('5')
  })

  it('should fallback to id when channel_name is missing', () => {
    const streamList = [
      { channel_id: 'abc' }
    ]
    const vm = createComponent({ streamList })
    expect(vm.streamOptions[0].text).toBe('abc')
  })
})
