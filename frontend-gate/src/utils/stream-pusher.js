var STREAM_INTERVAL = 200
var UPLOAD_URL = '/api/v1/video-monitor/gate-push-frame'

function GateStreamPusher (videoElement, pushKey) {
  this.video = videoElement
  this.pushKey = pushKey
  this.canvas = document.createElement('canvas')
  this.ctx = this.canvas.getContext('2d')
  this.timer = null
  this.running = false
}

GateStreamPusher.prototype.start = function () {
  if (this.running || !this.pushKey) return
  this.running = true
  var self = this
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
  var video = this.video
  if (!video || !video.videoWidth || !this.pushKey) return

  this.canvas.width = video.videoWidth
  this.canvas.height = video.videoHeight
  this.ctx.drawImage(video, 0, 0)

  var dataUrl = this.canvas.toDataURL('image/jpeg', 0.7)
  var base64 = dataUrl.split(',')[1]

  var xhr = new XMLHttpRequest()
  xhr.open('POST', UPLOAD_URL, true)
  xhr.setRequestHeader('Content-Type', 'application/json')
  xhr.timeout = 3000
  xhr.send(JSON.stringify({
    push_key: this.pushKey,
    frame: base64
  }))
}

export default GateStreamPusher
