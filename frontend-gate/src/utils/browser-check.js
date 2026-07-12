function checkBrowserSupport () {
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    return {
      supported: false,
      message: '当前浏览器不支持摄像头调用，请使用Chrome、Firefox、Edge或Safari浏览器访问'
    }
  }
  return { supported: true, message: '' }
}

function checkHTTPS () {
  if (window.location.protocol === 'https:' || window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    return { secure: true, message: '' }
  }
  return {
    secure: false,
    message: '当前非安全连接，摄像头功能不可用，请通过HTTPS访问'
  }
}

export { checkBrowserSupport, checkHTTPS }