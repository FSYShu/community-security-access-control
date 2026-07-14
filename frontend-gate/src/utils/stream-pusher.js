const STREAM_INTERVAL = 33
const UPLOAD_URL = '/api/v1/video-monitor/gate-push-frame'

function GateStreamPusher (videoElement, pushKey) {
  this.video = videoElement
  this.pushKey = pushKey
  this.canvas = document.createElement('canvas')
  this.ctx = this.canvas.getContext('2d')
  this.timer = null
  this.running = false
  this.lastSendTime = 0
  this.pendingFrames = 0
  this.maxPendingFrames = 3
}

GateStreamPusher.prototype.start = function () {
  if (this.running || !this.pushKey) return
  this.running = true
  this.lastSendTime = Date.now()
  const self = this
  this.timer = setInterval(function () {
    self.captureAndSend()
  }, STREAM_INTERVAL)
}

GateStreamPusher.prototype.stop = function () {
  this.running = false
  if (this.timer) {
    clearInterval(this.timer)
    this.timer = null
  }
}

GateStreamPusher.prototype.captureAndSend = function () {
  const video = this.video
  if (!video || !video.videoWidth || !this.pushKey) return

  if (this.pendingFrames >= this.maxPendingFrames) {
    return
  }

  const targetWidth = Math.min(video.videoWidth, 1280)
  const scale = targetWidth / video.videoWidth
  const targetHeight = Math.round(video.videoHeight * scale)

  this.canvas.width = targetWidth
  this.canvas.height = targetHeight
  this.ctx.drawImage(video, 0, 0, targetWidth, targetHeight)

  const dataUrl = this.canvas.toDataURL('image/jpeg', 0.85)
  const base64 = dataUrl.split(',')[1]

  const self = this
  const xhr = new XMLHttpRequest()
  xhr.open('POST', UPLOAD_URL, true)
  xhr.setRequestHeader('Content-Type', 'application/json')
  xhr.timeout = 2000

  self.pendingFrames++

  xhr.onload = function () {
    self.pendingFrames = Math.max(0, self.pendingFrames - 1)
    self.lastSendTime = Date.now()
  }

  xhr.onerror = function () {
    self.pendingFrames = Math.max(0, self.pendingFrames - 1)
  }

  xhr.ontimeout = function () {
    self.pendingFrames = Math.max(0, self.pendingFrames - 1)
  }

  xhr.send(JSON.stringify({
    push_key: this.pushKey,
    frame: base64,
    ts: Date.now()
  }))
}

export default GateStreamPusher
