<template>
  <section class="page" :data-module="meta.key">
    <header class="page-head">
      <div>
        <h2>{{ meta.label }}管理</h2>
        <p class="page-desc">
          维护{{ meta.entity }}，围绕{{ meta.filterFields.join('、') }}做登记、筛选与状态流转。
        </p>
      </div>
      <div class="page-actions">
        <button class="btn primary" type="button" @click="openCreate">登记{{ meta.entity }}</button>
        <button class="btn" type="button" @click="exportRows">导出{{ meta.label }}清单</button>
      </div>
    </header>

    <div class="stat-row">
      <article v-for="item in stats" :key="item.label" class="stat-card">
        <span class="stat-label">{{ item.label }}</span>
        <strong class="stat-value">{{ item.value }}</strong>
      </article>
    </div>

    <!-- 取数失败时先给说明，再允许重试；表格仍保留上次的数据 -->
    <div v-if="failed" class="filter-bar error-banner" role="alert">
      <span class="error-text">{{ errorMessage }}</span>
      <span class="error-hint">{{ meta.label }}列表暂时无法刷新，请检查服务后重试。</span>
      <button class="btn" type="button" :disabled="loading" @click="reload">
        {{ loading ? '加载中…' : '重试' }}
      </button>
    </div>

    <form class="filter-bar" @submit.prevent="reload">
      <label v-for="field in meta.filterFields" :key="field" class="filter-item">
        <span>{{ field }}</span>
        <input v-model="filters[field]" :placeholder="`按${field}检索`" />
      </label>
      <button class="btn" type="submit">查询</button>
      <button class="btn ghost" type="button" @click="resetFilters">重置条件</button>
    </form>

    <table class="data-table">
      <thead>
        <tr>
          <th v-for="column in meta.columns" :key="column">{{ column }}</th>
          <th>可执行动作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="row in rows" :key="String(row.id)">
          <td v-for="column in meta.columns" :key="column">{{ row[column] ?? '—' }}</td>
          <td class="row-actions">
            <button
              v-for="action in meta.actions"
              :key="action"
              class="link"
              type="button"
              @click="runAction(action, row)"
            >
              {{ action }}
            </button>
          </td>
        </tr>
        <tr v-if="!loading && !rows.length">
          <td :colspan="meta.columns.length + 1" class="empty-state">
            {{ failed ? `${meta.label}数据加载失败，可点击上方重试` : `暂无${meta.label}数据，可先登记${meta.entity}` }}
          </td>
        </tr>
      </tbody>
    </table>

    <footer class="page-foot">
      <span>共 {{ total }} 条{{ meta.entity }}记录</span>
      <span v-if="actionMessage" :class="actionFailed ? 'error-text' : ''">{{ actionMessage }}</span>
    </footer>
  </section>
</template>

<script setup lang="ts">
import { ref } from 'vue'

import { readError, request } from '@/api/client'
import { useModuleList } from '@/composables/useModuleList'
import type { ModuleMeta } from '@/modules'

const props = defineProps<{ meta: ModuleMeta }>()

const endpoint = `/api/${props.meta.key}`

const {
  rows,
  total,
  stats,
  filters,
  loading,
  failed,
  errorMessage,
  reload,
  resetFilters,
} = useModuleList({
  endpoint,
  fallbackStats: props.meta.fallbackStats,
  loadError: `${props.meta.label}列表读取失败`,
})

const actionMessage = ref('')
const actionFailed = ref(false)

function exportRows() {
  window.open(`${endpoint}/export`, '_blank')
}

function openCreate() {
  actionFailed.value = true
  actionMessage.value = `${props.meta.entity}登记入口尚未接入审批流`
}

async function runAction(action: string, row: Record<string, string | number | null>) {
  actionMessage.value = ''
  actionFailed.value = false
  try {
    const response = await request(`${endpoint}/${row.id}/actions`, {
      method: 'POST',
      body: JSON.stringify({ action }),
    })
    const payload = (await response.json()) as { ok?: boolean; message?: string }
    if (!response.ok) {
      throw await readError(response, `${props.meta.label}动作未生效，请稍后重试`)
    }
    if (payload.ok === false) {
      throw new Error(payload.message || `${props.meta.label}动作未生效，请稍后重试`)
    }
    actionMessage.value = payload.message || '操作已生效'
    await reload()
  } catch (error) {
    actionFailed.value = true
    actionMessage.value = error instanceof Error ? error.message : `${props.meta.label}操作失败`
  }
}
</script>
