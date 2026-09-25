<template>
  <section class="page">
    <header class="page-head">
      <div>
        <h2>运营概览</h2>
        <p class="page-desc">汇总各业务模块的关键指标，先看总量再看异常。</p>
      </div>
    </header>

    <div v-if="failed" class="error-banner" role="alert">
      <span class="error-text">{{ errorMessage }}</span>
      <span class="error-hint">概览数据暂时无法加载，页面仍显示上次的内容；请检查后端服务后重试。</span>
      <button class="btn" type="button" :disabled="loading" @click="loadOverview">
        {{ loading ? '加载中…' : '重试' }}
      </button>
    </div>

    <div class="stat-row">
      <article v-for="card in cards" :key="card.label" class="stat-card">
        <span class="stat-label">{{ card.label }}</span>
        <strong class="stat-value">{{ card.value }}</strong>
      </article>
    </div>
    <table class="data-table">
      <thead>
        <tr><th>业务模块</th><th>今日新增</th><th>待处理</th><th>异常量</th></tr>
      </thead>
      <tbody>
        <tr v-for="row in moduleRows" :key="row.name">
          <td>{{ moduleLabel(row.name) }}</td>
          <td>{{ row.created }}</td>
          <td>{{ row.pending }}</td>
          <td>{{ row.abnormal }}</td>
        </tr>
      </tbody>
    </table>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'

import { fetchJson } from '@/api/client'
import { MODULE_LABELS } from '@/modules'

type Overview = {
  cards: { label: string; value: number }[]
  modules: { name: string; created: number; pending: number; abnormal: number }[]
}

// 首屏占位：结构与真实响应一致，数值为 0；取数失败时也沿用这份空态
const EMPTY: Overview = {
  cards: [
    { label: '业务模块', value: 0 },
    { label: '今日新增', value: 0 },
    { label: '待处理', value: 0 },
    { label: '异常量', value: 0 },
  ],
  modules: Object.keys(MODULE_LABELS).map((name) => ({
    name,
    created: 0,
    pending: 0,
    abnormal: 0,
  })),
}

const cards = ref<Overview['cards']>(EMPTY.cards)
const moduleRows = ref<Overview['modules']>(EMPTY.modules)
const loading = ref(false)
const failed = ref(false)
const errorMessage = ref('')

function moduleLabel(name: string): string {
  return MODULE_LABELS[name] ?? name
}

async function loadOverview() {
  loading.value = true
  failed.value = false
  errorMessage.value = ''
  try {
    const payload = await fetchJson<Overview>('/api/overview')
    cards.value = payload.cards
    moduleRows.value = payload.modules
  } catch (error) {
    // 先给出说明再允许重试：不清空成误导性的数字，只回落到全 0 空态
    failed.value = true
    errorMessage.value = error instanceof Error ? error.message : '运营概览读取失败'
    cards.value = EMPTY.cards
    moduleRows.value = EMPTY.modules
  } finally {
    loading.value = false
  }
}

onMounted(loadOverview)
</script>
