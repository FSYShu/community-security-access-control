<template>
  <app-layout page-title="历史视频回放" :no-scroll="true">
    <van-loading v-if="loading" class="page-loading" size="24px" vertical>加载中...</van-loading>
    <div v-else-if="loadError" class="page-loading">
      <i class="el-icon-warning-outline" style="font-size:40px;color:var(--dark-orange)"></i>
      <p style="color:var(--dark-text-secondary);margin:12px 0 0">加载录像失败</p>
      <button class="retry-btn" @click="fetchRecordings">重试</button>
    </div>
    <van-empty v-else-if="recordings.length === 0" description="暂无历史录像" />

    <div v-else class="playback-layout">
      <div class="playback-left">
        <div class="playback-controls">
          <div class="group-mode-tabs">
            <div class="mode-tab" :class="{ 'is-active': groupMode === 'location' }" @click="groupMode = 'location'">按位置</div>
            <div class="mode-tab" :class="{ 'is-active': groupMode === 'date' }" @click="groupMode = 'date'">按日期</div>
          </div>
          <div class="filter-bar">
            <div class="custom-select" :class="{ 'is-open': showFilterDrop }">
              <div class="select-trigger" @click="showFilterDrop = !showFilterDrop">
                <span>{{ selectedFilterLabel }}</span>
                <i class="el-icon-arrow-down" :class="{ 'is-reverse': showFilterDrop }"></i>
              </div>
              <div v-if="showFilterDrop" class="select-dropdown">
                <div class="select-option" :class="{ 'is-active': selectedFilter === '' }" @click="selectFilter('')">全部</div>
                <div v-for="opt in filterOptions" :key="opt.value" class="select-option" :class="{ 'is-active': selectedFilter === opt.value }" @click="selectFilter(opt.value)">{{ opt.label }}</div>
              </div>
            </div>
          </div>
        </div>
        <div class="playback-list">
          <div v-for="(group, idx) in filteredGroups" :key="idx" class="record-group">
            <div class="group-header" @click="toggleGroup(idx)">
              <span class="group-name"><i class="el-icon-arrow-right group-arrow" :class="{ 'is-expanded': expandedGroups[idx] }"></i>{{ group.label }}</span>
              <span class="group-count">{{ group.files.length }}段录像</span>
            </div>
            <div class="card-grid" v-show="expandedGroups[idx]">
              <div
                v-for="file in group.files"
                :key="file.filename"
                class="video-card"
                :class="{ 'is-active': currentFile && currentFile.filename === file.filename }"
                @click="playRecording(file)"
              >
                <div class="card-icon">
                  <i class="el-icon-video-camera"></i>
                </div>
                <div class="card-info">
                  <span class="card-time">{{ file._gate_name }} {{ file.datetime }}</span>
                  <span class="card-meta">{{ file.duration_text }} | {{ file.file_size_text }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div class="playback-player">
        <div v-if="!currentFile" class="player-empty">
          <i class="el-icon-video-play" style="font-size:48px;color:var(--dark-text-dim)"></i>
          <p>选择录像开始播放</p>
        </div>
        <template v-else>
          <div class="player-header">{{ currentFile.datetime }}</div>
          <div class="player-wrapper">
            <video
              ref="videoPlayer"
              class="player-video"
              controls
              muted
            ></video>
          </div>
          <div v-if="playerError" class="player-error">
            <i class="el-icon-warning-outline" style="font-size:24px"></i>
            <p>{{ playerError }}</p>
          </div>
        </template>
      </div>
    </div>
  </app-layout>
</template>

<script>
import { getRecordings } from '@/api/videoMonitor'
import flvjs from 'flv.js'

export default {
  name: 'VideoPlayback',
  data () {
    return {
      loading: false,
      loadError: false,
      recordings: [],
      groupMode: 'location',
      selectedFilter: '',
      showFilterDrop: false,
      currentFile: null,
      flvPlayer: null,
      playerError: '',
      expandedGroups: {}
    }
  },
  computed: {
    filterOptions () {
      return this.groupedRecordings.map(function (g) {
        return { label: g.label, value: g.label }
      })
    },
    selectedFilterLabel () {
      if (!this.selectedFilter) return '全部类别'
      return this.selectedFilter
    },
    filteredGroups () {
      if (!this.selectedFilter) return this.groupedRecordings
      return this.groupedRecordings.filter(function (g) {
        return g.label === this.selectedFilter
      }.bind(this))
    },
    groupedRecordings () {
      if (this.groupMode === 'location') {
        return this.recordings.map(function (g) {
          return { label: g.gate_name, files: g.files.map(function (f) { return Object.assign({}, f, { _gate_name: g.gate_name }) }) }
        })
      }
      const dateMap = {}
      this.recordings.forEach(function (g) {
        g.files.forEach(function (f) {
          const dateKey = f.datetime ? f.datetime.split(' ')[0] : '未知日期'
          if (!dateMap[dateKey]) dateMap[dateKey] = []
          dateMap[dateKey].push(Object.assign({}, f, { _gate_name: g.gate_name }))
        })
      })
      const keys = Object.keys(dateMap).sort().reverse()
      return keys.map(function (k) {
        return { label: k, files: dateMap[k] }
      })
    }
  },
  created () {
    this.fetchRecordings()
  },
  watch: {
    groupedRecordings () {
      const groups = {}
      this.groupedRecordings.forEach(function (_, idx) {
        groups[idx] = true
      })
      this.expandedGroups = groups
    },
    groupMode () {
      this.selectedFilter = ''
    }
  },
  beforeDestroy () {
    this.stopPlayback()
  },
  methods: {
    selectFilter (value) {
      this.selectedFilter = value
      this.showFilterDrop = false
    },
    async fetchRecordings () {
      this.loading = true
      try {
        const res = await getRecordings()
        if (res.code === 0 && res.data) {
          const self = this
          this.recordings = (res.data || []).map(function (g) {
            return Object.assign({}, g, {
              files: g.files.map(function (f) {
                if (!f.duration_text) {
                  const est = self._estimate_duration(f.file_size)
                  f.duration_text = est ? est + '分钟' : '未知'
                }
                if (!f.file_size_text) {
                  f.file_size_text = f.file_size ? (f.file_size / 1024 / 1024).toFixed(1) + 'MB' : '未知'
                }
                return f
              })
            })
          })
        }
      } catch (error) {
        console.error('Failed to fetch recordings:', error)
        this.loadError = true
      } finally {
        this.loading = false
      }
    },
    toggleGroup (idx) {
      this.$set(this.expandedGroups, idx, !this.expandedGroups[idx])
    },
    playRecording (file) {
      this.stopPlayback()
      this.currentFile = file
      this.playerError = ''
      this.$nextTick(function () {
        this.startFlvPlayback(file.url)
      })
    },
    startFlvPlayback (url) {
      if (!flvjs.isSupported()) {
        this.playerError = '当前浏览器不支持FLV播放'
        return
      }
      const videoElement = this.$refs.videoPlayer
      if (!videoElement) return

      this.flvPlayer = flvjs.createPlayer({
        type: 'flv',
        url: url,
        isLive: false,
        hasAudio: false,
        hasVideo: true
      }, {
        enableWorker: false,
        enableStashBuffer: true,
        stashInitialSize: 1024,
        autoCleanupSourceBuffer: true,
        autoCleanupMaxBackDuration: 30,
        autoCleanupMinBackDuration: 10
      })
      this.flvPlayer.attachMediaElement(videoElement)
      this.flvPlayer.on(flvjs.Events.ERROR, function (errorType, errorDetail) {
        console.error('FLV player error:', errorType, errorDetail)
        this.playerError = '播放失败: ' + (errorDetail || errorType)
      }.bind(this))
      this.flvPlayer.load()
      this.flvPlayer.play().catch(function () {})
    },
    stopPlayback () {
      if (this.flvPlayer) {
        try {
          this.flvPlayer.pause()
          this.flvPlayer.unload()
          this.flvPlayer.detachMediaElement()
          this.flvPlayer.destroy()
        } catch (e) {
          // ignore
        }
        this.flvPlayer = null
      }
    },
    _estimate_duration (fileSize) {
      if (!fileSize) return null
      const bitrate = 1000 * 1024 / 8
      const seconds = fileSize / bitrate
      return Math.round(seconds / 60)
    }
  }
}
</script>

<style scoped>
.page-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: calc(100vh - 200px);
}

