
import { useEffect, useState } from 'react'
import {
  Activity,
  ArrowUpRight,
  ChartNoAxesCombined,
  ChevronDown,
  CircleHelp,
  Globe,
  LayoutDashboard,
  Settings2,
  ShieldCheck,
  Sparkles,
} from 'lucide-react'
import {
  createAnalysis,
  getAnalysis,
  getAnalysisReport,
  type Analysis,
  getAnalysisId
} from './services/api'
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from 'recharts'

type MethodSummary = {
  questions_evaluated?: number
  average_precision_at_k?: number
  average_recall_at_k?: number
  average_reciprocal_rank?: number
  average_ndcg_at_k?: number
}

type ReportSummary = {
  pages_analyzed?: number
  questions_evaluated?: number
  evaluation_results?: number
  retrieval_methods?: number
  total_findings?: number
  findings_by_severity?: Record<string, number>
  total_recommendation?: number
  [key: string]: unknown
}

type Finding = {
  type: string
  severity: 'high' | 'medium' | 'low' | 'info'
  title: string
  evidence?: Record<string, unknown>
  recommendation?: string
}

type Recommendation = {
  id: string
  title: string
  priority: 'high' | 'medium' | 'low' | 'informational'
  why_it_matters: string
  evidence?: Record<string, unknown>
  actions?: string[]
  verification: string
  source_finding_type?: string
  source_finding_title?: string
  original_diagnostic_recommendation?: string
}

type ReportData = {
  summary: ReportSummary
  method_summary: Record<string, MethodSummary>
  findings: Finding[]
  recommendations: Recommendation[]
  [key: string]: unknown
}

const navigation = [
  { label: 'Overview', icon: LayoutDashboard },
  { label: 'Analyses', icon: ChartNoAxesCombined },
]

