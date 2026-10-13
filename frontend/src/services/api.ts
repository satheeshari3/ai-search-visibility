export type Analysis = {
  id?: number
  analysis_id?: number
  url: string
  status: string
  created_at?: string
  updated_at?: string
}
export function getAnalysisId(analysis: Analysis): number {
  const id = analysis.analysis_id ?? analysis.id

  if (id === undefined || !Number.isFinite(id)) {
    throw new Error('The API response did not include a valid analysis ID.')
  }

  return id
}

const API_BASE = '/analyses/'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  })

  if (!response.ok) {
    const message = await response.text()
    throw new Error(
      message || `Request failed with status ${response.status}`,
    )
  }

  return response.json() as Promise<T>
}

export function createAnalysis(url: string): Promise<Analysis> {
  return request<Analysis>(API_BASE, {
    method: 'POST',
    body: JSON.stringify({ url }),
  })
}

export function getAnalysis(id: number): Promise<Analysis> {
  return request<Analysis>(`${API_BASE}${id}`)
}

export function getAnalysisReport(id: number): Promise<unknown> {
  return request<unknown>(`${API_BASE}${id}/report`)
}