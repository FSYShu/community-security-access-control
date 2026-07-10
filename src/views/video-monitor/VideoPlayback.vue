<template>
  <app-layout page-title="历史视频回放">
    <van-loading v-if="loading" class="page-loading" size="24px" vertical>加载中...</van-loading>
    <van-empty v-else-if="recordings.length === 0" description="暂无历史录像" />

    <template v-else>
      <van-collapse v-model="activeGroups">
        <van-collapse-item
          v-for="group in recordings"
          :key="group.push_key"
          :title="group.gate_name"
          :name="group.push_key"
        >
          <template #label>
            <span class="group-label">推流码: {{ group.push_key }} | {{ group.files.length }}段录像</span>
          </template>
          <van-cell
            v-for="file in group.files"
            :key="file.filename"
            clickable
            @click="playRecording(file)"
          >
            <template #title>
              <span class="file-time">{{ file.datetime }}</span>
            </template>
            <template #label>
              <span class="file-meta">{{ file.duration_text }} | {{ file.file_size_text }}</span>
            </template>
            <div class="file-actions">
              <van-icon name="delete-o" size="20" :style="{ color: 'var(--dark-danger)' }" class="action-icon" @click.stop="confirmDelete(file)" />
              <van-icon name="play-circle-o" size="20" :style="{ color: 'var(--dark-info)' }" />
            </div>
          </van-cell>
        </van-collapse-item>
      </van-collapse>
    </template>

    <van-popup
      v-model="showPlayer"
      position="bottom"
      :style="{ height: '70%' }"
      round
      closeable
      close-icon="cross"
      @close="stopPlayback"
    >
      <div class="player-popup">
        <div class="player-header">{{ currentFile ? currentFile.datetime : '' }}</div>
        <div class="player-wrapper">
          <video
            ref="videoPlayer"
            class="player-video"
            controls
            muted
          ></video>
        </div>
        <div v-if="playerError" class="player-error">
          <van-icon name="warning-o" size="24" />
          <p>{{ playerError }}</p>
        </div>
      </div>
    </van-popup>
  </app-layout>
</template>

<script>
import { getRecordings, deleteRecording } from '@/api/videoMonitor'
import flvjs from 'flv.js'

export default {
  name: 'VideoPlayback',
  data () {
    return {
      loading: false,
      recordings: [],
      activeGroups: [],
      showPlayer: false,
      currentFile: null,
      flvPlayer: null,
      playerError: ''
    }
  },
  created () {
    this.fetchRecordings()
  },
  beforeDestroy () {
    this.stopPlayback()
  },
  methods: {
    async fetchRecordings () {
      this.loading = true
      try {
        const res = await getRecordings()
        if (res.code === 0 && res.data) {
          this.recordings = res.data || []
          if (this.recordings.length > 0) {
            this.activeGroups = [this.recordings[0].push_key]
          }
        }
      } catch (error) {
        console.error('Failed to fetch recordings:', error)
      } finally {
        this.loading = false
      }
    },
    playRecording (file) {
      this.currentFile = file
      this.showPlayer = true
      this.playerError = ''
      this.$nextTick(function () {
        this.startFlvPlayback(file.url)
      })
    },
    startFlvPlayback (url) {
      this.stopPlayback()
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
        enableStashBuffer: false,
        autoCleanupSourceBuffer: true
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
    confirmDelete (file) {
      this.$dialog.confirm({
        title: '确认删除',
        message: '确定删除录像 ' + file.datetime + ' 吗？删除后不可恢复。'
      }).then(function () {
        this.doDelete(file)
      }.bind(this)).catch(function () {})
    },
    async doDelete (file) {
      try {
        const res = await deleteRecording(file.filename)
        if (res.code === 0) {
          this.$toast.success('删除成功')
          this.fetchRecordings()
        } else {
          this.$toast.fail(res.message || '删除失败')
        }
      } catch (error) {
        console.error('Failed to delete recording:', error)
        this.$toast.fail('删除失败')
      }
    }
  }
}
</script>

<style scoped>
.page-loading {
  display: flex;
  justify-content: center;
  padding: 40px 0;
}
.group-label {
  font-size: 12px;
  color: var(--dark-text-secondary);
}
.file-time {
  font-size: 14px;
  color: var(--dark-text);
}
.file-meta {
  font-size: 12px;
  color: var(--dark-text-secondary);
  margin-top: 2px;
}
.file-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}
.action-icon {
  cursor: pointer;
}
.player-popup {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #000;
}
.player-header {
  padding: 10px 16px;
  color: var(--dark-text);
  font-size: 14px;
  background: #1a1a1a;
  text-align: center;
}
.player-wrapper {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 8px;
}
.player-video {
  width: 100%;
  max-height: 100%;
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
</style>
