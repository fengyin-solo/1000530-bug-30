/** 运营概览与各模块统计卡片共用的取数入口：所有统计数字都来自 /api/overview。 */
import { fetchJson } from '@/api/client'

export type StatCard = { label: string; value: number }

export type OverviewModule = {
  name: string
  created: number
  pending: number
  abnormal: number
  stats: StatCard[]
}

export type Overview = {
  cards: StatCard[]
  modules: OverviewModule[]
}

export function fetchOverview(): Promise<Overview> {
  return fetchJson<Overview>('/api/overview')
}

/** 取某个模块的统计卡片；模块不存在时返回空数组，由调用方决定保留旧数据。 */
export async function fetchModuleStats(module: string): Promise<StatCard[]> {
  const payload = await fetchOverview()
  return payload.modules.find((item) => item.name === module)?.stats ?? []
}
