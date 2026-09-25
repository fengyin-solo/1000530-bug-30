import { computed, onMounted, ref } from 'vue'

import { request, readError } from '@/api/client'

export type StatItem = { label: string; value: number }
type PagePayload = {
  items: Record<string, string | number | null>[]
  total: number
  stats?: StatItem[]
}

/**
 * 所有模块列表页共用的取数逻辑：
 * - 与运营概览走同一套后端口径，列表里看到的条目数和概览待处理量一致；
 * - 取数失败时先展示错误说明并给出「重试」按钮，不会静默把列表清空成“查无数据”；
 * - 统计卡片取列表同一次响应里的 stats，其他入口的统计与表格保持同步。
 */
export function useModuleList(options: {
  endpoint: string
  fallbackStats: StatItem[]
  loadError: string
}) {
  const rows = ref<Record<string, string | number | null>[]>([])
  const total = ref(0)
  const stats = ref<StatItem[]>(options.fallbackStats.map((item) => ({ ...item })))
  const filters = ref<Record<string, string>>({})
  const loading = ref(false)
  const failed = ref(false)
  const errorMessage = ref('')

  const queryString = computed(() => {
    // URLSearchParams 会把空输入序列化成 key=，后端按“未传”处理
    return new URLSearchParams(filters.value as Record<string, string>).toString()
  })

  async function reload() {
    loading.value = true
    failed.value = false
    errorMessage.value = ''
    try {
      const response = await request(`${options.endpoint}?${queryString.value}`)
      if (!response.ok) {
        throw await readError(response, options.loadError)
      }
      const payload = (await response.json()) as PagePayload
      rows.value = payload.items ?? []
      total.value = payload.total ?? rows.value.length
      if (Array.isArray(payload.stats) && payload.stats.length) {
        stats.value = payload.stats
      }
    } catch (error) {
      // 失败时保留上一次的数据，仅给出说明与重试入口
      failed.value = true
      errorMessage.value = error instanceof Error ? error.message : options.loadError
    } finally {
      loading.value = false
    }
  }

  function resetFilters() {
    filters.value = {}
    void reload()
  }

  onMounted(reload)

  return {
    rows,
    total,
    stats,
    filters,
    loading,
    failed,
    errorMessage,
    reload,
    resetFilters,
  }
}
