<template>
  <div id="gate-app">
    <router-view />
  </div>
</template>

<script>
export default {
  name: 'GateApp'
}
</script>

<style>
#gate-app {
  width: 100%;
  min-height: 100vh;
  background: #0f1117;
  color: #e5e7eb;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
</style>