.playback-layout {
  display: flex;
  gap: 16px;
  flex: 1;
  overflow: hidden;
  min-height: 0;
}

.playback-left {
  width: 340px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  order: 1;
}

.playback-controls {
  flex-shrink: 0;
  margin-bottom: 14px;
}

.playback-list {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding-right: 4px;
}

.playback-list::-webkit-scrollbar {
  width: 4px;
}

.playback-list::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 2px;
}

.playback-list::-webkit-scrollbar-track {
  background: transparent;
}

.group-mode-tabs {
  display: flex;
  gap: 0;
  background: rgba(255, 255, 255, 0.04);
  border-radius: 8px;
  padding: 3px;
  border: 1px solid var(--dark-border-field);
  margin-bottom: 14px;
}

.mode-tab {
  flex: 1;
  padding: 6px 0;
  font-size: 12px;
  font-weight: 500;
  color: var(--dark-text-secondary);
  cursor: pointer;
  border-radius: 6px;
  text-align: center;
  transition: background 0.2s, color 0.2s;
  user-select: none;
}

.mode-tab:hover {
  color: var(--dark-text);
}

.mode-tab.is-active {
  background: var(--dark-accent);
  color: #fff;
}

.filter-bar {
  margin-bottom: 14px;
}

.custom-select {
  position: relative;
}

