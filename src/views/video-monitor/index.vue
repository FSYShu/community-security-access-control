<template>
  <app-layout page-title="实时视频监控">
    <div class="layout-controls">
      <van-button
        :type="layoutMode === 'single' ? 'primary' : 'default'"
        size="small"
        @click="layoutMode = 'single'"
      >单路</van-button>
      <van-button
        :type="layoutMode === 'grid' ? 'primary' : 'default'"
        size="small"
        @click="layoutMode = 'grid'"
      >四路</van-button>
      <van-button
        size="small"
        icon="video-o"
        type="info"
        plain
        class="playback-btn"
        @click="$router.push('/video-monitor/playback')"
      >历史回放</van-button>
    </div>

    <div v-if="layoutMode === 'single'" class="single-layout">
      <video-stream-viewer :gate-list="gateList" />
    </div>

    <div v-else class="grid-layout">
      <div
        v-for="index in 4"
        :key="index"
        class="grid-item"
      >
        <video-stream-viewer :gate-list="gateList" />
      </div>
    </div>
  </app-layout>
</template>

<script>
import VideoStreamViewer from './VideoStreamViewer.vue'
import { getGatesWithStream } from '@/api/videoMonitor'

export default {
  name: 'VideoMonitorPage',
  components: {
    VideoStreamViewer
  },
  data () {
    return {
      layoutMode: 'single',
      gateList: []
    }
  },
  created () {
    this.fetchGateList()
  },
  methods: {
    async fetchGateList () {
      try {
        const res = await getGatesWithStream()
        if (res.code === 0 && res.data) {
          this.gateList = res.data || []
        }
      } catch (error) {
        console.error('Failed to fetch gate list:', error)
        this.gateList = []
      }
    }
  }
}
</script>

<style scoped>
.layout-controls {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
  align-items: center;
}
.playback-btn {
  margin-left: auto;
}
.grid-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}
.grid-item {
  min-height: 180px;
}
</style>
