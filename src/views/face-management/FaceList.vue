<template>
  <div class="face-list">
    <van-pull-refresh v-model="refreshing" @refresh="onRefresh">
      <van-list v-model="loading" :finished="finished" finished-text="没有更多了" @load="loadData">
        <van-cell v-for="item in list" :key="item.id" :title="item.person_name" :label="typeMap[item.person_type] || item.person_type">
            <template #right-icon>
              <van-tag :type="item.status === 'active' ? 'success' : 'danger'" style="margin-right:8px">
                {{ item.status === 'active' ? '启用' : '停用' }}
              </van-tag>
              <van-button type="danger" size="mini" plain @click="onDelete(item)">删除</van-button>
            </template>
          </van-cell>
      </van-list>
      <van-empty v-if="!loading && list.length === 0" description="暂无人脸数据" />
    </van-pull-refresh>
  </div>
</template>

<script>
import { getFaceList, deleteFace } from '@/api/face'
import { Dialog, Toast } from 'vant'

export default {
  name: 'FaceList',
  data () {
    return {
      list: [],
      loading: false,
      finished: false,
      refreshing: false,
      page: 1,
      typeMap: {
        owner: '业主',
        blacklist: '黑名单'
      }
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
    },
    onDelete (item) {
      Dialog.confirm({
        title: '确认删除',
        message: '确定要删除「' + item.person_name + '」的人脸数据吗？'
      }).then(() => {
        this.doDelete(item.id)
      }).catch(() => {})
    },
    async doDelete (id) {
      try {
        await deleteFace(id)
        Toast.success('删除成功')
        this.onRefresh()
      } catch (err) {
        Toast.fail('删除失败')
      }
    }
  }
}
</script>

<style scoped>
.face-list {
  padding: 12px;
}

</style>
