<template>
  <div class="pass-result" :class="resultClass">
    <div class="result-icon">
      <i :class="passed ? 'el-icon-circle-check' : 'el-icon-close'" style="font-size:64px"></i>
    </div>
    <div class="result-title">{{ passed ? '认证通过' : '认证失败' }}</div>
    <div v-if="!passed && reason" class="result-reason">{{ reason }}</div>
    <div v-if="passed && personName" class="result-name">{{ personName }}</div>
  </div>
</template>

<script>
export default {
  name: 'PassResult',
  props: {
    passed: {
      type: Boolean,
      default: false
    },
    reason: {
      type: String,
      default: ''
    },
    personName: {
      type: String,
      default: ''
    }
  },
  computed: {
    resultClass () {
      return this.passed ? 'result-success' : 'result-fail'
    }
  }
}
</script>

<style scoped>
.pass-result {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 32px 16px;
  border-radius: var(--gate-radius);
  animation: fadeIn 0.3s ease;
}
@keyframes fadeIn {
  from { opacity: 0; transform: scale(0.9); }
  to { opacity: 1; transform: scale(1); }
}
.result-success {
  background: rgba(16, 185, 129, 0.1);
  border: 1px solid rgba(16, 185, 129, 0.3);
}
.result-success .result-icon {
  color: var(--gate-success);
}
.result-fail {
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
}
.result-fail .result-icon {
  color: var(--gate-danger);
}
.result-icon {
  margin-bottom: 16px;
}
.result-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--gate-text);
}
.result-reason {
  margin-top: 8px;
  font-size: 14px;
  color: var(--gate-text-secondary);
}
.result-name {
  margin-top: 8px;
  font-size: 16px;
  color: var(--gate-success);
  font-weight: 500;
}
</style>