function App() {
  const [activePage, setActivePage] = useState('Overview')
  const [websiteUrl, setWebsiteUrl] = useState('')
  const [analysis, setAnalysis] = useState<Analysis | null>(null)
  const [report, setReport] = useState<ReportData | null>(null)
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [reportLoading, setReportLoading] = useState(false)

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()

    setError('')
    setReport(null)
    setAnalysis(null)
    setSubmitting(true)

    try {
      const result = await createAnalysis(websiteUrl.trim())
      setAnalysis(result)
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Unable to start the analysis. Please try again.',
      )
    } finally {
      setSubmitting(false)
    }
  }

  // Poll the backend while an analysis is queued or processing.

  useEffect(() => {
    if (
      !analysis ||
      !Number.isFinite(analysis.analysis_id ?? analysis.id) ||
      ['completed', 'failed'].includes(analysis.status.toLowerCase())
    ) {
      return
    }

    let active = true

    const poll = async () => {
      try {
        const analysisId = getAnalysisId(analysis)
        const latest = await getAnalysis(analysisId)

        if (active) {
          setAnalysis((previous) => {
            if (!previous) return latest

            return {
              ...latest,
              id: latest.id ?? previous.id,
              analysis_id: latest.analysis_id ?? previous.analysis_id,
              url: latest.url ?? previous.url,
            }
          })
        }
      } catch (err) {
        if (active) {
          setError(
            err instanceof Error
              ? `Could not refresh analysis status: ${err.message}`
              : 'Could not refresh analysis status.',
          )
        }
      }
    }

    void poll()
    const intervalId = window.setInterval(poll, 3000)

    return () => {
      active = false
      window.clearInterval(intervalId)
    }
  }, [analysis?.id, analysis?.analysis_id, analysis?.status])

  // Fetch the real report after the backend marks the analysis completed.
  useEffect(() => {
    if (!analysis || analysis.status.toLowerCase() !== 'completed') {
      return
    }

    let active = true
    setReportLoading(true)

    getAnalysisReport(getAnalysisId(analysis))
      .then((result) => {
        if (active && result && typeof result === 'object') {
          setReport(result as ReportData)
        }
      })
      .catch((err) => {
        if (active) {
          setError(
            err instanceof Error
              ? `Analysis completed, but the report could not be loaded: ${err.message}`
              : 'Analysis completed, but the report could not be loaded.',
          )
        }
      })
      .finally(() => {
        if (active) {
          setReportLoading(false)
        }
      })

    return () => {
      active = false
    }
  }, [analysis?.id, analysis?.analysis_id, analysis?.status])

  const status = analysis?.status.toLowerCase()
  const isProcessing =
    status === 'queued' ||
    status === 'processing' ||
    status === 'pending'

  const reportSummary = report?.summary ?? null

  const methodSummary = report?.method_summary ?? null

  const retrievalData: { method: string; mrr: number }[] = [
    { key: 'semantic', label: 'Semantic' },
    { key: 'lexical', label: 'Lexical' },
    { key: 'hybrid', label: 'Hybrid' },
    { key: 'hybrid_reranker', label: 'Hybrid + reranker' },
  ].flatMap(({ key, label }) => {
    const value = methodSummary?.[key]?.average_reciprocal_rank

    return typeof value === 'number'
      ? [{ method: label, mrr: value }]
      : []
  })

  const metricCards = [
    {
      label: 'Pages analyzed',
      key: 'pages_analyzed',
      note: 'Pages successfully crawled',
    },
    {
      label: 'Questions evaluated',
      key: 'questions_evaluated',
      note: 'Evaluation questions tested',
    },
    {
      label: 'Findings',
      key: 'total_findings',
      note: 'Evidence-backed diagnostics',
    },
    {
      label: 'Recommendations',
      key: 'total_recommendation',
      note: 'Prioritized next steps',
    },
  ]

  function getMetric(key: string): string {
    const value = reportSummary?.[key]
    return typeof value === 'number' || typeof value === 'string'
      ? String(value)
      : '—'
  }

  return (
    <div className="min-h-screen bg-[#f8f9fc] text-slate-900">
      <div className="flex min-h-screen">
        <aside className="hidden w-64 shrink-0 border-r border-slate-200 bg-white px-5 py-6 md:flex md:flex-col">
          <a href="/" className="mb-10 flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-950 text-white">
              <Sparkles size={21} />
            </div>
            <div>
              <p className="text-sm font-bold tracking-tight">Visibility AI</p>
              <p className="mt-0.5 text-xs text-slate-500">
                Search intelligence
              </p>
            </div>
          </a>

          <p className="mb-3 px-3 text-[10px] font-bold uppercase tracking-[0.18em] text-slate-400">
            Workspace
          </p>

          <nav className="space-y-1">
            {navigation.map(({ label, icon: Icon }) => (
              <button
                key={label}
                onClick={() => setActivePage(label)}
                className={`flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm font-medium transition ${
                  activePage === label
                    ? 'bg-slate-100 text-slate-950'
                    : 'text-slate-500 hover:bg-slate-50 hover:text-slate-900'
                }`}
              >
                <Icon size={18} />
                {label}
              </button>
            ))}
          </nav>

          <div className="mt-auto space-y-1">
            <button className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm text-slate-500 hover:bg-slate-50">
              <CircleHelp size={18} />
              Help center
            </button>
            <button className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm text-slate-500 hover:bg-slate-50">
              <Settings2 size={18} />
              Settings
            </button>
            <div className="mt-4 flex items-center gap-3 border-t border-slate-100 pt-5">
              <div className="flex h-9 w-9 items-center justify-center rounded-full bg-violet-100 text-sm font-bold text-violet-700">
                G
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-sm font-semibold">Guest workspace</p>
                <p className="text-xs text-slate-500">Personal project</p>
              </div>
              <ChevronDown size={16} className="text-slate-400" />
            </div>
          </div>
        </aside>

        <main className="min-w-0 flex-1">
          <header className="flex h-[72px] items-center justify-between border-b border-slate-200 bg-white px-5 sm:px-8">
            <div className="flex items-center gap-2 text-sm text-slate-500">
              <span>Workspace</span>
              <span>/</span>
              <span className="font-semibold text-slate-900">
                {activePage}
              </span>
            </div>
            <div className="flex items-center gap-2 rounded-full border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-600">
              <span
                className={`h-2 w-2 rounded-full ${
                  isProcessing
                    ? 'animate-pulse bg-amber-500'
                    : 'bg-emerald-500'
                }`}
              />
              {isProcessing ? 'Analysis in progress' : 'API connected'}
            </div>
          </header>

          <div className="mx-auto max-w-6xl px-5 py-8 sm:px-8 sm:py-10">
            <div className="mb-8 flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
              <div>
                <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-violet-100 bg-violet-50 px-3 py-1.5 text-xs font-semibold text-violet-700">
                  <Sparkles size={14} />
                  AI Search Visibility Intelligence
                </div>
                <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">
                  Understand your AI search visibility.
                </h1>
                <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-500 sm:text-base">
                  Analyze your website's content and evaluate how effectively
                  relevant information can be retrieved by AI-style search.
                </p>
              </div>
              <div className="hidden items-center gap-2 text-sm text-slate-500 lg:flex">
                <ShieldCheck size={17} />
                Evidence-led analysis
              </div>
            </div>

            <section className="relative overflow-hidden rounded-2xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
              <div className="absolute right-0 top-0 h-40 w-40 rounded-full bg-violet-100/60 blur-3xl" />

              <div className="relative">
                <div className="mb-5 flex items-center gap-2">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-violet-50 text-violet-700">
                    <Globe size={20} />
                  </div>
                  <div>
                    <h2 className="font-semibold">Analyze a website</h2>
                    <p className="mt-0.5 text-xs text-slate-500">
                      Start with a public website URL
                    </p>
                  </div>
                </div>

                <form
                  className="flex flex-col gap-3 sm:flex-row"
                  onSubmit={handleSubmit}
                >
                  <div className="flex min-w-0 flex-1 items-center gap-3 rounded-xl border border-slate-200 bg-white px-4 focus-within:border-violet-400 focus-within:ring-4 focus-within:ring-violet-50">
                    <Globe size={18} className="shrink-0 text-slate-400" />
                    <input
                      type="url"
                      required
                      value={websiteUrl}
                      onChange={(event) => setWebsiteUrl(event.target.value)}
                      placeholder="https://example.com"
                      className="h-12 min-w-0 flex-1 bg-transparent text-sm outline-none placeholder:text-slate-400"
                    />
                  </div>
                  <button
                    type="submit"
                    disabled={submitting || isProcessing}
                    className="flex h-12 items-center justify-center gap-2 rounded-xl bg-slate-950 px-6 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {submitting ? 'Submitting...' : 'Analyze website'}
                    <ArrowUpRight size={17} />
                  </button>
                </form>

                <p className="mt-3 text-xs leading-5 text-slate-400">
                  Analyze only websites you are authorized to inspect. Results
                  depend on the pages successfully crawled.
                </p>

                {error && (
                  <div
                    role="alert"
                    className="mt-4 whitespace-pre-wrap break-words rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700"
                  >
                    {error}
                  </div>
                )}

                {analysis && (
                  <div className="mt-5 rounded-xl border border-slate-200 bg-slate-50 p-4">
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <div>
                        <p className="text-sm font-semibold">
                          Analysis #{analysis.id}
                        </p>
                        <p className="mt-1 break-all text-xs text-slate-500">
                          {analysis.url}
                        </p>
                      </div>
                      <span className="rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold capitalize text-slate-700">
                        {analysis.status}
                      </span>
                    </div>

                    {isProcessing && (
                      <p className="mt-3 flex items-center gap-2 text-sm text-slate-600">
                        <Activity size={16} className="animate-pulse" />
                        Your website is being analyzed. Checking for updates
                        automatically...
                      </p>
                    )}

                    {status === 'completed' && (
                      <p className="mt-3 text-sm font-medium text-emerald-700">
                        Analysis completed. Your report has been requested
                        below.
                      </p>
                    )}

                    {status === 'failed' && (
                      <p className="mt-3 text-sm text-rose-700">
                        The backend reported that this analysis failed. Check
                        the backend logs for the reason.
                      </p>
                    )}
                  </div>
                )}
              </div>
            </section>

            <div className="mb-4 mt-10 flex items-center justify-between">
              <div>
                <h2 className="text-lg font-bold tracking-tight">
                  Your workspace
                </h2>
                <p className="mt-1 text-sm text-slate-500">
                  Results from your current analysis.
                </p>
              </div>
              <span className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs font-medium text-slate-500">
                <Activity size={14} className="mr-1.5 inline" />
                Live API data
              </span>
            </div>

            <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
              {metricCards.map((item) => (
                <div
                  key={item.label}
                  className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"
                >
                  <p className="text-sm font-medium text-slate-500">
                    {item.label}
                  </p>
                  <p className="mt-4 text-3xl font-bold tracking-tight text-slate-800">
                    {getMetric(item.key)}
                  </p>
                  <p className="mt-2 text-xs text-slate-400">{item.note}</p>
                </div>
              ))}
            </section>

            <section className="mt-6 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
              {reportLoading ? (
                <p className="text-sm text-slate-500">
                  Loading your report...
                </p>
              ) : report ? (
                <>
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <h2 className="text-xl font-bold text-slate-900">
                        AI Search Visibility Report
                      </h2>
                      <p className="mt-1 text-sm text-slate-500">
                        {analysis?.url} · Analysis #{getAnalysisId(analysis!)}
                      </p>
                    </div>

                    <span className="rounded-full bg-emerald-50 px-3 py-1 text-sm font-medium text-emerald-700">
                      Completed
                    </span>
                  </div>

                  <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
                    {metricCards.map((card) => {
                      const value =
                        reportSummary?.[card.key] ??
                        (card.key === 'total_findings'
                          ? reportSummary?.findings_count
                          : card.key === 'total_recommendation'
                            ? reportSummary?.recommendations_count
                            : undefined)

                      return (
                        <div
                          key={card.key}
                          className="rounded-xl border border-slate-200 p-4"
                        >
                          <p className="text-sm text-slate-500">{card.label}</p>
                          <p className="mt-2 text-2xl font-bold text-slate-900">
                            {typeof value === 'number' ? value : '—'}
                          </p>
                          <p className="mt-1 text-xs text-slate-500">{card.note}</p>
                        </div>
                      )
                    })}
                  </div>

                  <div className="mt-8">
                    <h3 className="text-lg font-semibold text-slate-900">
                      Retrieval performance
                    </h3>
                    <p className="mt-1 text-sm text-slate-500">
                      Mean Reciprocal Rank (MRR): higher means relevant content tends
                      to appear closer to the top of the results.
                    </p>

                    {retrievalData.length > 0 ? (
                      <div className="mt-4 h-72 w-full">
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart
                            data={retrievalData}
                            margin={{ top: 10, right: 20, left: 0, bottom: 10 }}
                          >
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="method" tick={{ fontSize: 11 }} />
                            <YAxis domain={[0, 1]} />
                            <Tooltip
                              formatter={(value) => [
                                Number(value).toFixed(2),
                                'MRR',
                              ]}
                            />
                            <Bar
                              dataKey="mrr"
                              fill="#7c3aed"
                              radius={[6, 6, 0, 0]}
                            />
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                    ) : (
                      <p className="mt-3 text-sm text-slate-500">
                        Retrieval metrics are not available.
                      </p>
                    )}
                  </div>

                  <div className="mt-8">
                    <h3 className="text-lg font-semibold text-slate-900">
                      Findings
                    </h3>

                    <div className="mt-4 space-y-3">
                      {report.findings?.length ? (
                        report.findings.map((finding, index) => (
                          <div
                            key={`${finding.type}-${index}`}
                            className="rounded-xl border border-slate-200 p-4"
                          >
                            <div className="flex flex-wrap items-center gap-2">
                              <span className="rounded-full bg-amber-50 px-2.5 py-1 text-xs font-medium capitalize text-amber-700">
                                {finding.severity}
                              </span>
                              <span className="text-xs text-slate-500">
                                {finding.type.replaceAll('_', ' ')}
                              </span>
                            </div>

                            <h4 className="mt-2 font-semibold text-slate-900">
                              {finding.title}
                            </h4>

                            <p className="mt-2 text-sm text-slate-600">
                              {finding.recommendation}
                            </p>

                            {finding.evidence && (
                              <details className="mt-3">
                                <summary className="cursor-pointer text-sm font-medium text-violet-700">
                                  View evidence
                                </summary>
                                <pre className="mt-2 overflow-auto rounded-lg bg-slate-50 p-3 text-xs text-slate-700">
                                  {JSON.stringify(finding.evidence, null, 2)}
                                </pre>
                              </details>
                            )}
                          </div>
                        ))
                      ) : (
                        <p className="text-sm text-slate-500">
                          No findings are available for this analysis.
                        </p>
                      )}
                    </div>
                  </div>

                  <div className="mt-8">
                    <h3 className="text-lg font-semibold text-slate-900">
                      Prioritized recommendations
                    </h3>

                    <div className="mt-4 space-y-3">
                      {report.recommendations?.length ? (
                        report.recommendations.map((recommendation) => (
                          <div
                            key={recommendation.id}
                            className="rounded-xl border border-slate-200 p-4"
                          >
                            <div className="flex flex-wrap items-center gap-2">
                              <span className="rounded-full bg-violet-50 px-2.5 py-1 text-xs font-medium capitalize text-violet-700">
                                {recommendation.priority}
                              </span>
                              <span className="text-xs text-slate-500">
                                {recommendation.id}
                              </span>
                            </div>

                            <h4 className="mt-2 font-semibold text-slate-900">
                              {recommendation.title}
                            </h4>

                            <p className="mt-2 text-sm text-slate-600">
                              {recommendation.why_it_matters}
                            </p>

                            <ul className="mt-3 list-disc space-y-1 pl-5 text-sm text-slate-600">
                              {recommendation.actions?.map((action, index) => (
                                <li key={index}>{action}</li>
                              ))}
                            </ul>

                            <p className="mt-3 text-sm text-slate-700">
                              <strong>How to verify:</strong>{' '}
                              {recommendation.verification}
                            </p>
                          </div>
                        ))
                      ) : (
                        <p className="text-sm text-slate-500">
                          No recommendations are available.
                        </p>
                      )}
                    </div>
                  </div>

                  <p className="mt-8 border-t border-slate-200 pt-4 text-xs leading-5 text-slate-500">
                    These metrics evaluate simulated retrieval over the crawled website
                    content. They do not directly measure visibility or citations in
                    ChatGPT, Gemini, or other external AI search products.
                  </p>

                  <details className="mt-4">
                    <summary className="cursor-pointer text-sm font-medium text-violet-700">
                      Inspect raw report data
                    </summary>
                    <pre className="mt-3 max-h-96 overflow-auto rounded-xl bg-slate-950 p-4 text-xs leading-5 text-slate-100">
                      {JSON.stringify(report, null, 2)}
                    </pre>
                  </details>
                </>
              ) : (
                <p className="text-sm text-slate-500">
                  Submit a website URL to generate your report.
                </p>
              )}
            </section>

            <footer className="mt-10 flex flex-col gap-2 border-t border-slate-200 pt-5 text-xs text-slate-400 sm:flex-row sm:items-center sm:justify-between">
              <span>Visibility AI · AI Search Visibility Intelligence</span>
              <span>
                Retrieval evaluation, not a guarantee of external AI citations.
              </span>
            </footer>
          </div>
        </main>
      </div>
    </div>
  )
}

export default App