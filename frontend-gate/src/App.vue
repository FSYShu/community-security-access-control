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
  background: var(--gate-bg);
  color: var(--gate-text);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
</style>
