/** 统一请求封装：拼后端地址、抛网络错误、解析后端的可读错误说明。 */
const API_BASE = import.meta.env.VITE_API_BASE ?? ''

export function request(path: string, init?: RequestInit): Promise<Response> {
  const url = path.startsWith('http') ? path : `${API_BASE}${path}`
  return fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  }).catch((error: unknown) => {
    const detail = error instanceof Error ? error.message : '请求未送达'
    throw new Error(`接口请求失败：${detail}`)
  })
}

/** 从非 2xx 响应里取出后端 detail，没有时回退到状态码说明。 */
export async function readError(response: Response, fallback: string): Promise<Error> {
  try {
    const data = (await response.json()) as { detail?: unknown }
    if (typeof data.detail === 'string' && data.detail) {
      return new Error(data.detail)
    }
  } catch {
    // 响应体不是 JSON，按通用说明处理
  }
  return new Error(`${fallback}（接口返回 ${response.status}）`)
}

export async function fetchJson<T>(path: string): Promise<T> {
  const response = await request(path)
  if (!response.ok) {
    throw await readError(response, '数据未更新')
  }
  return (await response.json()) as T
}