.select-trigger {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--dark-border-field);
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
  color: var(--dark-text);
  transition: border-color 0.2s;
}

.custom-select.is-open .select-trigger {
  border-color: var(--dark-accent-light);
}

.select-trigger i {
  font-size: 12px;
  color: var(--dark-text-secondary);
  transition: transform 0.2s;
}

.select-trigger i.is-reverse {
  transform: rotate(180deg);
}

.select-dropdown {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  right: 0;
  background: #0A0A0A;
  border: 1px solid var(--dark-border);
  border-radius: 8px;
  padding: 4px 0;
  z-index: 10;
  max-height: 200px;
  overflow-y: auto;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.5);
}

.select-option {
  padding: 8px 12px;
  font-size: 13px;
  color: var(--dark-text-secondary);
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}

.select-option:hover {
  background: rgba(255, 255, 255, 0.06);
  color: var(--dark-text);
}

.select-option.is-active {
  background: rgba(99, 102, 241, 0.1);
  color: var(--dark-accent-light);
}

.record-group {
  margin-bottom: 16px;
}

.group-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
  padding: 0 4px;
  cursor: pointer;
}

.group-name {
  flex: 1;
  min-width: 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--dark-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.group-arrow {
  margin-right: 6px;
  font-size: 12px;
  transition: transform 0.2s;
}

.group-arrow.is-expanded {
  transform: rotate(90deg);
}

.group-count {
  font-size: 12px;
  color: var(--dark-text-muted);
}

.card-grid {
  display: flex;
  flex-direction: column;
  gap: 8px;
  overflow: hidden;
}

.video-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: var(--dark-card);
  border: 1px solid var(--dark-border);
  border-radius: 12px;
  cursor: pointer;
  transition: background 0.2s, border-color 0.2s;
}

.video-card:hover {
  background: rgba(255, 255, 255, 0.04);
  border-color: rgba(255, 255, 255, 0.1);
}

.video-card.is-active {
  background: rgba(99, 102, 241, 0.08);
  border-color: rgba(99, 102, 241, 0.3);
}

.card-icon {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.04);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  color: var(--dark-text-secondary);
  flex-shrink: 0;
}

.video-card.is-active .card-icon {
  background: rgba(99, 102, 241, 0.15);
  color: var(--dark-accent-light);
}

.card-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.card-time {
  font-size: 13px;
  font-weight: 500;
  color: var(--dark-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.video-card.is-active .card-time {
  color: var(--dark-accent-light);
}

.card-meta {
  font-size: 12px;
  color: var(--dark-text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.retry-btn {
  margin-top: 12px;
  padding: 8px 20px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid var(--dark-border-field);
  border-radius: 8px;
  color: var(--dark-text-secondary);
  font-size: 13px;
  cursor: pointer;
  transition: background 0.2s, color 0.2s;
}

.retry-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: var(--dark-text);
}

.playback-player {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--dark-card);
  border-radius: 16px;
  border: 1px solid var(--dark-border);
  overflow: hidden;
  position: relative;
  min-height: 0;
  order: 2;
}

.player-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: var(--dark-text-muted);
  font-size: 14px;
}

.player-header {
  padding: 10px 16px;
  color: var(--dark-text);
  font-size: 14px;
  background: rgba(255, 255, 255, 0.03);
  border-bottom: 1px solid var(--dark-border);
  text-align: center;
}

.player-wrapper {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 8px;
  background: #000;
  min-height: 0;
}

.player-video {
  width: 100%;
  height: 100%;
  object-fit: contain;
  background: #000;
}

.player-error {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: var(--dark-orange);
  text-align: center;
  font-size: 14px;
}

.player-error p {
  margin-top: 8px;
}

@media (max-width: 1280px) {
  .playback-layout {
    flex-direction: column;
    flex: 1;
    overflow: hidden;
    min-height: 0;
  }

  .playback-left {
    order: 2;
    width: 100%;
    flex: 1;
    display: flex;
    flex-direction: column;
    min-height: 0;
  }

  .playback-controls {
    flex-shrink: 0;
    padding: 8px 0;
    background: #0A0A0A;
    position: sticky;
    top: 0;
    z-index: 10;
  }

  .playback-player {
    order: 1;
    width: 100%;
    flex: none;
    flex-shrink: 0;
    aspect-ratio: 4 / 3;
  }

  .group-mode-tabs {
    margin-bottom: 8px;
  }

  .filter-bar {
    margin-bottom: 0;
  }

  .playback-list {
    flex: 1;
    overflow-y: auto;
    overflow-x: hidden;
    min-height: 0;
  }

  .card-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
  }
}

@media (max-width: 1024px) {
  .card-grid {
    grid-template-columns: 1fr;
  }
}
</style>
