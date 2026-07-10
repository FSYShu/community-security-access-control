<template>
  <app-layout page-title="实时视频监控" :no-scroll="true">
    <div class="monitor-page">
    <div class="monitor-header">
      <div class="monitor-tabs">
        <div
          class="monitor-tab"
          :class="{ 'is-active': layoutMode === 'single' }"
          @click="layoutMode = 'single'"
        >单路</div>
        <div
          class="monitor-tab"
          :class="{ 'is-active': layoutMode === 'grid' }"
          @click="layoutMode = 'grid'"
        >六路</div>
      </div>
      <div class="header-controls">
        <button
          class="detect-btn"
          :class="{ 'is-on': faceDetectionEnabled, 'is-off': !faceDetectionEnabled }"
          @click="toggleFaceDetection"
        >
          <i class="el-icon-view"></i>
          <span>人脸检测</span>
          <i :class="faceDetectionEnabled ? 'el-icon-check' : 'el-icon-close'" class="detect-indicator"></i>
        </button>
        <button class="refresh-btn" :class="{ 'is-loading': refreshing }" @click="handleRefresh">
          <i class="el-icon-refresh"></i>
          <span>刷新</span>
        </button>

      </div>
    </div>

    <div v-if="layoutMode === 'single'" class="single-layout">
      <video-stream-viewer
        ref="singleViewer"
        :gate-list="gateList"
        :face-detection-enabled="faceDetectionEnabled"
      />
    </div>

    <div v-else class="grid-layout">
      <div
        v-for="index in 6"
        :key="index"
        class="grid-item"
      >
        <video-stream-viewer
          :ref="'gridViewer' + index"
          :gate-list="gateList"
          :face-detection-enabled="faceDetectionEnabled"
        />
      </div>
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
      gateList: [],
      faceDetectionEnabled: false,
      refreshing: false
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
    },
    toggleFaceDetection () {
      this.faceDetectionEnabled = !this.faceDetectionEnabled
      this.$toast({
        message: this.faceDetectionEnabled ? '人脸检测已开启：绿色框=已注册人员，红色框=陌生人' : '人脸检测已关闭',
        position: 'top',
        duration: 2500
      })
    },
    handleRefresh () {
      this.refreshing = true
      if (this.layoutMode === 'single' && this.$refs.singleViewer) {
        this.$refs.singleViewer.manualRefresh()
      } else {
        for (let i = 1; i <= 6; i++) {
          const ref = this.$refs['gridViewer' + i]
          if (ref && ref[0]) {
            ref[0].manualRefresh()
          }
        }
      }
      const self = this
      setTimeout(function () {
        self.refreshing = false
      }, 1500)
    }
  }
}
</script>

<style scoped>
.monitor-page {
  height: calc(100vh - 120px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.monitor-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 10px;
}

.monitor-tabs {
  display: flex;
  align-items: center;
  gap: 0;
  background: rgba(255, 255, 255, 0.04);
  border-radius: 8px;
  padding: 3px;
  border: 1px solid var(--dark-border-field);
}

.monitor-tab {
  padding: 7px 20px;
  font-size: 13px;
  font-weight: 500;
  color: var(--dark-text-secondary);
  cursor: pointer;
  border-radius: 6px;
  transition: background 0.2s, color 0.2s;
  text-align: center;
  user-select: none;
}

.monitor-tab:hover {
  color: var(--dark-text);
}

.monitor-tab.is-active {
  background: var(--dark-accent);
  color: #fff;
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.3);
}

.header-controls {
  display: flex;
  align-items: center;
  gap: 10px;
}

.detect-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 7px 12px;
  background: rgba(255, 255, 255, 0.04);
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  transition: background 0.2s, color 0.2s, border-color 0.2s;
}

.detect-btn.is-on {
  border: 1px solid var(--dark-success-green);
  color: var(--dark-success-green);
  background: rgba(16, 185, 129, 0.08);
}

.detect-btn.is-off {
  border: 1px solid #ef4444;
  color: #ef4444;
  background: rgba(239, 68, 68, 0.08);
}

.detect-btn:hover {
  background: rgba(255, 255, 255, 0.08);
}

.detect-indicator {
  margin-left: 4px;
  font-size: 14px;
}

.detect-btn i:first-child {
  font-size: 14px;
}

.refresh-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 7px 12px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--dark-border-field);
  border-radius: 6px;
  color: var(--dark-text-secondary);
  font-size: 13px;
  cursor: pointer;
  transition: background 0.2s, color 0.2s;
}

.refresh-btn:hover {
  background: rgba(255, 255, 255, 0.08);
  color: var(--dark-text);
}

.refresh-btn.is-loading {
  opacity: 0.6;
  pointer-events: none;
}

.refresh-btn i {
  font-size: 14px;
}

.grid-layout {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  grid-template-rows: 1fr 1fr;
  gap: 8px;
  flex: 1;
  overflow: hidden;
}

.grid-item {
  background: var(--dark-card);
  border-radius: 8px;
  border: 1px solid var(--dark-border);
  overflow: hidden;
  min-height: 0;
}

.single-layout {
  background: var(--dark-card);
  border-radius: 8px;
  border: 1px solid var(--dark-border);
  overflow: hidden;
  flex: 1;
}
</style>
