var STORAGE_KEY = 'gate_offline_queue'
var MAX_QUEUE_SIZE = 20

function getQueue () {
  try {
    var data = localStorage.getItem(STORAGE_KEY)
    return data ? JSON.parse(data) : []
  } catch (e) {
    return []
  }
}

function saveQueue (queue) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(queue))
  } catch (e) {
    // storage full
  }
}

function enqueue (item) {
  var queue = getQueue()
  if (queue.length >= MAX_QUEUE_SIZE) {
    queue.shift()
  }
  queue.push({
    data: item,
    timestamp: Date.now()
  })
  saveQueue(queue)
}

function dequeueAll () {
  var queue = getQueue()
  saveQueue([])
  return queue
}

function getQueueSize () {
  return getQueue().length
}

function setupOnlineHandler (submitFn) {
  window.addEventListener('online', function () {
    var queue = dequeueAll()
    queue.forEach(function (item) {
      if (submitFn) {
        submitFn(item.data)
      }
    })
  })
}

export { enqueue, dequeueAll, getQueueSize, setupOnlineHandler }