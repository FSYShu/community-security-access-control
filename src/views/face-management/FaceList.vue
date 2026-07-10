<template>
  <div class="face-list">
    <van-pull-refresh v-model="refreshing" @refresh="onRefresh">
      <van-list v-model="loading" :finished="finished" finished-text="没有更多了" @load="loadData">
        <van-cell v-for="item in list" :key="item.id" :title="item.person_name" :label="item.person_type" is-link>
          <template #right-icon>
            <van-tag :type="item.status === 'active' ? 'success' : 'danger'">
              {{ item.status === 'active' ? '启用' : '停用' }}
            </van-tag>
          </template>
        </van-cell>
      </van-list>
      <van-empty v-if="!loading && list.length === 0" description="暂无人脸数据" />
    </van-pull-refresh>
  </div>
</template>

<script>
import { getFaceList } from '@/api/face'

export default {
  name: 'FaceList',
  data () {
    return {
      list: [],
      loading: false,
      finished: false,
      refreshing: false,
      page: 1
    }
  },
  methods: {
    async loadData () {
      try {
        const res = await getFaceList({ page: this.page, per_page: 20 })
        const data = res.data && res.data.data ? res.data.data : res.data
        if (data && data.items) {
          if (this.page === 1) {
            this.list = data.items
          } else {
            this.list = this.list.concat(data.items)
          }
          this.finished = this.list.length >= data.total
        } else {
          this.finished = true
        }
      } catch (err) {
        this.finished = true
      } finally {
        this.loading = false
        this.refreshing = false
      }
    },
    onRefresh () {
      this.page = 1
      this.finished = false
      this.loadData()
    }
  }
}
</script>

<style scoped>
.face-list {
  padding: 12px;
}
</style>
