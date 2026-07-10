import * as videoMonitorApi from '@/api/videoMonitor'

describe('videoMonitor.js API', () => {
  it('should export getMonitorList function', () => {
    expect(typeof videoMonitorApi.getMonitorList).toBe('function')
  })

  it('should export getVideoPlayback function', () => {
    expect(typeof videoMonitorApi.getVideoPlayback).toBe('function')
  })

  it('should export getStreamList function', () => {
    expect(typeof videoMonitorApi.getStreamList).toBe('function')
  })
})
